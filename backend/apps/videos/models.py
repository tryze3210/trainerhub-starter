from django.db import models
from apps.core.models import UUIDModel, TimeStampedModel, SoftDeleteModel
from apps.users.models import User
from apps.trainers.models import TrainerProfile


class MediaAsset(UUIDModel, TimeStampedModel, SoftDeleteModel):
    class Visibility(models.TextChoices):
        PRIVATE = "private", "Private"
        PUBLIC = "public", "Public"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        UPLOADED = "uploaded", "Uploaded"
        VERIFIED = "verified", "Verified"
        FAILED = "failed", "Failed"
        DELETED = "deleted", "Deleted"

    owner_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="media_assets")
    bucket_name = models.CharField(max_length=128)
    object_key = models.CharField(max_length=512, unique=True)
    asset_type = models.CharField(max_length=32)
    visibility = models.CharField(max_length=16, choices=Visibility.choices)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.DRAFT)
    content_type = models.CharField(max_length=128)
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    original_filename = models.CharField(max_length=255, blank=True)
    checksum_sha256 = models.CharField(max_length=64, blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.object_key


class Video(UUIDModel, TimeStampedModel, SoftDeleteModel):
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name="videos")
    media_asset = models.OneToOneField(MediaAsset, on_delete=models.PROTECT, related_name="video")
    slug = models.SlugField(max_length=160, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    is_free = models.BooleanField(default=False)
    status = models.CharField(max_length=32, default="draft")

    def __str__(self):
        return self.title


class VideoAccessLog(UUIDModel, TimeStampedModel):
    class Decision(models.TextChoices):
        GRANTED = "granted", "Granted"
        DENIED = "denied", "Denied"

    class AccessReason(models.TextChoices):
        ADMIN = "admin", "Admin"
        TRAINER_OWNER = "trainer_owner", "Trainer owner"
        FREE_VIDEO = "free_video", "Free video"
        ENTITLEMENT = "entitlement", "Entitlement"
        DENIED = "denied", "Denied"

    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="video_access_logs")
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="access_logs")
    media_asset = models.ForeignKey(MediaAsset, on_delete=models.PROTECT, related_name="access_logs")
    decision = models.CharField(max_length=32, choices=Decision.choices)
    reason = models.CharField(max_length=64, choices=AccessReason.choices)
    access_token_hash = models.CharField(max_length=64, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referer = models.TextField(blank=True)
    origin = models.TextField(blank=True)
    anti_leech = models.JSONField(default=dict, blank=True)
    entitlement_decision = models.JSONField(default=dict, blank=True)
