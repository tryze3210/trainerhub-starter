from django.db import models
from apps.core.models import UUIDModel, TimeStampedModel
from apps.users.models import User

class CustomerProfile(UUIDModel, TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="customer_profile")
    display_name = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    streak_count = models.PositiveIntegerField(default=0)
