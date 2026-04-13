import uuid
from django.conf import settings
from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class DisputeCase(TimestampedModel):
    STATUS_NEW = "new"
    STATUS_UNDER_REVIEW = "under_review"
    STATUS_RESOLVED = "resolved"
    STATUS_REJECTED = "rejected"
    STATUS_ESCALATED = "escalated"

    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_UNDER_REVIEW, "Under review"),
        (STATUS_RESOLVED, "Resolved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_ESCALATED, "Escalated"),
    ]

    TYPE_REFUND = "refund"
    TYPE_CHARGEBACK = "chargeback"
    TYPE_SUPPORT = "support"
    TYPE_CHOICES = [
        (TYPE_REFUND, "Refund"),
        (TYPE_CHARGEBACK, "Chargeback"),
        (TYPE_SUPPORT, "Support"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(max_length=32, unique=True)
    dispute_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    opened_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="opened_disputes")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_disputes")
    trainer_id = models.UUIDField(null=True, blank=True)
    order_id = models.UUIDField(null=True, blank=True)
    payment_id = models.UUIDField(null=True, blank=True)
    subject = models.CharField(max_length=255)
    reason_code = models.CharField(max_length=64, blank=True)
    summary = models.TextField(blank=True)
    resolution_note = models.TextField(blank=True)
    opened_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "dispute_type"]),
            models.Index(fields=["opened_at"]),
            models.Index(fields=["trainer_id"]),
            models.Index(fields=["order_id"]),
        ]


class DisputeEvent(TimestampedModel):
    EVENT_CREATED = "created"
    EVENT_COMMENT = "comment"
    EVENT_STATUS_CHANGED = "status_changed"
    EVENT_REFUND_REVIEWED = "refund_reviewed"
    EVENT_CHARGEBACK_SYNCED = "chargeback_synced"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dispute_case = models.ForeignKey(DisputeCase, on_delete=models.CASCADE, related_name="events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    event_type = models.CharField(max_length=50)
    body = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["created_at"]


class RefundReview(TimestampedModel):
    DECISION_PENDING = "pending"
    DECISION_APPROVED = "approved"
    DECISION_REJECTED = "rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dispute_case = models.OneToOneField(DisputeCase, on_delete=models.CASCADE, related_name="refund_review")
    requested_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=8, default="RUB")
    decision = models.CharField(max_length=20, default=DECISION_PENDING)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rationale = models.TextField(blank=True)


class ChargebackOperation(TimestampedModel):
    STATUS_OPEN = "open"
    STATUS_WON = "won"
    STATUS_LOST = "lost"
    STATUS_NEEDS_EVIDENCE = "needs_evidence"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dispute_case = models.OneToOneField(DisputeCase, on_delete=models.CASCADE, related_name="chargeback_operation")
    provider_case_id = models.CharField(max_length=128, blank=True)
    network = models.CharField(max_length=32, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=8, default="RUB")
    status = models.CharField(max_length=32, default=STATUS_OPEN)
    evidence_due_at = models.DateTimeField(null=True, blank=True)
    evidence_payload = models.JSONField(default=dict, blank=True)
    provider_payload = models.JSONField(default=dict, blank=True)


class SupportInboxItem(TimestampedModel):
    PRIORITY_LOW = "low"
    PRIORITY_NORMAL = "normal"
    PRIORITY_HIGH = "high"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dispute_case = models.OneToOneField(DisputeCase, on_delete=models.CASCADE, related_name="support_inbox_item")
    priority = models.CharField(max_length=20, default=PRIORITY_NORMAL)
    channel = models.CharField(max_length=32, default="in_app")
    last_message_at = models.DateTimeField(null=True, blank=True)
    unread_for_admin = models.BooleanField(default=True)
    unread_for_user = models.BooleanField(default=False)
