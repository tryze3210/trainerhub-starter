from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from apps.entitlements.models import Entitlement, EntitlementSourceType, EntitlementStatus
from apps.subscriptions.lifecycle import SubscriptionLifecycleService
from apps.subscriptions.models import Subscription, SubscriptionPlan, SubscriptionStatus
from apps.subscriptions.services import SubscriptionService


pytestmark = pytest.mark.django_db


def make_user(email='subscriber@example.com', *, is_staff=False, is_superuser=False):
    return get_user_model().objects.create_user(
        email=email,
        password='pass12345',
        is_staff=is_staff,
        is_superuser=is_superuser,
    )


def make_plan(title='Monthly plan'):
    return SubscriptionPlan.objects.create(
        title=title,
        period_days=30,
        price=Decimal('990.00'),
        currency='RUB',
        is_active=True,
    )


def test_subscription_lifecycle_policy_and_renewal_projection_are_available():
    user = make_user()
    plan = make_plan()
    subscription = SubscriptionService.activate_subscription(user=user, plan=plan, auto_renew=True)

    client = APIClient()
    client.force_authenticate(user=user)

    policy_response = client.get('/api/v1/subscriptions/lifecycle-policy/')
    projection_response = client.get(f'/api/v1/subscriptions/{subscription.id}/renewal-projection/')

    assert policy_response.status_code == 200, policy_response.data
    assert 'active' in policy_response.data['supported_statuses']
    assert policy_response.data['virtual_statuses']['trialing']['persisted'] is False
    assert projection_response.status_code == 200, projection_response.data
    assert projection_response.data['subscription_id'] == str(subscription.id)
    assert projection_response.data['can_renew'] is True
    assert projection_response.data['amount'] == '990.00'


def test_cancel_resume_and_sync_entitlements_are_idempotent():
    user = make_user('subscriber-sync@example.com')
    plan = make_plan('Sync plan')
    subscription = SubscriptionService.activate_subscription(user=user, plan=plan, auto_renew=True)
    assert Entitlement.objects.filter(
        user=user,
        source_type=EntitlementSourceType.SUBSCRIPTION,
        source_subscription=subscription,
        status=EntitlementStatus.ACTIVE,
    ).count() == 1

    client = APIClient()
    client.force_authenticate(user=user)

    cancel_response = client.post(
        f'/api/v1/subscriptions/{subscription.id}/cancel/',
        {'reason': 'customer_test_cancel'},
        format='json',
    )
    assert cancel_response.status_code == 200, cancel_response.data
    assert cancel_response.data['status'] == SubscriptionStatus.CANCELLED
    assert Entitlement.objects.filter(
        user=user,
        source_subscription=subscription,
        status=EntitlementStatus.ACTIVE,
    ).count() == 0

    resume_response = client.post(
        f'/api/v1/subscriptions/{subscription.id}/resume/',
        {'reason': 'customer_test_resume'},
        format='json',
    )
    assert resume_response.status_code == 200, resume_response.data
    assert resume_response.data['status'] == SubscriptionStatus.ACTIVE
    assert Entitlement.objects.filter(
        user=user,
        source_subscription=subscription,
        status=EntitlementStatus.ACTIVE,
    ).count() == 1

    sync_response = client.post(
        f'/api/v1/subscriptions/{subscription.id}/sync-entitlements/',
        {'reason': 'customer_test_sync'},
        format='json',
    )
    assert sync_response.status_code == 200, sync_response.data
    assert sync_response.data['action'] in {'granted_or_refreshed', 'noop'}
    assert Entitlement.objects.filter(
        user=user,
        source_subscription=subscription,
        status=EntitlementStatus.ACTIVE,
    ).count() == 1


def test_admin_reconcile_entitlements_revokes_expired_access_and_command_outputs_json(capsys):
    admin = make_user('admin-subscriptions@example.com', is_staff=True, is_superuser=True)
    user = make_user('expired-subscriber@example.com')
    plan = make_plan('Expired plan')
    now = timezone.now()
    subscription = Subscription.objects.create(
        user=user,
        plan=plan,
        status=SubscriptionStatus.EXPIRED,
        starts_at=now - timedelta(days=40),
        ends_at=now - timedelta(days=10),
        auto_renew=False,
    )
    Entitlement.objects.create(
        user=user,
        source_type=EntitlementSourceType.SUBSCRIPTION,
        source_subscription=subscription,
        target_type='library',
        target_id=None,
        status=EntitlementStatus.ACTIVE,
        starts_at=subscription.starts_at,
        ends_at=subscription.ends_at,
        metadata={'fixture': True},
    )

    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.post(
        '/api/v1/subscriptions/admin/reconcile-entitlements/',
        {'subscription_id': str(subscription.id)},
        format='json',
    )
    assert response.status_code == 200, response.data
    assert response.data['checked_count'] == 1
    assert response.data['revoked_count'] == 1
    assert Entitlement.objects.filter(
        source_subscription=subscription,
        status=EntitlementStatus.ACTIVE,
    ).count() == 0

    call_command('sync_subscription_entitlements', '--subscription-id', str(subscription.id), '--json')
    stdout = capsys.readouterr().out
    assert 'checked_count' in stdout


def test_lifecycle_summary_marks_due_soon_and_expired_due():
    user = make_user('summary-subscriber@example.com')
    plan = make_plan('Summary plan')
    now = timezone.now()
    Subscription.objects.create(
        user=user,
        plan=plan,
        status=SubscriptionStatus.ACTIVE,
        starts_at=now - timedelta(days=20),
        ends_at=now + timedelta(days=3),
        auto_renew=True,
    )
    Subscription.objects.create(
        user=user,
        plan=plan,
        status=SubscriptionStatus.PAST_DUE,
        starts_at=now - timedelta(days=40),
        ends_at=now - timedelta(days=1),
        auto_renew=True,
    )

    payload = SubscriptionLifecycleService.get_lifecycle_summary(user=user, days=30)

    assert payload['summary']['due_soon_count'] == 1
    assert payload['summary']['expired_due_count'] == 1
    assert payload['summary']['active_count'] == 1
    assert payload['summary']['past_due_count'] == 1
