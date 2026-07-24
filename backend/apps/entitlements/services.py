from __future__ import annotations

import logging
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.audit.services import AuditService
from apps.entitlements.models import Entitlement, EntitlementSourceType, EntitlementStatus
from apps.events.services import DomainEventService


logger = logging.getLogger('apps.entitlements')


class EntitlementService:
    @staticmethod
    def _activation_context(entitlement: Entitlement) -> dict[str, Any]:
        return {
            'entitlement_id': str(entitlement.id),
            'user_id': str(entitlement.user_id),
            'source_type': entitlement.source_type,
            'source_order_id': str(entitlement.source_order_id or ''),
            'source_subscription_id': str(entitlement.source_subscription_id or ''),
            'source_reference': entitlement.source_reference or '',
            'target_type': entitlement.target_type,
            'target_id': str(entitlement.target_id or ''),
            'status': entitlement.status,
            'starts_at': entitlement.starts_at.isoformat() if entitlement.starts_at else None,
            'ends_at': entitlement.ends_at.isoformat() if entitlement.ends_at else None,
            'metadata': entitlement.metadata or {},
        }

    @staticmethod
    def _revocation_context(*, entitlement: Entitlement, previous_status: str, reason: str, revoked_by: str) -> dict[str, Any]:
        return {
            **EntitlementService._activation_context(entitlement),
            'previous_status': previous_status,
            'reason': reason,
            'revoked_by': revoked_by,
            'revoked_at': (entitlement.metadata or {}).get('revoked_at', ''),
        }

    @staticmethod
    def _emit_granted(entitlement: Entitlement) -> None:
        DomainEventService().emit(
            event_type='entitlement.granted',
            aggregate_type='entitlement',
            aggregate_id=str(entitlement.id),
            idempotency_key=f'entitlement:{entitlement.id}:granted',
            payload=EntitlementService._activation_context(entitlement),
        )

    @staticmethod
    def _audit_granted(entitlement: Entitlement) -> None:
        AuditService.log(
            actor=entitlement.user,
            event_type='entitlement.activated',
            entity_type='entitlement',
            entity_id=str(entitlement.id),
            context=EntitlementService._activation_context(entitlement),
        )
        try:
            from apps.notifications.domain.triggers import DomainNotificationTriggers

            DomainNotificationTriggers().on_access_granted(user=entitlement.user, entitlement=entitlement)
        except Exception as exc:
            AuditService.log(
                actor=entitlement.user,
                event_type='side_effect.failed',
                entity_type='entitlement',
                entity_id=str(entitlement.id),
                context={
                    **EntitlementService._activation_context(entitlement),
                    'side_effect': 'notification.access_granted',
                    'error': str(exc),
                },
            )
            logger.exception('entitlement.access_granted_notification_failed entitlement_id=%s', entitlement.id)

    @staticmethod
    def _emit_revoked(*, entitlement: Entitlement, previous_status: str, reason: str, revoked_by: str) -> None:
        revoked_at = (entitlement.metadata or {}).get('revoked_at') or timezone.now().isoformat()
        DomainEventService().emit(
            event_type='entitlement.revoked',
            aggregate_type='entitlement',
            aggregate_id=str(entitlement.id),
            idempotency_key=f'entitlement:{entitlement.id}:revoked:{revoked_at}',
            payload=EntitlementService._revocation_context(
                entitlement=entitlement,
                previous_status=previous_status,
                reason=reason,
                revoked_by=revoked_by,
            ),
        )

    @staticmethod
    def _audit_revoked(*, entitlement: Entitlement, previous_status: str, reason: str, revoked_by: str, request=None) -> None:
        AuditService.log(
            actor=entitlement.user,
            event_type='entitlement.revoked',
            entity_type='entitlement',
            entity_id=str(entitlement.id),
            context=EntitlementService._revocation_context(
                entitlement=entitlement,
                previous_status=previous_status,
                reason=reason,
                revoked_by=revoked_by,
            ),
            request=request,
        )

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
        metadata.setdefault('activated_via', source_type)
        metadata.setdefault('activated_at', timezone.now().isoformat())
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
        existing = Entitlement.objects.select_for_update().filter(**lookup).first()
        previous_status = existing.status if existing else None
        entitlement, created = Entitlement.objects.update_or_create(
            **lookup,
            defaults={
                'status': EntitlementStatus.ACTIVE,
                'starts_at': starts_at,
                'ends_at': ends_at,
                'metadata': metadata,
            },
        )
        EntitlementService._emit_granted(entitlement)
        if created or previous_status != EntitlementStatus.ACTIVE:
            EntitlementService._audit_granted(entitlement)
        return entitlement

    @staticmethod
    @transaction.atomic
    def revoke(*, entitlement: Entitlement, reason: str = '', revoked_by: str = 'system', request=None) -> bool:
        entitlement = Entitlement.objects.select_for_update().get(pk=entitlement.pk)
        if entitlement.status == EntitlementStatus.REVOKED:
            return False

        previous_status = entitlement.status
        metadata = dict(entitlement.metadata or {})
        revoked_at = timezone.now().isoformat()
        metadata.update({
            'revoked_at': revoked_at,
            'revoked_by': revoked_by,
            'revocation_reason': reason,
        })
        entitlement.status = EntitlementStatus.REVOKED
        entitlement.metadata = metadata
        entitlement.save(update_fields=['status', 'metadata', 'updated_at'])

        EntitlementService._emit_revoked(
            entitlement=entitlement,
            previous_status=previous_status,
            reason=reason,
            revoked_by=revoked_by,
        )
        EntitlementService._audit_revoked(
            entitlement=entitlement,
            previous_status=previous_status,
            reason=reason,
            revoked_by=revoked_by,
            request=request,
        )
        return True

    @staticmethod
    @transaction.atomic
    def revoke_by_source(
        *,
        source_type: str | None = None,
        source_order=None,
        source_subscription=None,
        source: str | None = None,
        source_reference: str | None = None,
        reason: str = '',
        revoked_by: str = 'system',
        request=None,
    ):
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
        entitlement_ids = list(queryset.values_list('id', flat=True)[:500])
        updated = 0
        for entitlement in Entitlement.objects.filter(id__in=entitlement_ids).order_by('created_at'):
            if EntitlementService.revoke(
                entitlement=entitlement,
                reason=reason,
                revoked_by=revoked_by,
                request=request,
            ):
                updated += 1
        if updated:
            DomainEventService().emit(
                event_type='entitlement.revoked_by_source',
                aggregate_type='entitlement_batch',
                aggregate_id=str(source_order.id if source_order is not None else source_subscription.id if source_subscription is not None else source_reference or source_type or 'unknown'),
                idempotency_key='entitlement:revoked_by_source:' + ':'.join([
                    str(source_type or ''),
                    str(getattr(source_order, 'id', '') or ''),
                    str(getattr(source_subscription, 'id', '') or ''),
                    str(source_reference or ''),
                ]),
                payload={
                    'source_type': source_type,
                    'source_order_id': str(getattr(source_order, 'id', '') or ''),
                    'source_subscription_id': str(getattr(source_subscription, 'id', '') or ''),
                    'source_reference': source_reference,
                    'updated_count': updated,
                    'entitlement_ids': [str(value) for value in entitlement_ids],
                    'reason': reason,
                    'revoked_by': revoked_by,
                },
            )
        return updated

    @staticmethod
    @transaction.atomic
    def expire_due_entitlements(*, now=None) -> int:
        now = now or timezone.now()
        queryset = Entitlement.objects.filter(status=EntitlementStatus.ACTIVE, ends_at__lt=now)
        entitlement_ids = list(queryset.values_list('id', flat=True)[:500])
        updated = queryset.update(status=EntitlementStatus.EXPIRED, updated_at=now)
        if updated:
            DomainEventService().emit(
                event_type='entitlement.expired_due',
                aggregate_type='entitlement_batch',
                aggregate_id=now.date().isoformat(),
                idempotency_key=f'entitlement:expired_due:{now.date().isoformat()}',
                payload={
                    'expired_at': now.isoformat(),
                    'updated_count': updated,
                    'entitlement_ids': [str(value) for value in entitlement_ids],
                },
            )
        return updated
