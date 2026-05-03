from __future__ import annotations

from typing import Any

from django.db.models import QuerySet

from apps.events.models import DomainEvent, InboxMessage, OutboxMessage


def _dt(value) -> str | None:
    return value.isoformat() if value else None


def serialize_domain_event(event: DomainEvent) -> dict[str, Any]:
    return {
        'id': str(event.id),
        'event_type': event.event_type,
        'aggregate_type': event.aggregate_type,
        'aggregate_id': event.aggregate_id,
        'tenant_id': event.tenant_id,
        'payload': event.payload or {},
        'metadata': event.metadata or {},
        'idempotency_key': event.idempotency_key,
        'version': event.version,
        'occurred_at': _dt(event.occurred_at),
        'created_at': _dt(event.created_at),
        'updated_at': _dt(event.updated_at),
    }


def serialize_outbox_message(message: OutboxMessage) -> dict[str, Any]:
    event = getattr(message, 'event', None)
    return {
        'id': str(message.id),
        'event_id': str(message.event_id),
        'event_type': event.event_type if event else None,
        'aggregate_type': event.aggregate_type if event else None,
        'aggregate_id': event.aggregate_id if event else None,
        'topic': message.topic,
        'status': message.status,
        'attempts': message.attempts,
        'max_attempts': message.max_attempts,
        'payload': message.payload or {},
        'next_retry_at': _dt(message.next_retry_at),
        'locked_at': _dt(message.locked_at),
        'processed_at': _dt(message.processed_at),
        'last_error': message.last_error,
        'created_at': _dt(message.created_at),
        'updated_at': _dt(message.updated_at),
    }


def serialize_inbox_message(message: InboxMessage) -> dict[str, Any]:
    return {
        'id': str(message.id),
        'consumer': message.consumer,
        'message_key': message.message_key,
        'status': message.status,
        'payload': message.payload or {},
        'received_at': _dt(message.received_at),
        'processed_at': _dt(message.processed_at),
        'last_error': message.last_error,
        'created_at': _dt(message.created_at),
        'updated_at': _dt(message.updated_at),
    }


def _cap_limit(limit: int) -> int:
    return max(1, min(int(limit), 500))


def domain_events_queryset(
    *,
    event_type: str | None = None,
    aggregate_type: str | None = None,
    aggregate_id: str | None = None,
    tenant_id: str | None = None,
    idempotency_key: str | None = None,
) -> QuerySet[DomainEvent]:
    queryset = DomainEvent.objects.order_by('-occurred_at', '-created_at')
    if event_type:
        queryset = queryset.filter(event_type=event_type)
    if aggregate_type:
        queryset = queryset.filter(aggregate_type=aggregate_type)
    if aggregate_id:
        queryset = queryset.filter(aggregate_id=str(aggregate_id))
    if tenant_id:
        queryset = queryset.filter(tenant_id=str(tenant_id))
    if idempotency_key:
        queryset = queryset.filter(idempotency_key=str(idempotency_key))
    return queryset


def outbox_queryset(
    *,
    status: str | None = None,
    topic: str | None = None,
    event_type: str | None = None,
    aggregate_type: str | None = None,
    aggregate_id: str | None = None,
) -> QuerySet[OutboxMessage]:
    queryset = OutboxMessage.objects.select_related('event').order_by('-created_at')
    if status:
        queryset = queryset.filter(status=status)
    if topic:
        queryset = queryset.filter(topic=topic)
    if event_type:
        queryset = queryset.filter(event__event_type=event_type)
    if aggregate_type:
        queryset = queryset.filter(event__aggregate_type=aggregate_type)
    if aggregate_id:
        queryset = queryset.filter(event__aggregate_id=str(aggregate_id))
    return queryset


def list_domain_events(
    *,
    event_type: str | None = None,
    aggregate_type: str | None = None,
    aggregate_id: str | None = None,
    tenant_id: str | None = None,
    idempotency_key: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    queryset = domain_events_queryset(
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        tenant_id=tenant_id,
        idempotency_key=idempotency_key,
    )
    return [serialize_domain_event(item) for item in queryset[:_cap_limit(limit)]]


def get_domain_event(event_id: str) -> dict[str, Any]:
    return serialize_domain_event(DomainEvent.objects.get(pk=event_id))


def list_outbox_messages(
    *,
    status: str | None = None,
    topic: str | None = None,
    event_type: str | None = None,
    aggregate_type: str | None = None,
    aggregate_id: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    queryset = outbox_queryset(
        status=status,
        topic=topic,
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
    )
    return [serialize_outbox_message(item) for item in queryset[:_cap_limit(limit)]]


def get_outbox_message(message_id: str) -> dict[str, Any]:
    return serialize_outbox_message(OutboxMessage.objects.select_related('event').get(pk=message_id))


def list_inbox_messages(*, consumer: str | None = None, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    queryset = InboxMessage.objects.order_by('-received_at', '-created_at')
    if consumer:
        queryset = queryset.filter(consumer=consumer)
    if status:
        queryset = queryset.filter(status=status)
    return [serialize_inbox_message(item) for item in queryset[:_cap_limit(limit)]]
