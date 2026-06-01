from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent
from apps.referrals.models import ReferralCode, ReferralInvite, ReferralProgram
from apps.referrals.services import ReferralEngine, ReferralRewardService


@pytest.fixture
def referral_csv_audit_fixture(db):
    User = get_user_model()
    admin = User.objects.create_superuser(email="admin-v56@example.com", password="strong-pass-123")
    owner = User.objects.create_user(email="owner-v56@example.com", password="strong-pass-123")
    referred = User.objects.create_user(email="buyer-v56@example.com", password="strong-pass-123")
    outsider = User.objects.create_user(email="outsider-v56@example.com", password="strong-pass-123")

    program = ReferralProgram.objects.create(
        slug="ambassador-v56",
        name="Ambassador v56",
        reward_kind="fixed",
        reward_amount=Decimal("250.00"),
    )
    code = ReferralCode.objects.create(program=program, owner=owner, code="AMBV56")
    invite = ReferralInvite.objects.create(
        code=code,
        landing_path="/catalog",
        utm_source="vk",
        utm_medium="social",
        utm_campaign="summer-v56",
        click_session_key="session-v56",
    )
    attribution = ReferralEngine.bind_signup(invite=invite, referred_user=referred)
    reward = ReferralRewardService.reward_for_paid_order(
        attribution=attribution,
        trigger_reference="order-v56-1",
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


@pytest.mark.django_db
def test_admin_referral_rewards_csv_export_writes_audit_event(referral_csv_audit_fixture):
    client = APIClient()
    client.force_authenticate(referral_csv_audit_fixture["admin"])

    response = client.get(
        "/api/v1/referrals/admin/rewards/export.csv",
        {"program_slug": "ambassador-v56", "search": "order-v56-1"},
        HTTP_X_CORRELATION_ID="corr-v56-rewards",
        HTTP_USER_AGENT="pytest-v56",
        REMOTE_ADDR="127.0.0.56",
    )

    assert response.status_code == 200
    event = AuditEvent.objects.get(
        event_type="admin.referrals.csv_export",
        entity_type="referral_export",
        entity_id="rewards",
    )
    assert event.actor == referral_csv_audit_fixture["admin"]
    assert event.ip_address == "127.0.0.56"
    assert event.user_agent == "pytest-v56"
    assert event.context["action"] == "referrals.csv_export"
    assert event.context["target_type"] == "referral_export"
    assert event.context["target_id"] == "rewards"
    assert event.context["request"]["method"] == "GET"
    assert event.context["request"]["correlation_id"] == "corr-v56-rewards"
    assert event.context["context"]["export_kind"] == "rewards"
    assert event.context["context"]["filename"] == "referral_rewards.csv"
    assert event.context["context"]["row_count"] == 1
    assert event.context["context"]["total_count"] == 1
    assert event.context["context"]["limit"] == 10000
    assert event.context["context"]["truncated"] is False
    assert event.context["context"]["filters"] == {
        "program_slug": "ambassador-v56",
        "search": "order-v56-1",
    }


@pytest.mark.django_db
def test_admin_referral_ledger_and_invite_csv_exports_write_separate_audit_events(referral_csv_audit_fixture):
    client = APIClient()
    client.force_authenticate(referral_csv_audit_fixture["admin"])

    ledger_response = client.get(
        "/api/v1/referrals/admin/ledger/export.csv",
        {"program_slug": "ambassador-v56"},
    )
    invite_response = client.get(
        "/api/v1/referrals/admin/invites/export.csv",
        {"status": ReferralInvite.STATUS_CONVERTED, "utm_campaign": "summer-v56"},
    )

    assert ledger_response.status_code == 200
    assert invite_response.status_code == 200

    ledger_event = AuditEvent.objects.get(entity_id="ledger")
    invite_event = AuditEvent.objects.get(entity_id="invites")

    assert ledger_event.event_type == "admin.referrals.csv_export"
    assert ledger_event.context["context"]["export_kind"] == "ledger"
    assert ledger_event.context["context"]["filename"] == "referral_ledger.csv"
    assert ledger_event.context["context"]["row_count"] == 1
    assert ledger_event.context["context"]["filters"] == {"program_slug": "ambassador-v56"}

    assert invite_event.event_type == "admin.referrals.csv_export"
    assert invite_event.context["context"]["export_kind"] == "invites"
    assert invite_event.context["context"]["filename"] == "referral_invites.csv"
    assert invite_event.context["context"]["row_count"] == 1
    assert invite_event.context["context"]["filters"] == {
        "status": ReferralInvite.STATUS_CONVERTED,
        "utm_campaign": "summer-v56",
    }


@pytest.mark.django_db
def test_forbidden_referral_csv_export_does_not_write_audit_event(referral_csv_audit_fixture):
    client = APIClient()
    client.force_authenticate(referral_csv_audit_fixture["outsider"])

    response = client.get("/api/v1/referrals/admin/rewards/export.csv")

    assert response.status_code == 403
    assert AuditEvent.objects.count() == 0
