import uuid
from django.db import models
from apps.common.models import TimeStampedModel


class MediaAsset(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class Type(models.TextChoices):
        VIDEO = "video", "Video"
        THUMBNAIL = "thumbnail", "Thumbnail"
        PREVIEW = "preview", "Preview"

    class UploadStatus(models.TextChoices):
        CREATED = "created", "Created"
        UPLOADING = "uploading", "Uploading"
        UPLOADED = "uploaded", "Uploaded"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    class ModerationStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    trainer_id = models.UUIDField(db_index=True)
    asset_type = models.CharField(max_length=32, choices=Type.choices)
    title = models.CharField(max_length=255)
    storage_bucket = models.CharField(max_length=255)
    storage_key = models.CharField(max_length=1024, unique=True)
    upload_status = models.CharField(max_length=32, choices=UploadStatus.choices, default=UploadStatus.CREATED)
    moderation_status = models.CharField(max_length=32, choices=ModerationStatus.choices, default=ModerationStatus.PENDING)
    mime_type = models.CharField(max_length=128, blank=True)
    size_bytes = models.BigIntegerField(default=0)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.asset_type}:{self.title}"
