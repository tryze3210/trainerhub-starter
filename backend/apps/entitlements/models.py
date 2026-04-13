from django.conf import settings
from django.db import models
from apps.common.db import UUIDModel
from apps.orders.models import Order
from apps.subscriptions.models import Subscription


class EntitlementSourceType(models.TextChoices):
    ORDER = 'order', 'Order'
    SUBSCRIPTION = 'subscription', 'Subscription'
    ADMIN = 'admin', 'Admin'


class EntitlementTargetType(models.TextChoices):
    VIDEO = 'video', 'Video'
    PROGRAM = 'program', 'Program'
    BUNDLE = 'bundle', 'Bundle'
    LIBRARY = 'library', 'Library'


class EntitlementStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    REVOKED = 'revoked', 'Revoked'
    EXPIRED = 'expired', 'Expired'


class Entitlement(UUIDModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='entitlements')
    source_type = models.CharField(max_length=32, choices=EntitlementSourceType.choices)
    source_order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.PROTECT, related_name='granted_entitlements')
    source_subscription = models.ForeignKey(Subscription, null=True, blank=True, on_delete=models.PROTECT, related_name='granted_entitlements')
    target_type = models.CharField(max_length=32, choices=EntitlementTargetType.choices)
    target_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=EntitlementStatus.choices, default=EntitlementStatus.ACTIVE)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
