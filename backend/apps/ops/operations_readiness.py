from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any

from django.core.management import get_commands
from django.urls import NoReverseMatch, reverse
from django.utils import timezone


_STATUS_RANK = {
    'ok': 0,
    'warning': 1,
    'degraded': 2,
    'critical': 3,
}


@dataclass(frozen=True)
class UrlContract:
    key: str
    name: str
    expected_path: str
    args: tuple[str, ...] = ()


@dataclass(frozen=True)
class SymbolContract:
    key: str
    module: str
    attr: str
    version: str
    description: str


URL_CONTRACTS = [
    UrlContract('ops_diagnostics', 'ops-diagnostics', '/api/v1/ops/diagnostics/'),
    UrlContract('ops_diagnostics_run', 'ops-diagnostics-run', '/api/v1/ops/diagnostics/run/'),
    UrlContract('operations_dashboard', 'ops-admin-operations-dashboard', '/api/v1/ops/admin/operations-dashboard/'),
    UrlContract('operations_hub', 'ops-admin-operations-hub', '/api/v1/ops/admin/operations-hub/'),
    UrlContract('operations_readiness', 'ops-admin-operations-readiness', '/api/v1/ops/admin/operations-readiness/'),
    UrlContract('reconciliation_report', 'ops-admin-reconciliation-report', '/api/v1/ops/admin/reconciliation-report/'),
    UrlContract('reconciliation_repair', 'ops-admin-reconciliation-repair', '/api/v1/ops/admin/reconciliation-repair/'),
    UrlContract('reconciliation_repair_policy', 'ops-admin-reconciliation-repair-policy', '/api/v1/ops/admin/reconciliation-repair/policy/'),
    UrlContract('snapshot_list', 'ops-admin-reconciliation-snapshots', '/api/v1/ops/admin/reconciliation-snapshots/'),
    UrlContract('snapshot_capture', 'ops-admin-reconciliation-snapshot-capture', '/api/v1/ops/admin/reconciliation-snapshots/capture/'),
    UrlContract('snapshot_latest', 'ops-admin-reconciliation-snapshot-latest', '/api/v1/ops/admin/reconciliation-snapshots/latest/'),
    UrlContract('snapshot_trend', 'ops-admin-reconciliation-snapshot-trend', '/api/v1/ops/admin/reconciliation-snapshots/trend/'),
    UrlContract('snapshot_metrics', 'ops-admin-reconciliation-snapshot-metrics', '/api/v1/ops/admin/reconciliation-snapshots/metrics/'),
    UrlContract('snapshot_alerts', 'ops-admin-reconciliation-snapshot-alerts', '/api/v1/ops/admin/reconciliation-snapshots/alerts/'),
    UrlContract('snapshot_retention', 'ops-admin-reconciliation-snapshot-retention', '/api/v1/ops/admin/reconciliation-snapshots/retention/'),
    UrlContract('snapshot_schedule', 'ops-admin-reconciliation-snapshot-schedule', '/api/v1/ops/admin/reconciliation-snapshots/schedule/'),
    UrlContract('snapshot_issues', 'ops-admin-reconciliation-snapshot-issues', '/api/v1/ops/admin/reconciliation-snapshots/issues/'),
    UrlContract('snapshot_compare', 'ops-admin-reconciliation-snapshot-compare', '/api/v1/ops/admin/reconciliation-snapshots/compare/'),
    UrlContract('entity_detail', 'ops-admin-entity-detail', '/api/v1/ops/admin/entities/outbox_message/example-id/', ('outbox_message', 'example-id')),
]


