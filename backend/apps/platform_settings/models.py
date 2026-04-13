from django.db import models
from apps.core.models import UUIDModel, TimeStampedModel

class PlatformSettings(UUIDModel, TimeStampedModel):
    default_currency = models.CharField(max_length=8, default="RUB")
    global_commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=20)
    media_presigned_read_ttl_seconds = models.IntegerField(default=300)
    media_upload_ttl_seconds = models.IntegerField(default=900)
    homepage_config = models.JSONField(default=dict, blank=True)
