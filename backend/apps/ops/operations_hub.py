from __future__ import annotations

from collections.abc import Callable
from typing import Any

from django.utils import timezone

from apps.ops.operations import get_admin_operations_dashboard
from apps.ops.reconciliation_snapshots import (
    get_reconciliation_issue_registry,
    get_reconciliation_snapshot_alerts,
    get_reconciliation_snapshot_metrics,
    get_reconciliation_snapshot_schedule,
)


_STATUS_RANK = {
    'ok': 0,
    'healthy': 0,
    'missing': 1,
    'unavailable': 1,
    'degraded': 2,
    'warning': 2,
    'failed': 3,
    'critical': 3,
}


HUB_NAVIGATION = [
    {
        'key': 'operations',
        'title': 'Operations dashboard',
        'href': '/admin/operations',
        'description': 'Unified operations command center.',
    },
    {
        'key': 'reconciliation_report',
        'title': 'Live reconciliation report',
        'href': '/admin/reconciliation/report',
        'api_href': '/api/v1/ops/admin/reconciliation-report/',
        'description': 'On-demand report without persisting a snapshot.',
    },
    {
        'key': 'reconciliation_snapshots',
        'title': 'Reconciliation snapshots',
        'href': '/admin/reconciliation/snapshots',
        'api_href': '/api/v1/ops/admin/reconciliation-snapshots/',
        'description': 'Snapshot history, compare, metrics and retention.',
    },
    {
        'key': 'events_outbox',
        'title': 'Outbox operations',
        'href': '/admin/operations#outbox',
        'api_href': '/api/v1/events/outbox/',
        'description': 'Retry dead/failed outbox messages and drain backlog.',
    },
    {
        'key': 'payment_risk',
        'title': 'Payment risk',
        'href': '/admin/payment-risk',
        'description': 'Disputes, chargebacks, risk holds and payout protection.',
    },
]


HUB_ACTIONS = [
    {
        'key': 'capture_reconciliation_snapshot',
        'title': 'Capture reconciliation snapshot',
        'method': 'POST',
        'api_href': '/api/v1/ops/admin/reconciliation-snapshots/capture/',
        'risk': 'low',
        'description': 'Persist a manual reconciliation snapshot for current platform state.',
    },
    {
        'key': 'evaluate_reconciliation_alerts',
        'title': 'Evaluate reconciliation alerts',
        'method': 'GET',
        'api_href': '/api/v1/ops/admin/reconciliation-snapshots/alerts/',
        'risk': 'low',
        'description': 'Check whether snapshot trend should alert admins.',
    },
    {
        'key': 'preview_snapshot_retention',
        'title': 'Preview snapshot retention',
        'method': 'GET',
        'api_href': '/api/v1/ops/admin/reconciliation-snapshots/retention/',
        'risk': 'low',
        'description': 'Preview old snapshots eligible for pruning.',
    },
    {
        'key': 'dispatch_outbox',
        'title': 'Dispatch outbox batch',
        'method': 'POST',
        'api_href': '/api/v1/events/outbox/dispatch/',
        'risk': 'medium',
        'description': 'Claim and dispatch pending outbox messages.',
    },
    {
        'key': 'requeue_stuck_outbox',
        'title': 'Requeue stuck outbox messages',
        'method': 'POST',
        'api_href': '/api/v1/events/outbox/requeue-stuck/',
        'risk': 'medium',
        'description': 'Move stale processing messages back to pending.',
    },
]


def _now_iso() -> str:
    return timezone.now().isoformat()


def _rank(status: str | None) -> int:
    return _STATUS_RANK.get(str(status or 'missing'), 1)


def _worst_status(*statuses: str | None) -> str:
    ranked = sorted((str(status or 'missing') for status in statuses), key=_rank, reverse=True)
    return ranked[0] if ranked else 'missing'


def _safe_call(
    key: str,
    factory: Callable[..., dict[str, Any]],
    /,
    **kwargs: Any,
) -> dict[str, Any]:
    try:
        payload = factory(**kwargs)
        if not isinstance(payload, dict):
            return {
                'status': 'unavailable',
                'generated_at': _now_iso(),
                'key': key,
                'detail': 'Service returned non-dict payload.',
            }
        return payload
    except Exception as exc:  # pragma: no cover - defensive boundary for admin hub resilience.
        return {
            'status': 'unavailable',
            'generated_at': _now_iso(),
            'key': key,
            'detail': str(exc),
        }


def _section_status(base_dashboard: dict[str, Any], section_key: str) -> str:
    section = (base_dashboard.get('sections') or {}).get(section_key) or {}
    return str(section.get('status') or 'missing')


def _issue_counts_from_registry(registry: dict[str, Any]) -> dict[str, int]:
    summary = registry.get('summary') or {}
    return {
        'total': int(summary.get('total_count') or 0),
        'critical': int(summary.get('critical_count') or 0),
        'warning': int(summary.get('warning_count') or 0),
        'repairable': int(summary.get('repairable_count') or 0),
    }


