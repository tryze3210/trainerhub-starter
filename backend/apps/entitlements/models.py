from __future__ import annotations

from django.conf import settings
from django.db import models
from apps.common.db import UUIDModel
from apps.orders.models import Order
from apps.subscriptions.models import Subscription


class EntitlementSourceType(models.TextChoices):
    ORDER = 'order', 'Order'
    SUBSCRIPTION = 'subscription', 'Subscription'
    ADMIN = 'admin', 'Admin'
    ADMIN_GRANT = 'admin_grant', 'Admin grant'


class EntitlementTargetType(models.TextChoices):
    VIDEO = 'video', 'Video'
    COURSE = 'course', 'Course'
    PROGRAM = 'program', 'Program'
    BUNDLE = 'bundle', 'Bundle'
    LIBRARY = 'library', 'Library'


class EntitlementStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    REVOKED = 'revoked', 'Revoked'
    EXPIRED = 'expired', 'Expired'


class EntitlementQuerySet(models.QuerySet):
    @staticmethod
    def _translate_filter_kwargs(kwargs: dict) -> dict:
        translated = dict(kwargs)
        alias_map = {
            'kind': 'target_type',
            'object_id': 'target_id',
            'source': 'source_type',
            'source_reference': 'metadata__source_reference',
        }
        for old_key, new_key in alias_map.items():
            if old_key in translated:
                translated[new_key] = translated.pop(old_key)
        if 'is_active' in translated:
            is_active = translated.pop('is_active')
            if is_active is True:
                translated['status'] = EntitlementStatus.ACTIVE
            elif is_active is False:
                translated['status__in'] = [EntitlementStatus.REVOKED, EntitlementStatus.EXPIRED]
        if 'target_id' in translated and translated['target_id'] is not None:
            translated['target_id'] = str(translated['target_id'])
        return translated

    def filter(self, *args, **kwargs):
        return super().filter(*args, **self._translate_filter_kwargs(kwargs))

    def exclude(self, *args, **kwargs):
        return super().exclude(*args, **self._translate_filter_kwargs(kwargs))

    def get(self, *args, **kwargs):
        return super().get(*args, **self._translate_filter_kwargs(kwargs))


class EntitlementManager(models.Manager.from_queryset(EntitlementQuerySet)):
    @staticmethod
    def _translate_create_kwargs(kwargs: dict) -> dict:
        translated = dict(kwargs)
        if 'kind' in translated:
            translated['target_type'] = translated.pop('kind')
        if 'object_id' in translated:
            translated['target_id'] = translated.pop('object_id')
        if 'source' in translated:
            translated['source_type'] = translated.pop('source')
        source_reference = translated.pop('source_reference', None)
        is_active = translated.pop('is_active', None)
        metadata = dict(translated.get('metadata') or {})
        if source_reference is not None:
            metadata['source_reference'] = str(source_reference)
        translated['metadata'] = metadata
        if is_active is not None:
            translated['status'] = EntitlementStatus.ACTIVE if is_active else EntitlementStatus.REVOKED
        if translated.get('target_id') is not None:
            translated['target_id'] = str(translated['target_id'])
        translated.setdefault('source_type', EntitlementSourceType.ADMIN)
        translated.setdefault('status', EntitlementStatus.ACTIVE)
        return translated

    def create(self, **kwargs):
        return super().create(**self._translate_create_kwargs(kwargs))

    def update_or_create(self, defaults=None, **kwargs):
        return super().update_or_create(
            defaults=defaults,
            **EntitlementQuerySet._translate_filter_kwargs(kwargs),
        )


class Entitlement(UUIDModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='entitlements')
    source_type = models.CharField(max_length=32, choices=EntitlementSourceType.choices)
    source_order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.PROTECT, related_name='granted_entitlements')
    source_subscription = models.ForeignKey(Subscription, null=True, blank=True, on_delete=models.PROTECT, related_name='granted_entitlements')
    target_type = models.CharField(max_length=32, choices=EntitlementTargetType.choices)
    target_id = models.CharField(max_length=64, null=True, blank=True)
    status = models.CharField(max_length=32, choices=EntitlementStatus.choices, default=EntitlementStatus.ACTIVE)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    objects = EntitlementManager()

    # Backward-compatible aliases for older service/tests that used Entitlement.Kind/Source.
    Kind = EntitlementTargetType
    Source = EntitlementSourceType
    Status = EntitlementStatus

    def __init__(self, *args, **kwargs):
        translated = EntitlementManager._translate_create_kwargs(kwargs) if kwargs else kwargs
        super().__init__(*args, **translated)

    @property
    def kind(self):
        return self.target_type

    @kind.setter
    def kind(self, value):
        self.target_type = value

    @property
    def object_id(self):
        return self.target_id

    @object_id.setter
    def object_id(self, value):
        self.target_id = str(value) if value is not None else None

    @property
    def source(self):
        return self.source_type

    @source.setter
    def source(self, value):
        self.source_type = value

    @property
    def source_reference(self):
        metadata_reference = (self.metadata or {}).get('source_reference')
        if metadata_reference:
            return str(metadata_reference)
        if self.source_order_id:
            return str(self.source_order_id)
        if self.source_subscription_id:
            return str(self.source_subscription_id)
        return None

    @source_reference.setter
    def source_reference(self, value):
        metadata = dict(self.metadata or {})
        if value is None:
            metadata.pop('source_reference', None)
        else:
            metadata['source_reference'] = str(value)
        self.metadata = metadata

    @property
    def is_active(self) -> bool:
        return self.status == EntitlementStatus.ACTIVE

    @is_active.setter
    def is_active(self, value: bool):
        self.status = EntitlementStatus.ACTIVE if value else EntitlementStatus.REVOKED
