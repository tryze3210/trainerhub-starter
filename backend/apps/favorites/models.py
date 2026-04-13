from django.conf import settings
from django.db import models
from apps.common.db.models import TimeStampedModel

class Favorite(TimeStampedModel):
    class TargetType(models.TextChoices):
        TRAINER = 'trainer', 'Trainer'
        VIDEO = 'video', 'Video'
        PROGRAM = 'program', 'Program'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    target_type = models.CharField(max_length=32, choices=TargetType.choices)
    target_id = models.CharField(max_length=64)

    class Meta:
        db_table = 'favorites_favorite'
        constraints = [
            models.UniqueConstraint(fields=['user', 'target_type', 'target_id'], name='uniq_user_favorite')
        ]
        indexes = [models.Index(fields=['user', 'target_type'])]
