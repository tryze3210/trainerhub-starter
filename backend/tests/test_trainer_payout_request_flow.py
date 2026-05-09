from __future__ import annotations

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.payouts.models import BalanceEntry, PayoutRequest, TrainerWallet
from apps.trainers.models import TrainerProfile


@pytest.fixture
def trainer_user(db):
    User = get_user_model()
    user = User.objects.create_user(email="payout-trainer@example.com", password="pass", role="trainer")
    profile = TrainerProfile.objects.create(
        user=user,
        slug="payout-trainer",
        display_name="Payout Trainer",
        status="active",
    )
    wallet = TrainerWallet.objects.create(
        trainer=profile,
        currency="RUB",
        available_amount=Decimal("1000.00"),
        locked_amount=Decimal("0.00"),
        pending_amount=Decimal("0.00"),
    )
    return user, profile, wallet


@pytest.fixture
def admin_user(db):
    User = get_user_model()
    return User.objects.create_superuser(email="payout-admin@example.com", password="pass")


@pytest.mark.django_db
def test_trainer_can_request_payout_and_balance_is_reserved(trainer_user):
    user, profile, wallet = trainer_user
    client = APIClient()
    client.force_authenticate(user=user)

    balance_response = client.get("/api/v1/payouts/my/balance/")
    assert balance_response.status_code == 200
    assert balance_response.data["available_amount"] == "1000.00"
    assert balance_response.data["can_request_payout"] is True

    response = client.post(
        "/api/v1/payouts/my/request/",
        {"amount": "300.00", "destination_masked": "Tinkoff **** 4242"},
        format="json",
    )

    assert response.status_code == 201
    assert response.data["payout"]["amount"] == "300.00"
    assert response.data["payout"]["status"] == PayoutRequest.Status.PENDING
    assert response.data["wallet"]["available_amount"] == "700.00"
    assert response.data["wallet"]["locked_amount"] == "300.00"

    wallet.refresh_from_db()
    assert wallet.available_amount == Decimal("700.00")
    assert wallet.locked_amount == Decimal("300.00")

    payout = PayoutRequest.objects.get(trainer=profile)
    assert payout.destination_masked == "Tinkoff **** 4242"
    assert BalanceEntry.objects.filter(
        wallet=wallet,
        source_type="payout_request",
        source_id=payout.id,
        entry_type=BalanceEntry.EntryType.RESERVE,
        direction="debit",
    ).exists()


@pytest.mark.django_db
def test_payout_request_reject_releases_reserved_balance(trainer_user, admin_user):
    trainer, profile, wallet = trainer_user
    trainer_client = APIClient()
    trainer_client.force_authenticate(user=trainer)
    create_response = trainer_client.post(
        "/api/v1/payouts/my/request/",
        {"amount": "250.00", "destination_masked": "SBP **** 0199"},
        format="json",
    )
    assert create_response.status_code == 201
    payout_id = create_response.data["payout"]["id"]

    admin_client = APIClient()
    admin_client.force_authenticate(user=admin_user)
    reject_response = admin_client.post(
        f"/api/v1/payouts/admin/{payout_id}/reject/",
        {"reason": "Incorrect payout destination"},
        format="json",
    )

    assert reject_response.status_code == 200
    assert reject_response.data["status"] == PayoutRequest.Status.REJECTED
    assert reject_response.data["rejected_reason"] == "Incorrect payout destination"

    wallet.refresh_from_db()
    assert wallet.available_amount == Decimal("1000.00")
    assert wallet.locked_amount == Decimal("0.00")
    assert BalanceEntry.objects.filter(
        wallet=wallet,
        source_type="payout_request",
        source_id=payout_id,
        entry_type=BalanceEntry.EntryType.RELEASE,
        direction="credit",
    ).exists()


@pytest.mark.django_db
def test_admin_can_approve_process_and_mark_payout_paid(trainer_user, admin_user):
    trainer, profile, wallet = trainer_user
    trainer_client = APIClient()
    trainer_client.force_authenticate(user=trainer)
    create_response = trainer_client.post(
        "/api/v1/payouts/my/request/",
        {"amount": "400.00", "destination_masked": "Bank card **** 7777"},
        format="json",
    )
    assert create_response.status_code == 201
    payout_id = create_response.data["payout"]["id"]

    admin_client = APIClient()
    admin_client.force_authenticate(user=admin_user)

    approve_response = admin_client.post(f"/api/v1/payouts/admin/{payout_id}/approve/", {}, format="json")
    assert approve_response.status_code == 200
    assert approve_response.data["status"] == PayoutRequest.Status.APPROVED

    processing_response = admin_client.post(
        f"/api/v1/payouts/admin/{payout_id}/processing/",
        {"external_reference": "batch-42"},
        format="json",
    )
    assert processing_response.status_code == 200
    assert processing_response.data["status"] == PayoutRequest.Status.PROCESSING

    paid_response = admin_client.post(
        f"/api/v1/payouts/admin/{payout_id}/mark-paid/",
        {"external_reference": "bank-transfer-42"},
        format="json",
    )
    assert paid_response.status_code == 200
    assert paid_response.data["status"] == PayoutRequest.Status.PAID
    assert paid_response.data["processed_at"]

    wallet.refresh_from_db()
    assert wallet.available_amount == Decimal("600.00")
    assert wallet.locked_amount == Decimal("0.00")
    assert BalanceEntry.objects.filter(
        wallet=wallet,
        source_type="payout_request",
        source_id=payout_id,
        entry_type=BalanceEntry.EntryType.PAYOUT,
        direction="debit",
        status="paid",
    ).exists()


@pytest.mark.django_db
def test_non_admin_cannot_read_admin_payouts(trainer_user):
    user, _, _ = trainer_user
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/v1/payouts/admin/")

    assert response.status_code == 403
