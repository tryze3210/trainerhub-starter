from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.models import AccountRoleAssignment
from apps.audit.models import AuditEvent
from apps.finance_documents.models import FinanceDocument
from apps.finance_documents.services.commercial_documents import FinanceCommercialDocumentService
from apps.orders.models import Order, OrderItem, OrderStatus, OrderType, PurchasedItemType
from apps.payments.models import Payment, PaymentProvider, PaymentStatus


def _user(email, role="customer"):
    return get_user_model().objects.create_user(email=email, password="pass12345", role=role)


def _finance(email):
    user = _user(email)
    AccountRoleAssignment.objects.create(user=user, role=AccountRoleAssignment.ROLE_FINANCE, is_active=True)
    return user


def _commerce(*, student, marker="v112"):
    order = Order.objects.create(
        user=student,
        order_type=OrderType.ONE_TIME,
        status=OrderStatus.COMPLETED,
        currency="RUB",
        total_amount=Decimal("390.00"),
        external_checkout_id=f"checkout-{marker}",
    )
    OrderItem.objects.create(
        order=order,
        item_type=PurchasedItemType.PROGRAM,
        item_id=f"program-{marker}",
        title_snapshot=f"{marker} program",
        quantity=1,
        unit_price=Decimal("390.00"),
        total_price=Decimal("390.00"),
        metadata={"trainer_id": str(student.id)},
    )
    payment = Payment.objects.create(
        order=order,
        provider=PaymentProvider.MOCK,
        status=PaymentStatus.SUCCEEDED,
        amount=Decimal("390.00"),
        currency="RUB",
        external_payment_id=f"pay-{marker}",
    )
    return order, payment


@pytest.mark.django_db
def test_v112_build_invoice_and_receipt_documents():
    operator = _finance("v112-finance-docs@example.com")
    student = _user("v112-student-docs@example.com")
    order, payment = _commerce(student=student, marker="v112-docs")

    invoice = FinanceCommercialDocumentService.build_for_order(
        document_type=FinanceDocument.DOC_INVOICE,
        order=order,
        payment=payment,
        actor=operator,
    )
    receipt = FinanceCommercialDocumentService.build_for_order(
        document_type=FinanceDocument.DOC_RECEIPT,
        order=order,
        payment=payment,
        actor=operator,
    )

    assert invoice.created is True
    assert receipt.created is True
    assert invoice.document.document_type == FinanceDocument.DOC_INVOICE
    assert receipt.document.document_type == FinanceDocument.DOC_RECEIPT
    assert invoice.document.payload["order_id"] == str(order.id)
    assert receipt.document.payload["payment_id"] == str(payment.id)
    assert "Invoice" in invoice.document.rendered_html
    assert "Receipt" in receipt.document.rendered_html
    assert AuditEvent.objects.filter(event_type="admin.finance_document.invoice.built").exists()
    assert AuditEvent.objects.filter(event_type="admin.finance_document.receipt.built").exists()


@pytest.mark.django_db
def test_v112_build_credit_note_and_refund_document():
    operator = _finance("v112-finance-refund@example.com")
    student = _user("v112-student-refund@example.com")
    _order, payment = _commerce(student=student, marker="v112-refund")

    credit_note = FinanceCommercialDocumentService.build_refund_document(
        document_type=FinanceDocument.DOC_CREDIT_NOTE,
        payment=payment,
        refund_id="refund-v112",
        amount=Decimal("120.00"),
        reason="partial refund",
        actor=operator,
    )
    refund_doc = FinanceCommercialDocumentService.build_refund_document(
        document_type=FinanceDocument.DOC_REFUND_DOCUMENT,
        payment=payment,
        refund_id="refund-v112",
        amount=Decimal("120.00"),
        reason="partial refund",
        actor=operator,
    )

    assert credit_note.document.document_type == FinanceDocument.DOC_CREDIT_NOTE
    assert refund_doc.document.document_type == FinanceDocument.DOC_REFUND_DOCUMENT
    assert credit_note.document.payload["refund_id"] == "refund-v112"
    assert refund_doc.document.payload["refund_amount"] == "120.00"
    assert "Credit Note" in credit_note.document.rendered_html
    assert "Refund Document" in refund_doc.document.rendered_html
    assert AuditEvent.objects.filter(event_type="admin.finance_document.credit_note.built").exists()
    assert AuditEvent.objects.filter(event_type="admin.finance_document.refund_document.built").exists()


@pytest.mark.django_db
def test_v112_accountant_export_contains_finance_document_rows():
    student = _user("v112-student-export@example.com")
    order, payment = _commerce(student=student, marker="v112-export")
    FinanceCommercialDocumentService.build_for_order(
        document_type=FinanceDocument.DOC_INVOICE,
        order=order,
        payment=payment,
    )

    csv_body = FinanceCommercialDocumentService.export_for_accountant(queryset=FinanceDocument.objects.all())

    assert "document_number,document_type,status" in csv_body
    assert str(order.id) in csv_body
    assert str(payment.id) in csv_body
    assert "invoice" in csv_body


@pytest.mark.django_db
def test_v112_finance_documents_api_contract():
    admin = get_user_model().objects.create_superuser(email="v112-admin@example.com", password="pass12345")
    student = _user("v112-api-student@example.com")
    order, payment = _commerce(student=student, marker="v112-api")
    client = APIClient()
    client.force_authenticate(user=admin)

    build_response = client.post(
        "/api/v1/finance-documents/admin/documents/build/",
        {
            "document_type": FinanceDocument.DOC_RECEIPT,
            "order_id": str(order.id),
            "payment_id": str(payment.id),
        },
        format="json",
    )
    assert build_response.status_code == 201
    assert build_response.json()["document"]["document_type"] == FinanceDocument.DOC_RECEIPT

    export_response = client.get("/api/v1/finance-documents/admin/documents/accountant-export/")
    assert export_response.status_code == 200
    assert export_response["Content-Type"] == "text/csv"
    assert "receipt" in export_response.content.decode()
