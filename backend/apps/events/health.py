from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.db.models import Count, Q
from django.utils import timezone

from apps.events.models import DomainEvent, InboxMessage, OutboxMessage


def _iso(value) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _age_seconds(value, *, now) -> int | None:
    if value is None:
        return None
    return max(0, int((now - value).total_seconds()))


def get_outbox_health(
    *,
    max_pending_age_minutes: int = 15,
    max_processing_age_minutes: int = 15,
    max_dead_messages: int = 0,
    max_failed_messages: int = 50,
) -> dict[str, Any]:
    """Return an operator-friendly health snapshot for the event outbox.

    This function is intentionally read-only. It is safe to use from HTTP
    health endpoints, Docker healthchecks, cron, CI smoke checks and manual
    management commands.
    """

    now = timezone.now()
    pending_age_limit = max(1, int(max_pending_age_minutes))
    processing_age_limit = max(1, int(max_processing_age_minutes))
    dead_limit = max(0, int(max_dead_messages))
    failed_limit = max(0, int(max_failed_messages))

    pending_queryset = OutboxMessage.objects.filter(status=OutboxMessage.Status.PENDING)
    failed_queryset = OutboxMessage.objects.filter(status=OutboxMessage.Status.FAILED)
    processing_queryset = OutboxMessage.objects.filter(status=OutboxMessage.Status.PROCESSING)
    dead_queryset = OutboxMessage.objects.filter(status=OutboxMessage.Status.DEAD)

    oldest_pending = pending_queryset.order_by('created_at').first()
    oldest_failed = failed_queryset.order_by('updated_at').first()
    latest_processed = (
        OutboxMessage.objects
        .filter(status=OutboxMessage.Status.PROCESSED, processed_at__isnull=False)
        .order_by('-processed_at')
        .first()
    )

    processing_cutoff = now - timedelta(minutes=processing_age_limit)
    pending_cutoff = now - timedelta(minutes=pending_age_limit)

    stuck_processing_count = processing_queryset.filter(
        Q(locked_at__isnull=True) | Q(locked_at__lte=processing_cutoff)
    ).count()
    stale_pending_count = pending_queryset.filter(created_at__lte=pending_cutoff).count()

    status_counts = {
        row['status']: row['count']
        for row in OutboxMessage.objects.values('status').annotate(count=Count('id'))
    }
    for status_value in OutboxMessage.Status.values:
        status_counts.setdefault(status_value, 0)

    dead_count = int(status_counts[OutboxMessage.Status.DEAD])
    failed_count = int(status_counts[OutboxMessage.Status.FAILED])

    reasons: list[str] = []
    severity = 'ok'

    if dead_count > dead_limit:
        severity = 'critical'
        reasons.append(f'dead messages exceed limit: {dead_count} > {dead_limit}')

    if stuck_processing_count > 0:
        severity = 'critical'
        reasons.append(f'stuck processing messages detected: {stuck_processing_count}')

    if stale_pending_count > 0 and severity != 'critical':
        severity = 'degraded'
        reasons.append(f'stale pending messages detected: {stale_pending_count}')
    elif stale_pending_count > 0:
        reasons.append(f'stale pending messages detected: {stale_pending_count}')

    if failed_count > failed_limit and severity != 'critical':
        severity = 'degraded'
        reasons.append(f'failed messages exceed limit: {failed_count} > {failed_limit}')
    elif failed_count > failed_limit:
        reasons.append(f'failed messages exceed limit: {failed_count} > {failed_limit}')

    return {
        'status': severity,
        'ok': severity == 'ok',
        'checked_at': _iso(now),
        'thresholds': {
            'max_pending_age_minutes': pending_age_limit,
            'max_processing_age_minutes': processing_age_limit,
            'max_dead_messages': dead_limit,
            'max_failed_messages': failed_limit,
        },
        'reasons': reasons,
        'outbox': {
            'total': OutboxMessage.objects.count(),
            'status_counts': status_counts,
            'pending_count': int(status_counts[OutboxMessage.Status.PENDING]),
            'processing_count': int(status_counts[OutboxMessage.Status.PROCESSING]),
            'failed_count': failed_count,
            'dead_count': dead_count,
            'processed_count': int(status_counts[OutboxMessage.Status.PROCESSED]),
            'stale_pending_count': stale_pending_count,
            'stuck_processing_count': stuck_processing_count,
            'oldest_pending': {
                'id': str(oldest_pending.id),
                'topic': oldest_pending.topic,
                'created_at': _iso(oldest_pending.created_at),
                'age_seconds': _age_seconds(oldest_pending.created_at, now=now),
            } if oldest_pending else None,
            'oldest_failed': {
                'id': str(oldest_failed.id),
                'topic': oldest_failed.topic,
                'updated_at': _iso(oldest_failed.updated_at),
                'age_seconds': _age_seconds(oldest_failed.updated_at, now=now),
                'last_error': oldest_failed.last_error[:500],
            } if oldest_failed else None,
            'latest_processed': {
                'id': str(latest_processed.id),
                'topic': latest_processed.topic,
                'processed_at': _iso(latest_processed.processed_at),
                'age_seconds': _age_seconds(latest_processed.processed_at, now=now),
            } if latest_processed else None,
        },
        'inbox': {
            'total': InboxMessage.objects.count(),
            'status_counts': {
                row['status']: row['count']
                for row in InboxMessage.objects.values('status').annotate(count=Count('id'))
            },
        },
        'events': {
            'total': DomainEvent.objects.count(),
            'latest_event_at': _iso(DomainEvent.objects.order_by('-occurred_at').values_list('occurred_at', flat=True).first()),
        },
    }
