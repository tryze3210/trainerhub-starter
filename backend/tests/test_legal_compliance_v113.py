from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.finance_documents.models import FinanceDocument
from apps.finance_documents.services.commercial_documents import FinanceCommercialDocumentService
from apps.legal_compliance.models import ConsentLog, LegalDocumentTemplate, PayoutEligibilitySnapshot, TrainerKYCProfile
from apps.legal_compliance.services.acceptance import LegalAcceptanceService
from apps.orders.models import Order, OrderItem, OrderStatus, OrderType, PurchasedItemType
from apps.payments.models import Payment, PaymentProvider, PaymentStatus


def _user(email, role="customer"):
    return get_user_model().objects.create_user(email=email, password="pass12345", role=role)


def _document(doc_type, version="2026.06"):
    return LegalDocumentTemplate.objects.create(
        doc_type=doc_type,
        version=version,
        title=f"{doc_type} {version}",
        body_markdown=f"# {doc_type}",
        is_active=True,
        published_at=timezone.now(),
    )


def _commerce(*, student):
    order = Order.objects.create(
        user=student,
        order_type=OrderType.ONE_TIME,
        status=OrderStatus.COMPLETED,
        currency="RUB",
        total_amount=Decimal("500.00"),
    )
    OrderItem.objects.create(
        order=order,
        item_type=PurchasedItemType.PROGRAM,
        item_id="program-v113",
        title_snapshot="v113 program",
        quantity=1,
        unit_price=Decimal("500.00"),
        total_price=Decimal("500.00"),
    )
    payment = Payment.objects.create(
        order=order,
        provider=PaymentProvider.MOCK,
        status=PaymentStatus.SUCCEEDED,
        amount=Decimal("500.00"),
        currency="RUB",
    )
    return order, payment


@pytest.mark.django_db
def test_v113_required_policy_acceptances_create_consent_logs():
    user = _user("v113-legal-user@example.com")
    terms = _document(LegalDocumentTemplate.DOC_TERMS)
    privacy = _document(LegalDocumentTemplate.DOC_PRIVACY)
    refund = _document(LegalDocumentTemplate.DOC_REFUND_POLICY)

    initial = LegalAcceptanceService.compliance_status(user=user)
    assert initial["is_compliant"] is False
    assert set(initial["missing"]) == {
        LegalDocumentTemplate.DOC_TERMS,
        LegalDocumentTemplate.DOC_PRIVACY,
        LegalDocumentTemplate.DOC_REFUND_POLICY,
    }

    for document in (terms, privacy, refund):
        LegalAcceptanceService.accept_document(
            user=user,
            actor_type="user",
            document=document,
            ip_address="127.0.0.1",
            user_agent="pytest",
        )

    final = LegalAcceptanceService.compliance_status(user=user)
    assert final["is_compliant"] is True
    assert final["missing"] == []
    assert ConsentLog.objects.filter(user=user, consent_type=ConsentLog.CONSENT_TERMS).exists()
    assert ConsentLog.objects.filter(user=user, consent_type=ConsentLog.CONSENT_PRIVACY).exists()
    assert ConsentLog.objects.filter(user=user, consent_type=ConsentLog.CONSENT_REFUND_POLICY).exists()


@pytest.mark.django_db
def test_v113_compliance_status_and_consent_log_endpoints():
    user = _user("v113-api-user@example.com")
    document = _document(LegalDocumentTemplate.DOC_TERMS)
    client = APIClient()
    client.force_authenticate(user=user)

    status_response = client.get("/api/v1/legal/me/compliance-status/")
    assert status_response.status_code == 200
    assert status_response.json()["is_compliant"] is False

    accept_response = client.post(f"/api/v1/legal/me/documents/{document.id}/accept/")
    assert accept_response.status_code == 201
    assert accept_response.json()["status"] == "accepted"

    logs_response = client.get("/api/v1/legal/me/consent-logs/")
    assert logs_response.status_code == 200
    assert logs_response.json()["results"][0]["consent_type"] == ConsentLog.CONSENT_TERMS


@pytest.mark.django_db
def test_v113_legal_documents_endpoint_exposes_only_latest_active_versions():
    user = _user("v113-latest-docs@example.com")
    old_terms = _document(LegalDocumentTemplate.DOC_TERMS, version="2026.01")
    latest_terms = _document(LegalDocumentTemplate.DOC_TERMS, version="2026.07")
    privacy = _document(LegalDocumentTemplate.DOC_PRIVACY, version="2026.07")
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/v1/legal/me/documents/")

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["results"]}
    assert str(latest_terms.id) in ids
    assert str(privacy.id) in ids
    assert str(old_terms.id) not in ids


