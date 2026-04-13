from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ProjectionStatus:
    projection_key: str
    status: str
    last_event_id: str | None
    lag: int
    failed_messages: int
    updated_at: str
