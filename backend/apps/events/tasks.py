from __future__ import annotations

from typing import Any

from celery import shared_task
from django.conf import settings

from apps.events.health import get_outbox_health
from apps.events.services import DomainEventService


def _positive_int(value: Any, *, default: int, minimum: int = 1, maximum: int = 10000) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(parsed, maximum))


@shared_task(
    name='apps.events.tasks.dispatch_pending_outbox_task',
    bind=True,
    acks_late=True,
    ignore_result=False,
)
def dispatch_pending_outbox_task(self, *, batch_size: int | None = None, max_batches: int | None = None) -> dict[str, Any]:
    """Dispatch pending outbox messages in bounded batches.

    This task is intentionally bounded. Celery Beat should run it frequently;
    the task itself must not run forever because that makes deploys, retries and
    shutdowns unsafe. For an always-on worker use Beat with a short interval.
    """

    size = _positive_int(
        batch_size,
        default=getattr(settings, 'CELERY_OUTBOX_DISPATCH_BATCH_SIZE', 100),
        minimum=1,
        maximum=1000,
    )
    batches = _positive_int(
        max_batches,
        default=getattr(settings, 'CELERY_OUTBOX_DISPATCH_MAX_BATCHES', 5),
        minimum=1,
        maximum=100,
    )

    service = DomainEventService()
    summary = {
        'task_id': getattr(self.request, 'id', None),
        'batch_size': size,
        'max_batches': batches,
        'batches': 0,
        'claimed': 0,
        'processed': 0,
        'failed': 0,
        'stopped_reason': 'max_batches_reached',
    }

    for _ in range(batches):
        result = service.dispatch_pending_batch(batch_size=size)
        summary['batches'] += 1
        summary['claimed'] += int(result.get('claimed', 0))
        summary['processed'] += int(result.get('processed', 0))
        summary['failed'] += int(result.get('failed', 0))
        if int(result.get('claimed', 0)) == 0:
            summary['stopped_reason'] = 'empty_batch'
            break

    return summary


@shared_task(
    name='apps.events.tasks.requeue_stuck_outbox_task',
    bind=True,
    acks_late=True,
    ignore_result=False,
)
def requeue_stuck_outbox_task(
    self,
    *,
    older_than_minutes: int | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Return stale processing messages back to pending for another worker."""

    service = DomainEventService()
    result = service.requeue_stuck_processing(
        older_than_minutes=_positive_int(
            older_than_minutes,
            default=getattr(settings, 'CELERY_OUTBOX_REQUEUE_OLDER_THAN_MINUTES', 15),
            minimum=1,
            maximum=1440,
        ),
        limit=_positive_int(
            limit,
            default=getattr(settings, 'CELERY_OUTBOX_REQUEUE_LIMIT', 100),
            minimum=1,
            maximum=1000,
        ),
    )
    result['task_id'] = getattr(self.request, 'id', None)
    return result


@shared_task(
    name='apps.events.tasks.outbox_healthcheck_task',
    bind=True,
    acks_late=False,
    ignore_result=False,
)
def outbox_healthcheck_task(self, *, fail_on_unhealthy: bool = False) -> dict[str, Any]:
    """Periodic outbox health snapshot for Celery result backend / monitoring."""

    health = get_outbox_health(
        max_pending_age_minutes=getattr(settings, 'CELERY_OUTBOX_HEALTH_MAX_PENDING_AGE_MINUTES', 15),
        max_processing_age_minutes=getattr(settings, 'CELERY_OUTBOX_HEALTH_MAX_PROCESSING_AGE_MINUTES', 15),
        max_dead_messages=getattr(settings, 'CELERY_OUTBOX_HEALTH_MAX_DEAD_MESSAGES', 0),
        max_failed_messages=getattr(settings, 'CELERY_OUTBOX_HEALTH_MAX_FAILED_MESSAGES', 50),
    )
    health['task_id'] = getattr(self.request, 'id', None)
    if fail_on_unhealthy and not health.get('ok'):
        raise RuntimeError(f"Outbox health is {health.get('status')}: {health.get('reasons')}")
    return health
