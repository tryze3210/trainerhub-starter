from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any

from django.core.management import get_commands
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from rest_framework.permissions import IsAdminUser, IsAuthenticated


_STATUS_RANK = {'ok': 0, 'warning': 1, 'degraded': 2, 'critical': 3}


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
    description: str


@dataclass(frozen=True)
class PermissionContract:
    key: str
    module: str
    view_class: str
    expected_permissions: tuple[type, ...]
    description: str


@dataclass(frozen=True)
class FileContract:
    key: str
    path: str
    description: str


URL_CONTRACTS = [
    UrlContract('payment_admin', 'payments-admin-list', '/api/v1/payments-admin/'),
    UrlContract('payment_webhooks_admin', 'payments-webhooks-list', '/api/v1/payments-webhooks/'),
    UrlContract('customer_billing_orders', 'orders-list', '/api/v1/orders/'),
    UrlContract('customer_billing_payments', 'payments-list', '/api/v1/payments/'),
    UrlContract('customer_billing_entitlements', 'entitlements-list', '/api/v1/entitlements/'),
    UrlContract('subscriptions', 'subscriptions-list', '/api/v1/subscriptions/'),
    UrlContract('trainer_crm', 'trainer-crm-list', '/api/v1/customer/trainer-crm/'),
    UrlContract('trainer_schedule', 'booking-me-schedule', '/api/v1/booking/me/schedule/'),
    UrlContract('booking_check_in', 'booking-attendance-check-in', '/api/v1/booking/attendance/check-in/'),
    UrlContract('booking_attendance_history', 'booking-attendance-history', '/api/v1/booking/attendance/'),
    UrlContract('notifications_admin_center', 'admin-notification-center', '/api/v1/notifications/admin/center/'),
    UrlContract('ops_production_readiness', 'ops-admin-production-readiness', '/api/v1/ops/admin/production-readiness/'),
]


SYMBOL_CONTRACTS = [
    SymbolContract('payment_webhook_service', 'apps.payments.services', 'PaymentWebhookService', 'Webhook hardening, replay and duplicate protection.'),
    SymbolContract('payment_reconciliation', 'apps.ops.payment_reconciliation', 'get_payment_reconciliation_report', 'Payment/provider/entitlement reconciliation report.'),
    SymbolContract('entitlement_access_audit', 'apps.entitlements.access_audit', 'AccessControlAuditService', 'Runtime access guard policy.'),
    SymbolContract('subscription_lifecycle', 'apps.subscriptions.lifecycle', 'SubscriptionLifecycleService', 'Subscription lifecycle and renewal helpers.'),
    SymbolContract('domain_notifications', 'apps.notifications.domain.triggers', 'DomainNotificationTriggers', 'Commerce notification triggers.'),
    SymbolContract('trainer_crm_selector', 'apps.customers.selectors', 'TrainerCRMSelector', 'Trainer CRM read model.'),
    SymbolContract('booking_attendance_service', 'apps.booking.services.attendance', 'BookingAttendanceService', 'Attendance and check-in service.'),
]


PERMISSION_CONTRACTS = [
    PermissionContract('payment_admin_permissions', 'apps.payments.api.views', 'AdminPaymentViewSet', (IsAdminUser,), 'Payment admin UI is admin-only.'),
    PermissionContract('subscription_permissions', 'apps.subscriptions.api.views', 'SubscriptionViewSet', (IsAuthenticated,), 'Subscription self-service requires auth.'),
    PermissionContract('trainer_crm_permissions', 'apps.customers.api.views', 'TrainerCRMViewSet', (IsAuthenticated,), 'Trainer CRM requires auth plus role guard.'),
    PermissionContract('booking_schedule_permissions', 'apps.booking.api.views', 'TrainerScheduleView', (IsAuthenticated,), 'Trainer schedule requires auth.'),
    PermissionContract('booking_checkin_permissions', 'apps.booking.api.views', 'AttendanceCheckInView', (IsAuthenticated,), 'Attendance check-in requires auth.'),
    PermissionContract('ops_readiness_permissions', 'apps.ops.api.views', 'AdminProductionReadinessView', (IsAdminUser,), 'Production readiness is admin-only.'),
]


