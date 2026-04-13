from django.db import models
from apps.common.models import TimeStampedModel
from apps.trainer_profiles.models import TrainerPublicProfile


class Visibility(models.TextChoices):
    PUBLIC = 'public', 'Public'
    UNLISTED = 'unlisted', 'Unlisted'
    PRIVATE = 'private', 'Private'


class Difficulty(models.TextChoices):
    BEGINNER = 'beginner', 'Beginner'
    INTERMEDIATE = 'intermediate', 'Intermediate'
    ADVANCED = 'advanced', 'Advanced'


class PublishedVideo(TimeStampedModel):
    trainer_profile = models.ForeignKey(TrainerPublicProfile, on_delete=models.CASCADE, related_name='videos')
    source_draft_id = models.UUIDField(unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=64, default='fitness')
    difficulty = models.CharField(max_length=32, choices=Difficulty.choices, default=Difficulty.BEGINNER)
    visibility = models.CharField(max_length=32, choices=Visibility.choices, default=Visibility.PUBLIC)
    cover_asset_id = models.UUIDField(null=True, blank=True)
    video_asset_id = models.UUIDField(null=True, blank=True)
    price_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='EUR')
    duration_minutes = models.PositiveIntegerField(default=0)
    version_number = models.PositiveIntegerField(default=1)
    published_at = models.DateTimeField(auto_now_add=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'content_published_video'
        ordering = ['-published_at', '-created_at']


class PublishedProgram(TimeStampedModel):
    trainer_profile = models.ForeignKey(TrainerPublicProfile, on_delete=models.CASCADE, related_name='programs')
    source_draft_id = models.UUIDField(unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=64, default='fitness')
    difficulty = models.CharField(max_length=32, choices=Difficulty.choices, default=Difficulty.BEGINNER)
    visibility = models.CharField(max_length=32, choices=Visibility.choices, default=Visibility.PUBLIC)
    price_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='EUR')
    duration_minutes = models.PositiveIntegerField(default=0)
    version_number = models.PositiveIntegerField(default=1)
    published_at = models.DateTimeField(auto_now_add=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'content_published_program'
        ordering = ['-published_at', '-created_at']


class PublishedLesson(TimeStampedModel):
    program = models.ForeignKey(PublishedProgram, on_delete=models.CASCADE, related_name='lessons')
    source_draft_id = models.UUIDField(unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    position = models.PositiveIntegerField(default=1)
    video_asset_id = models.UUIDField(null=True, blank=True)
    is_preview = models.BooleanField(default=False)
    duration_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'content_published_lesson'
        ordering = ['position', 'created_at']


class PublishedBundle(TimeStampedModel):
    trainer_profile = models.ForeignKey(TrainerPublicProfile, on_delete=models.CASCADE, related_name='bundles')
    source_draft_id = models.UUIDField(unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=64, default='fitness')
    difficulty = models.CharField(max_length=32, choices=Difficulty.choices, default=Difficulty.BEGINNER)
    visibility = models.CharField(max_length=32, choices=Visibility.choices, default=Visibility.PUBLIC)
    price_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='EUR')
    duration_minutes = models.PositiveIntegerField(default=0)
    version_number = models.PositiveIntegerField(default=1)
    published_at = models.DateTimeField(auto_now_add=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'content_published_bundle'
        ordering = ['-published_at', '-created_at']


class PublishedBundleItem(TimeStampedModel):
    class ItemType(models.TextChoices):
        VIDEO = 'video', 'Video'
        PROGRAM = 'program', 'Program'

    bundle = models.ForeignKey(PublishedBundle, on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(max_length=32, choices=ItemType.choices)
    target_slug = models.SlugField(max_length=255)
    position = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'content_published_bundle_item'
        ordering = ['position', 'created_at']
