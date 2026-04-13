import uuid
from django.db import models
from apps.common.models import TimeStampedModel


class PublishStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    REVIEW = "review", "In review"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


class TrainerVideoDraft(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trainer_id = models.UUIDField(db_index=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True)
    cover_asset_id = models.UUIDField(null=True, blank=True)
    video_asset_id = models.UUIDField(null=True, blank=True)
    price_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="RUB")
    status = models.CharField(max_length=32, choices=PublishStatus.choices, default=PublishStatus.DRAFT)
    current_version_number = models.PositiveIntegerField(default=0)


class TrainerProgramDraft(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trainer_id = models.UUIDField(db_index=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True)
    price_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="RUB")
    status = models.CharField(max_length=32, choices=PublishStatus.choices, default=PublishStatus.DRAFT)
    current_version_number = models.PositiveIntegerField(default=0)


class ProgramLessonDraft(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    program_draft = models.ForeignKey(TrainerProgramDraft, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    position = models.PositiveIntegerField()
    video_asset_id = models.UUIDField(null=True, blank=True)
    is_preview = models.BooleanField(default=False)


class TrainerBundleDraft(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trainer_id = models.UUIDField(db_index=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True)
    price_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="RUB")
    status = models.CharField(max_length=32, choices=PublishStatus.choices, default=PublishStatus.DRAFT)


class BundleItemDraft(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class ItemType(models.TextChoices):
        VIDEO = "video", "Video"
        PROGRAM = "program", "Program"

    bundle_draft = models.ForeignKey(TrainerBundleDraft, on_delete=models.CASCADE, related_name="items")
    item_type = models.CharField(max_length=32, choices=ItemType.choices)
    target_id = models.UUIDField()
    position = models.PositiveIntegerField()


class ContentVersion(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class EntityType(models.TextChoices):
        VIDEO = "video", "Video"
        PROGRAM = "program", "Program"
        BUNDLE = "bundle", "Bundle"

    trainer_id = models.UUIDField(db_index=True)
    entity_type = models.CharField(max_length=32, choices=EntityType.choices)
    entity_id = models.UUIDField(db_index=True)
    version_number = models.PositiveIntegerField()
    snapshot = models.JSONField()
    published_by_id = models.UUIDField()
