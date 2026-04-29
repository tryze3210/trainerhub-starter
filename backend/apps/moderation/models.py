import uuid
from django.conf import settings
from django.db import models


class ModerationTargetType(models.TextChoices):
    TRAINER_PROFILE = "trainer_profile", "Trainer profile"
    CONTENT = "content", "Content"
    PROGRAM = "program", "Program"
    DOCUMENT = "document", "Document"


class ModerationStatus(models.TextChoices):
    OPEN = "open", "Open"
    IN_REVIEW = "in_review", "In review"
    RESOLVED = "resolved", "Resolved"
    ESCALATED = "escalated", "Escalated"


class ModerationDecision(models.TextChoices):
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    NEEDS_CHANGES = "needs_changes", "Needs changes"
    ESCALATED = "escalated", "Escalated"


class RiskLevel(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"


class ModerationCase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    target_type = models.CharField(max_length=64, choices=ModerationTargetType.choices)
    target_id = models.CharField(max_length=64)
    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moderation_cases",
    )
    status = models.CharField(max_length=32, choices=ModerationStatus.choices, default=ModerationStatus.OPEN)
    priority = models.PositiveSmallIntegerField(default=50)
    queue = models.CharField(max_length=64, default="default")
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True)
    latest_decision = models.CharField(max_length=32, choices=ModerationDecision.choices, blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_moderation_cases",
    )
    opened_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["priority", "-opened_at"]
        indexes = [
            models.Index(fields=["status", "queue"]),
            models.Index(fields=["target_type", "target_id"]),
        ]


class ModerationCaseEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(ModerationCase, on_delete=models.CASCADE, related_name="events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=64)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class TrainerRiskFlag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trainer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="risk_flags")
    code = models.CharField(max_length=64)
    label = models.CharField(max_length=255)
    risk_level = models.CharField(max_length=16, choices=RiskLevel.choices, default=RiskLevel.LOW)
    is_active = models.BooleanField(default=True)
    source = models.CharField(max_length=64, default="manual")
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["trainer", "is_active"])]


class ModerationReviewDecision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(ModerationCase, on_delete=models.CASCADE, related_name="decisions")
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    decision = models.CharField(max_length=32, choices=ModerationDecision.choices)
    reason = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