FILE_CONTRACTS = [
    FileContract('ci_workflow', '.github/workflows/ci.yml', 'CI workflow exists.'),
    FileContract('readme_current_version', 'README.md', 'Current-version README exists.'),
    FileContract('seed_demo', 'scripts/bootstrap/seed_demo.py', 'Seed data helper exists.'),
    FileContract('booking_v93_test', 'backend/tests/test_booking_v93_schedule_waitlist.py', 'Booking schedule regression test exists.'),
    FileContract('booking_v94_test', 'backend/tests/test_booking_v94_attendance_checkin.py', 'Attendance check-in regression test exists.'),
    FileContract('customer_crm_v92_test', 'backend/tests/test_customer_crm_v92.py', 'CRM regression test exists.'),
    FileContract('notifications_v91_test', 'backend/tests/test_notifications_v91_domain_triggers.py', 'Notification regression test exists.'),
]


SMOKE_COMMANDS = [
    {'key': 'django_check', 'title': 'Django system checks', 'command': 'cd backend && python manage.py check'},
    {'key': 'migration_check', 'title': 'Migration drift check', 'command': 'cd backend && python manage.py makemigrations --check --dry-run'},
    {'key': 'backend_contracts', 'title': 'Backend roadmap tests', 'command': 'cd backend && pytest tests/test_customer_crm_v92.py tests/test_booking_v93_schedule_waitlist.py tests/test_booking_v94_attendance_checkin.py tests/test_notifications_v91_domain_triggers.py'},
    {'key': 'readiness_gate', 'title': 'Production readiness gate', 'command': 'cd backend && python manage.py check_production_readiness --json --fail-on-degraded'},
    {'key': 'frontend_typecheck', 'title': 'Frontend typecheck', 'command': 'cd frontend && npm run typecheck'},
    {'key': 'frontend_build', 'title': 'Frontend build', 'command': 'cd frontend && npm run build'},
]


FRONTEND_SURFACE = [
    {'key': 'payment_admin', 'href': '/admin/payments', 'description': 'Payment admin UI.'},
    {'key': 'customer_billing', 'href': '/billing', 'description': 'Customer billing UI.'},
    {'key': 'trainer_sales', 'href': '/trainer/dashboard/sales', 'description': 'Trainer sales dashboard.'},
    {'key': 'trainer_crm', 'href': '/trainer/dashboard/crm', 'description': 'Trainer CRM dashboard.'},
    {'key': 'trainer_schedule', 'href': '/trainer/dashboard/schedule', 'description': 'Trainer booking/attendance dashboard.'},
]


def _rank(status: str) -> int:
    return _STATUS_RANK.get(status, 2)


def _worst_status(statuses: list[str]) -> str:
    if not statuses:
        return 'ok'
    return sorted(statuses, key=_rank, reverse=True)[0]


def _check(key: str, category: str, title: str, status: str = 'ok', **extra: Any) -> dict[str, Any]:
    return {'key': key, 'category': category, 'title': title, 'status': status, **extra}


def _check_url(contract: UrlContract) -> dict[str, Any]:
    try:
        actual = reverse(contract.name, args=contract.args)
    except NoReverseMatch as exc:
        return _check(contract.key, 'api_contract', contract.name, 'critical', detail=f'URL name is not resolvable: {exc}', expected_path=contract.expected_path)
    if actual != contract.expected_path:
        return _check(contract.key, 'api_contract', contract.name, 'degraded', detail=f'URL resolved to {actual}, expected {contract.expected_path}.', expected_path=contract.expected_path, actual_path=actual)
    return _check(contract.key, 'api_contract', contract.name, expected_path=contract.expected_path, actual_path=actual)


def _check_symbol(contract: SymbolContract) -> dict[str, Any]:
    try:
        module = import_module(contract.module)
    except Exception as exc:
        return _check(contract.key, 'python_contract', f'{contract.module}.{contract.attr}', 'critical', detail=f'Module import failed: {exc}', description=contract.description)
    if not hasattr(module, contract.attr):
        return _check(contract.key, 'python_contract', f'{contract.module}.{contract.attr}', 'critical', detail='Expected symbol is missing.', description=contract.description)
    return _check(contract.key, 'python_contract', f'{contract.module}.{contract.attr}', description=contract.description)


