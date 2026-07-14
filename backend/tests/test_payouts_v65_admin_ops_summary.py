from __future__ import annotations

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.payouts.models import BalanceEntry, PayoutRequest, TrainerWallet
from apps.trainers.models import TrainerProfile


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    User = get_user_model()
    return User.objects.create_superuser(email="admin-payout-v65@example.com", password="strong-pass-123")


@pytest.fixture
def regular_user(db):
    User = get_user_model()
    return User.objects.create_user(email="regular-payout-v65@example.com", password="strong-pass-123")


@pytest.fixture
def payout_dataset(db):
    User = get_user_model()
    trainer_user = User.objects.create_user(
        email="trainer-payout-v65@example.com",
        password="strong-pass-123",
        role="trainer",
    )
    trainer = TrainerProfile.objects.create(
        user=trainer_user,
        slug="trainer-payout-v65",
        display_name="Trainer Payout V65",
        status="active",
    )
    wallet = TrainerWallet.objects.create(
        trainer=trainer,
        currency="RUB",
        available_amount=Decimal("1000.00"),
        pending_amount=Decimal("0.00"),
        locked_amount=Decimal("250.00"),
    )
    pending = PayoutRequest.objects.create(
        trainer=trainer,
        wallet=wallet,
        amount=Decimal("250.00"),
        currency="RUB",
        status=PayoutRequest.Status.PENDING,
        destination_json={"destination_masked": "****1111"},
    )
    paid = PayoutRequest.objects.create(
        trainer=trainer,
        wallet=wallet,
        amount=Decimal("150.00"),
        currency="RUB",
        status=PayoutRequest.Status.PAID,
        destination_json={"destination_masked": "****2222"},
    )
    BalanceEntry.objects.create(
        wallet=wallet,
        entry_type=BalanceEntry.EntryType.ACCRUAL,
        direction="credit",
        amount=Decimal("400.00"),
        currency="RUB",
        status="available",
        source_type="payment",
        source_id=pending.id,
    )
    BalanceEntry.objects.create(
        wallet=wallet,
        entry_type=BalanceEntry.EntryType.RESERVE,
        direction="debit",
        amount=Decimal("250.00"),
        currency="RUB",
        status="locked",
        source_type="payout_request",
        source_id=pending.id,
    )
    return {"trainer": trainer, "wallet": wallet, "pending": pending, "paid": paid}


@pytest.mark.django_db
def test_admin_can_read_payout_ops_summary(api_client, admin_user, payout_dataset):
    api_client.force_authenticate(admin_user)

    response = api_client.get("/api/v1/payouts/admin-ops/summary/?currency=RUB&limit=10")

    assert response.status_code == 200
    payload = response.json()
    assert payload["filters"]["currency"] == "RUB"
    assert payload["summary"]["total_payout_requests"] == 2
    assert payload["summary"]["active_payout_count"] == 1
    assert payload["summary"]["active_payout_amount"] == "250.00"
    assert payload["wallets"]["available_amount"] == "1000.00"
    assert payload["wallets"]["locked_amount"] == "250.00"
    assert payload["reconciliation"]["status"] in {"healthy", "attention_required"}
    assert len(payload["recent_payouts"]) == 2
    assert "payout_eligibility" in payload["recent_payouts"][0]
    assert payload["recent_payouts"][0]["payout_eligibility"]["is_eligible"] is False
    assert "kyc_profile_missing" in payload["recent_payouts"][0]["payout_eligibility"]["block_reason"]


@pytest.mark.django_db
def test_payout_ops_summary_supports_status_and_trainer_filters(api_client, admin_user, payout_dataset):
    api_client.force_authenticate(admin_user)
    trainer_id = payout_dataset["trainer"].user_id

    response = api_client.get(
        f"/api/v1/payouts/admin-ops/summary/?status=pending&trainer_id={trainer_id}"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["filters"]["status"] == "pending"
    assert payload["filters"]["trainer_id"] == str(trainer_id)
    assert payload["summary"]["total_payout_requests"] == 1
    assert payload["recent_payouts"][0]["status"] == "pending"


@pytest.mark.django_db
def test_payout_ops_summary_is_admin_only(api_client, regular_user, payout_dataset):
    api_client.force_authenticate(regular_user)

    response = api_client.get("/api/v1/payouts/admin-ops/summary/")

    assert response.status_code == 403
