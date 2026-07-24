from django.conf import settings
from django.db import models
from django.utils import timezone

from .constants import (
    DeliveryStatus,
    NotificationCategory,
    NotificationChannel,
    TemplateStatus,
)


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class NotificationTemplate(TimestampedModel):
    key = models.CharField(max_length=128, unique=True)
    category = models.CharField(max_length=32, choices=NotificationCategory.CHOICES)
    channel = models.CharField(max_length=16, choices=NotificationChannel.CHOICES)
    locale = models.CharField(max_length=16, default="en")
    status = models.CharField(max_length=16, choices=TemplateStatus.CHOICES, default=TemplateStatus.DRAFT)
    subject_template = models.TextField(blank=True)
    title_template = models.TextField(blank=True)
    body_template = models.TextField()
    metadata_schema = models.JSONField(default=dict, blank=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "comms_notification_template"
        ordering = ("key", "channel", "locale", "-version")


class NotificationPreference(TimestampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_preferences")
    category = models.CharField(max_length=32, choices=NotificationCategory.CHOICES)
    channel = models.CharField(max_length=16, choices=NotificationChannel.CHOICES)
    is_enabled = models.BooleanField(default=True)

    class Meta:
        db_table = "comms_notification_preference"
        unique_together = ("user", "category", "channel")


class SuppressionRule(TimestampedModel):
    code = models.CharField(max_length=64, unique=True)
    category = models.CharField(max_length=32, choices=NotificationCategory.CHOICES, blank=True)
    channel = models.CharField(max_length=16, choices=NotificationChannel.CHOICES, blank=True)
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    conditions = models.JSONField(default=dict, blank=True)
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "comms_suppression_rule"

    def is_currently_active(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.starts_at and self.starts_at > now:
            return False
        if self.ends_at and self.ends_at < now:
            return False
        return True


class NotificationMessage(TimestampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_messages")
    category = models.CharField(max_length=32, choices=NotificationCategory.CHOICES)
    channel = models.CharField(max_length=16, choices=NotificationChannel.CHOICES)
    template = models.ForeignKey(NotificationTemplate, null=True, blank=True, on_delete=models.SET_NULL, related_name="messages")
    event_key = models.CharField(max_length=128)
    idempotency_key = models.CharField(max_length=255, unique=True)
    subject = models.TextField(blank=True)
    title = models.TextField(blank=True)
    body = models.TextField()
    payload = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    correlation_id = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=16, choices=DeliveryStatus.CHOICES, default=DeliveryStatus.PENDING)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    suppressed_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "comms_notification_message"
        ordering = ("-created_at",)


class DeliveryAttempt(TimestampedModel):
    message = models.ForeignKey(NotificationMessage, on_delete=models.CASCADE, related_name="delivery_attempts")
    provider = models.CharField(max_length=64)
    status = models.CharField(max_length=16, choices=DeliveryStatus.CHOICES)
    request_payload = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    response_code = models.CharField(max_length=32, blank=True)
    error_message = models.TextField(blank=True)
    attempted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "comms_delivery_attempt"
        ordering = ("-attempted_at",)


class CommunicationLedger(TimestampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="communication_ledger_entries")
    event_key = models.CharField(max_length=128)
    channel = models.CharField(max_length=16, choices=NotificationChannel.CHOICES)
    category = models.CharField(max_length=32, choices=NotificationCategory.CHOICES)
    message = models.ForeignKey(NotificationMessage, null=True, blank=True, on_delete=models.SET_NULL, related_name="ledger_entries")
    direction = models.CharField(max_length=16, default="outbound")
    outcome = models.CharField(max_length=32)
    provider = models.CharField(max_length=64, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now)
    data = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "comms_communication_ledger"
        ordering = ("-occurred_at",)
