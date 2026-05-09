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
    version: str
    description: str
    args: tuple[str, ...] = ()


@dataclass(frozen=True)
class SymbolContract:
    key: str
    module: str
    attr: str
    version: str
    description: str


URL_CONTRACTS: list[UrlContract] = [
    UrlContract(
        'trainer_revenue_summary',
        'trainer-me-revenue-summary',
        '/api/v1/trainers/me/revenue/summary/',
        'v8.41',
        'Trainer revenue dashboard summary endpoint.',
    ),
    UrlContract(
        'trainer_revenue_transactions',
        'trainer-me-revenue-transactions',
        '/api/v1/trainers/me/revenue/transactions/',
        'v8.41',
        'Trainer revenue ledger/transactions endpoint.',
    ),
    UrlContract(
        'trainer_revenue_payouts',
        'trainer-me-revenue-payouts',
        '/api/v1/trainers/me/revenue/payouts/',
        'v8.41',
        'Trainer revenue payout history endpoint.',
    ),
    UrlContract(
        'trainer_payout_balance',
        'my-payouts-balance',
        '/api/v1/payouts/my/balance/',
        'v8.42',
        'Trainer payout balance endpoint.',
    ),
    UrlContract(
        'trainer_payout_request',
        'my-payouts-request-payout',
        '/api/v1/payouts/my/request/',
        'v8.42',
        'Trainer payout request creation endpoint.',
    ),
    UrlContract(
        'admin_payout_overview',
        'admin-payouts-overview',
        '/api/v1/payouts/admin/overview/',
        'v8.42',
        'Admin payout operations overview endpoint.',
    ),
    UrlContract(
        'admin_payout_approve',
        'admin-payouts-approve',
        '/api/v1/payouts/admin/00000000-0000-0000-0000-000000000000/approve/',
        'v8.42',
        'Admin payout approve transition endpoint.',
        ('00000000-0000-0000-0000-000000000000',),
    ),
    UrlContract(
        'trainer_analytics_overview',
        'trainer-me-analytics-overview',
        '/api/v1/trainers/me/analytics/overview/',
        'v8.43',
        'Trainer content analytics overview endpoint.',
    ),
    UrlContract(
        'trainer_analytics_content',
        'trainer-me-analytics-content',
        '/api/v1/trainers/me/analytics/content/',
        'v8.43',
        'Trainer content performance rows endpoint.',
    ),
    UrlContract(
        'trainer_analytics_sales',
        'trainer-me-analytics-sales',
        '/api/v1/trainers/me/analytics/sales/',
        'v8.43',
        'Trainer sales analytics endpoint.',
    ),
    UrlContract(
        'trainer_products_list',
        'trainer-products-list',
        '/api/v1/products/trainer/',
        'v8.44',
        'Trainer product/bundle builder list endpoint.',
    ),
    UrlContract(
        'trainer_product_readiness',
        'trainer-products-readiness',
        '/api/v1/products/trainer/00000000-0000-0000-0000-000000000000/readiness/',
        'v8.44',
        'Trainer product publish readiness endpoint.',
        ('00000000-0000-0000-0000-000000000000',),
    ),
    UrlContract(
        'trainer_product_publish',
        'trainer-products-publish',
        '/api/v1/products/trainer/00000000-0000-0000-0000-000000000000/publish/',
        'v8.44',
        'Trainer product publish endpoint.',
        ('00000000-0000-0000-0000-000000000000',),
    ),
    UrlContract(
        'order_checkout',
        'orders-checkout',
        '/api/v1/orders/checkout/',
        'v8.45',
        'Checkout endpoint with idempotency and price snapshot integrity.',
    ),
    UrlContract(
        'subscription_lifecycle_policy',
        'subscriptions-lifecycle-policy',
        '/api/v1/subscriptions/lifecycle-policy/',
        'v8.46',
        'Subscription lifecycle policy endpoint.',
    ),
    UrlContract(
        'subscription_lifecycle_summary',
        'subscriptions-lifecycle-summary',
        '/api/v1/subscriptions/lifecycle-summary/',
        'v8.46',
        'Subscription lifecycle summary endpoint.',
    ),
    UrlContract(
        'subscription_renewal_projection',
        'subscriptions-renewal-projection',
        '/api/v1/subscriptions/00000000-0000-0000-0000-000000000000/renewal-projection/',
        'v8.46',
        'Single subscription renewal projection endpoint.',
        ('00000000-0000-0000-0000-000000000000',),
    ),
    UrlContract(
        'subscription_resume',
        'subscriptions-resume',
        '/api/v1/subscriptions/00000000-0000-0000-0000-000000000000/resume/',
        'v8.46',
        'Subscription resume endpoint.',
        ('00000000-0000-0000-0000-000000000000',),
    ),
    UrlContract(
        'subscription_admin_reconcile_entitlements',
        'subscriptions-admin-reconcile-entitlements',
        '/api/v1/subscriptions/admin/reconcile-entitlements/',
        'v8.46',
        'Admin subscription entitlement reconciliation endpoint.',
    ),
    UrlContract(
        'entitlement_access_check',
        'entitlements-me-access-check',
        '/api/v1/entitlements/me/access-check/',
        'v8.47',
        'Runtime access-control audit endpoint.',
    ),
    UrlContract(
        'trainer_onboarding_status',
        'trainer-me-onboarding-status',
        '/api/v1/trainers/me/onboarding/status/',
        'v8.48',
        'Trainer onboarding state endpoint.',
    ),
    UrlContract(
        'trainer_application_status',
        'trainer-me-application-status',
        '/api/v1/trainers/me/application-status/',
        'v8.48',
        'Trainer application status endpoint.',
    ),
    UrlContract(
        'admin_trainer_applications',
        'trainer-admin-application-list',
        '/api/v1/trainers/admin/applications/',
        'v8.48',
        'Admin trainer application queue endpoint.',
    ),
]


