from __future__ import annotations

from apps.events.services import DomainEventService


def dispatch_outbox_batch(batch_size: int = 100) -> dict:
    """Dispatch pending outbox messages.

    Uses the events dispatcher registry by default. Built-in handlers record
    idempotent InboxMessage projections; production integrations can register
    external adapters without changing the task contract.
    """
    return {
        'status': 'completed',
        'task': 'dispatch_outbox_batch',
        'batch_size': batch_size,
        **DomainEventService().dispatch_pending_batch(batch_size=batch_size),
    }


def rebuild_projection(projection_key: str) -> dict:
    return {'status': 'scheduled', 'task': 'rebuild_projection', 'projection_key': projection_key}
