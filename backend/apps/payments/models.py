from django.db import models
from django.utils import timezone

from apps.common.db import UUIDModel
from apps.orders.models import Order


class PaymentStatus(models.TextChoices):
    CREATED = 'created', 'Created'
    PENDING = 'pending', 'Pending'
    SUCCEEDED = 'succeeded', 'Succeeded'
    FAILED = 'failed', 'Failed'
    CANCELLED = 'cancelled', 'Cancelled'
    REFUNDED = 'refunded', 'Refunded'
    DISPUTED = 'disputed', 'Disputed'
    CHARGED_BACK = 'charged_back', 'Charged back'


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
    class Status(models.TextChoices):
        RECEIVED = 'received', 'Received'
        PROCESSING = 'processing', 'Processing'
        PROCESSED = 'processed', 'Processed'
        DUPLICATE = 'duplicate', 'Duplicate'
        IGNORED = 'ignored', 'Ignored'
        FAILED = 'failed', 'Failed'
        REJECTED = 'rejected', 'Rejected'

    provider = models.CharField(max_length=64, db_index=True)
    event_type = models.CharField(max_length=96, db_index=True)
    external_event_id = models.CharField(max_length=160, db_index=True)
    provider_event_id = models.CharField(max_length=240, unique=True, null=True, blank=True)
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        related_name='webhook_events',
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.RECEIVED, db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    headers = models.JSONField(default=dict, blank=True)
    signature = models.CharField(max_length=512, blank=True)
    raw_payload_hash = models.CharField(max_length=128, blank=True, db_index=True)
    error_message = models.TextField(blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    received_at = models.DateTimeField(default=timezone.now, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['provider', 'status'], name='pay_wh_provider_status_idx'),
            models.Index(fields=['event_type', 'received_at'], name='pay_wh_type_recv_idx'),
            models.Index(fields=['payment', 'status'], name='pay_wh_payment_status_idx'),
        ]

    def __str__(self) -> str:
        return f'{self.provider}:{self.event_type}:{self.external_event_id}:{self.status}'
