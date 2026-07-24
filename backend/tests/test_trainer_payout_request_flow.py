from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent
from apps.legal_compliance.models import LegalDocumentTemplate, TrainerContractArtifact, TrainerKYCProfile
from apps.payouts.models import BalanceEntry, PayoutRequest, TrainerWallet
from apps.payouts.services import PayoutService
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


def _make_trainer_legally_eligible(user):
    document = LegalDocumentTemplate.objects.create(
        doc_type=LegalDocumentTemplate.DOC_TRAINER_AGREEMENT,
        version=f"v1-{user.id}",
        title="Trainer agreement",
        body_markdown="Agreement",
        is_active=True,
        published_at=timezone.now(),
    )
    kyc = TrainerKYCProfile.objects.create(
        trainer=user,
        full_name="Payout Trainer",
        country="RU",
        tax_id="7700000000",
        legal_address="Moscow, Test street",
        payout_legal_entity_name="Payout Trainer LLC",
        status=TrainerKYCProfile.STATUS_APPROVED,
    )
    TrainerContractArtifact.objects.create(
        trainer=user,
        document_template=document,
        artifact_path=f"contracts/{user.id}-v1.pdf",
        version=document.version,
        status=TrainerContractArtifact.STATUS_SIGNED,
        generated_at=timezone.now(),
        signed_at=timezone.now(),
    )
    return kyc


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
def test_payout_accrual_rejects_missing_trainer_profile_without_synthetic_user():
    missing_trainer_id = uuid4()

    with pytest.raises(ValidationError) as exc_info:
        PayoutService.get_or_create_balance(trainer_id=missing_trainer_id)

    assert "Trainer profile not found" in str(exc_info.value)
    assert not get_user_model().objects.filter(email__endswith="@example.invalid").exists()
    assert not TrainerProfile.objects.filter(id=missing_trainer_id).exists()
    assert not TrainerWallet.objects.exists()


@pytest.mark.django_db
@override_settings(PAYOUTS_REQUIRE_LEGAL_ELIGIBILITY=True)
def test_payout_request_requires_approved_kyc_and_active_agreement(trainer_user):
    user, profile, wallet = trainer_user
    client = APIClient()
    client.force_authenticate(user=user)

    balance_response = client.get("/api/v1/payouts/my/balance/")
    assert balance_response.status_code == 200
    assert balance_response.data["can_request_payout"] is False

    response = client.post(
        "/api/v1/payouts/my/request/",
        {"amount": "300.00", "destination_masked": "Tinkoff **** 4242"},
        format="json",
    )

    assert response.status_code == 400
    assert response.data["detail"] == "Trainer is not eligible for payouts."
    assert "kyc_profile_missing" in response.data["block_reason"]
    assert "active_trainer_agreement_missing" in response.data["block_reason"]
    wallet.refresh_from_db()
    assert wallet.available_amount == Decimal("1000.00")
    assert wallet.locked_amount == Decimal("0.00")
    assert not PayoutRequest.objects.filter(trainer=profile).exists()
    audit_event = AuditEvent.objects.get(event_type="payout.eligibility_blocked", entity_type="trainer")
    assert audit_event.actor == user
    assert audit_event.entity_id == str(user.id)
    assert audit_event.context["action"] == "request"
    assert "kyc_profile_missing" in audit_event.context["block_reason"]


@pytest.mark.django_db
@override_settings(PAYOUTS_REQUIRE_LEGAL_ELIGIBILITY=True)
def test_payout_request_succeeds_for_legally_eligible_trainer(trainer_user):
    user, _, wallet = trainer_user
    _make_trainer_legally_eligible(user)
    client = APIClient()
    client.force_authenticate(user=user)

    balance_response = client.get("/api/v1/payouts/my/balance/")
    assert balance_response.status_code == 200
    assert balance_response.data["can_request_payout"] is True

    response = client.post(
        "/api/v1/payouts/my/request/",
        {"amount": "300.00", "destination_masked": "Tinkoff **** 4242"},
        format="json",
    )

    assert response.status_code == 201
    assert response.data["payout"]["payout_eligibility"]["is_eligible"] is True
    wallet.refresh_from_db()
    assert wallet.available_amount == Decimal("700.00")
    assert wallet.locked_amount == Decimal("300.00")


