from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class DiagnosticsCheck:
    key: str
    title: str
    status: str
    severity: str
    message: str
    owner: str
    updated_at: str = field(default_factory=utcnow_iso)


@dataclass(slots=True)
class DiagnosticsRun:
    id: str
    suite_key: str
    triggered_by: str
    status: str
    started_at: str = field(default_factory=utcnow_iso)
    completed_at: str | None = None
    checks: list[dict] = field(default_factory=list)
