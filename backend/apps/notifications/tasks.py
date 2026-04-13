from celery import shared_task
from apps.notifications.models import NotificationDelivery, NotificationStatus, NotificationChannel
from apps.notifications.services.delivery_service import NotificationDeliveryService


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def deliver_pending_email_notification(self, delivery_id: str):
    delivery = NotificationDelivery.objects.get(id=delivery_id, channel=NotificationChannel.EMAIL)
    service = NotificationDeliveryService()
    service.send_pending_email(delivery)
    return {"delivery_id": delivery_id, "status": delivery.status}


@shared_task
def sweep_pending_email_notifications(limit: int = 200):
    deliveries = NotificationDelivery.objects.filter(
        channel=NotificationChannel.EMAIL,
        status=NotificationStatus.PENDING,
    ).order_by("created_at")[:limit]
    for delivery in deliveries:
        deliver_pending_email_notification.delay(str(delivery.id))
    return deliveries.count()
