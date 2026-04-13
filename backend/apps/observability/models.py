from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class MetricSample:
    key: str
    value: float
    unit: str
    status: str
    updated_at: str = field(default_factory=utcnow_iso)
    labels: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class LogRecord:
    id: str
    level: str
    service: str
    message: str
    correlation_id: str | None
    occurred_at: str = field(default_factory=utcnow_iso)
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TraceSpan:
    trace_id: str
    span_id: str
    parent_span_id: str | None
    operation: str
    service: str
    status: str
    duration_ms: int
    correlation_id: str | None
    started_at: str = field(default_factory=utcnow_iso)
    tags: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CorrelationView:
    correlation_id: str
    summary: dict[str, Any]
    related_events: list[dict[str, Any]]
    related_workflows: list[dict[str, Any]]
    related_projection_keys: list[str]
    logs: list[LogRecord]
    traces: list[TraceSpan]


@dataclass(slots=True)
class ObservabilityOverview:
    generated_at: str
    platform_health: str
    counters: dict[str, int]
    error_budget: dict[str, Any]
    hot_correlations: list[str]
