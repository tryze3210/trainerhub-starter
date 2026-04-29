from __future__ import annotations

from dataclasses import asdict
from uuid import uuid4

from apps.events import selectors
from apps.events.models import DomainEvent, OutboxMessage


class DomainEventService:
    """In-process domain event service.

    This is intentionally lightweight for the modular-monolith stage: it gives
    workflows, diagnostics and API endpoints one stable contract without forcing
    us to introduce a database-backed outbox before the commercial flows settle.
    The public API mirrors a future persistent outbox implementation.
    """

    def emit(
        self,
        *,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        payload: dict,
        tenant_id: str | None = None,
    ) -> dict:
        event = DomainEvent(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=str(aggregate_id),
            payload=payload or {},
            tenant_id=tenant_id or None,
        )
        outbox_message = OutboxMessage(
            id=f"out_{uuid4().hex[:12]}",
            event_id=event.event_id,
            topic=event.event_type,
            status="pending",
            attempts=0,
            payload=asdict(event),
            next_retry_at=None,
        )
        selectors.OUTBOX_MESSAGES.insert(0, outbox_message)
        return {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "aggregate_type": event.aggregate_type,
            "aggregate_id": event.aggregate_id,
            "tenant_id": event.tenant_id,
            "payload": event.payload,
            "outbox_message_id": outbox_message.id,
            "status": "accepted",
        }

    def list_outbox(self) -> list[dict]:
        return [asdict(item) for item in selectors.list_outbox_messages()]

    def list_inbox(self) -> list[dict]:
        return [asdict(item) for item in selectors.list_inbox_messages()]


def emit_event(*, event_name: str, aggregate_type: str, aggregate_id: str, payload: dict) -> dict:
    """Legacy contract used by older tests/integration snippets."""
    return DomainEventService().emit(
        event_type=event_name,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload=payload,
    ) | {"event_name": event_name}
