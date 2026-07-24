from django.conf import settings
from django.db import models
from django.utils import timezone

from .constants import AuditActorType, DeliveryTargetType, EventStatus


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AuditLogEntry(models.Model):
    action = models.CharField(max_length=128, db_index=True)
    actor_type = models.CharField(max_length=32, choices=AuditActorType.CHOICES)
    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="integration_audit_entries",
    )
    object_type = models.CharField(max_length=128, db_index=True)
    object_id = models.CharField(max_length=64, db_index=True)
    correlation_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]


class EventSubscription(TimeStampedModel):
    code = models.CharField(max_length=64, unique=True)
    target_type = models.CharField(max_length=32, choices=DeliveryTargetType.CHOICES)
    endpoint = models.CharField(max_length=512, blank=True, default="")
    topic = models.CharField(max_length=128, blank=True, default="")
    is_enabled = models.BooleanField(default=True)
    event_names = models.JSONField(default=list, blank=True)
    signing_secret = models.CharField(max_length=255, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.code


class DomainOutboxEvent(TimeStampedModel):
    event_name = models.CharField(max_length=128, db_index=True)
    aggregate_type = models.CharField(max_length=128, db_index=True)
    aggregate_id = models.CharField(max_length=64, db_index=True)
    correlation_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    causation_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    idempotency_key = models.CharField(max_length=191, unique=True)
    payload = models.JSONField(default=dict, blank=True)
    headers = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=32, choices=EventStatus.CHOICES, default=EventStatus.PENDING, db_index=True)
    available_at = models.DateTimeField(default=timezone.now, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    dead_lettered_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default="")
    attempt_count = models.PositiveIntegerField(default=0)
    source_app = models.CharField(max_length=64, blank=True, default="")
    source_model = models.CharField(max_length=128, blank=True, default="")
    source_id = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(fields=["status", "available_at"]),
            models.Index(fields=["event_name", "created_at"]),
        ]


class EventDeliveryAttempt(models.Model):
    outbox_event = models.ForeignKey(DomainOutboxEvent, on_delete=models.CASCADE, related_name="delivery_attempts")
    subscription = models.ForeignKey(EventSubscription, on_delete=models.PROTECT, related_name="delivery_attempts")
    attempt_no = models.PositiveIntegerField()
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    success = models.BooleanField(default=False)
    response_code = models.CharField(max_length=32, blank=True, default="")
    response_body = models.TextField(blank=True, default="")
    error_message = models.TextField(blank=True, default="")

    class Meta:
        unique_together = [("outbox_event", "subscription", "attempt_no")]
        ordering = ["-started_at", "-id"]


class DeadLetterEvent(models.Model):
    outbox_event = models.OneToOneField(DomainOutboxEvent, on_delete=models.CASCADE, related_name="dead_letter_record")
    reason = models.CharField(max_length=255)
    payload_snapshot = models.JSONField(default=dict, blank=True)
    headers_snapshot = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_note = models.TextField(blank=True, default="")


class InboundMessage(TimeStampedModel):
    provider = models.CharField(max_length=64, db_index=True)
    message_type = models.CharField(max_length=128, db_index=True)
    external_event_key = models.CharField(max_length=191, db_index=True)
    correlation_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    headers = models.JSONField(default=dict, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    is_duplicate = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True, default="")

    class Meta:
        unique_together = [("provider", "external_event_key")]
        ordering = ["-received_at", "-id"]
