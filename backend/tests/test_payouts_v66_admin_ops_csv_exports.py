from __future__ import annotations

import csv
import io
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
    user = User.objects.create_user(email="admin-payout-v66@example.com", password="strong-pass-123")
    user.is_staff = True
    user.is_superuser = True
    user.save(update_fields=["is_staff", "is_superuser"])
    return user


@pytest.fixture
def payout_export_dataset(db):
    User = get_user_model()
    trainer_user = User.objects.create_user(email="trainer-payout-v66@example.com", password="strong-pass-123")
    trainer_user.role = "trainer"
    trainer_user.save(update_fields=["role"])

    trainer = TrainerProfile.objects.create(
        user=trainer_user,
        slug="trainer-payout-v66",
        display_name="Trainer Payout V66",
        status="active",
    )
    wallet = TrainerWallet.objects.create(
        trainer=trainer,
        currency="RUB",
        available_amount=Decimal("1000.00"),
        pending_amount=Decimal("250.00"),
        locked_amount=Decimal("0.00"),
    )
    payout = PayoutRequest.objects.create(
        trainer=trainer,
        wallet=wallet,
        amount=Decimal("250.00"),
        currency="RUB",
        status=PayoutRequest.Status.PENDING,
        destination_json={"destination_masked": "**** 4242"},
    )
    ledger = BalanceEntry.objects.create(
        wallet=wallet,
        entry_type=BalanceEntry.EntryType.PAYOUT,
        direction="debit",
        status="pending",
        amount=Decimal("250.00"),
        currency="RUB",
        source_type="payout_request",
        source_id=payout.id,
    )
    return {"trainer": trainer, "wallet": wallet, "payout": payout, "ledger": ledger}


def _read_csv(response):
    body = response.content.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(body)))


@pytest.mark.django_db
def test_admin_can_export_payout_requests_csv(api_client, admin_user, payout_export_dataset):
    api_client.force_authenticate(admin_user)

    response = api_client.get("/api/v1/payouts/admin-ops/requests/export.csv?currency=RUB&limit=10")

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv")
    assert "payout_admin_requests_export.csv" in response["Content-Disposition"]
    rows = _read_csv(response)
    assert len(rows) == 1
    assert rows[0]["id"] == str(payout_export_dataset["payout"].id)
    assert rows[0]["trainer_name"] == "Trainer Payout V66"
    assert rows[0]["status"] == PayoutRequest.Status.PENDING
    assert rows[0]["amount"] == "250.00"
    assert rows[0]["currency"] == "RUB"

    event = AuditEvent.objects.get(event_type="admin.payouts.admin_ops.csv_export", entity_type="payout_export", entity_id="requests")
    assert event.actor == admin_user
    assert event.context["context"]["exported_rows"] == 1
    assert event.context["context"]["total_rows"] == 1
    assert event.context["context"]["truncated"] is False


@pytest.mark.django_db
def test_admin_can_export_payout_ledger_csv(api_client, admin_user, payout_export_dataset):
    api_client.force_authenticate(admin_user)

    response = api_client.get("/api/v1/payouts/admin-ops/ledger/export.csv?currency=RUB&entry_type=payout&limit=10")

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv")
    assert "payout_admin_ledger_export.csv" in response["Content-Disposition"]
    rows = _read_csv(response)
    assert len(rows) == 1
    assert rows[0]["id"] == str(payout_export_dataset["ledger"].id)
    assert rows[0]["trainer_name"] == "Trainer Payout V66"
    assert rows[0]["entry_type"] == BalanceEntry.EntryType.PAYOUT
    assert rows[0]["direction"] == "debit"
    assert rows[0]["amount"] == "250.00"
    assert rows[0]["source_id"] == str(payout_export_dataset["payout"].id)

    event = AuditEvent.objects.get(event_type="admin.payouts.admin_ops.csv_export", entity_type="payout_export", entity_id="ledger")
    assert event.actor == admin_user
    assert event.context["context"]["export_type"] == "ledger"
    assert event.context["context"]["exported_rows"] == 1


@pytest.mark.django_db
def test_non_admin_cannot_export_payout_ops_csv(api_client, payout_export_dataset):
    User = get_user_model()
    user = User.objects.create_user(email="not-admin-payout-v66@example.com", password="strong-pass-123")
    api_client.force_authenticate(user)

    response = api_client.get("/api/v1/payouts/admin-ops/requests/export.csv")

    assert response.status_code == 403
