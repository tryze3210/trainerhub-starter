from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.audit.services import AuditService
from apps.entitlements.models import Entitlement, EntitlementSourceType, EntitlementStatus
from apps.entitlements.services import EntitlementService
from apps.notifications.models import NotificationDelivery, NotificationStatus
from apps.orders.models import Order
from apps.payments.models import Payment, PaymentWebhookEvent
from apps.tenancy.scoping import (
    is_global_operator,
    scope_entitlements_for_user,
    scope_orders_for_user,
    scope_payment_webhooks_for_user,
    scope_payments_for_user,
)


class SupportConsoleTargetNotFound(ValueError):
    pass


class SupportConsoleAccessDenied(PermissionError):
    pass


def _user_payload(user) -> dict[str, Any]:
    return {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": getattr(user, "role", ""),
        "is_active": user.is_active,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


def _order_payload(order: Order) -> dict[str, Any]:
    return {
        "id": str(order.id),
        "status": order.status,
        "total_amount": str(order.total_amount),
        "currency": order.currency,
        "created_at": order.created_at,
        "paid_at": order.paid_at,
        "href": f"/admin/entities/order/{order.id}",
    }


def _payment_payload(payment: Payment) -> dict[str, Any]:
    return {
        "id": str(payment.id),
        "order_id": str(payment.order_id),
        "provider": payment.provider,
        "status": payment.status,
        "amount": str(payment.amount),
        "currency": payment.currency,
        "external_payment_id": payment.external_payment_id,
        "confirmed_at": payment.confirmed_at,
        "href": f"/admin/entities/payment/{payment.id}",
    }


def _entitlement_payload(entitlement: Entitlement) -> dict[str, Any]:
    return {
        "id": str(entitlement.id),
        "source_type": entitlement.source_type,
        "source_order_id": str(entitlement.source_order_id or ""),
        "source_subscription_id": str(entitlement.source_subscription_id or ""),
        "target_type": entitlement.target_type,
        "target_id": str(entitlement.target_id or ""),
        "status": entitlement.status,
        "starts_at": entitlement.starts_at,
        "ends_at": entitlement.ends_at,
        "metadata": entitlement.metadata or {},
        "href": f"/admin/entities/entitlement/{entitlement.id}",
    }


def _webhook_payload(event: PaymentWebhookEvent) -> dict[str, Any]:
    return {
        "id": str(event.id),
        "payment_id": str(event.payment_id or ""),
        "provider": event.provider,
        "event_type": event.event_type,
        "external_event_id": event.external_event_id,
        "status": event.status,
        "error_message": event.error_message,
        "attempts": event.attempts,
        "received_at": event.received_at,
        "processed_at": event.processed_at,
        "href": f"/admin/entities/payment_webhook/{event.id}",
    }


def _delivery_payload(delivery: NotificationDelivery) -> dict[str, Any]:
    return {
        "id": str(delivery.id),
        "user_id": str(delivery.user_id),
        "channel": delivery.channel,
        "type": delivery.type,
        "template_code": delivery.template_code,
        "subject": delivery.subject,
        "status": delivery.status,
        "error_message": delivery.error_message,
        "provider": delivery.provider,
        "provider_message_id": delivery.provider_message_id,
        "sent_at": delivery.sent_at,
        "created_at": delivery.created_at,
    }


def resolve_support_user(*, user_id: str = "", email: str = ""):
    User = get_user_model()
    queryset = User.objects.all()
    if user_id:
        queryset = queryset.filter(id=user_id)
    elif email:
        queryset = queryset.filter(email__iexact=email.strip())
    else:
        raise SupportConsoleTargetNotFound("user_id or email is required.")
    target = queryset.first()
    if not target:
        raise SupportConsoleTargetNotFound("User was not found.")
    return target


def _operator_can_view_user(*, operator, target_user) -> bool:
    if is_global_operator(operator):
        return True
    return (
        scope_orders_for_user(Order.objects.filter(user=target_user), operator).exists()
        or scope_entitlements_for_user(Entitlement.objects.filter(user=target_user), operator).exists()
        or scope_payments_for_user(Payment.objects.filter(order__user=target_user), operator).exists()
    )


def get_support_console_snapshot(*, operator, user_id: str = "", email: str = "", limit: int = 25) -> dict[str, Any]:
    target = resolve_support_user(user_id=user_id, email=email)
    if not _operator_can_view_user(operator=operator, target_user=target):
        raise SupportConsoleAccessDenied("User is outside the operator tenant scope.")
    limit = max(1, min(int(limit or 25), 100))
    orders = scope_orders_for_user(
        Order.objects.filter(user=target).prefetch_related("items").order_by("-created_at"),
        operator,
    )[:limit]
    payments = scope_payments_for_user(
        Payment.objects.select_related("order").filter(order__user=target).order_by("-created_at"),
        operator,
    )[:limit]
    entitlements = scope_entitlements_for_user(
        Entitlement.objects.filter(user=target).select_related("source_order", "source_subscription").order_by("-created_at"),
        operator,
    )[:limit]
    webhook_errors = scope_payment_webhooks_for_user(
        PaymentWebhookEvent.objects.select_related("payment", "payment__order").filter(
            Q(payment__order__user=target),
            status__in=[
                PaymentWebhookEvent.Status.FAILED,
                PaymentWebhookEvent.Status.REJECTED,
                PaymentWebhookEvent.Status.IGNORED,
            ],
        ).order_by("-received_at", "-created_at"),
        operator,
    )[:limit]
    deliveries = NotificationDelivery.objects.filter(user=target).order_by("-created_at")[:limit]
    return {
        "user": _user_payload(target),
        "orders": [_order_payload(item) for item in orders],
        "payments": [_payment_payload(item) for item in payments],
        "entitlements": [_entitlement_payload(item) for item in entitlements],
        "webhook_errors": [_webhook_payload(item) for item in webhook_errors],
        "notification_deliveries": [_delivery_payload(item) for item in deliveries],
        "summary": {
            "orders_count": len(orders),
            "payments_count": len(payments),
            "entitlements_count": len(entitlements),
            "webhook_errors_count": len(webhook_errors),
            "notification_deliveries_count": len(deliveries),
        },
        "generated_at": timezone.now(),
    }


def _delivery_for_operator(*, operator, delivery_id: str) -> NotificationDelivery:
    delivery = NotificationDelivery.objects.select_related("user").get(pk=delivery_id)
    if not _operator_can_view_user(operator=operator, target_user=delivery.user):
        raise SupportConsoleAccessDenied("Notification delivery is outside the operator tenant scope.")
    return delivery


@transaction.atomic
def resend_notification_delivery(*, operator, delivery_id: str, reason: str, request=None) -> dict[str, Any]:
    delivery = _delivery_for_operator(operator=operator, delivery_id=delivery_id)
    previous_status = delivery.status
    delivery.status = NotificationStatus.PENDING
    delivery.error_message = ""
    delivery.provider = ""
    delivery.provider_message_id = ""
    delivery.sent_at = None
    delivery.save(update_fields=["status", "error_message", "provider", "provider_message_id", "sent_at", "updated_at"])
    audit_event = AuditService.log_admin_action(
        request=request,
        actor=operator,
        action="support.notification_resend",
        target_type="notification_delivery",
        target_id=str(delivery.id),
        reason=reason,
        status="accepted",
        context={"previous_status": previous_status, "new_status": delivery.status, "user_id": str(delivery.user_id)},
    )
    return {
        "status": "queued",
        "delivery": _delivery_payload(delivery),
        "previous_status": previous_status,
        "audit_event_id": str(audit_event.id),
    }


def _entitlement_for_operator(*, operator, entitlement_id: str) -> Entitlement:
    entitlement = Entitlement.objects.select_related("user").filter(pk=entitlement_id).first()
    if not entitlement:
        raise SupportConsoleTargetNotFound("Entitlement was not found.")
    if not _operator_can_view_user(operator=operator, target_user=entitlement.user):
        raise SupportConsoleAccessDenied("Entitlement is outside the operator tenant scope.")
    return entitlement


@transaction.atomic
def fix_entitlement(
    *,
    operator,
    action: str,
    reason: str,
    user_id: str = "",
    email: str = "",
    entitlement_id: str = "",
    target_type: str = "",
    target_id: str = "",
    request=None,
) -> dict[str, Any]:
    action = action.strip().lower()
    if action == "grant":
        target = resolve_support_user(user_id=user_id, email=email)
        if not _operator_can_view_user(operator=operator, target_user=target):
            raise SupportConsoleAccessDenied("User is outside the operator tenant scope.")
        entitlement = EntitlementService.grant(
            user=target,
            target_type=target_type,
            target_id=target_id,
            source_type=EntitlementSourceType.ADMIN_GRANT,
            metadata={
                "source": "support_console",
                "reason": reason,
                "operator_id": str(operator.id),
            },
        )
        changed = True
        previous_status = ""
    elif action == "revoke":
        if entitlement_id:
            entitlement = _entitlement_for_operator(operator=operator, entitlement_id=entitlement_id)
        else:
            target = resolve_support_user(user_id=user_id, email=email)
            if not _operator_can_view_user(operator=operator, target_user=target):
                raise SupportConsoleAccessDenied("User is outside the operator tenant scope.")
            queryset = Entitlement.objects.filter(user=target)
            entitlement = queryset.filter(target_type=target_type, target_id=str(target_id), status=EntitlementStatus.ACTIVE).first()
            if not entitlement:
                raise SupportConsoleTargetNotFound("Active entitlement was not found.")
        previous_status = entitlement.status
        changed = EntitlementService.revoke(
            entitlement=entitlement,
            reason=reason or "support_console",
            revoked_by="support_console",
            request=request,
        )
        entitlement.refresh_from_db()
    else:
        raise ValueError("Unsupported entitlement fix action.")

    audit_event = AuditService.log_admin_action(
        request=request,
        actor=operator,
        action=f"support.entitlement_{action}",
        target_type="entitlement",
        target_id=str(entitlement.id),
        reason=reason,
        status="completed" if changed else "skipped",
        context={
            "action": action,
            "previous_status": previous_status,
            "new_status": entitlement.status,
            "user_id": str(entitlement.user_id),
            "target_type": entitlement.target_type,
            "target_id": str(entitlement.target_id or ""),
        },
    )
    return {
        "status": "completed" if changed else "skipped",
        "entitlement": _entitlement_payload(entitlement),
        "previous_status": previous_status,
        "audit_event_id": str(audit_event.id),
    }
