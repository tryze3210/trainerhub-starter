from __future__ import annotations

import json
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.payouts.models import PayoutRequest, TrainerWallet
from apps.payouts.services import PayoutService
from apps.trainers.models import TrainerProfile


@pytest.mark.django_db
def test_payout_readiness_endpoint_is_admin_only():
    user = get_user_model().objects.create_user(email="payout-readiness-user@example.com", password="pass12345")
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/v1/payouts/admin/readiness/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_read_payout_readiness_endpoint():
    admin = get_user_model().objects.create_superuser(email="payout-readiness-admin@example.com", password="pass12345")
    trainer_user = get_user_model().objects.create_user(
        email="payout-readiness-trainer@example.com",
        password="pass12345",
        role="trainer",
    )
    trainer = TrainerProfile.objects.create(
        user=trainer_user,
        slug="payout-readiness-trainer",
        display_name="Payout Readiness Trainer",
        status="active",
    )
    wallet = TrainerWallet.objects.create(
        trainer=trainer,
        currency="RUB",
        available_amount=Decimal("1000.00"),
    )
    payout = PayoutService.request_payout(
        trainer_id=trainer_user.id,
        amount=Decimal("250.00"),
        destination_masked="**** 4242",
    )

    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get("/api/v1/payouts/admin/readiness/?include_projection=false")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"ok", "degraded", "critical"}
    assert payload["summary"]["active_payouts"]["count"] >= 1
    assert any(item["code"] == "payout_transition_surface" for item in payload["checks"])
    assert "GET /api/v1/payouts/admin/readiness/" in payload["api_surface"]["admin"]
    assert payload["workflow"]["transition_matrix"][PayoutRequest.Status.PENDING] == ["approve", "reject"]
    wallet.refresh_from_db()
    assert wallet.locked_amount == Decimal("250.00")
    assert payout.status == PayoutRequest.Status.PENDING


@pytest.mark.django_db
def test_check_payout_readiness_management_command_outputs_json():
    buffer = __import__("io").StringIO()

    call_command("check_payout_readiness", "--json", "--skip-projection", stdout=buffer)

    payload = json.loads(buffer.getvalue())
    assert payload["status"] in {"ok", "degraded", "critical"}
    assert "summary" in payload
    assert any(item["code"] == "wallet_non_negative_balances" for item in payload["checks"])
