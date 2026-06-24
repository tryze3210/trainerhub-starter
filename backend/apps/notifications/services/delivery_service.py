from django.db import transaction
from django.utils import timezone

from apps.notifications.models import (
    DeliveryStatus,
    Notification,
    NotificationChannel,
    NotificationDelivery,
    NotificationStatus,
    NotificationTemplate,
    NotificationType,
)
from apps.notifications.services.email_backends import DjangoEmailBackendAdapter
from apps.notifications.services.template_renderer import NotificationTemplateRenderer


_DELIVERY_TO_NOTIFICATION_TYPE = {
    NotificationType.ORDER_PAID: NotificationType.ORDER,
    NotificationType.PAYMENT_SUCCEEDED: NotificationType.PAYMENT,
    NotificationType.PAYMENT_FAILED: NotificationType.PAYMENT,
    NotificationType.PAYMENT_REFUNDED: NotificationType.PAYMENT,
    NotificationType.ACCESS_GRANTED: NotificationType.SYSTEM,
    NotificationType.SUBSCRIPTION_ACTIVATED: NotificationType.SUBSCRIPTION,
    NotificationType.SUBSCRIPTION_EXPIRING: NotificationType.SUBSCRIPTION,
    NotificationType.PAYOUT_PAID: NotificationType.SYSTEM,
    NotificationType.ADMIN_ANNOUNCEMENT: NotificationType.ANNOUNCEMENT,
}


class NotificationDeliveryService:
    def __init__(self):
        self.renderer = NotificationTemplateRenderer()
        self.email_backend = DjangoEmailBackendAdapter()

    @transaction.atomic
    def create_in_app(
        self,
        *,
        user,
        type: str,
        title: str,
        body: str,
        metadata: dict | None = None,
        event_key: str = '',
        cta_label: str = '',
        cta_url: str = '',
    ) -> Notification:
        metadata = dict(metadata or {})
        if event_key:
            metadata['event_key'] = event_key
            existing = Notification.objects.filter(user=user, metadata__event_key=event_key).order_by('-created_at').first()
            if existing:
                return existing
        return Notification.objects.create(
            user=user,
            notification_type=_DELIVERY_TO_NOTIFICATION_TYPE.get(type, NotificationType.SYSTEM),
            channel=NotificationChannel.IN_APP,
            title=title,
            body=body,
            cta_label=cta_label,
            cta_url=cta_url,
            metadata=metadata,
            status=DeliveryStatus.SENT,
            sent_at=timezone.now(),
        )

    @transaction.atomic
    def queue_email_from_template(
        self,
        *,
        user,
        type: str,
        template_code: str,
        context: dict,
        notification=None,
        fallback_subject: str = '',
        fallback_body: str = '',
    ) -> NotificationDelivery:
        if notification is not None:
            existing = NotificationDelivery.objects.filter(
                notification=notification,
                user=user,
                channel=NotificationChannel.EMAIL,
                type=type,
            ).order_by('-created_at').first()
            if existing:
                return existing
        try:
            rendered = self.renderer.render(code=template_code, context=context)
            status = NotificationStatus.PENDING
            subject = rendered.subject
            body = rendered.body
            error_message = ''
        except NotificationTemplate.DoesNotExist:
            status = NotificationStatus.SKIPPED
            subject = fallback_subject
            body = fallback_body
            error_message = f"Notification template '{template_code}' is not configured."
        return NotificationDelivery.objects.create(
            notification=notification,
            user=user,
            channel=NotificationChannel.EMAIL,
            type=type,
            template_code=template_code,
            subject=subject,
            rendered_body=body,
            status=status,
            error_message=error_message,
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
