from __future__ import annotations

from dataclasses import asdict
from uuid import uuid4

from apps.events import selectors
from apps.events.models import DomainEvent, OutboxMessage


class DomainEventService:
    def emit(self, *, event_type: str, aggregate_type: str, aggregate_id: str, payload: dict, tenant_id: str | None = None) -> dict:
        event = DomainEvent(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload,
            tenant_id=tenant_id,
        )
        message = OutboxMessage(
            id=f'out_{uuid4().hex[:10]}',
            event_id=event.event_id,
            topic=event.event_type,
            status='pending',
            attempts=0,
            payload={'event': asdict(event)},
            next_retry_at=None,
        )
        selectors.OUTBOX_MESSAGES.insert(0, message)
        return {
            'event': asdict(event),
            'outbox_message': asdict(message),
            'status': 'queued',
        }

    def list_outbox(self) -> list[dict]:
        return [asdict(item) for item in selectors.list_outbox_messages()]

    def list_inbox(self) -> list[dict]:
        return [asdict(item) for item in selectors.list_inbox_messages()]
