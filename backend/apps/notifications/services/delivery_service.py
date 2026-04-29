from django.db import transaction
from django.utils import timezone

from apps.notifications.models import (
    DeliveryStatus,
    Notification,
    NotificationChannel,
    NotificationDelivery,
    NotificationStatus,
    NotificationType,
)
from apps.notifications.services.email_backends import DjangoEmailBackendAdapter
from apps.notifications.services.template_renderer import NotificationTemplateRenderer


_DELIVERY_TO_NOTIFICATION_TYPE = {
    NotificationType.ORDER_PAID: NotificationType.ORDER,
    NotificationType.PAYMENT_FAILED: NotificationType.PAYMENT,
    NotificationType.SUBSCRIPTION_ACTIVATED: NotificationType.SUBSCRIPTION,
    NotificationType.ADMIN_ANNOUNCEMENT: NotificationType.ANNOUNCEMENT,
}


class NotificationDeliveryService:
    def __init__(self):
        self.renderer = NotificationTemplateRenderer()
        self.email_backend = DjangoEmailBackendAdapter()

    @transaction.atomic
    def create_in_app(self, *, user, type: str, title: str, body: str) -> Notification:
        return Notification.objects.create(
            user=user,
            notification_type=_DELIVERY_TO_NOTIFICATION_TYPE.get(type, NotificationType.SYSTEM),
            channel=NotificationChannel.IN_APP,
            title=title,
            body=body,
            status=DeliveryStatus.SENT,
            sent_at=timezone.now(),
        )

    @transaction.atomic
    def queue_email_from_template(self, *, user, type: str, template_code: str, context: dict, notification=None) -> NotificationDelivery:
        rendered = self.renderer.render(code=template_code, context=context)
        return NotificationDelivery.objects.create(
            notification=notification,
            user=user,
            channel=NotificationChannel.EMAIL,
            type=type,
            template_code=rendered.template_code,
            subject=rendered.subject,
            rendered_body=rendered.body,
            status=NotificationStatus.PENDING,
        )

    def send_pending_email(self, delivery: NotificationDelivery) -> NotificationDelivery:
        if delivery.channel != NotificationChannel.EMAIL:
            delivery.mark_failed('Unsupported channel')
            return delivery
        try:
            result = self.email_backend.send(
                to_email=delivery.user.email,
                subject=delivery.subject,
                body=delivery.rendered_body,
            )
            delivery.mark_sent(provider=result.provider, provider_message_id=result.provider_message_id)
        except Exception as exc:
            delivery.mark_failed(str(exc))
        return delivery