SYMBOL_CONTRACTS = [
    SymbolContract('snapshot_capture', 'apps.ops.reconciliation_snapshots', 'capture_reconciliation_snapshot', 'v8.30', 'Manual snapshot capture service.'),
    SymbolContract('repair_snapshot_capture', 'apps.ops.reconciliation_snapshots', 'capture_repair_reconciliation_snapshot', 'v8.30', 'Auto-capture source=repair snapshot after repair action.'),
    SymbolContract('snapshot_compare', 'apps.ops.reconciliation_snapshots', 'compare_reconciliation_snapshots', 'v8.31', 'Compare two reconciliation snapshots.'),
    SymbolContract('snapshot_metrics', 'apps.ops.reconciliation_snapshots', 'get_reconciliation_snapshot_metrics', 'v8.32', 'Dashboard metrics from persisted snapshots.'),
    SymbolContract('scheduled_snapshot_guard', 'apps.ops.reconciliation_snapshots', 'capture_reconciliation_snapshot_if_due', 'v8.33', 'Guarded scheduled snapshot capture.'),
    SymbolContract('snapshot_schedule_status', 'apps.ops.reconciliation_snapshots', 'get_reconciliation_snapshot_schedule', 'v8.33', 'Scheduled capture freshness status.'),
    SymbolContract('snapshot_retention_policy', 'apps.ops.reconciliation_snapshots', 'get_reconciliation_snapshot_retention_policy', 'v8.34', 'Retention preview/prune policy.'),
    SymbolContract('snapshot_prune', 'apps.ops.reconciliation_snapshots', 'prune_reconciliation_snapshots', 'v8.34', 'Snapshot pruning service.'),
    SymbolContract('snapshot_alerts', 'apps.ops.reconciliation_snapshots', 'get_reconciliation_snapshot_alerts', 'v8.37', 'Alert evaluation from snapshot trend.'),
    SymbolContract('snapshot_alert_notifications', 'apps.ops.reconciliation_snapshots', 'notify_reconciliation_snapshot_alerts', 'v8.37', 'Admin alert notification emitter.'),
    SymbolContract('issue_registry', 'apps.ops.reconciliation_snapshots', 'get_reconciliation_issue_registry', 'v8.38', 'Normalized issue registry from snapshot report.'),
    SymbolContract('repair_execution', 'apps.ops.repair', 'run_reconciliation_repair', 'v8.36', 'Hardened reconciliation repair workflow.'),
    SymbolContract('repair_policy', 'apps.ops.repair', 'get_reconciliation_repair_policy', 'v8.36', 'Dry-run/confirmation repair policy endpoint support.'),
    SymbolContract('operations_hub', 'apps.ops.operations_hub', 'get_admin_operations_hub', 'v8.39', 'Unified admin operations hub payload.'),
    SymbolContract('operations_readiness', 'apps.ops.operations_readiness', 'get_ops_production_readiness', 'v8.40', 'Ops production readiness self-check.'),
    SymbolContract('scheduled_snapshot_task', 'apps.ops.tasks', 'capture_reconciliation_snapshot_task', 'v8.33', 'Celery task for scheduled capture.'),
    SymbolContract('snapshot_prune_task', 'apps.ops.tasks', 'prune_reconciliation_snapshots_task', 'v8.34', 'Celery task for retention pruning.'),
]


MANAGEMENT_COMMANDS = [
    {
        'key': 'capture_reconciliation_snapshot',
        'name': 'capture_reconciliation_snapshot',
        'version': 'v8.33',
        'description': 'Manual/guarded reconciliation snapshot capture.',
        'recommended_smoke': 'python manage.py capture_reconciliation_snapshot --if-due --source scheduled --min-age-minutes 60 --json',
    },
    {
        'key': 'prune_reconciliation_snapshots',
        'name': 'prune_reconciliation_snapshots',
        'version': 'v8.34',
        'description': 'Preview/execute reconciliation snapshot retention policy.',
        'recommended_smoke': 'python manage.py prune_reconciliation_snapshots --json',
    },
    {
        'key': 'check_ops_readiness',
        'name': 'check_ops_readiness',
        'version': 'v8.40',
        'description': 'Emit this production readiness report from CLI.',
        'recommended_smoke': 'python manage.py check_ops_readiness --json',
    },
]


SMOKE_COMMANDS = [
    {
        'key': 'backend_syntax',
        'title': 'Backend syntax/import surface',
        'command': 'python -m py_compile apps/ops/operations_readiness.py apps/ops/operations_hub.py apps/ops/reconciliation_snapshots.py apps/ops/repair.py apps/ops/tasks.py apps/ops/api/views.py apps/ops/api/urls.py',
    },
    {
        'key': 'django_check',
        'title': 'Django system checks',
        'command': 'python manage.py check',
    },
    {
        'key': 'migration_check',
        'title': 'Migration drift check',
        'command': 'python manage.py makemigrations --check --dry-run',
    },
    {
        'key': 'ops_tests',
        'title': 'Ops/reconciliation test subset',
        'command': 'pytest -q tests/test_ops_admin_operations_readiness.py tests/test_ops_admin_operations_hub.py tests/test_ops_reconciliation_issue_registry.py tests/test_ops_reconciliation_snapshot_alerting.py tests/test_ops_reconciliation_repair_snapshot_autocapture.py',
    },
    {
        'key': 'frontend_typecheck',
        'title': 'Frontend typecheck',
        'command': 'cd ../frontend && npm run typecheck',
    },
    {
        'key': 'frontend_build',
        'title': 'Frontend production build',
        'command': 'cd ../frontend && npm run build',
    },
    {
        'key': 'frontend_contracts',
        'title': 'Frontend API contract smoke',
        'command': 'cd ../frontend && npm run test:contracts',
    },
]


