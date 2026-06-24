from __future__ import annotations

from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils.text import slugify
from apps.common.db import UUIDModel
from apps.orders.models import Order


class SubscriptionPlan(UUIDModel):
    class BillingPeriod(models.TextChoices):
        MONTH = 'month', 'Month'
        YEAR = 'year', 'Year'

    code = models.CharField(max_length=64, unique=True, blank=True)
    trainer_id = models.CharField(max_length=64, blank=True, db_index=True)
    title = models.CharField(max_length=255)
    billing_period = models.CharField(max_length=16, choices=BillingPeriod.choices, default=BillingPeriod.MONTH)
    period_days = models.PositiveIntegerField(default=30)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default='RUB')
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.billing_period == self.BillingPeriod.YEAR and (not self.period_days or self.period_days == 30):
            self.period_days = 365
        elif self.billing_period == self.BillingPeriod.MONTH and not self.period_days:
            self.period_days = 30
        if not self.code:
            title_slug = slugify(self.title or 'plan')[:32] or 'plan'
            self.code = f'{title_slug}-{str(uuid4())[:8]}'
        super().save(*args, **kwargs)


class SubscriptionStatus(models.TextChoices):
    TRIAL = 'trial', 'Trial'
    PENDING = 'pending', 'Pending'
    ACTIVE = 'active', 'Active'
    PAST_DUE = 'past_due', 'Past due'
    CANCELLED = 'cancelled', 'Cancelled'
    EXPIRED = 'expired', 'Expired'


class Subscription(UUIDModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name='subscriptions')
    source_order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.PROTECT, related_name='created_subscriptions')
    status = models.CharField(max_length=32, choices=SubscriptionStatus.choices, default=SubscriptionStatus.PENDING)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=False)
