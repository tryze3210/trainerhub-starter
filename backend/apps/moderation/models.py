from django.db import models
from apps.common.models import TimeStampedModel


class ModerationCase(TimeStampedModel):
    class TargetType(models.TextChoices):
        MEDIA_ASSET = "media_asset", "Media Asset"
        VIDEO = "video", "Video"
        PROGRAM = "program", "Program"
        BUNDLE = "bundle", "Bundle"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    target_type = models.CharField(max_length=32, choices=TargetType.choices)
    target_id = models.UUIDField(db_index=True)
    trainer_id = models.UUIDField(db_index=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.OPEN)
    queue_reason = models.CharField(max_length=255, blank=True)


class ModerationDecision(TimeStampedModel):
    case = models.ForeignKey(ModerationCase, on_delete=models.CASCADE, related_name="decisions")
    actor_id = models.UUIDField()
    decision = models.CharField(max_length=32)
    comment = models.TextField(blank=True)
