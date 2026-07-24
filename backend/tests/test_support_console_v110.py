from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.models import AccountRoleAssignment
from apps.audit.models import AuditEvent
from apps.entitlements.models import Entitlement, EntitlementSourceType, EntitlementStatus, EntitlementTargetType
from apps.notifications.models import NotificationChannel, NotificationDelivery, NotificationStatus, NotificationType
from apps.ops.api.operations_serializers import SupportEntitlementFixSerializer
from apps.ops.support_console import fix_entitlement, get_support_console_snapshot, resend_notification_delivery
from apps.orders.models import Order, OrderItem, OrderStatus, OrderType, PurchasedItemType
from apps.payments.models import Payment, PaymentProvider, PaymentStatus, PaymentWebhookEvent
from apps.subscriptions.models import SubscriptionPlan
from apps.tenancy.models import Tenant, TenantMembership


def _user(email, role="customer"):
    return get_user_model().objects.create_user(email=email, password="pass12345", role=role)


def _support(email):
    user = _user(email)
    AccountRoleAssignment.objects.create(user=user, role=AccountRoleAssignment.ROLE_SUPPORT, is_active=True)
    return user


def _trainer(email):
    return _user(email, role="trainer")


def _tenant_for_trainer(trainer, operator=None):
    tenant = Tenant.objects.create(
        code=f"v110-tenant-{trainer.id}",
        kind="trainer_space",
        name=f"Tenant {trainer.email}",
        owner_account_id=str(trainer.id),
        status="active",
    )
    TenantMembership.objects.create(tenant_id=str(tenant.id), account_id=str(trainer.id), role="owner", status="active")
    if operator:
        TenantMembership.objects.create(tenant_id=str(tenant.id), account_id=str(operator.id), role="support", status="active")
    return tenant


def _commerce(*, trainer, student, marker="v110"):
    plan = SubscriptionPlan.objects.create(
        trainer_id=str(trainer.id),
        title=f"{marker} plan",
        price=Decimal("100.00"),
    )
    order = Order.objects.create(
        user=student,
        order_type=OrderType.SUBSCRIPTION,
        status=OrderStatus.PAID,
        currency="RUB",
        total_amount=Decimal("100.00"),
        external_checkout_id=f"checkout-{marker}",
    )
    OrderItem.objects.create(
        order=order,
        item_type=PurchasedItemType.SUBSCRIPTION_PLAN,
        item_id=str(plan.id),
        title_snapshot=plan.title,
        quantity=1,
        unit_price=Decimal("100.00"),
        total_price=Decimal("100.00"),
    )
    payment = Payment.objects.create(
        order=order,
        provider=PaymentProvider.MOCK,
        status=PaymentStatus.SUCCEEDED,
        amount=Decimal("100.00"),
        currency="RUB",
    )
    webhook = PaymentWebhookEvent.objects.create(
        provider=PaymentProvider.MOCK,
        event_type="payment.succeeded",
        external_event_id=f"event-{marker}",
        payment=payment,
        status=PaymentWebhookEvent.Status.FAILED,
        payload={"marker": marker},
        error_message="boom",
    )
    entitlement = Entitlement.objects.create(
        user=student,
        source_type=EntitlementSourceType.ORDER,
        source_order=order,
        target_type=EntitlementTargetType.PROGRAM,
        target_id=str(plan.id),
        status=EntitlementStatus.ACTIVE,
    )
    delivery = NotificationDelivery.objects.create(
        user=student,
        channel=NotificationChannel.IN_APP,
        type=NotificationType.ACCESS_GRANTED,
        template_code="access_granted",
        subject="Access granted",
        rendered_body="Body",
        status=NotificationStatus.FAILED,
        error_message="provider failed",
    )
    return order, payment, webhook, entitlement, delivery


@pytest.mark.django_db
def test_v110_support_console_snapshot_is_tenant_scoped():
    support = _support("v110-support@example.com")
    trainer = _trainer("v110-trainer@example.com")
    _tenant_for_trainer(trainer, operator=support)
    student = _user("v110-student@example.com")
    _commerce(trainer=trainer, student=student)

    payload = get_support_console_snapshot(operator=support, email=student.email)

    assert payload["user"]["email"] == student.email
    assert payload["orders"]
    assert payload["payments"]
    assert payload["entitlements"]
    assert payload["webhook_errors"]
    assert payload["notification_deliveries"]