@pytest.mark.django_db
@override_settings(PAYOUTS_REQUIRE_LEGAL_ELIGIBILITY=True)
def test_admin_cannot_approve_payout_when_trainer_loses_legal_eligibility(trainer_user, admin_user):
    user, _, wallet = trainer_user
    kyc = _make_trainer_legally_eligible(user)
    trainer_client = APIClient()
    trainer_client.force_authenticate(user=user)
    create_response = trainer_client.post(
        "/api/v1/payouts/my/request/",
        {"amount": "300.00", "destination_masked": "Tinkoff **** 4242"},
        format="json",
    )
    assert create_response.status_code == 201
    payout_id = create_response.data["payout"]["id"]

    kyc.status = TrainerKYCProfile.STATUS_REJECTED
    kyc.rejection_reason = "Documents expired"
    kyc.save(update_fields=["status", "rejection_reason", "updated_at"])

    admin_client = APIClient()
    admin_client.force_authenticate(user=admin_user)
    approve_response = admin_client.post(f"/api/v1/payouts/admin/{payout_id}/approve/", {}, format="json")

    assert approve_response.status_code == 400
    assert approve_response.data["detail"] == "Trainer is not eligible for payouts."
    assert "kyc_not_approved" in approve_response.data["block_reason"]
    payout = PayoutRequest.objects.get(id=payout_id)
    assert payout.status == PayoutRequest.Status.PENDING
    wallet.refresh_from_db()
    assert wallet.available_amount == Decimal("700.00")
    assert wallet.locked_amount == Decimal("300.00")
    audit_event = AuditEvent.objects.get(event_type="payout.eligibility_blocked", entity_id=payout_id)
    assert audit_event.actor == admin_user
    assert audit_event.context["action"] == "approve"
    assert audit_event.context["status"] == PayoutRequest.Status.PENDING
    assert "kyc_not_approved" in audit_event.context["block_reason"]


@pytest.mark.django_db
@override_settings(PAYOUTS_REQUIRE_LEGAL_ELIGIBILITY=True)
def test_admin_cannot_move_payout_to_processing_when_trainer_loses_legal_eligibility(trainer_user, admin_user):
    user, _, wallet = trainer_user
    kyc = _make_trainer_legally_eligible(user)
    trainer_client = APIClient()
    trainer_client.force_authenticate(user=user)
    create_response = trainer_client.post(
        "/api/v1/payouts/my/request/",
        {"amount": "300.00", "destination_masked": "Tinkoff **** 4242"},
        format="json",
    )
    assert create_response.status_code == 201
    payout_id = create_response.data["payout"]["id"]

    admin_client = APIClient()
    admin_client.force_authenticate(user=admin_user)
    approve_response = admin_client.post(f"/api/v1/payouts/admin/{payout_id}/approve/", {}, format="json")
    assert approve_response.status_code == 200

    kyc.status = TrainerKYCProfile.STATUS_REJECTED
    kyc.rejection_reason = "Documents expired"
    kyc.save(update_fields=["status", "rejection_reason", "updated_at"])

    processing_response = admin_client.post(f"/api/v1/payouts/admin/{payout_id}/processing/", {}, format="json")

    assert processing_response.status_code == 400
    assert processing_response.data["detail"] == "Trainer is not eligible for payouts."
    assert "kyc_not_approved" in processing_response.data["block_reason"]
    payout = PayoutRequest.objects.get(id=payout_id)
    assert payout.status == PayoutRequest.Status.APPROVED
    wallet.refresh_from_db()
    assert wallet.available_amount == Decimal("700.00")
    assert wallet.locked_amount == Decimal("300.00")


@pytest.mark.django_db
@override_settings(PAYOUTS_REQUIRE_LEGAL_ELIGIBILITY=True)
def test_admin_cannot_mark_payout_paid_when_trainer_loses_legal_eligibility(trainer_user, admin_user):
    user, _, wallet = trainer_user
    kyc = _make_trainer_legally_eligible(user)
    trainer_client = APIClient()
    trainer_client.force_authenticate(user=user)
    create_response = trainer_client.post(
        "/api/v1/payouts/my/request/",
        {"amount": "300.00", "destination_masked": "Tinkoff **** 4242"},
        format="json",
    )
    assert create_response.status_code == 201
    payout_id = create_response.data["payout"]["id"]

    admin_client = APIClient()
    admin_client.force_authenticate(user=admin_user)
    assert admin_client.post(f"/api/v1/payouts/admin/{payout_id}/approve/", {}, format="json").status_code == 200
    assert admin_client.post(f"/api/v1/payouts/admin/{payout_id}/processing/", {}, format="json").status_code == 200

    kyc.status = TrainerKYCProfile.STATUS_REJECTED
    kyc.rejection_reason = "Documents expired"
    kyc.save(update_fields=["status", "rejection_reason", "updated_at"])

    paid_response = admin_client.post(
        f"/api/v1/payouts/admin/{payout_id}/mark-paid/",
        {"external_reference": "bank-transfer-42"},
        format="json",
    )

    assert paid_response.status_code == 400
    assert paid_response.data["detail"] == "Trainer is not eligible for payouts."
    assert "kyc_not_approved" in paid_response.data["block_reason"]
    payout = PayoutRequest.objects.get(id=payout_id)
    assert payout.status == PayoutRequest.Status.PROCESSING
    wallet.refresh_from_db()
    assert wallet.available_amount == Decimal("700.00")
    assert wallet.locked_amount == Decimal("300.00")


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
