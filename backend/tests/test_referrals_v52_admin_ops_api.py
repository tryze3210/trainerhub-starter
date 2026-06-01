from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.referrals.models import ReferralCode, ReferralInvite, ReferralLedger, ReferralProgram, ReferralReward
from apps.referrals.services import ReferralEngine, ReferralRewardService


@pytest.fixture
def referral_ops_fixture(db):
    User = get_user_model()
    admin = User.objects.create_superuser(email="admin-v52@example.com", password="strong-pass-123")
    owner = User.objects.create_user(email="owner-v52@example.com", password="strong-pass-123")
    referred = User.objects.create_user(email="buyer-v52@example.com", password="strong-pass-123")

    program = ReferralProgram.objects.create(
        slug="ambassador-v52",
        name="Ambassador v52",
        reward_kind="fixed",
        reward_amount=Decimal("250.00"),
    )
    code = ReferralCode.objects.create(program=program, owner=owner, code="AMBV52")
    invite = ReferralInvite.objects.create(
        code=code,
        landing_path="/catalog",
        utm_source="vk",
        utm_medium="social",
        utm_campaign="summer-v52",
        click_session_key="session-v52",
    )
    attribution = ReferralEngine.bind_signup(invite=invite, referred_user=referred)
    reward = ReferralRewardService.reward_for_paid_order(
        attribution=attribution,
        trigger_reference="order-v52-1",
        order_amount=Decimal("1000.00"),
    )
    return {
        "admin": admin,
        "owner": owner,
        "referred": referred,
        "program": program,
        "invite": invite,
        "attribution": attribution,
        "reward": reward,
    }


def _results(payload):
    return payload.get("results", payload)


@pytest.mark.django_db
def test_admin_referral_ops_overview_returns_financial_and_integrity_snapshot(referral_ops_fixture):
    client = APIClient()
    client.force_authenticate(referral_ops_fixture["admin"])

    response = client.get("/api/v1/referrals/admin/ops/overview/?days=30")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["summary"]["programs"] == 1
    assert payload["summary"]["codes"] == 1
    assert payload["summary"]["invites"] == 1
    assert payload["summary"]["converted_invites"] == 1
    assert payload["summary"]["attributions"] == 1
    assert payload["summary"]["approved_rewards"] == 1
    assert payload["summary"]["approved_reward_amount"] == "250.00"
    assert payload["integrity"]["approved_rewards_without_ledger"] == 0
    assert payload["latest_rewards"][0]["trigger_reference"] == "order-v52-1"


@pytest.mark.django_db
def test_admin_referral_rewards_endpoint_supports_filters_and_detail(referral_ops_fixture):
    client = APIClient()
    client.force_authenticate(referral_ops_fixture["admin"])
    reward = referral_ops_fixture["reward"]

    list_response = client.get(
        "/api/v1/referrals/admin/rewards/",
        {"status": ReferralReward.STATUS_APPROVED, "program_slug": "ambassador-v52", "search": "order-v52-1"},
    )

    assert list_response.status_code == 200
    rows = _results(list_response.json())
    assert len(rows) == 1
    assert rows[0]["id"] == str(reward.id)
    assert rows[0]["owner_email"] == "owner-v52@example.com"
    assert rows[0]["referred_user_email"] == "buyer-v52@example.com"
    assert rows[0]["ledger_entry_count"] == 1

    detail_response = client.get(f"/api/v1/referrals/admin/rewards/{reward.id}/")

    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["trigger_reference"] == "order-v52-1"
    assert detail["amount"] == "250.00"


@pytest.mark.django_db
def test_admin_referral_ledger_and_invites_endpoints_are_staff_only(referral_ops_fixture):
    User = get_user_model()
    non_admin = User.objects.create_user(email="not-admin-v52@example.com", password="strong-pass-123")
    client = APIClient()
    client.force_authenticate(non_admin)

    forbidden = client.get("/api/v1/referrals/admin/ledger/")
    assert forbidden.status_code == 403

    client.force_authenticate(referral_ops_fixture["admin"])
    ledger_response = client.get("/api/v1/referrals/admin/ledger/", {"program_slug": "ambassador-v52"})
    invite_response = client.get("/api/v1/referrals/admin/invites/", {"status": ReferralInvite.STATUS_CONVERTED})
    attribution_response = client.get("/api/v1/referrals/admin/attributions/", {"program_slug": "ambassador-v52"})

    assert ledger_response.status_code == 200
    assert invite_response.status_code == 200
    assert attribution_response.status_code == 200

    ledger_rows = _results(ledger_response.json())
    invite_rows = _results(invite_response.json())
    attribution_rows = _results(attribution_response.json())

    assert len(ledger_rows) == 1
    assert len(invite_rows) == 1
    assert len(attribution_rows) == 1
    assert ReferralLedger.objects.count() == 1
