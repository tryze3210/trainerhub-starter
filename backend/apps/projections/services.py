from __future__ import annotations

from apps.projections import selectors
from apps.workflows.tasks import rebuild_projection


class ProjectionService:
    def list_statuses(self) -> list[dict]:
        return selectors.list_projection_statuses()

    def rebuild(self, projection_key: str) -> dict:
        task = rebuild_projection(projection_key)
        return {'projection_key': projection_key, 'status': 'rebuild_requested', 'task': task}
