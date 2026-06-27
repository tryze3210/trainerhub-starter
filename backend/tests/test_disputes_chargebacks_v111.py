from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.models import AccountRoleAssignment
from apps.audit.models import AuditEvent
from apps.disputes.models import ChargebackOperation, DisputeCase, DisputeEvent
from apps.disputes.services.case_service import ChargebackDisputeService
from apps.entitlements.access_audit import AccessControlAuditService
from apps.entitlements.models import Entitlement, EntitlementSourceType, EntitlementStatus, EntitlementTargetType
from apps.orders.models import Order, OrderItem, OrderStatus, OrderType, PurchasedItemType
from apps.payments.models import Payment, PaymentProvider, PaymentStatus


def _user(email, role="customer"):
    return get_user_model().objects.create_user(email=email, password="pass12345", role=role)


def _finance(email):
    user = _user(email)
    AccountRoleAssignment.objects.create(user=user, role=AccountRoleAssignment.ROLE_FINANCE, is_active=True)
    return user


def _commerce(*, student, marker="v111"):
    order = Order.objects.create(
        user=student,
        order_type=OrderType.ONE_TIME,
        status=OrderStatus.COMPLETED,
        currency="RUB",
        total_amount=Decimal("250.00"),
        external_checkout_id=f"checkout-{marker}",
    )
    OrderItem.objects.create(
        order=order,
        item_type=PurchasedItemType.PROGRAM,
        item_id=f"program-{marker}",
        title_snapshot=f"{marker} program",
        quantity=1,
        unit_price=Decimal("250.00"),
        total_price=Decimal("250.00"),
        metadata={"trainer_id": str(student.id)},
    )
    payment = Payment.objects.create(
        order=order,
        provider=PaymentProvider.MOCK,
        status=PaymentStatus.SUCCEEDED,
        amount=Decimal("250.00"),
        currency="RUB",
        provider_payload={},
    )
    entitlement = Entitlement.objects.create(
        user=student,
        source_type=EntitlementSourceType.ORDER,
        source_order=order,
        target_type=EntitlementTargetType.PROGRAM,
        target_id=f"program-{marker}",
        status=EntitlementStatus.ACTIVE,
        metadata={},
    )
    return order, payment, entitlement


@pytest.mark.django_db
def test_v111_chargeback_open_holds_access_and_audits():
    operator = _finance("v111-finance-open@example.com")
    student = _user("v111-student-open@example.com")
    order, payment, entitlement = _commerce(student=student, marker="v111-open")

    payload = ChargebackDisputeService.open_chargeback(
        operator=operator,
        payment_id=str(payment.id),
        provider_case_id="cb-open-1",
        network="visa",
        reason="provider dispute opened",
    )
    payment.refresh_from_db()
    order.refresh_from_db()
    entitlement.refresh_from_db()

    assert payload["status"] == ChargebackOperation.STATUS_OPEN
    assert payload["held_entitlements_count"] == 1
    assert payment.status == PaymentStatus.DISPUTED
    assert order.status == OrderStatus.DISPUTED
    assert entitlement.metadata["access_hold"] is True
    assert entitlement.metadata["chargeback_operation_id"] == payload["id"]
    assert DisputeCase.objects.filter(payment_id=payment.id, dispute_type=DisputeCase.TYPE_CHARGEBACK).exists()
    assert DisputeEvent.objects.filter(payload__action="opened").exists()
    assert AuditEvent.objects.filter(event_type="admin.chargeback.opened", entity_id=payload["id"]).exists()

    decision = AccessControlAuditService.check(
        user=student,
        target_type=EntitlementTargetType.PROGRAM,
        target_id="program-v111-open",
        include_admin_override=False,
    )
    assert decision["allowed"] is False
    assert decision["code"] == "entitlement_access_held"


