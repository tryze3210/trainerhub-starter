from django.conf import settings
from django.db import models
from apps.common.db import UUIDModel
from apps.orders.models import Order


class SubscriptionPlan(UUIDModel):
    code = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=255)
    period_days = models.PositiveIntegerField(default=30)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default='RUB')
    is_active = models.BooleanField(default=True)


class SubscriptionStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    ACTIVE = 'active', 'Active'
    PAST_DUE = 'past_due', 'Past due'
    CANCELLED = 'cancelled', 'Cancelled'
    EXPIRED = 'expired', 'Expired'


class Subscription(UUIDModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name='subscriptions')
    source_order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='created_subscriptions')
    status = models.CharField(max_length=32, choices=SubscriptionStatus.choices, default=SubscriptionStatus.PENDING)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=False)