FRONTEND_SURFACE = [
    {
        'key': 'operations_hub_page',
        'href': '/admin/operations',
        'api_href': '/api/v1/ops/admin/operations-hub/',
        'description': 'Unified operations command center page.',
    },
    {
        'key': 'reconciliation_snapshots_page',
        'href': '/admin/reconciliation/snapshots',
        'api_href': '/api/v1/ops/admin/reconciliation-snapshots/metrics/',
        'description': 'Snapshot dashboard with trend, compare, retention and repair impact.',
    },
]


ENVIRONMENT_FLAGS = [
    {
        'key': 'CELERY_RECONCILIATION_SNAPSHOT_EVERY_SECONDS',
        'default': '3600',
        'description': 'Scheduled snapshot capture cadence.',
    },
    {
        'key': 'CELERY_RECONCILIATION_SNAPSHOT_MIN_AGE_MINUTES',
        'default': '60',
        'description': 'Idempotency guard for scheduled capture.',
    },
    {
        'key': 'CELERY_RECONCILIATION_SNAPSHOT_ALERTS_ENABLED',
        'default': 'true',
        'description': 'Emit alerts after scheduled capture.',
    },
    {
        'key': 'CELERY_RECONCILIATION_ALERT_STALE_AFTER_MINUTES',
        'default': '180',
        'description': 'Scheduled snapshot freshness alert threshold.',
    },
    {
        'key': 'CELERY_RECONCILIATION_SNAPSHOT_RETENTION_EVERY_SECONDS',
        'default': '86400',
        'description': 'Retention pruning cadence.',
    },
]


def _rank(status: str) -> int:
    return _STATUS_RANK.get(status, 2)


def _worst_status(statuses: list[str]) -> str:
    if not statuses:
        return 'ok'
    return sorted(statuses, key=_rank, reverse=True)[0]


def _ok_check(key: str, category: str, title: str, **extra: Any) -> dict[str, Any]:
    return {'key': key, 'category': category, 'title': title, 'status': 'ok', **extra}


def _failed_check(key: str, category: str, title: str, detail: str, status: str = 'critical', **extra: Any) -> dict[str, Any]:
    return {'key': key, 'category': category, 'title': title, 'status': status, 'detail': detail, **extra}


def _check_url(contract: UrlContract) -> dict[str, Any]:
    try:
        actual = reverse(contract.name, args=contract.args)
    except NoReverseMatch as exc:
        return _failed_check(
            contract.key,
            'api_surface',
            contract.name,
            f'URL name is not resolvable: {exc}',
            expected_path=contract.expected_path,
        )

    if actual != contract.expected_path:
        return _failed_check(
            contract.key,
            'api_surface',
            contract.name,
            f'URL resolved to {actual}, expected {contract.expected_path}.',
            status='degraded',
            expected_path=contract.expected_path,
            actual_path=actual,
        )
    return _ok_check(contract.key, 'api_surface', contract.name, expected_path=contract.expected_path, actual_path=actual)


def _check_symbol(contract: SymbolContract) -> dict[str, Any]:
    try:
        module = import_module(contract.module)
    except Exception as exc:
        return _failed_check(
            contract.key,
            'python_surface',
            f'{contract.module}.{contract.attr}',
            f'Module import failed: {exc}',
            version=contract.version,
            description=contract.description,
        )

    if not hasattr(module, contract.attr):
        return _failed_check(
            contract.key,
            'python_surface',
            f'{contract.module}.{contract.attr}',
            'Expected symbol is missing.',
            version=contract.version,
            description=contract.description,
        )
    return _ok_check(
        contract.key,
        'python_surface',
        f'{contract.module}.{contract.attr}',
        version=contract.version,
        description=contract.description,
    )


