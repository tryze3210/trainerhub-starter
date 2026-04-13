from django.db import models
from apps.core.models import UUIDModel, TimeStampedModel, SoftDeleteModel
from apps.users.models import User


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
