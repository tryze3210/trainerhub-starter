from __future__ import annotations

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.admin_panel.api.views import PayoutAdminViewSet
from apps.audit.models import AuditEvent
from apps.payouts.models import PayoutRequest, TrainerWallet
from apps.trainers.models import TrainerProfile


@pytest.fixture
def payout_dataset(db):
    User = get_user_model()
    admin = User.objects.create_superuser(email="legacy-payout-admin@example.com", password="pass")
    trainer_user = User.objects.create_user(
        email="legacy-payout-trainer@example.com",
        password="pass",
        role="trainer",
    )
    trainer = TrainerProfile.objects.create(
        user=trainer_user,
        slug="legacy-payout-trainer",
        display_name="Legacy Payout Trainer",
        status="active",
    )
    wallet = TrainerWallet.objects.create(
        trainer=trainer,
        currency="RUB",
        available_amount=Decimal("700.00"),
        locked_amount=Decimal("300.00"),
    )
    payout = PayoutRequest.objects.create(
        trainer=trainer,
        wallet=wallet,
        amount=Decimal("300.00"),
        currency="RUB",
        status=PayoutRequest.Status.PENDING,
        destination_json={"destination_masked": "Tinkoff **** 4242"},
    )
    return admin, trainer, payout


@pytest.mark.django_db
@override_settings(PAYOUTS_REQUIRE_LEGAL_ELIGIBILITY=True)
def test_legacy_admin_panel_payout_approve_logs_eligibility_block(payout_dataset):
    admin, trainer, payout = payout_dataset
    factory = APIRequestFactory()
    request = factory.post(f"/legacy/payouts/{payout.id}/approve/")
    force_authenticate(request, user=admin)
    view = PayoutAdminViewSet.as_view({"post": "approve"})

    response = view(request, pk=str(payout.id))

    assert response.status_code == 400
    payout.refresh_from_db()
    assert payout.status == PayoutRequest.Status.PENDING
    audit_event = AuditEvent.objects.get(event_type="payout.eligibility_blocked", entity_id=str(payout.id))
    assert audit_event.actor == admin
    assert audit_event.context["action"] == "approve"
    assert audit_event.context["trainer_id"] == str(trainer.user_id)
    assert audit_event.context["surface"] == "legacy_admin_panel"
    assert "kyc_profile_missing" in audit_event.context["block_reason"]


@pytest.mark.django_db
def test_legacy_admin_panel_payout_list_exposes_eligibility(payout_dataset):
    admin, trainer, payout = payout_dataset
    factory = APIRequestFactory()
    request = factory.get("/legacy/payouts/")
    force_authenticate(request, user=admin)
    view = PayoutAdminViewSet.as_view({"get": "list"})

    response = view(request)

    assert response.status_code == 200
    row = response.data[0]
    assert row["id"] == str(payout.id)
    assert row["trainer_id"] == str(trainer.user_id)
    assert row["status"] == PayoutRequest.Status.PENDING
    assert row["payout_eligibility"]["is_eligible"] is False
    assert "kyc_profile_missing" in row["payout_eligibility"]["block_reason"]
