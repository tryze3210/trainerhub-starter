from __future__ import annotations

from dataclasses import dataclass

import pytest
from django.urls import resolve


@dataclass(frozen=True)
class ApiRouteCase:
    key: str
    path: str
    url_name: str
    area: str


FRONTEND_API_ROUTE_MATRIX = (
    ApiRouteCase('auth_register', '/api/v1/auth/register/', 'auth-register', 'auth'),
    ApiRouteCase('auth_login', '/api/v1/auth/login/', 'auth-login', 'auth'),
    ApiRouteCase('auth_refresh', '/api/v1/auth/refresh/', 'auth-refresh', 'auth'),
    ApiRouteCase('auth_logout', '/api/v1/auth/logout/', 'auth-logout', 'auth'),
    ApiRouteCase('auth_me', '/api/v1/auth/me/', 'auth-me', 'auth'),
    ApiRouteCase(
        'marketplace_home',
        '/api/v1/public-catalog/',
        'public-marketplace-home',
        'public',
    ),
    ApiRouteCase(
        'content_landing',
        '/api/v1/public-catalog/landing/program/demo-program/',
        'public-marketplace-content-landing',
        'public',
    ),
    ApiRouteCase(
        'trainer_landing',
        '/api/v1/public-catalog/trainers/demo-trainer/landing/',
        'public-marketplace-trainer-landing',
        'public',
    ),
    ApiRouteCase('content_videos', '/api/v1/content/videos/', 'published-videos-list', 'catalog'),
    ApiRouteCase(
        'content_video_detail',
        '/api/v1/content/videos/demo-video/',
        'published-videos-detail',
        'catalog',
    ),
    ApiRouteCase(
        'content_programs',
        '/api/v1/content/programs/',
        'published-programs-list',
        'catalog',
    ),
    ApiRouteCase(
        'content_program_detail',
        '/api/v1/content/programs/demo-program/',
        'published-programs-detail',
        'catalog',
    ),
    ApiRouteCase(
        'content_bundles',
        '/api/v1/content/bundles/',
        'published-bundles-list',
        'catalog',
    ),
    ApiRouteCase(
        'content_bundle_detail',
        '/api/v1/content/bundles/demo-bundle/',
        'published-bundles-detail',
        'catalog',
    ),
    ApiRouteCase('trainers_catalog', '/api/v1/trainers/', 'trainer-catalog', 'trainers'),
    ApiRouteCase('trainer_detail', '/api/v1/trainers/demo-trainer/', 'trainer-detail', 'trainers'),
    ApiRouteCase(
        'trainer_onboarding_status',
        '/api/v1/trainers/me/onboarding/status/',
        'trainer-me-onboarding-status',
        'trainers',
    ),
    ApiRouteCase(
        'trainer_application_status',
        '/api/v1/trainers/me/application-status/',
        'trainer-me-application-status',
        'trainers',
    ),
    ApiRouteCase(
        'admin_trainer_applications',
        '/api/v1/trainers/admin/applications/',
        'trainer-admin-application-list',
        'admin',
    ),
    ApiRouteCase(
        'admin_trainer_application_readiness',
        '/api/v1/trainers/admin/applications/readiness/',
        'trainer-admin-application-readiness',
        'admin',
    ),
    ApiRouteCase('order_checkout', '/api/v1/orders/checkout/', 'orders-checkout', 'commerce'),
    ApiRouteCase(
        'payment_webhook_receive',
        '/api/v1/payments-webhooks/receive/',
        'payments-webhooks-receive',
        'commerce',
    ),
    ApiRouteCase('payout_wallet', '/api/v1/payouts/my/balance/', 'my-payouts-balance', 'payouts'),
    ApiRouteCase(
        'payout_request',
        '/api/v1/payouts/my/request/',
        'my-payouts-request-payout',
        'payouts',
    ),
    ApiRouteCase(
        'admin_payout_overview',
        '/api/v1/payouts/admin/overview/',
        'admin-payouts-overview',
        'payouts',
    ),
    ApiRouteCase(
        'admin_payout_approve',
        '/api/v1/payouts/admin/demo-payout/approve/',
        'admin-payouts-approve',
        'payouts',
    ),
    ApiRouteCase(
        'trainer_products',
        '/api/v1/products/trainer/',
        'trainer-products-list',
        'products',
    ),
    ApiRouteCase(
        'subscription_lifecycle_policy',
        '/api/v1/subscriptions/lifecycle-policy/',
        'subscriptions-lifecycle-policy',
        'subscriptions',
    ),
    ApiRouteCase(
        'subscription_admin_reconcile_entitlements',
        '/api/v1/subscriptions/admin/reconcile-entitlements/',
        'subscriptions-admin-reconcile-entitlements',
        'subscriptions',
    ),
    ApiRouteCase(
        'entitlement_access_check',
        '/api/v1/entitlements/me/access-check/',
        'entitlements-me-access-check',
        'access',
    ),
    ApiRouteCase(
        'ops_operations_dashboard',
        '/api/v1/ops/admin/operations-dashboard/',
        'ops-admin-operations-dashboard',
        'ops',
    ),
    ApiRouteCase(
        'ops_production_readiness',
        '/api/v1/ops/admin/production-readiness/',
        'ops-admin-production-readiness',
        'ops',
    ),
    ApiRouteCase(
        'ops_reconciliation_snapshot_issues',
        '/api/v1/ops/admin/reconciliation-snapshots/issues/',
        'ops-admin-reconciliation-snapshot-issues',
        'ops',
    ),
    ApiRouteCase(
        'referrals_admin_ops',
        '/api/v1/referrals/admin/ops/overview/',
        'referrals-admin-ops-overview',
        'referrals',
    ),
    ApiRouteCase(
        'referrals_rewards_export',
        '/api/v1/referrals/admin/rewards/export.csv',
        'referrals-admin-rewards-export',
        'referrals',
    ),
    ApiRouteCase(
        'audit_events_export',
        '/api/v1/audit/admin/events/export.csv',
        'admin-audit-events-export',
        'audit',
    ),
    ApiRouteCase(
        'booking_schedule',
        '/api/v1/booking/me/schedule/',
        'booking-me-schedule',
        'booking',
    ),
    ApiRouteCase(
        'booking_attendance_check_in',
        '/api/v1/booking/attendance/check-in/',
        'booking-attendance-check-in',
        'booking',
    ),
    ApiRouteCase('messaging_inbox', '/api/v1/messaging/me/inbox/', 'messaging-inbox', 'messaging'),
    ApiRouteCase(
        'notifications_inbox',
        '/api/v1/notifications/inbox/',
        'notification-inbox',
        'notifications',
    ),
)


@pytest.mark.parametrize('case', FRONTEND_API_ROUTE_MATRIX, ids=lambda case: case.key)
def test_v167_frontend_api_route_matrix_resolves_to_expected_url_name(
    case: ApiRouteCase,
) -> None:
    match = resolve(case.path)

    assert match.url_name == case.url_name


def test_v167_frontend_api_route_matrix_covers_core_areas() -> None:
    areas = {case.area for case in FRONTEND_API_ROUTE_MATRIX}

    assert {
        'auth',
        'public',
        'catalog',
        'trainers',
        'commerce',
        'payouts',
        'ops',
        'booking',
        'messaging',
        'notifications',
    }.issubset(areas)
