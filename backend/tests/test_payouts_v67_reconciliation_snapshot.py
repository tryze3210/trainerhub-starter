from __future__ import annotations

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.payouts.models import PayoutRequest, TrainerWallet
from apps.trainers.models import TrainerProfile


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    User = get_user_model()
    user = User.objects.create_user(email="admin-payout-v67@example.com", password="strong-pass-123")
    user.is_staff = True
    user.is_superuser = True
    user.save(update_fields=["is_staff", "is_superuser"])
    return user


@pytest.fixture
def reconciliation_dataset(db):
    User = get_user_model()
    trainer_user = User.objects.create_user(
        email="trainer-payout-v67@example.com",
        password="strong-pass-123",
        role="trainer",
    )
    trainer = TrainerProfile.objects.create(
        user=trainer_user,
        slug="trainer-payout-v67",
        display_name="Trainer Payout V67",
        status="active",
    )
    wallet = TrainerWallet.objects.create(
        trainer=trainer,
        currency="RUB",
        available_amount=Decimal("1000.00"),
        pending_amount=Decimal("0.00"),
        locked_amount=Decimal("50.00"),
    )
    payout = PayoutRequest.objects.create(
        trainer=trainer,
        wallet=wallet,
        amount=Decimal("250.00"),
        currency="RUB",
        status=PayoutRequest.Status.PENDING,
        destination_json={"destination_masked": "**** 6767"},
    )
    return {"trainer": trainer, "wallet": wallet, "payout": payout}


@pytest.mark.django_db
def test_admin_can_read_payout_reconciliation_snapshot(api_client, admin_user, reconciliation_dataset):
    api_client.force_authenticate(admin_user)

    response = api_client.get("/api/v1/payouts/admin-ops/reconciliation/snapshot/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "read_only_snapshot"
    assert payload["actions"]["repair_performed"] is False
    assert payload["summary"]["status"] in {"healthy", "attention_required"}
    assert payload["summary"]["issue_count"] >= 1
    assert payload["snapshot"]["issue_count"] >= 1
    assert isinstance(payload["snapshot"].get("issues", []), list)

    issue_codes = {issue.get("code") for issue in payload["snapshot"].get("issues", [])}
    assert "reserved_mismatch" in issue_codes


@pytest.mark.django_db
def test_payout_reconciliation_snapshot_is_admin_only(api_client, reconciliation_dataset):
    User = get_user_model()
    user = User.objects.create_user(email="not-admin-payout-v67@example.com", password="strong-pass-123")
    api_client.force_authenticate(user)

    response = api_client.get("/api/v1/payouts/admin-ops/reconciliation/snapshot/")

    assert response.status_code == 403
