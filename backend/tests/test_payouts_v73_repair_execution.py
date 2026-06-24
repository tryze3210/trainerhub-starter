from __future__ import annotations

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent
from apps.payouts.models import BalanceEntry, PayoutRequest, TrainerWallet
from apps.trainers.models import TrainerProfile


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    User = get_user_model()
    return User.objects.create_superuser(email="admin-payout-v73@example.com", password="strong-pass-123")


@pytest.fixture
def regular_user(db):
    User = get_user_model()
    return User.objects.create_user(email="regular-payout-v73@example.com", password="strong-pass-123")


@pytest.fixture
def repair_execution_dataset(db):
    User = get_user_model()
    trainer_user = User.objects.create_user(
        email="trainer-payout-v73@example.com",
        password="strong-pass-123",
        role="trainer",
    )
    trainer = TrainerProfile.objects.create(
        user=trainer_user,
        slug="trainer-payout-v73",
        display_name="Trainer Payout V73",
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
    rejected = PayoutRequest.objects.create(
        trainer=trainer,
        wallet=wallet,
        amount=Decimal("50.00"),
        currency="RUB",
        status=PayoutRequest.Status.REJECTED,
        destination_json={"destination_masked": "****3333"},
    )
    return {"trainer": trainer, "wallet": wallet, "active": active, "paid": paid, "rejected": rejected}


@pytest.mark.django_db
def test_admin_can_execute_safe_payout_repairs(api_client, admin_user, repair_execution_dataset):
    api_client.force_authenticate(admin_user)

    response = api_client.post(
        "/api/v1/payouts/admin-ops/repair/execute/",
        {"currency": "RUB", "batch_size": 10},
        format="json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "repair_execution"
    assert payload["summary"]["repaired_count"] >= 2
    assert payload["summary"]["manual_review_count"] >= 1

    action_codes = {result["action_code"] for result in payload["results"]}
    assert "release_excess_locked_to_available" in action_codes
    assert "create_missing_reserve_ledger" in action_codes
    assert "manual_review_required" in action_codes

    wallet = repair_execution_dataset["wallet"]
    wallet.refresh_from_db()
    assert wallet.locked_amount == Decimal("250.00")
    assert wallet.available_amount == Decimal("1050.00")

    active = repair_execution_dataset["active"]
    assert BalanceEntry.objects.filter(
        wallet=wallet,
        source_type="payout_request",
        source_id=active.id,
        entry_type=BalanceEntry.EntryType.RESERVE,
        amount=active.amount,
        currency="RUB",
    ).exists()
    assert BalanceEntry.objects.filter(source_type="payout_repair_execution").exists()
    assert AuditEvent.objects.filter(event_type="admin.payouts.repair_execution").exists()


@pytest.mark.django_db
def test_payout_repair_execution_keeps_currency_mismatch_manual(api_client, admin_user, repair_execution_dataset):
    api_client.force_authenticate(admin_user)
    paid = repair_execution_dataset["paid"]
    paid.currency = "USD"
    paid.save(update_fields=["currency", "updated_at"])

    response = api_client.post(
        "/api/v1/payouts/admin-ops/repair/execute/",
        {"batch_size": 10},
        format="json",
    )

    assert response.status_code == 200
    payload = response.json()
    manual_results = [result for result in payload["results"] if result["status"] == "manual_review_required"]
    assert manual_results
    assert any(result["issue_code"] in {"payout_wallet_currency_mismatch", "ledger_payout_currency_mismatch", "paid_payout_missing_payout_ledger"} for result in manual_results)


@pytest.mark.django_db
def test_payout_repair_execution_is_admin_only(api_client, regular_user, repair_execution_dataset):
    api_client.force_authenticate(regular_user)
    response = api_client.post("/api/v1/payouts/admin-ops/repair/execute/", {}, format="json")
    assert response.status_code == 403
