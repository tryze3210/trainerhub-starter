"""
Example integration snippet.
Call from application services, not from serializers/views directly.
"""
from apps.notifications.domain.triggers import DomainNotificationTriggers


def emit_order_paid_notification(*, user, order):
    DomainNotificationTriggers().on_order_paid(user=user, order=order)


def emit_payment_failed_notification(*, user, payment):
    DomainNotificationTriggers().on_payment_failed(user=user, payment=payment)


def emit_subscription_activated_notification(*, user, subscription):
    DomainNotificationTriggers().on_subscription_activated(user=user, subscription=subscription)
