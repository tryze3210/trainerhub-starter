from decimal import Decimal
from django.conf import settings
from django.db import models
from apps.common.db.models import TimeStampedModel


class CheckoutSession(TimeStampedModel):
    class Status(models.TextChoices):
        CREATED = 'created', 'Created'
        PENDING_PROVIDER = 'pending_provider', 'Pending provider'
        REQUIRES_ACTION = 'requires_action', 'Requires action'
        PAID = 'paid', 'Paid'
        EXPIRED = 'expired', 'Expired'
        FAILED = 'failed', 'Failed'

    class CheckoutType(models.TextChoices):
        SUBSCRIPTION = 'subscription', 'Subscription'
        PURCHASE = 'purchase', 'Purchase'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='checkout_sessions')
    checkout_type = models.CharField(max_length=32, choices=CheckoutType.choices)
    target_id = models.CharField(max_length=64)
    order_id = models.CharField(max_length=64, blank=True)
    currency = models.CharField(max_length=8, default='RUB')
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.CREATED)
    provider = models.CharField(max_length=32, default='demo')
    provider_session_id = models.CharField(max_length=128, blank=True)
    success_url = models.URLField(blank=True)
    cancel_url = models.URLField(blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'billing_checkout_session'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['provider', 'provider_session_id']),
            models.Index(fields=['checkout_type', 'target_id']),
            models.Index(fields=['order_id']),
        ]
