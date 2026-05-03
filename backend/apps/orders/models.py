from django.conf import settings
from django.db import models
from apps.common.db import UUIDModel


class OrderStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    AWAITING_PAYMENT = 'awaiting_payment', 'Awaiting payment'
    PAID = 'paid', 'Paid'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'
    FAILED = 'failed', 'Failed'
    REFUNDED = 'refunded', 'Refunded'
    DISPUTED = 'disputed', 'Disputed'
    CHARGED_BACK = 'charged_back', 'Charged back'


class OrderType(models.TextChoices):
    ONE_TIME = 'one_time', 'One-time'
    SUBSCRIPTION = 'subscription', 'Subscription'


class PurchasedItemType(models.TextChoices):
    VIDEO = 'video', 'Video'
    PROGRAM = 'program', 'Program'
    BUNDLE = 'bundle', 'Bundle'
    SUBSCRIPTION_PLAN = 'subscription_plan', 'Subscription plan'


class Order(UUIDModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='orders')
    order_type = models.CharField(max_length=32, choices=OrderType.choices)
    status = models.CharField(max_length=32, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    currency = models.CharField(max_length=8, default='RUB')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    external_checkout_id = models.CharField(max_length=128, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Legacy aliases kept for older tests/services.
    Status = OrderStatus
    Type = OrderType
    ItemType = PurchasedItemType


class OrderItem(UUIDModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(max_length=32, choices=PurchasedItemType.choices)
    # Public content can be addressed by UUID/source_draft_id, slug, integer legacy id,
    # or synthetic fixture ids. Store polymorphic ids as text.
    item_id = models.CharField(max_length=64)
    title_snapshot = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    metadata = models.JSONField(default=dict, blank=True)
