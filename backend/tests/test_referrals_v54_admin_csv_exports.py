from decimal import Decimal
import csv
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.referrals.models import ReferralCode, ReferralInvite, ReferralLedger, ReferralProgram
from apps.referrals.services import ReferralEngine, ReferralRewardService


@pytest.fixture
def referral_export_fixture(db):
    User = get_user_model()
    admin = User.objects.create_superuser(email="admin-v54@example.com", password="strong-pass-123")
    owner = User.objects.create_user(email="owner-v54@example.com", password="strong-pass-123")
    referred = User.objects.create_user(email="buyer-v54@example.com", password="strong-pass-123")
    outsider = User.objects.create_user(email="outsider-v54@example.com", password="strong-pass-123")

    program = ReferralProgram.objects.create(
        slug="ambassador-v54",
        name="Ambassador v54",
        reward_kind="fixed",
        reward_amount=Decimal("250.00"),
    )
    code = ReferralCode.objects.create(program=program, owner=owner, code="AMBV54")
    invite = ReferralInvite.objects.create(
        code=code,
        landing_path="/catalog",
        utm_source="vk",
        utm_medium="social",
        utm_campaign="summer-v54",
        click_session_key="session-v54",
    )
    attribution = ReferralEngine.bind_signup(invite=invite, referred_user=referred)
    reward = ReferralRewardService.reward_for_paid_order(
        attribution=attribution,
        trigger_reference="order-v54-1",
        order_amount=Decimal("1000.00"),
    )
    return {
        "admin": admin,
        "owner": owner,
        "referred": referred,
        "outsider": outsider,
        "program": program,
        "invite": invite,
        "attribution": attribution,
        "reward": reward,
    }


def _csv_rows(response):
    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv")
    content = response.content.decode("utf-8-sig")
    return list(csv.DictReader(StringIO(content)))


@pytest.mark.django_db
def test_admin_can_export_referral_rewards_csv_with_existing_filters(referral_export_fixture):
    client = APIClient()
    client.force_authenticate(referral_export_fixture["admin"])

    response = client.get(
        "/api/v1/referrals/admin/rewards/export.csv",
        {"program_slug": "ambassador-v54", "search": "order-v54-1"},
    )

    rows = _csv_rows(response)
    assert response["Content-Disposition"] == 'attachment; filename="referral_rewards.csv"'
    assert len(rows) == 1
    assert rows[0]["trigger_reference"] == "order-v54-1"
    assert rows[0]["amount"] == "250.00"
    assert rows[0]["program_slug"] == "ambassador-v54"
    assert rows[0]["owner_email"] == "owner-v54@example.com"
    assert rows[0]["referred_user_email"] == "buyer-v54@example.com"
    assert rows[0]["ledger_entry_count"] == "1"


@pytest.mark.django_db
def test_admin_can_export_referral_ledger_and_invites_csv(referral_export_fixture):
    client = APIClient()
    client.force_authenticate(referral_export_fixture["admin"])

    ledger_response = client.get("/api/v1/referrals/admin/ledger/export.csv", {"program_slug": "ambassador-v54"})
    invite_response = client.get("/api/v1/referrals/admin/invites/export.csv", {"status": ReferralInvite.STATUS_CONVERTED})

    ledger_rows = _csv_rows(ledger_response)
    invite_rows = _csv_rows(invite_response)

    assert len(ledger_rows) == 1
    assert ledger_rows[0]["entry_type"] == ReferralLedger.ENTRY_REWARD
    assert ledger_rows[0]["balance_after"] == "250.00"
    assert ledger_rows[0]["reward_status"] == "approved"

    assert len(invite_rows) == 1
    assert invite_rows[0]["code_value"] == "AMBV54"
    assert invite_rows[0]["status"] == ReferralInvite.STATUS_CONVERTED
    assert invite_rows[0]["utm_campaign"] == "summer-v54"
    assert invite_rows[0]["referred_user_email"] == "buyer-v54@example.com"


@pytest.mark.django_db
def test_referral_csv_exports_are_admin_only(referral_export_fixture):
    client = APIClient()
    client.force_authenticate(referral_export_fixture["outsider"])

    rewards = client.get("/api/v1/referrals/admin/rewards/export.csv")
    ledger = client.get("/api/v1/referrals/admin/ledger/export.csv")
    invites = client.get("/api/v1/referrals/admin/invites/export.csv")

    assert rewards.status_code == 403
    assert ledger.status_code == 403
    assert invites.status_code == 403
