from __future__ import annotations

from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.entitlements.models import Entitlement, EntitlementSourceType, EntitlementStatus


class EntitlementService:
    @staticmethod
    @transaction.atomic
    def grant(
        *,
        user,
        target_type: str | None = None,
        target_id=None,
        source_type: str | None = None,
        source_order=None,
        source_subscription=None,
        starts_at=None,
        ends_at=None,
        metadata: dict[str, Any] | None = None,
        # legacy aliases kept for older internal calls/contracts
        kind: str | None = None,
        object_id=None,
        source: str | None = None,
        source_reference: str | None = None,
    ) -> Entitlement:
        target_type = target_type or kind
        target_id = target_id or object_id
        source_type = source_type or source or EntitlementSourceType.ADMIN
        starts_at = starts_at or timezone.now()
        metadata = dict(metadata or {})
        if source_reference is None and source_order is not None:
            source_reference = str(source_order.id)
        if source_reference is None and source_subscription is not None:
            source_reference = str(source_subscription.id)
        if source_reference:
            metadata['source_reference'] = str(source_reference)
        if not target_type:
            raise ValueError('target_type is required')
        if target_id is not None:
            target_id = str(target_id)

        lookup = {
            'user': user,
            'source_type': source_type,
            'source_order': source_order,
            'source_subscription': source_subscription,
            'target_type': target_type,
            'target_id': target_id,
        }
        entitlement, _ = Entitlement.objects.update_or_create(
            **lookup,
            defaults={
                'status': EntitlementStatus.ACTIVE,
                'starts_at': starts_at,
                'ends_at': ends_at,
                'metadata': metadata,
            },
        )
        return entitlement

    @staticmethod
    @transaction.atomic
    def revoke_by_source(*, source_type: str | None = None, source_order=None, source_subscription=None, source: str | None = None, source_reference: str | None = None):
        source_type = source_type or source
        queryset = Entitlement.objects.filter(status=EntitlementStatus.ACTIVE)
        if source_type:
            queryset = queryset.filter(source_type=source_type)
        if source_order is not None:
            queryset = queryset.filter(source_order=source_order)
        if source_subscription is not None:
            queryset = queryset.filter(source_subscription=source_subscription)
        if source_reference:
            queryset = queryset.filter(metadata__source_reference=source_reference)
        return queryset.update(status=EntitlementStatus.REVOKED, updated_at=timezone.now())

    @staticmethod
    @transaction.atomic
    def expire_due_entitlements(*, now=None) -> int:
        now = now or timezone.now()
        return Entitlement.objects.filter(status=EntitlementStatus.ACTIVE, ends_at__lt=now).update(status=EntitlementStatus.EXPIRED, updated_at=now)