@pytest.mark.django_db
def test_v113_cannot_accept_stale_active_legal_document_version():
    user = _user("v113-stale-accept@example.com")
    old_terms = _document(LegalDocumentTemplate.DOC_TERMS, version="2026.01")
    latest_terms = _document(LegalDocumentTemplate.DOC_TERMS, version="2026.07")
    client = APIClient()
    client.force_authenticate(user=user)

    stale_response = client.post(f"/api/v1/legal/me/documents/{old_terms.id}/accept/")
    latest_response = client.post(f"/api/v1/legal/me/documents/{latest_terms.id}/accept/")

    assert stale_response.status_code == 400
    assert latest_response.status_code == 201
    assert ConsentLog.objects.filter(user=user, document=old_terms).count() == 0
    assert ConsentLog.objects.filter(user=user, document=latest_terms).count() == 1


@pytest.mark.django_db
def test_v113_finance_document_payload_contains_legal_fields():
    student = _user("v113-finance-legal@example.com")
    TrainerKYCProfile.objects.create(
        trainer=student,
        full_name="Student Buyer",
        country="RU",
        tax_id="7700000000",
        legal_address="Moscow, Test street",
        payout_legal_entity_name="Student Buyer LLC",
        status=TrainerKYCProfile.STATUS_APPROVED,
    )
    order, payment = _commerce(student=student)

    result = FinanceCommercialDocumentService.build_for_order(
        document_type=FinanceDocument.DOC_INVOICE,
        order=order,
        payment=payment,
    )

    legal = result.document.payload["buyer_legal"]
    assert legal["legal_name"] == "Student Buyer LLC"
    assert legal["tax_id"] == "7700000000"
    assert legal["legal_address"] == "Moscow, Test street"


@pytest.mark.django_db
def test_v113_admin_kyc_review_requires_complete_profile_for_approval():
    admin = get_user_model().objects.create_superuser(email="v113-kyc-admin@example.com", password="pass12345")
    trainer = _user("v113-kyc-trainer@example.com", role="trainer")
    profile = TrainerKYCProfile.objects.create(
        trainer=trainer,
        full_name="Trainer Legal",
        country="RU",
        tax_id="7700000000",
    )
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.post(f"/api/v1/legal/admin/kyc/{profile.id}/review/", {"decision": "approve"}, format="json")

    profile.refresh_from_db()
    assert response.status_code == 400
    assert set(response.json()["missing_fields"]) == {"legal_address", "payout_legal_entity_name"}
    assert profile.status == TrainerKYCProfile.STATUS_DRAFT


@pytest.mark.django_db
def test_v113_admin_kyc_reject_requires_reason():
    admin = get_user_model().objects.create_superuser(email="v113-kyc-reject-admin@example.com", password="pass12345")
    trainer = _user("v113-kyc-reject-trainer@example.com", role="trainer")
    profile = TrainerKYCProfile.objects.create(trainer=trainer, status=TrainerKYCProfile.STATUS_PENDING)
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.post(f"/api/v1/legal/admin/kyc/{profile.id}/review/", {"decision": "reject"}, format="json")

    profile.refresh_from_db()
    assert response.status_code == 400
    assert profile.status == TrainerKYCProfile.STATUS_PENDING
    assert profile.rejection_reason == ""


@pytest.mark.django_db
def test_v113_admin_kyc_approval_refreshes_payout_eligibility_snapshot():
    admin = get_user_model().objects.create_superuser(email="v113-kyc-ok-admin@example.com", password="pass12345")
    trainer = _user("v113-kyc-ok-trainer@example.com", role="trainer")
    profile = TrainerKYCProfile.objects.create(
        trainer=trainer,
        full_name="Trainer Legal",
        country="RU",
        tax_id="7700000000",
        legal_address="Moscow, Test street",
        payout_legal_entity_name="Trainer LLC",
        status=TrainerKYCProfile.STATUS_PENDING,
    )
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.post(f"/api/v1/legal/admin/kyc/{profile.id}/review/", {"decision": "approve"}, format="json")

    profile.refresh_from_db()
    snapshot = PayoutEligibilitySnapshot.objects.get(trainer=trainer)
    assert response.status_code == 200
    assert profile.status == TrainerKYCProfile.STATUS_APPROVED
    assert profile.reviewed_by == admin
    assert snapshot.kyc_status == TrainerKYCProfile.STATUS_APPROVED
