from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class DomainEvent:
    event_type: str
    aggregate_type: str
    aggregate_id: str
    payload: dict[str, Any]
    tenant_id: str | None = None
    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: int = 1


@dataclass(slots=True)
class OutboxMessage:
    id: str
    event_id: str
    topic: str
    status: str
    attempts: int
    payload: dict[str, Any]
    next_retry_at: str | None = None


@dataclass(slots=True)
class InboxMessage:
    id: str
    consumer: str
    message_key: str
    status: str
    processed_at: str | None = None