@pytest.mark.django_db
def test_v110_support_console_resend_notification_records_audit():
    support = _support("v110-resend-support@example.com")
    trainer = _trainer("v110-resend-trainer@example.com")
    _tenant_for_trainer(trainer, operator=support)
    student = _user("v110-resend-student@example.com")
    _order, _payment, _webhook, _entitlement, delivery = _commerce(trainer=trainer, student=student, marker="v110-resend")

    payload = resend_notification_delivery(operator=support, delivery_id=str(delivery.id), reason="support retry")
    delivery.refresh_from_db()

    assert payload["status"] == "queued"
    assert delivery.status == NotificationStatus.PENDING
    assert AuditEvent.objects.filter(event_type="admin.support.notification_resend", entity_id=str(delivery.id)).exists()


@pytest.mark.django_db
def test_v110_support_console_resend_notification_is_tenant_scoped():
    support = _support("v110-resend-scope-support@example.com")
    trainer = _trainer("v110-resend-scope-trainer@example.com")
    _tenant_for_trainer(trainer, operator=support)
    hidden_student = _user("v110-resend-hidden@example.com")
    hidden_delivery = NotificationDelivery.objects.create(
        user=hidden_student,
        channel=NotificationChannel.IN_APP,
        type=NotificationType.ACCESS_GRANTED,
        template_code="access_granted",
        subject="Hidden delivery",
        rendered_body="Body",
        status=NotificationStatus.FAILED,
        error_message="provider failed",
    )

    with pytest.raises(PermissionError, match="outside the operator tenant scope"):
        resend_notification_delivery(operator=support, delivery_id=str(hidden_delivery.id), reason="retry")


@pytest.mark.django_db
def test_v110_support_console_manual_entitlement_fix_records_audit():
    support = _support("v110-fix-support@example.com")
    trainer = _trainer("v110-fix-trainer@example.com")
    _tenant_for_trainer(trainer, operator=support)
    student = _user("v110-fix-student@example.com")
    _commerce(trainer=trainer, student=student, marker="v110-fix")

    grant_payload = fix_entitlement(
        operator=support,
        action="grant",
        reason="support manual grant",
        user_id=str(student.id),
        target_type=EntitlementTargetType.VIDEO,
        target_id="video-v110",
    )
    entitlement_id = grant_payload["entitlement"]["id"]
    revoke_payload = fix_entitlement(
        operator=support,
        action="revoke",
        reason="support manual revoke",
        entitlement_id=entitlement_id,
    )

    assert grant_payload["status"] == "completed"
    assert revoke_payload["status"] == "completed"
    assert AuditEvent.objects.filter(event_type="admin.support.entitlement_grant", entity_id=entitlement_id).exists()
    assert AuditEvent.objects.filter(event_type="admin.support.entitlement_revoke", entity_id=entitlement_id).exists()


@pytest.mark.django_db
def test_v110_support_console_manual_entitlement_grant_requires_specific_target():
    support = _support("v110-fix-target-support@example.com")
    trainer = _trainer("v110-fix-target-trainer@example.com")
    _tenant_for_trainer(trainer, operator=support)
    student = _user("v110-fix-target-student@example.com")
    _commerce(trainer=trainer, student=student, marker="v110-fix-target")

    with pytest.raises(ValueError, match="target_id is required"):
        fix_entitlement(
            operator=support,
            action="grant",
            reason="support manual grant",
            user_id=str(student.id),
            target_type=EntitlementTargetType.VIDEO,
            target_id="",
        )

    assert not Entitlement.objects.filter(
        user=student,
        source_type=EntitlementSourceType.ADMIN_GRANT,
        target_type=EntitlementTargetType.VIDEO,
    ).exists()


def test_v110_support_entitlement_fix_serializer_requires_specific_target():
    serializer = SupportEntitlementFixSerializer(
        data={
            "action": "grant",
            "reason": "support manual grant",
            "email": "student@example.com",
            "target_type": EntitlementTargetType.VIDEO,
            "target_id": "",
        }
    )

    assert serializer.is_valid() is False
    assert "target_id" in serializer.errors


@pytest.mark.django_db
def test_v110_support_console_endpoint_contract():
    admin = get_user_model().objects.create_superuser(email="v110-admin@example.com", password="pass12345")
    trainer = _trainer("v110-endpoint-trainer@example.com")
    student = _user("v110-endpoint-student@example.com")
    _commerce(trainer=trainer, student=student, marker="v110-endpoint")
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get(f"/api/v1/ops/admin/support-console/?email={student.email}")

    assert response.status_code == 200
    assert response.json()["user"]["email"] == student.email
