from django.conf import settings
from django.db import models
from django.utils import timezone
import uuid


class NotificationChannel(models.TextChoices):
    IN_APP = "in_app", "In-app"
    EMAIL = "email", "Email"


class NotificationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"
    SKIPPED = "skipped", "Skipped"


class NotificationType(models.TextChoices):
    ORDER_PAID = "order_paid", "Order paid"
    PAYMENT_FAILED = "payment_failed", "Payment failed"
    SUBSCRIPTION_ACTIVATED = "subscription_activated", "Subscription activated"
    ADMIN_ANNOUNCEMENT = "admin_announcement", "Admin announcement"


class NotificationTemplate(models.Model):
    code = models.CharField(max_length=100, unique=True)
    channel = models.CharField(max_length=20, choices=NotificationChannel.choices)
    subject_template = models.CharField(max_length=255, blank=True)
    body_template = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code}:{self.channel}"


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=50, choices=NotificationType.choices)
    title = models.CharField(max_length=255)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class NotificationDelivery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name="deliveries", null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_deliveries")
    channel = models.CharField(max_length=20, choices=NotificationChannel.choices)
    type = models.CharField(max_length=50, choices=NotificationType.choices)
    template_code = models.CharField(max_length=100, blank=True)
    subject = models.CharField(max_length=255, blank=True)
    rendered_body = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=NotificationStatus.choices, default=NotificationStatus.PENDING)
    error_message = models.TextField(blank=True)
    provider = models.CharField(max_length=100, blank=True)
    provider_message_id = models.CharField(max_length=255, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["channel", "status", "created_at"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["type", "created_at"]),
        ]

    def mark_sent(self, provider: str = "", provider_message_id: str = ""):
        self.status = NotificationStatus.SENT
        self.provider = provider
        self.provider_message_id = provider_message_id
        self.sent_at = timezone.now()
        self.error_message = ""
        self.save(update_fields=["status", "provider", "provider_message_id", "sent_at", "error_message", "updated_at"])

    def mark_failed(self, error_message: str):
        self.status = NotificationStatus.FAILED
        self.error_message = error_message[:4000]
        self.save(update_fields=["status", "error_message", "updated_at"])
