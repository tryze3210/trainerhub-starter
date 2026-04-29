from django.conf import settings
from django.db import models
from apps.core.models import UUIDModel, TimeStampedModel, SoftDeleteModel
from apps.users.models import User


class TrainerApplication(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SUBMITTED = 'submitted', 'Submitted'
        UNDER_REVIEW = 'under_review', 'Under review'
        APPROVED = 'approved', 'Approved'
        CHANGES_REQUESTED = 'changes_requested', 'Changes requested'
        REJECTED = 'rejected', 'Rejected'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trainer_application')
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.DRAFT)
    legal_name = models.CharField(max_length=255, blank=True)
    brand_name = models.CharField(max_length=255, blank=True)
    contact_phone = models.CharField(max_length=32, blank=True)
    country = models.CharField(max_length=2, blank=True)
    city = models.CharField(max_length=255, blank=True)
    specialties = models.JSONField(default=list, blank=True)
    links = models.JSONField(default=list, blank=True)
    bio = models.TextField(blank=True)
    experience_years = models.PositiveSmallIntegerField(default=0)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer_note = models.TextField(blank=True)
    latest_moderation_case_id = models.UUIDField(null=True, blank=True)
    moderation_snapshot = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'trainers_application'


class TrainerProfile(UUIDModel, TimeStampedModel, SoftDeleteModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="trainer_profile")
    slug = models.SlugField(max_length=160, unique=True)
    display_name = models.CharField(max_length=255)
    headline = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    rating_avg = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    views_count = models.BigIntegerField(default=0)
    sales_count = models.BigIntegerField(default=0)
    is_public = models.BooleanField(default=True)
    status = models.CharField(max_length=32, default="pending")

    def __str__(self):
        return self.display_name
