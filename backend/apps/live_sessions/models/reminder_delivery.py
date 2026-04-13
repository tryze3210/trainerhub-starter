import uuid
from django.db import models


class ReminderDelivery(models.Model):
    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        IN_APP = "in_app", "In-app"
        PUSH = "push", "Push"

    class DeliveryStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    live_session_id = models.UUIDField(db_index=True)
    attendance_id = models.UUIDField(db_index=True)
    channel = models.CharField(max_length=32, choices=Channel.choices)
    scheduled_for = models.DateTimeField()
    status = models.CharField(max_length=32, choices=DeliveryStatus.choices, default=DeliveryStatus.PENDING)
    provider_message_id = models.CharField(max_length=255, blank=True)
    failure_reason = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "live_sessions_reminder_delivery"
