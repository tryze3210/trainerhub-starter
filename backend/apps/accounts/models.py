from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class AccountProfile(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='account_profile')
    full_name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    country = models.CharField(max_length=2, blank=True)
    city = models.CharField(max_length=255, blank=True)
    timezone = models.CharField(max_length=64, default='Europe/Berlin')
    preferred_language = models.CharField(max_length=16, default='en')

    class Meta:
        db_table = 'accounts_profile'


class AccountSettings(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='account_settings')
    marketing_emails_enabled = models.BooleanField(default=True)
    product_updates_enabled = models.BooleanField(default=True)
    push_notifications_enabled = models.BooleanField(default=True)
    favorite_categories = models.JSONField(default=list)

    class Meta:
        db_table = 'accounts_settings'


class AccountRoleAssignment(TimeStampedModel):
    ROLE_USER = 'user'
    ROLE_TRAINER = 'trainer'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = (
        (ROLE_USER, 'User'),
        (ROLE_TRAINER, 'Trainer'),
        (ROLE_ADMIN, 'Admin'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='role_assignments')
    role = models.CharField(max_length=32, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=False)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='granted_role_assignments',
    )

    class Meta:
        db_table = 'accounts_role_assignment'
        constraints = [
            models.UniqueConstraint(fields=['user', 'role'], name='uq_accounts_role_assignment_user_role'),
        ]

    def __str__(self) -> str:
        return f'{self.user_id}:{self.role}'
