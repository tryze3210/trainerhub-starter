from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class OnboardingStepState(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='onboarding_steps')
    step_code = models.CharField(max_length=64)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    payload = models.JSONField(default=dict)

    class Meta:
        db_table = 'onboarding_step_state'
        constraints = [
            models.UniqueConstraint(fields=['user', 'step_code'], name='uq_onboarding_user_step_code'),
        ]
