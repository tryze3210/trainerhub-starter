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
    return User.objects.create_superuser(email="admin-payout-v72@example.com", password="strong-pass-123")


@pytest.fixture
def regular_user(db):
    User = get_user_model()
    return User.objects.create_user(email="regular-payout-v72@example.com", password="strong-pass-123")


@pytest.fixture
def repair_preview_dataset(db):
    User = get_user_model()
    trainer_user = User.objects.create_user(
        email="trainer-payout-v72@example.com",
        password="strong-pass-123",
        role="trainer",
    )
    trainer = TrainerProfile.objects.create(
        user=trainer_user,
        slug="trainer-payout-v72",
        display_name="Trainer Payout V72",
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
    return {"trainer": trainer, "wallet": wallet, "active": active, "paid": paid}


@pytest.mark.django_db
def test_admin_can_preview_payout_repair_actions_without_mutation(api_client, admin_user, repair_preview_dataset):
    api_client.force_authenticate(admin_user)
    wallet = repair_preview_dataset["wallet"]
    before_available = wallet.available_amount
    before_locked = wallet.locked_amount
    before_ledger_count = BalanceEntry.objects.count()
    before_payout_count = PayoutRequest.objects.count()

    response = api_client.get("/api/v1/payouts/admin-ops/repair/preview/?currency=RUB&batch_size=10")

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "dry_run_repair_preview"
    assert payload["repair_performed"] is False
    assert payload["safety"]["dry_run_only"] is True
    assert payload["filters"]["currency"] == "RUB"
    assert payload["filters"]["batch_size"] == 10
    assert payload["summary"]["issue_count"] >= 2
    assert payload["summary"]["preview_count"] >= 2

    action_codes = {action["action_code"] for action in payload["actions"]}
    assert "release_excess_locked_to_available" in action_codes
    assert "create_missing_reserve_ledger" in action_codes
    assert "create_missing_payout_ledger" in action_codes

    wallet.refresh_from_db()
    assert wallet.available_amount == before_available
    assert wallet.locked_amount == before_locked
    assert BalanceEntry.objects.count() == before_ledger_count
    assert PayoutRequest.objects.count() == before_payout_count


@pytest.mark.django_db
def test_payout_repair_preview_supports_post_body_filters(api_client, admin_user, repair_preview_dataset):
    api_client.force_authenticate(admin_user)
    trainer_id = repair_preview_dataset["trainer"].user_id

    response = api_client.post(
        "/api/v1/payouts/admin-ops/repair/preview/",
        {"trainer_id": str(trainer_id), "batch_size": 1},
        format="json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["filters"]["trainer_id"] == str(trainer_id)
    assert payload["filters"]["batch_size"] == 1
    assert payload["summary"]["preview_count"] == 1
    assert payload["summary"]["has_more"] is True


@pytest.mark.django_db
def test_payout_repair_preview_is_admin_only(api_client, regular_user, repair_preview_dataset):
    api_client.force_authenticate(regular_user)

    response = api_client.get("/api/v1/payouts/admin-ops/repair/preview/")

    assert response.status_code == 403
