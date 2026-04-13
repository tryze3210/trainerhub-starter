from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from uuid import uuid4

from apps.events.services import DomainEventService
from apps.ops import selectors
from apps.ops.models import DiagnosticsRun


class DiagnosticsService:
    event_service = DomainEventService()

    def snapshot(self) -> dict:
        checks = [asdict(item) for item in selectors.list_checks()]
        overall = 'degraded' if any(item['status'] == 'warning' for item in checks) else 'healthy'
        return {
            'overall_status': overall,
            'checks': checks,
            'recent_runs': [asdict(item) for item in selectors.list_runs()[:5]],
        }

    def run(self, *, suite_key: str, triggered_by: str = 'admin_console') -> dict:
        checks = [asdict(item) for item in selectors.list_checks()]
        run = DiagnosticsRun(
            id=f'diag_{uuid4().hex[:10]}',
            suite_key=suite_key,
            triggered_by=triggered_by,
            status='completed',
            completed_at=datetime.now(timezone.utc).isoformat(),
            checks=checks,
        )
        selectors.DIAGNOSTICS_RUNS.insert(0, run)
        self.event_service.emit(
            event_type='ops.diagnostics.run_completed',
            aggregate_type='diagnostics_run',
            aggregate_id=run.id,
            payload={'suite_key': suite_key, 'correlation_id': f'corr_diag_{run.id}'},
            tenant_id=None,
        )
        return {
            'run': asdict(run),
            'status': 'accepted',
        }
