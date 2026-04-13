from django.db import models
from apps.common.db import UUIDModel
from apps.orders.models import Order


class PaymentStatus(models.TextChoices):
    CREATED = 'created', 'Created'
    PENDING = 'pending', 'Pending'
    SUCCEEDED = 'succeeded', 'Succeeded'
    FAILED = 'failed', 'Failed'
    CANCELLED = 'cancelled', 'Cancelled'
    REFUNDED = 'refunded', 'Refunded'


class PaymentProvider(models.TextChoices):
    MOCK = 'mock', 'Mock'
    CLOUDPAYMENTS = 'cloudpayments', 'CloudPayments'
    YOOKASSA = 'yookassa', 'YooKassa'


class Payment(UUIDModel):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='payments')
    provider = models.CharField(max_length=64, choices=PaymentProvider.choices, default=PaymentProvider.MOCK)
    status = models.CharField(max_length=32, choices=PaymentStatus.choices, default=PaymentStatus.CREATED)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default='RUB')
    external_payment_id = models.CharField(max_length=128, blank=True)
    external_checkout_url = models.URLField(blank=True)
    provider_payload = models.JSONField(default=dict, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)


class PaymentWebhookEvent(UUIDModel):
    provider = models.CharField(max_length=64)
    event_type = models.CharField(max_length=64)
    external_event_id = models.CharField(max_length=128, unique=True)
    payload = models.JSONField(default=dict, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