def _check_management_command(spec: dict[str, Any], available_commands: dict[str, str]) -> dict[str, Any]:
    name = spec['name']
    if name not in available_commands:
        return _failed_check(
            spec['key'],
            'management_commands',
            name,
            'Management command is not registered.',
            version=spec['version'],
            description=spec['description'],
            recommended_smoke=spec['recommended_smoke'],
        )
    return _ok_check(
        spec['key'],
        'management_commands',
        name,
        app=available_commands[name],
        version=spec['version'],
        description=spec['description'],
        recommended_smoke=spec['recommended_smoke'],
    )


def _summarize(checks: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(checks)
    by_status: dict[str, int] = {'ok': 0, 'warning': 0, 'degraded': 0, 'critical': 0}
    by_category: dict[str, dict[str, int]] = {}

    for check in checks:
        status = str(check.get('status') or 'critical')
        category = str(check.get('category') or 'unknown')
        by_status[status] = by_status.get(status, 0) + 1
        by_category.setdefault(category, {'ok': 0, 'warning': 0, 'degraded': 0, 'critical': 0})
        by_category[category][status] = by_category[category].get(status, 0) + 1

    return {
        'total_checks': total,
        'ok_count': by_status.get('ok', 0),
        'warning_count': by_status.get('warning', 0),
        'degraded_count': by_status.get('degraded', 0),
        'critical_count': by_status.get('critical', 0),
        'by_status': by_status,
        'by_category': by_category,
    }


def _recommendations(summary: dict[str, Any], checks: list[dict[str, Any]]) -> list[dict[str, str]]:
    recommendations: list[dict[str, str]] = []
    if summary.get('critical_count'):
        recommendations.append(
            {
                'key': 'fix_critical_surface',
                'severity': 'critical',
                'title': 'Fix missing critical ops surface before shipping.',
                'description': 'At least one required URL, service symbol or management command is missing.',
            }
        )
    if summary.get('degraded_count'):
        recommendations.append(
            {
                'key': 'align_contract_paths',
                'severity': 'warning',
                'title': 'Align degraded contracts.',
                'description': 'A contract exists but does not match the expected production path or shape.',
            }
        )
    missing_commands = [check['title'] for check in checks if check.get('category') == 'management_commands' and check.get('status') != 'ok']
    if missing_commands:
        recommendations.append(
            {
                'key': 'restore_management_commands',
                'severity': 'critical',
                'title': 'Restore ops management commands.',
                'description': ', '.join(missing_commands),
            }
        )
    recommendations.append(
        {
            'key': 'run_v840_smoke_suite',
            'severity': 'info',
            'title': 'Run the v8.40 smoke suite before committing.',
            'description': 'Execute backend checks, targeted ops pytest subset, frontend typecheck/build and contract tests.',
        }
    )
    return recommendations


def get_ops_production_readiness(
    *,
    include_commands: bool = True,
    include_recommendations: bool = True,
) -> dict[str, Any]:
    """Return a read-only production-readiness report for the v8.30-v8.40 ops surface.

    This deliberately validates import/URL/command contracts without executing
    repair actions, outbox dispatch, snapshot capture, retention pruning or any
    other mutating workflow.
    """
    checks: list[dict[str, Any]] = []
    checks.extend(_check_url(contract) for contract in URL_CONTRACTS)
    checks.extend(_check_symbol(contract) for contract in SYMBOL_CONTRACTS)

    available_commands = get_commands()
    checks.extend(_check_management_command(spec, available_commands) for spec in MANAGEMENT_COMMANDS)

    summary = _summarize(checks)
    status = _worst_status([str(check.get('status') or 'critical') for check in checks])

    payload: dict[str, Any] = {
        'status': status,
        'generated_at': timezone.now(),
        'version': 'v8.40',
        'scope': 'ops/reconciliation production readiness',
        'summary': summary,
        'checks': checks,
        'api_surface': [
            {'key': contract.key, 'name': contract.name, 'expected_path': contract.expected_path}
            for contract in URL_CONTRACTS
        ],
        'frontend_surface': FRONTEND_SURFACE,
        'environment_flags': ENVIRONMENT_FLAGS,
    }

    if include_commands:
        payload['smoke_commands'] = SMOKE_COMMANDS
        payload['management_commands'] = MANAGEMENT_COMMANDS

    if include_recommendations:
        payload['recommendations'] = _recommendations(summary, checks)

    return payload