SYMBOL_CONTRACTS: list[SymbolContract] = [
    SymbolContract('trainer_revenue_summary', 'apps.trainers.revenue', 'build_trainer_revenue_summary', 'v8.41', 'Trainer revenue summary builder.'),
    SymbolContract('trainer_revenue_transactions', 'apps.trainers.revenue', 'list_trainer_revenue_transactions', 'v8.41', 'Trainer revenue transaction listing.'),
    SymbolContract('trainer_revenue_payouts', 'apps.trainers.revenue', 'list_trainer_revenue_payouts', 'v8.41', 'Trainer payout history listing for revenue dashboard.'),
    SymbolContract('trainer_content_analytics_overview', 'apps.trainers.content_analytics', 'build_trainer_content_analytics_overview', 'v8.43', 'Trainer content analytics overview builder.'),
    SymbolContract('trainer_content_performance', 'apps.trainers.content_analytics', 'list_trainer_content_performance', 'v8.43', 'Trainer content performance listing.'),
    SymbolContract('trainer_sales_analytics', 'apps.trainers.content_analytics', 'list_trainer_sales_analytics', 'v8.43', 'Trainer sales analytics listing.'),
    SymbolContract('trainer_product_builder', 'apps.products.services', 'TrainerProductBuilderService', 'v8.44', 'Trainer product/bundle builder service.'),
    SymbolContract('checkout_integrity_service', 'apps.orders.checkout_integrity', 'CheckoutIntegrityService', 'v8.45', 'Checkout idempotency and snapshot integrity service.'),
    SymbolContract('subscription_lifecycle_service', 'apps.subscriptions.lifecycle', 'SubscriptionLifecycleService', 'v8.46', 'Subscription lifecycle hardening service.'),
    SymbolContract('access_control_audit_service', 'apps.entitlements.access_audit', 'AccessControlAuditService', 'v8.47', 'Runtime access-control audit service.'),
    SymbolContract('trainer_onboarding_state', 'apps.trainers.onboarding_flow', 'get_trainer_onboarding_state', 'v8.48', 'Trainer onboarding production state builder.'),
    SymbolContract('trainer_application_review', 'apps.trainers.onboarding_flow', 'review_trainer_application', 'v8.48', 'Admin trainer application review service.'),
]


