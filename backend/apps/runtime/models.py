from django.db import models


class RuntimeProbeLog(models.Model):
    probe = models.CharField(max_length=64)
    status = models.CharField(max_length=32)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
