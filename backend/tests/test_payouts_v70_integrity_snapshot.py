from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

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
    return User.objects.create_superuser(email="admin-payout-v70@example.com", password="strong-pass-123")


@pytest.fixture
def regular_user(db):
    User = get_user_model()
    return User.objects.create_user(email="regular-payout-v70@example.com", password="strong-pass-123")


@pytest.fixture
def inconsistent_payout_dataset(db):
    User = get_user_model()
    trainer_user = User.objects.create_user(
        email="trainer-payout-v70@example.com",
        password="strong-pass-123",
        role="trainer",
    )
    trainer = TrainerProfile.objects.create(
        user=trainer_user,
        slug="trainer-payout-v70",
        display_name="Trainer Payout V70",
        status="active",
    )
    wallet = TrainerWallet.objects.create(
        trainer=trainer,
        currency="RUB",
        available_amount=Decimal("1000.00"),
        pending_amount=Decimal("0.00"),
        locked_amount=Decimal("300.00"),
    )
    active = PayoutRequest.objects.create(
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
        source_id=uuid4(),
    )
    BalanceEntry.objects.create(
        wallet=wallet,
        entry_type=BalanceEntry.EntryType.RESERVE,
        direction="debit",
        amount=Decimal("10.00"),
        currency="RUB",
        status="locked",
        source_type="payout_request",
        source_id=uuid4(),
    )
    return {"trainer": trainer, "wallet": wallet, "active": active, "paid": paid}


@pytest.mark.django_db
def test_admin_can_read_payout_integrity_snapshot(api_client, admin_user, inconsistent_payout_dataset):
    api_client.force_authenticate(admin_user)
    wallet = inconsistent_payout_dataset["wallet"]
    before_locked = wallet.locked_amount
    before_ledger_count = BalanceEntry.objects.count()

    response = api_client.get("/api/v1/payouts/admin-ops/integrity/?currency=RUB&limit=50")

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "read_only_integrity_snapshot"
    assert payload["actions"]["repair_performed"] is False
    assert payload["summary"]["status"] == "attention_required"
    assert payload["summary"]["issue_count"] >= 3
    assert payload["filters"]["currency"] == "RUB"

    issue_codes = {issue["code"] for issue in payload["issues"]}
    assert "locked_balance_mismatch" in issue_codes
    assert "active_payout_missing_reserve_ledger" in issue_codes
    assert "paid_payout_missing_payout_ledger" in issue_codes
    assert "orphan_payout_ledger_entry" in issue_codes

    wallet.refresh_from_db()
    assert wallet.locked_amount == before_locked
    assert BalanceEntry.objects.count() == before_ledger_count


@pytest.mark.django_db
def test_payout_integrity_snapshot_supports_trainer_filter(api_client, admin_user, inconsistent_payout_dataset):
    api_client.force_authenticate(admin_user)
    trainer_id = inconsistent_payout_dataset["trainer"].user_id

    response = api_client.get(f"/api/v1/payouts/admin-ops/integrity/?trainer_id={trainer_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["filters"]["trainer_id"] == str(trainer_id)
    assert payload["summary"]["wallet_count"] == 1
    assert payload["summary"]["payouts_scanned"] == 2


@pytest.mark.django_db
def test_payout_integrity_snapshot_is_admin_only(api_client, regular_user, inconsistent_payout_dataset):
    api_client.force_authenticate(regular_user)

    response = api_client.get("/api/v1/payouts/admin-ops/integrity/")

    assert response.status_code == 403
