import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from scripts.bootstrap.seed_demo import build_demo_seed_payload
from scripts.bootstrap.seed_demo import _assert_demo_seed_allowed


def test_demo_seed_payload_declares_launch_scenarios():
    payload = build_demo_seed_payload()

    assert payload['version'] == 'v117'
    assert set(payload['scenarios']) == {
        'trainer_with_products',
        'student_with_active_course',
        'failed_payment',
        'refunded_order',
        'payout_ready',
        'subscription_expired',
    }


def test_demo_seed_payload_has_business_fixture_sections():
    payload = build_demo_seed_payload()

    assert {account['key'] for account in payload['accounts']} == {'trainer_anna', 'student_mila'}
    assert payload['trainers'][0]['products'] == [
        'mobility-foundations',
        'kettlebell-basics',
        'starter-bundle',
    ]
    assert {order['key'] for order in payload['commerce']['orders']} == {
        'student_active_course_order',
        'student_failed_payment_order',
        'student_refunded_order',
    }
    assert payload['commerce']['entitlements'][0]['status'] == 'active'
    assert payload['commerce']['subscriptions'][0]['status'] == 'expired'
    assert payload['finance']['payouts'][0]['status'] == 'approved'


@override_settings(IS_PRODUCTION=True)
def test_demo_seed_script_is_blocked_in_production_without_explicit_allow(monkeypatch):
    monkeypatch.delenv('ALLOW_DEMO_SEED', raising=False)

    with pytest.raises(RuntimeError, match='Demo seed is disabled in production'):
        _assert_demo_seed_allowed()


@pytest.mark.django_db
@override_settings(IS_PRODUCTION=True)
def test_create_demo_users_command_is_blocked_in_production_without_explicit_allow(monkeypatch):
    monkeypatch.delenv('ALLOW_DEMO_SEED', raising=False)

    with pytest.raises(CommandError, match='Demo users are disabled in production'):
        call_command('create_demo_users')
