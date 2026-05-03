from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.events.models import OutboxMessage
from apps.events.services import DomainEventService
from apps.events.tasks import (
    dispatch_pending_outbox_task,
    outbox_healthcheck_task,
    requeue_stuck_outbox_task,
)


@pytest.mark.django_db
def test_dispatch_pending_outbox_task_processes_bounded_batch():
    emitted = DomainEventService().emit(
        event_type='order.completed',
        aggregate_type='order',
        aggregate_id='order-celery-001',
        payload={'user_id': None, 'amount': '100.00'},
        idempotency_key='order:order-celery-001:completed',
    )

    result = dispatch_pending_outbox_task(batch_size=10, max_batches=2)

    assert result['claimed'] == 1
    assert result['processed'] == 1
    assert result['failed'] == 0
    assert OutboxMessage.objects.get(pk=emitted['outbox_message_id']).status == OutboxMessage.Status.PROCESSED


@pytest.mark.django_db
def test_requeue_stuck_outbox_task_returns_processing_message_to_pending():
    emitted = DomainEventService().emit(
        event_type='payment.succeeded',
        aggregate_type='payment',
        aggregate_id='pay-celery-stuck-001',
        payload={'amount': '49.00'},
        idempotency_key='payment:pay-celery-stuck-001:succeeded',
    )
    message = OutboxMessage.objects.get(pk=emitted['outbox_message_id'])
    message.status = OutboxMessage.Status.PROCESSING
    message.locked_at = timezone.now() - timedelta(minutes=30)
    message.save(update_fields=['status', 'locked_at', 'updated_at'])

    result = requeue_stuck_outbox_task(older_than_minutes=15, limit=10)

    assert result['requeued'] == 1
    message.refresh_from_db()
    assert message.status == OutboxMessage.Status.PENDING
    assert message.locked_at is None


@pytest.mark.django_db
def test_outbox_healthcheck_task_returns_snapshot():
    result = outbox_healthcheck_task()

    assert result['status'] in {'ok', 'degraded', 'critical'}
    assert 'outbox' in result
    assert 'inbox' in result
    assert 'events' in result
