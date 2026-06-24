from apps.notifications.models import NotificationType
from apps.notifications.services.delivery_service import NotificationDeliveryService


class DomainNotificationTriggers:
    def __init__(self):
        self.delivery = NotificationDeliveryService()

    def _queue_email(self, *, user, type, template_code, context, notification, subject, body):
        return self.delivery.queue_email_from_template(
            user=user,
            type=type,
            template_code=template_code,
            context=context,
            notification=notification,
            fallback_subject=subject,
            fallback_body=body,
        )

    @staticmethod
    def _money(value, currency=''):
        if value in (None, ''):
            return ''
        return f"{value} {currency}".strip()

    @staticmethod
    def _period_end(subscription):
        value = getattr(subscription, 'ends_at', None) or getattr(subscription, 'current_period_end', None)
        return value.isoformat() if hasattr(value, 'isoformat') else value

    def on_order_paid(self, *, user, order):
        event_key = f"order:{order.id}:paid"
        title = "Order paid"
        body = f"Your order #{order.id} has been paid successfully."
        notification = self.delivery.create_in_app(
            user=user,
            type=NotificationType.ORDER_PAID,
            title=title,
            body=body,
            event_key=event_key,
            metadata={'order_id': str(order.id), 'source': 'domain_trigger'},
        )
        self._queue_email(
            user=user,
            type=NotificationType.ORDER_PAID,
            template_code="order_paid_email",
            context={"user": user, "order": order},
            notification=notification,
            subject=title,
            body=body,
        )

    def on_payment_succeeded(self, *, user, payment):
        event_key = f"payment:{payment.id}:succeeded"
        amount = self._money(getattr(payment, 'amount', ''), getattr(payment, 'currency', ''))
        title = "Payment succeeded"
        body = f"Payment #{payment.id} was processed successfully."
        if amount:
            body = f"{body} Amount: {amount}."
        notification = self.delivery.create_in_app(
            user=user,
            type=NotificationType.PAYMENT_SUCCEEDED,
            title=title,
            body=body,
            event_key=event_key,
            metadata={
                'payment_id': str(payment.id),
                'order_id': str(getattr(payment, 'order_id', '') or ''),
                'source': 'domain_trigger',
            },
            cta_label='Open billing',
            cta_url='/billing',
        )
        self._queue_email(
            user=user,
            type=NotificationType.PAYMENT_SUCCEEDED,
            template_code="payment_succeeded_email",
            context={"user": user, "payment": payment},
            notification=notification,
            subject=title,
            body=body,
        )

    def on_payment_failed(self, *, user, payment):
        event_key = f"payment:{payment.id}:failed"
        title = "Payment failed"
        body = f"Payment for order #{payment.order_id} failed. Please retry."
        notification = self.delivery.create_in_app(
            user=user,
            type=NotificationType.PAYMENT_FAILED,
            title=title,
            body=body,
            event_key=event_key,
            metadata={
                'payment_id': str(payment.id),
                'order_id': str(getattr(payment, 'order_id', '') or ''),
                'source': 'domain_trigger',
            },
        )
        self._queue_email(
            user=user,
            type=NotificationType.PAYMENT_FAILED,
            template_code="payment_failed_email",
            context={"user": user, "payment": payment},
            notification=notification,
            subject=title,
            body=body,
        )

    def on_payment_refunded(self, *, user, payment, refund_id='', refund_kind='full', amount=None):
        refund_key = refund_id or getattr(payment, 'id', '')
        event_key = f"payment:{payment.id}:refund:{refund_key}"
        refund_amount = self._money(amount, getattr(payment, 'currency', ''))
        title = "Payment refunded"
        body = f"A {refund_kind} refund was processed for payment #{payment.id}."
        if refund_amount:
            body = f"{body} Amount: {refund_amount}."
        notification = self.delivery.create_in_app(
            user=user,
            type=NotificationType.PAYMENT_REFUNDED,
            title=title,
            body=body,
            event_key=event_key,
            metadata={
                'payment_id': str(payment.id),
                'order_id': str(getattr(payment, 'order_id', '') or ''),
                'refund_id': str(refund_id or ''),
                'refund_kind': refund_kind,
                'source': 'domain_trigger',
            },
            cta_label='Open billing',
            cta_url='/billing',
        )
        self._queue_email(
            user=user,
            type=NotificationType.PAYMENT_REFUNDED,
            template_code="payment_refunded_email",
            context={"user": user, "payment": payment, "refund_id": refund_id, "refund_kind": refund_kind, "amount": amount},
            notification=notification,
            subject=title,
            body=body,
        )

    def on_access_granted(self, *, user, entitlement):
        event_key = f"entitlement:{entitlement.id}:granted"
        target_type = getattr(entitlement, 'target_type', 'content')
        title = "Access opened"
        body = f"New access to {target_type} is active in your account."
        notification = self.delivery.create_in_app(
            user=user,
            type=NotificationType.ACCESS_GRANTED,
            title=title,
            body=body,
            event_key=event_key,
            metadata={
                'entitlement_id': str(entitlement.id),
                'target_type': str(target_type or ''),
                'target_id': str(getattr(entitlement, 'target_id', '') or ''),
                'source': 'domain_trigger',
            },
            cta_label='Open access',
            cta_url='/cabinet',
        )
        self._queue_email(
            user=user,
            type=NotificationType.ACCESS_GRANTED,
            template_code="access_granted_email",
            context={"user": user, "entitlement": entitlement},
            notification=notification,
            subject=title,
            body=body,
        )

    def on_subscription_activated(self, *, user, subscription):
        period_end = self._period_end(subscription)
        event_key = f"subscription:{subscription.id}:activated"
        title = "Subscription activated"
        body = f"Subscription #{subscription.id} is active."
        if period_end:
            body = f"{body} Paid period ends at {period_end}."
        notification = self.delivery.create_in_app(
            user=user,
            type=NotificationType.SUBSCRIPTION_ACTIVATED,
            title=title,
            body=body,
            event_key=event_key,
            metadata={'subscription_id': str(subscription.id), 'source': 'domain_trigger'},
            cta_label='Open subscriptions',
            cta_url='/subscriptions',
        )
        self._queue_email(
            user=user,
            type=NotificationType.SUBSCRIPTION_ACTIVATED,
            template_code="subscription_activated_email",
            context={"user": user, "subscription": subscription},
            notification=notification,
            subject=title,
            body=body,
        )

    def on_subscription_expiring(self, *, user, subscription, days_left=None):
        period_end = self._period_end(subscription)
        date_key = str(period_end or '')
        event_key = f"subscription:{subscription.id}:expiring:{date_key}"
        title = "Subscription expiring"
        body = f"Subscription #{subscription.id} is nearing the end of its paid period."
        if days_left is not None:
            body = f"{body} Days left: {days_left}."
        if period_end:
            body = f"{body} Ends at {period_end}."
        notification = self.delivery.create_in_app(
            user=user,
            type=NotificationType.SUBSCRIPTION_EXPIRING,
            title=title,
            body=body,
            event_key=event_key,
            metadata={
                'subscription_id': str(subscription.id),
                'days_left': days_left,
                'source': 'domain_trigger',
            },
            cta_label='Open subscriptions',
            cta_url='/subscriptions',
        )
        self._queue_email(
            user=user,
            type=NotificationType.SUBSCRIPTION_EXPIRING,
            template_code="subscription_expiring_email",
            context={"user": user, "subscription": subscription, "days_left": days_left},
            notification=notification,
            subject=title,
            body=body,
        )

    def on_payout_paid(self, *, user, payout):
        event_key = f"payout:{payout.id}:paid"
        amount = self._money(getattr(payout, 'amount', ''), getattr(payout, 'currency', ''))
        title = "Payout paid"
        body = f"Payout #{payout.id} was marked as paid."
        if amount:
            body = f"{body} Amount: {amount}."
        notification = self.delivery.create_in_app(
            user=user,
            type=NotificationType.PAYOUT_PAID,
            title=title,
            body=body,
            event_key=event_key,
            metadata={'payout_id': str(payout.id), 'source': 'domain_trigger'},
            cta_label='Open payouts',
            cta_url='/trainer/dashboard/sales',
        )
        self._queue_email(
            user=user,
            type=NotificationType.PAYOUT_PAID,
            template_code="payout_paid_email",
            context={"user": user, "payout": payout},
            notification=notification,
            subject=title,
            body=body,
        )
