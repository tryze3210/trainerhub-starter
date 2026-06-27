from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.finance_documents.models import FinanceDocument
from apps.finance_documents.services.commercial_documents import FinanceCommercialDocumentService
from apps.legal_compliance.models import ConsentLog, LegalDocumentTemplate, TrainerKYCProfile
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
