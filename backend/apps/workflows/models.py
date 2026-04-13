from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class WorkflowRun:
    id: str
    workflow_key: str
    subject_type: str
    subject_id: str
    status: str
    current_step: str
    tenant_id: str | None
    context: dict[str, Any]
