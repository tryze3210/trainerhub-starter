from __future__ import annotations

from dataclasses import asdict

from apps.events.services import DomainEventService
from apps.observability import selectors
from apps.workflows.services import WorkflowService


class ObservabilityService:
    event_service = DomainEventService()
    workflow_service = WorkflowService()

    def overview(self) -> dict:
        metrics = selectors.list_metrics()
        logs = selectors.list_logs()
        traces = selectors.list_traces()
        platform_health = 'degraded' if any(item.status in {'warning', 'error'} for item in metrics) else 'healthy'
        hot_correlations = [item.correlation_id for item in traces if item.correlation_id][:3]
        return {
            'generated_at': metrics[0].updated_at if metrics else None,
            'platform_health': platform_health,
            'counters': {
                'metrics': len(metrics),
                'logs': len(logs),
                'traces': len(traces),
                'outbox_pending': len([item for item in self.event_service.list_outbox() if item['status'] == 'pending']),
                'workflow_running': len([item for item in self.workflow_service.list_runs() if item['status'] in {'pending', 'running'}]),
            },
            'error_budget': {
                'window': '30d',
                'consumed_percent': 18.6,
                'remaining_percent': 81.4,
                'status': 'healthy',
            },
            'hot_correlations': hot_correlations,
        }

    def metrics(self) -> list[dict]:
        return [asdict(item) for item in selectors.list_metrics()]

    def logs(self) -> list[dict]:
        return [asdict(item) for item in selectors.list_logs()]

    def traces(self) -> list[dict]:
        return [asdict(item) for item in selectors.list_traces()]

    def correlation(self, correlation_id: str) -> dict:
        logs = [asdict(item) for item in selectors.list_logs() if item.correlation_id == correlation_id]
        traces = [asdict(item) for item in selectors.list_traces() if item.correlation_id == correlation_id]
        related_events = [item for item in self.event_service.list_outbox() if item['payload'].get('event', {}).get('payload', {}).get('correlation_id') == correlation_id]
        related_workflows = [item for item in self.workflow_service.list_runs() if item['context'].get('correlation_id') == correlation_id]
        related_projection_keys = sorted({item['tags'].get('projection_key') for item in traces if item['tags'].get('projection_key')})
        return {
            'correlation_id': correlation_id,
            'summary': {
                'logs_count': len(logs),
                'traces_count': len(traces),
                'related_events_count': len(related_events),
                'related_workflows_count': len(related_workflows),
            },
            'related_events': related_events,
            'related_workflows': related_workflows,
            'related_projection_keys': related_projection_keys,
            'logs': logs,
            'traces': traces,
        }
