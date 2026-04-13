from django.db import models
from apps.core.models import UUIDModel, TimeStampedModel
from apps.customers.models import CustomerProfile

class Challenge(UUIDModel, TimeStampedModel):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    challenge_type = models.CharField(max_length=32)
    status = models.CharField(max_length=32, default="draft")
    rules_json = models.JSONField(default=dict)

class UserChallengeProgress(UUIDModel, TimeStampedModel):
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name="progress_items")
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name="challenge_progress")
    status = models.CharField(max_length=32, default="active")
    progress_value = models.IntegerField(default=0)
    target_value = models.IntegerField(default=0)