FRONTEND_SURFACE = [
    {'key': 'trainer_revenue_dashboard', 'href': '/trainer/dashboard/revenue', 'version': 'v8.41', 'description': 'Trainer revenue dashboard.'},
    {'key': 'trainer_payouts_dashboard', 'href': '/trainer/dashboard/payouts', 'version': 'v8.42', 'description': 'Trainer payout request dashboard.'},
    {'key': 'trainer_analytics_dashboard', 'href': '/trainer/dashboard/analytics', 'version': 'v8.43', 'description': 'Trainer content performance analytics dashboard.'},
    {'key': 'trainer_products_dashboard', 'href': '/trainer/dashboard/products', 'version': 'v8.44', 'description': 'Trainer product/bundle builder page.'},
    {'key': 'subscriptions_lifecycle_page', 'href': '/subscriptions', 'version': 'v8.46', 'description': 'Subscription lifecycle center.'},
    {'key': 'trainer_onboarding_page', 'href': '/trainer/onboarding', 'version': 'v8.48', 'description': 'Trainer onboarding flow.'},
    {'key': 'trainer_application_status_page', 'href': '/trainer/application-status', 'version': 'v8.48', 'description': 'Trainer application status page.'},
    {'key': 'admin_trainer_applications_page', 'href': '/admin/trainers/applications', 'version': 'v8.48', 'description': 'Admin trainer application review queue.'},
    {'key': 'marketplace_catalog', 'href': '/catalog', 'version': 'v8.49', 'description': 'Public marketplace catalog storefront.'},
    {'key': 'marketplace_video_detail', 'href': '/catalog/videos/example-slug', 'version': 'v8.49', 'description': 'Public video detail storefront.'},
    {'key': 'marketplace_program_detail', 'href': '/catalog/programs/example-slug', 'version': 'v8.49', 'description': 'Public program detail storefront.'},
    {'key': 'marketplace_bundle_detail', 'href': '/catalog/bundles/example-slug', 'version': 'v8.49', 'description': 'Public bundle detail storefront.'},
    {'key': 'trainer_directory', 'href': '/trainers', 'version': 'v8.49', 'description': 'Public trainer directory storefront.'},
    {'key': 'trainer_storefront_detail', 'href': '/trainers/example-trainer', 'version': 'v8.49', 'description': 'Public trainer storefront detail page.'},
]


MANAGEMENT_COMMANDS = [
    {
        'key': 'sync_subscription_entitlements',
        'name': 'sync_subscription_entitlements',
        'version': 'v8.46',
        'description': 'Subscription entitlement sync/reconciliation command.',
        'recommended_smoke': 'python manage.py sync_subscription_entitlements --limit 100 --json',
    },
    {
        'key': 'check_commerce_readiness',
        'name': 'check_commerce_readiness',
        'version': 'v8.50',
        'description': 'Emit this trainer commerce readiness report from CLI.',
        'recommended_smoke': 'python manage.py check_commerce_readiness --json',
    },
]