def _summary(
    *,
    base_dashboard: dict[str, Any],
    reconciliation_metrics: dict[str, Any],
    reconciliation_alerts: dict[str, Any],
    issue_registry: dict[str, Any],
    schedule: dict[str, Any],
) -> dict[str, Any]:
    base_summary = base_dashboard.get('summary') or {}
    headline = reconciliation_metrics.get('headline') or {}
    issue_counts = _issue_counts_from_registry(issue_registry)
    alerts = reconciliation_alerts.get('alerts') or []

    return {
        'status': _worst_status(
            base_dashboard.get('status'),
            reconciliation_metrics.get('status'),
            'critical' if reconciliation_alerts.get('has_alerts') else 'ok',
            'degraded' if schedule.get('due') else schedule.get('status'),
        ),
        'operations_critical_count': int(base_summary.get('critical_count') or 0),
        'operations_warning_count': int(base_summary.get('warning_count') or 0),
        'reconciliation_total_issues': int(
            headline.get('current_total_issues')
            if headline.get('current_total_issues') is not None
            else issue_counts['total']
        ),
        'reconciliation_critical_count': int(
            headline.get('current_critical_count')
            if headline.get('current_critical_count') is not None
            else issue_counts['critical']
        ),
        'reconciliation_repairable_issues': issue_counts['repairable'],
        'reconciliation_alert_count': len(alerts),
        'scheduled_snapshot_due': bool(schedule.get('due')),
        'latest_reconciliation_snapshot_id': headline.get('latest_snapshot_id'),
        'latest_reconciliation_status': headline.get('latest_status') or reconciliation_metrics.get('status'),
        'latest_reconciliation_direction': headline.get('direction'),
    }


def get_admin_operations_hub(
    *,
    snapshot_limit: int = 30,
    issue_limit: int = 20,
    source: str = '',
    include_issues: bool = True,
    include_alerts: bool = True,
) -> dict[str, Any]:
    """Build a single payload for the admin operations command center.

    The hub is deliberately read-only and composes existing operations and
    reconciliation services. It does not introduce operational state and is safe
    to ship without migrations.
    """
    snapshot_limit = max(2, min(int(snapshot_limit or 30), 250))
    issue_limit = max(1, min(int(issue_limit or 20), 250))
    generated_at = timezone.now()

    base_dashboard = _safe_call('operations_dashboard', get_admin_operations_dashboard)
    reconciliation_metrics = _safe_call(
        'reconciliation_metrics',
        get_reconciliation_snapshot_metrics,
        limit=snapshot_limit,
        source=source,
    )
    schedule = _safe_call(
        'reconciliation_schedule',
        get_reconciliation_snapshot_schedule,
        source='scheduled',
        min_age_minutes=60,
    )
    reconciliation_alerts = (
        _safe_call('reconciliation_alerts', get_reconciliation_snapshot_alerts, source=source)
        if include_alerts
        else {'status': 'skipped', 'alerts': [], 'has_alerts': False}
    )
    issue_registry = (
        _safe_call(
            'reconciliation_issue_registry',
            get_reconciliation_issue_registry,
            source=source,
            limit=issue_limit,
            include_report=False,
        )
        if include_issues
        else {'status': 'skipped', 'issues': [], 'summary': {'total_count': 0, 'repairable_count': 0}}
    )

    summary = _summary(
        base_dashboard=base_dashboard,
        reconciliation_metrics=reconciliation_metrics,
        reconciliation_alerts=reconciliation_alerts,
        issue_registry=issue_registry,
        schedule=schedule,
    )

    return {
        'status': summary['status'],
        'generated_at': generated_at,
        'filters': {
            'snapshot_limit': snapshot_limit,
            'issue_limit': issue_limit,
            'source': source,
            'include_issues': include_issues,
            'include_alerts': include_alerts,
        },
        'summary': summary,
        'sections': {
            'async_infra': {
                'status': _worst_status(_section_status(base_dashboard, 'outbox'), _section_status(base_dashboard, 'webhooks')),
                'outbox': (base_dashboard.get('sections') or {}).get('outbox') or {},
                'webhooks': (base_dashboard.get('sections') or {}).get('webhooks') or {},
            },
            'money_risk': {
                'status': _worst_status(
                    _section_status(base_dashboard, 'payments'),
                    _section_status(base_dashboard, 'payouts'),
                    _section_status(base_dashboard, 'moderation'),
                ),
                'payments': (base_dashboard.get('sections') or {}).get('payments') or {},
                'payouts': (base_dashboard.get('sections') or {}).get('payouts') or {},
                'moderation': (base_dashboard.get('sections') or {}).get('moderation') or {},
            },
            'reconciliation': {
                'status': _worst_status(
                    reconciliation_metrics.get('status'),
                    'critical' if reconciliation_alerts.get('has_alerts') else 'ok',
                    'degraded' if schedule.get('due') else schedule.get('status'),
                ),
                'metrics': reconciliation_metrics,
                'schedule': schedule,
                'alerts': reconciliation_alerts,
                'issue_registry': issue_registry,
            },
        },
        'raw_operations_dashboard': base_dashboard,
        'quick_actions': HUB_ACTIONS,
        'navigation': HUB_NAVIGATION,
    }
