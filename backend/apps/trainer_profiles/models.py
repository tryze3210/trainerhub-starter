from __future__ import annotations

from uuid import uuid4
from django.conf import settings
from django.db import models
from django.utils.text import slugify
from apps.common.models import TimeStampedModel


class TrainerPublicProfile(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trainer_public_profile')
    trainer_uuid = models.UUIDField(default=uuid4, unique=True, editable=False)
    slug = models.SlugField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)
    headline = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    avatar_url = models.URLField(blank=True)
    specialties = models.JSONField(default=list)
    languages = models.JSONField(default=list)
    is_public = models.BooleanField(default=True)

    class Meta:
        db_table = 'trainer_public_profile'

    def save(self, *args, **kwargs):
        if not self.slug:
            email_prefix = self.user.email.split('@')[0] if getattr(self.user, 'email', '') else 'trainer'
            full_name = (self.display_name or getattr(getattr(self.user, 'account_profile', None), 'display_name', '') or getattr(getattr(self.user, 'account_profile', None), 'full_name', '') or self.user.get_full_name() or email_prefix)
            base = slugify(full_name) or 'trainer'
            self.slug = base
        super().save(*args, **kwargs)
