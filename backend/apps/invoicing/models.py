from django.conf import settings
from django.db import models
from apps.common.db.models import TimeStampedModel


class Invoice(TimeStampedModel):
    class Type(models.TextChoices):
        INVOICE = 'invoice', 'Invoice'
        RECEIPT = 'receipt', 'Receipt'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='invoices')
    order_id = models.CharField(max_length=64)
    payment_id = models.CharField(max_length=64, blank=True)
    document_type = models.CharField(max_length=16, choices=Type.choices)
    document_number = models.CharField(max_length=64, unique=True)
    currency = models.CharField(max_length=8)
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'invoicing_invoice'
        indexes = [models.Index(fields=['user', 'document_type']), models.Index(fields=['order_id'])]