SMOKE_COMMANDS = [
    {
        'key': 'backend_syntax_commerce',
        'title': 'Backend commerce syntax/import surface',
        'command': 'python -m py_compile apps/ops/commerce_readiness.py apps/trainers/revenue.py apps/trainers/content_analytics.py apps/products/services.py apps/orders/checkout_integrity.py apps/subscriptions/lifecycle.py apps/entitlements/access_audit.py apps/trainers/onboarding_flow.py',
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
        'key': 'commerce_tests',
        'title': 'Commerce readiness test subset',
        'command': 'pytest -q tests/test_trainer_revenue_dashboard.py tests/test_trainer_payout_request_flow.py tests/test_trainer_content_analytics.py tests/test_trainer_product_builder.py tests/test_checkout_order_integrity.py tests/test_subscription_lifecycle_hardening.py tests/test_entitlement_access_control_audit.py tests/test_trainer_onboarding_production_flow.py tests/test_ops_admin_commerce_readiness.py',
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


def _rank(status: str) -> int:
    return _STATUS_RANK.get(status, 2)


def _worst_status(statuses: list[str]) -> str:
    if not statuses:
        return 'ok'
    return sorted(statuses, key=_rank, reverse=True)[0]


def _ok_check(key: str, category: str, title: str, **extra: Any) -> dict[str, Any]:
    return {'key': key, 'category': category, 'title': title, 'status': 'ok', **extra}


def _problem_check(key: str, category: str, title: str, status: str, detail: str, **extra: Any) -> dict[str, Any]:
    return {'key': key, 'category': category, 'title': title, 'status': status, 'detail': detail, **extra}


def _check_url(contract: UrlContract) -> dict[str, Any]:
    try:
        actual = reverse(contract.name, args=contract.args)
    except NoReverseMatch as exc:
        return _problem_check(
            contract.key,
            'api_surface',
            contract.description,
            'critical',
            f'Route name {contract.name!r} is not registered: {exc}',
            version=contract.version,
            name=contract.name,
            expected_path=contract.expected_path,
        )

    if actual != contract.expected_path:
        return _problem_check(
            contract.key,
            'api_surface',
            contract.description,
            'degraded',
            f'Expected {contract.expected_path}, got {actual}',
            version=contract.version,
            name=contract.name,
            expected_path=contract.expected_path,
            actual_path=actual,
        )

    return _ok_check(
        contract.key,
        'api_surface',
        contract.description,
        version=contract.version,
        name=contract.name,
        expected_path=contract.expected_path,
        actual_path=actual,
    )


def _check_symbol(contract: SymbolContract) -> dict[str, Any]:
    try:
        module = import_module(contract.module)
    except Exception as exc:  # pragma: no cover - exact import error depends on deployment config
        return _problem_check(
            contract.key,
            'python_surface',
            contract.description,
            'critical',
            f'Cannot import {contract.module}: {exc}',
            version=contract.version,
            module=contract.module,
            attr=contract.attr,
        )

    if not hasattr(module, contract.attr):
        return _problem_check(
            contract.key,
            'python_surface',
            contract.description,
            'critical',
            f'{contract.module}.{contract.attr} is missing.',
            version=contract.version,
            module=contract.module,
            attr=contract.attr,
        )

    return _ok_check(
        contract.key,
        'python_surface',
        contract.description,
        version=contract.version,
        module=contract.module,
        attr=contract.attr,
    )


def _check_command(item: dict[str, Any]) -> dict[str, Any]:
    commands = get_commands()
    name = item['name']
    if name not in commands:
        return _problem_check(
            item['key'],
            'management_commands',
            item['description'],
            'degraded',
            f'Management command {name!r} is not registered.',
            version=item['version'],
            command=name,
            recommended_smoke=item.get('recommended_smoke'),
        )
    return _ok_check(
        item['key'],
        'management_commands',
        item['description'],
        version=item['version'],
        command=name,
        app_label=commands.get(name),
        recommended_smoke=item.get('recommended_smoke'),
    )


def _summary(checks: list[dict[str, Any]]) -> dict[str, Any]:
    by_status: dict[str, int] = {}
    by_category: dict[str, int] = {}
    for check in checks:
        by_status[check['status']] = by_status.get(check['status'], 0) + 1
        by_category[check['category']] = by_category.get(check['category'], 0) + 1
    return {
        'total_checks': len(checks),
        'ok_count': by_status.get('ok', 0),
        'warning_count': by_status.get('warning', 0),
        'degraded_count': by_status.get('degraded', 0),
        'critical_count': by_status.get('critical', 0),
        'by_status': by_status,
        'by_category': by_category,
        'commerce_blocks': {
            'trainer_money': ['v8.41', 'v8.42'],
            'trainer_growth': ['v8.43', 'v8.44'],
            'checkout_access': ['v8.45', 'v8.46', 'v8.47'],
            'trainer_activation': ['v8.48'],
            'public_storefront': ['v8.49'],
            'readiness_checkpoint': ['v8.50'],
        },
    }


def _recommendations(checks: list[dict[str, Any]]) -> list[dict[str, str]]:
    failed = [check for check in checks if check['status'] in {'degraded', 'critical'}]
    if not failed:
        return [
            {
                'key': 'run_full_smoke',
                'priority': 'normal',
                'title': 'Run full commerce smoke before the next feature block.',
                'detail': 'Run pytest -q, manage.py check, npm run typecheck, npm run build and npm run test:contracts.',
            }
        ]
    return [
        {
            'key': f"fix_{check['key']}",
            'priority': 'high' if check['status'] == 'critical' else 'normal',
            'title': f"Fix {check['category']}::{check['key']}",
            'detail': check.get('detail', check.get('title', 'Readiness check failed.')),
        }
        for check in failed[:10]
    ]


def get_commerce_readiness(
    *,
    include_commands: bool = True,
    include_frontend: bool = True,
    include_recommendations: bool = True,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    checks.extend(_check_url(contract) for contract in URL_CONTRACTS)
    checks.extend(_check_symbol(contract) for contract in SYMBOL_CONTRACTS)
    if include_commands:
        checks.extend(_check_command(item) for item in MANAGEMENT_COMMANDS)

    statuses = [check['status'] for check in checks]
    payload: dict[str, Any] = {
        'status': _worst_status(statuses),
        'generated_at': timezone.now(),
        'version': 'v8.50',
        'scope': 'trainer commerce readiness',
        'summary': _summary(checks),
        'checks': checks,
        'api_surface': [check for check in checks if check['category'] == 'api_surface'],
    }
    if include_frontend:
        payload['frontend_surface'] = FRONTEND_SURFACE
    if include_commands:
        payload['management_commands'] = MANAGEMENT_COMMANDS
        payload['smoke_commands'] = SMOKE_COMMANDS
    if include_recommendations:
        payload['recommendations'] = _recommendations(checks)
    return payload
