from apps.notifications.models import NotificationType
from apps.notifications.services.delivery_service import NotificationDeliveryService


class DomainNotificationTriggers:
    def __init__(self):
        self.delivery = NotificationDeliveryService()

    def on_order_paid(self, *, user, order):
        notification = self.delivery.create_in_app(
            user=user,
            type=NotificationType.ORDER_PAID,
            title="Order paid",
            body=f"Your order #{order.id} has been paid successfully.",
        )
        self.delivery.queue_email_from_template(
            user=user,
            type=NotificationType.ORDER_PAID,
            template_code="order_paid_email",
            context={"user": user, "order": order},
            notification=notification,
        )

    def on_payment_failed(self, *, user, payment):
        notification = self.delivery.create_in_app(
            user=user,
            type=NotificationType.PAYMENT_FAILED,
            title="Payment failed",
            body=f"Payment for order #{payment.order_id} failed. Please retry.",
        )
        self.delivery.queue_email_from_template(
            user=user,
            type=NotificationType.PAYMENT_FAILED,
            template_code="payment_failed_email",
            context={"user": user, "payment": payment},
            notification=notification,
        )

    def on_subscription_activated(self, *, user, subscription):
        notification = self.delivery.create_in_app(
            user=user,
            type=NotificationType.SUBSCRIPTION_ACTIVATED,
            title="Subscription activated",
            body=f"Subscription #{subscription.id} is active until {subscription.current_period_end}.",
        )
        self.delivery.queue_email_from_template(
            user=user,
            type=NotificationType.SUBSCRIPTION_ACTIVATED,
            template_code="subscription_activated_email",
            context={"user": user, "subscription": subscription},
            notification=notification,
        )