@pytest.mark.django_db
def test_v111_chargeback_evidence_and_won_releases_hold():
    operator = _finance("v111-finance-won@example.com")
    student = _user("v111-student-won@example.com")
    order, payment, entitlement = _commerce(student=student, marker="v111-won")
    opened = ChargebackDisputeService.open_chargeback(
        operator=operator,
        payment_id=str(payment.id),
        provider_case_id="cb-won-1",
    )
    operation = ChargebackOperation.objects.get(id=opened["id"])

    evidence = ChargebackDisputeService.submit_evidence(
        operator=operator,
        operation=operation,
        evidence_payload={"invoice_url": "https://example.test/invoice.pdf", "access_logs": ["lesson-opened"]},
        note="submitted evidence",
    )
    operation.refresh_from_db()
    assert evidence["status"] == ChargebackOperation.STATUS_OPEN
    assert operation.evidence_payload["invoice_url"].endswith("invoice.pdf")
    assert operation.evidence_payload["submitted_by_id"] == str(operator.id)

    resolved = ChargebackDisputeService.resolve(
        operator=operator,
        operation=operation,
        outcome=ChargebackOperation.STATUS_WON,
        note="provider accepted evidence",
    )
    payment.refresh_from_db()
    order.refresh_from_db()
    entitlement.refresh_from_db()
    operation.refresh_from_db()

    assert resolved["status"] == ChargebackOperation.STATUS_WON
    assert resolved["released_entitlements_count"] == 1
    assert payment.status == PaymentStatus.SUCCEEDED
    assert order.status == OrderStatus.COMPLETED
    assert DisputeCase.objects.get(id=operation.dispute_case_id).status == DisputeCase.STATUS_RESOLVED
    assert "access_hold" not in entitlement.metadata
    assert AuditEvent.objects.filter(event_type="admin.chargeback.won", entity_id=str(operation.id)).exists()


@pytest.mark.django_db
def test_v111_chargeback_lost_revokes_entitlement():
    operator = _finance("v111-finance-lost@example.com")
    student = _user("v111-student-lost@example.com")
    order, payment, entitlement = _commerce(student=student, marker="v111-lost")
    opened = ChargebackDisputeService.open_chargeback(
        operator=operator,
        payment_id=str(payment.id),
        provider_case_id="cb-lost-1",
    )
    operation = ChargebackOperation.objects.get(id=opened["id"])

    payload = ChargebackDisputeService.resolve(
        operator=operator,
        operation=operation,
        outcome=ChargebackOperation.STATUS_LOST,
        note="provider ruled against platform",
    )
    payment.refresh_from_db()
    order.refresh_from_db()
    entitlement.refresh_from_db()
    operation.refresh_from_db()

    assert payload["status"] == ChargebackOperation.STATUS_LOST
    assert payment.status == PaymentStatus.CHARGED_BACK
    assert order.status == OrderStatus.CHARGED_BACK
    assert entitlement.status == EntitlementStatus.REVOKED
    assert entitlement.metadata["revocation_reason"] == "payment_chargeback_lost"
    assert DisputeCase.objects.get(id=operation.dispute_case_id).status == DisputeCase.STATUS_REJECTED
    assert AuditEvent.objects.filter(event_type="admin.chargeback.lost", entity_id=str(operation.id)).exists()


@pytest.mark.django_db
def test_v111_chargeback_api_contract():
    admin = get_user_model().objects.create_superuser(email="v111-admin@example.com", password="pass12345")
    student = _user("v111-api-student@example.com")
    _order, payment, _entitlement = _commerce(student=student, marker="v111-api")
    client = APIClient()
    client.force_authenticate(user=admin)

    open_response = client.post(
        "/api/v1/disputes/admin/chargebacks/open/",
        {
            "payment_id": str(payment.id),
            "provider_case_id": "cb-api-1",
            "network": "visa",
            "reason": "api open",
        },
        format="json",
    )
    assert open_response.status_code == 201
    operation_id = open_response.json()["id"]

    evidence_response = client.post(
        f"/api/v1/disputes/admin/chargebacks/{operation_id}/evidence/",
        {"evidence_payload": {"invoice_id": "inv-api-1"}, "note": "api evidence"},
        format="json",
    )
    assert evidence_response.status_code == 200

    resolve_response = client.post(
        f"/api/v1/disputes/admin/chargebacks/{operation_id}/resolve/",
        {"outcome": ChargebackOperation.STATUS_WON, "note": "api won"},
        format="json",
    )
    assert resolve_response.status_code == 200
    assert resolve_response.json()["status"] == ChargebackOperation.STATUS_WON
