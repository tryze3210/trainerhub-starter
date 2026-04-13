from django.conf import settings
from django.db import models
from apps.common.db.models import TimeStampedModel


class AuditEvent(TimeStampedModel):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    event_type = models.CharField(max_length=64)
    entity_type = models.CharField(max_length=64)
    entity_id = models.CharField(max_length=64)
    context = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = 'audit_event'
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['entity_type', 'entity_id']),
        ]
