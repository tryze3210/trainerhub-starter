from __future__ import annotations

try:
    from celery import shared_task
except Exception:  # pragma: no cover - Celery is optional in some local test runs.
    shared_task = None


def _capture(*, limit: int = 100, source: str = 'scheduled', correlation_id: str = 'celery:reconciliation_snapshot') -> dict:
    from apps.ops.reconciliation_snapshots import capture_reconciliation_snapshot

    return capture_reconciliation_snapshot(limit=limit, source=source, correlation_id=correlation_id)


if shared_task is not None:

    @shared_task(name='apps.ops.tasks.capture_reconciliation_snapshot_task', queue='ops')
    def capture_reconciliation_snapshot_task(limit: int = 100, source: str = 'scheduled') -> dict:
        return _capture(limit=limit, source=source)

else:

    def capture_reconciliation_snapshot_task(limit: int = 100, source: str = 'scheduled') -> dict:
        return _capture(limit=limit, source=source)