def _check_permissions(contract: PermissionContract) -> dict[str, Any]:
    try:
        view_class = getattr(import_module(contract.module), contract.view_class)
    except Exception as exc:
        return _check(contract.key, 'permissions', contract.view_class, 'critical', detail=f'View import failed: {exc}', description=contract.description)
    configured = tuple(getattr(view_class, 'permission_classes', ()) or ())
    missing = [permission.__name__ for permission in contract.expected_permissions if permission not in configured]
    if missing:
        return _check(
            contract.key,
            'permissions',
            contract.view_class,
            'critical',
            detail=f'Missing permission classes: {", ".join(missing)}',
            configured=[permission.__name__ for permission in configured],
            expected=[permission.__name__ for permission in contract.expected_permissions],
            description=contract.description,
        )
    return _check(
        contract.key,
        'permissions',
        contract.view_class,
        configured=[permission.__name__ for permission in configured],
        expected=[permission.__name__ for permission in contract.expected_permissions],
        description=contract.description,
    )


def _check_file(contract: FileContract, *, repo_root: Path) -> dict[str, Any]:
    path = repo_root / contract.path
    if not path.exists():
        return _check(contract.key, 'files', contract.path, 'critical', detail='Required file is missing.', description=contract.description)
    return _check(contract.key, 'files', contract.path, description=contract.description)


def _check_management_command() -> dict[str, Any]:
    commands = get_commands()
    if 'check_production_readiness' not in commands:
        return _check('check_production_readiness', 'management_commands', 'check_production_readiness', 'critical', detail='Management command is not registered.')
    return _check('check_production_readiness', 'management_commands', 'check_production_readiness', app=commands['check_production_readiness'])


def _summarize(checks: list[dict[str, Any]]) -> dict[str, Any]:
    by_status = {'ok': 0, 'warning': 0, 'degraded': 0, 'critical': 0}
    by_category: dict[str, dict[str, int]] = {}
    for check in checks:
        status = str(check.get('status') or 'critical')
        category = str(check.get('category') or 'unknown')
        by_status[status] = by_status.get(status, 0) + 1
        by_category.setdefault(category, {'ok': 0, 'warning': 0, 'degraded': 0, 'critical': 0})
        by_category[category][status] = by_category[category].get(status, 0) + 1
    return {
        'total_checks': len(checks),
        'ok_count': by_status.get('ok', 0),
        'warning_count': by_status.get('warning', 0),
        'degraded_count': by_status.get('degraded', 0),
        'critical_count': by_status.get('critical', 0),
        'by_status': by_status,
        'by_category': by_category,
    }


def _recommendations(summary: dict[str, Any]) -> list[dict[str, str]]:
    rows = []
    if summary.get('critical_count'):
        rows.append({'key': 'fix_critical_gate', 'severity': 'critical', 'title': 'Fix critical production readiness checks before release.'})
    if summary.get('degraded_count'):
        rows.append({'key': 'fix_degraded_contracts', 'severity': 'warning', 'title': 'Align degraded API or file contracts before release.'})
    rows.append({'key': 'run_smoke_suite', 'severity': 'info', 'title': 'Run the full v95 smoke suite in CI before tagging a release.'})
    return rows


def get_platform_production_readiness(
    *,
    include_commands: bool = True,
    include_recommendations: bool = True,
) -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[3]
    checks: list[dict[str, Any]] = []
    checks.extend(_check_url(contract) for contract in URL_CONTRACTS)
    checks.extend(_check_symbol(contract) for contract in SYMBOL_CONTRACTS)
    checks.extend(_check_permissions(contract) for contract in PERMISSION_CONTRACTS)
    checks.extend(_check_file(contract, repo_root=repo_root) for contract in FILE_CONTRACTS)
    checks.append(_check_management_command())

    summary = _summarize(checks)
    status = _worst_status([str(check.get('status') or 'critical') for check in checks])
    payload: dict[str, Any] = {
        'status': status,
        'generated_at': timezone.now(),
        'version': 'v95',
        'scope': 'full platform production readiness',
        'summary': summary,
        'checks': checks,
        'api_surface': [{'key': item.key, 'name': item.name, 'expected_path': item.expected_path} for item in URL_CONTRACTS],
        'frontend_surface': FRONTEND_SURFACE,
        'seed_data': [{'key': 'seed_demo', 'command': 'python scripts/bootstrap/seed_demo.py', 'description': 'Create local demo trainer/user data.'}],
    }
    if include_commands:
        payload['smoke_commands'] = SMOKE_COMMANDS
        payload['management_commands'] = [{'key': 'check_production_readiness', 'name': 'check_production_readiness'}]
    if include_recommendations:
        payload['recommendations'] = _recommendations(summary)
    return payload
