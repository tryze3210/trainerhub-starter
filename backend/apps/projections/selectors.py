from __future__ import annotations

from dataclasses import asdict

from apps.projections.models import ProjectionStatus

PROJECTION_STATUSES = [
    ProjectionStatus('public_catalog', 'healthy', 'evt_2', 0, 0, '2026-04-09T11:15:00Z'),
    ProjectionStatus('trainer_profile_stats', 'degraded', 'evt_7', 4, 1, '2026-04-09T11:13:00Z'),
]


def list_projection_statuses() -> list[dict]:
    return [asdict(item) for item in PROJECTION_STATUSES]
