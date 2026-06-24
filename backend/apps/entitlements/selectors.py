from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from django.db.models import Q
from django.utils import timezone

from apps.entitlements.models import Entitlement, EntitlementStatus, EntitlementTargetType


def _iso(value: Any) -> str | None:
    return value.isoformat() if value else None


def _money(value: Any) -> str:
    if value is None:
        value = Decimal('0.00')
    if not isinstance(value, Decimal):
        try:
            value = Decimal(str(value))
        except Exception:
            value = Decimal('0.00')
    return f"{value.quantize(Decimal('0.01'))}"


def _uuid_or_none(value: Any) -> UUID | None:
    try:
        return UUID(str(value))
    except Exception:
        return None


def _is_intish(value: Any) -> bool:
    return str(value).isdigit()


def _target_id_candidates(*values: Any) -> list[str]:
    candidates: list[str] = []
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text and text not in candidates:
            candidates.append(text)
    return candidates


def _active_filter(now=None) -> Q:
    now = now or timezone.now()
    return (
        Q(status=EntitlementStatus.ACTIVE)
        & (Q(starts_at__isnull=True) | Q(starts_at__lte=now))
        & (Q(ends_at__isnull=True) | Q(ends_at__gte=now))
    )


def _resolve_content(target_type: str, target_id: Any) -> dict[str, Any]:
    if not target_id:
        return {}
    try:
        from apps.content.models import PublishedBundle, PublishedProgram, PublishedVideo
    except Exception:
        return {}

    model_map = {
        EntitlementTargetType.VIDEO: PublishedVideo,
        EntitlementTargetType.PROGRAM: PublishedProgram,
        EntitlementTargetType.BUNDLE: PublishedBundle,
        'video': PublishedVideo,
        'program': PublishedProgram,
        'bundle': PublishedBundle,
    }
    model = model_map.get(str(target_type))
    if not model:
        return {}

    lookup = Q(slug=str(target_id))
    uuid_value = _uuid_or_none(target_id)
    if uuid_value:
        lookup = lookup | Q(source_draft_id=uuid_value)
    if _is_intish(target_id):
        lookup = lookup | Q(id=int(str(target_id)))

    obj = model.objects.select_related('trainer_profile').filter(lookup).first()
    if not obj:
        return {}

    trainer_profile = getattr(obj, 'trainer_profile', None)
    return {
        'id': str(obj.id),
        'source_draft_id': str(obj.source_draft_id),
        'slug': obj.slug,
        'title': obj.title,
        'description': obj.description,
        'target_type': str(target_type),
        'trainer_id': str(getattr(trainer_profile, 'user_id', '') or ''),
        'trainer_slug': getattr(trainer_profile, 'slug', ''),
        'trainer_name': getattr(trainer_profile, 'display_name', ''),
        'category': getattr(obj, 'category', ''),
        'difficulty': getattr(obj, 'difficulty', ''),
        'duration_minutes': getattr(obj, 'duration_minutes', 0),
        'price_amount': _money(getattr(obj, 'price_amount', Decimal('0.00'))),
        'currency': getattr(obj, 'currency', 'RUB'),
    }


def resolve_access_target(*, target_type: str, target_id: Any) -> dict[str, Any]:
    content = _resolve_content(target_type, target_id)
    if content.get('source_draft_id'):
        return {
            'target_type': str(target_type),
            'target_id': str(content['source_draft_id']),
            'content': content,
        }
    uuid_value = _uuid_or_none(target_id)
    return {
        'target_type': str(target_type),
        'target_id': str(uuid_value) if uuid_value else str(target_id or ''),
        'content': {},
    }


def get_user_active_entitlements(*, user):
    now = timezone.now()
    return Entitlement.objects.filter(user=user).filter(_active_filter(now)).order_by('-created_at')


def has_active_entitlement(*, user, target_type: str, target_id: Any) -> bool:
    from apps.entitlements.access_audit import AccessControlAuditService

    decision = AccessControlAuditService.check(
        user=user,
        target_type=target_type,
        target_id=target_id,
        include_admin_override=False,
    )
    return bool(decision.get('allowed'))


class EntitlementAccessCenterSelector:
    """Buyer-facing read model for commercial access.

    This selector is intentionally schema-neutral: it uses the existing Entitlement
    model and resolves public content lazily by source_draft_id, integer public id
    or slug. That keeps checkout, library and content pages compatible while the
    product catalog evolves.
    """

    def build(self, *, user, days: int = 30) -> dict[str, Any]:
        days = max(1, min(int(days or 30), 365))
        now = timezone.now()
        expiring_before = now + timedelta(days=7)
        queryset = (
            Entitlement.objects.filter(user=user)
            .select_related('source_order', 'source_subscription')
            .order_by('-created_at')
        )
        active_query = queryset.filter(_active_filter(now))
        expiring_query = active_query.filter(ends_at__isnull=False, ends_at__lte=expiring_before)
        items = [self._item(entitlement=entitlement, now=now) for entitlement in queryset[:100]]

        by_type: dict[str, int] = {}
        for item in items:
            by_type[item['target_type']] = by_type.get(item['target_type'], 0) + 1

        return {
            'summary': {
                'period_days': days,
                'total_count': queryset.count(),
                'active_count': active_query.count(),
                'expired_count': queryset.filter(status=EntitlementStatus.EXPIRED).count(),
                'revoked_count': queryset.filter(status=EntitlementStatus.REVOKED).count(),
                'expiring_soon_count': expiring_query.count(),
                'library_access_active': active_query.filter(target_type=EntitlementTargetType.LIBRARY).exists(),
                'by_type': by_type,
            },
            'items': items,
            'readiness': self._readiness(items=items, active_count=active_query.count()),
        }

    def check(self, *, user, target_type: str, target_id: Any) -> dict[str, Any]:
        from apps.entitlements.access_audit import AccessControlAuditService

        return AccessControlAuditService.check(
            user=user,
            target_type=target_type,
            target_id=target_id,
            include_admin_override=False,
        )

    def legacy_check(self, *, user, target_type: str, target_id: Any) -> dict[str, Any]:
        resolved = resolve_access_target(target_type=target_type, target_id=target_id)
        allowed = has_active_entitlement(user=user, target_type=target_type, target_id=target_id)
        entitlement = None
        target_ids = _target_id_candidates(resolved.get('target_id'), target_id)
        if target_ids:
            entitlement = (
                Entitlement.objects.filter(user=user, target_type=target_type, target_id__in=target_ids)
                .filter(_active_filter(timezone.now()))
                .order_by('-created_at')
                .first()
            )
        library = (
            Entitlement.objects.filter(user=user, target_type=EntitlementTargetType.LIBRARY)
            .filter(_active_filter(timezone.now()))
            .order_by('-created_at')
            .first()
        )
        return {
            'allowed': allowed,
            'code': 'access_granted' if allowed else 'access_required',
            'reason': 'active_entitlement' if entitlement else ('active_library_subscription' if library else 'no_active_entitlement'),
            'target_type': target_type,
            'target_id': resolved['target_id'],
            'content': resolved['content'],
            'entitlement_id': str(entitlement.id) if entitlement else (str(library.id) if library else None),
            'source': 'direct' if entitlement else ('library' if library else None),
        }

    @staticmethod
    def _item(*, entitlement: Entitlement, now) -> dict[str, Any]:
        content = _resolve_content(entitlement.target_type, entitlement.target_id)
        starts_ok = not entitlement.starts_at or entitlement.starts_at <= now
        ends_ok = not entitlement.ends_at or entitlement.ends_at >= now
        is_available = entitlement.status == EntitlementStatus.ACTIVE and starts_ok and ends_ok
        return {
            'id': str(entitlement.id),
            'source_type': entitlement.source_type,
            'source_order_id': str(entitlement.source_order_id) if entitlement.source_order_id else None,
            'source_subscription_id': str(entitlement.source_subscription_id) if entitlement.source_subscription_id else None,
            'target_type': entitlement.target_type,
            'target_id': str(entitlement.target_id) if entitlement.target_id else None,
            'status': entitlement.status,
            'is_available': is_available,
            'starts_at': _iso(entitlement.starts_at),
            'ends_at': _iso(entitlement.ends_at),
            'created_at': _iso(entitlement.created_at),
            'updated_at': _iso(entitlement.updated_at),
            'metadata': entitlement.metadata or {},
            'content': content,
            'title': content.get('title') or (entitlement.metadata or {}).get('title') or entitlement.target_type,
            'trainer_name': content.get('trainer_name') or (entitlement.metadata or {}).get('trainer_name') or '',
            'slug': content.get('slug') or (entitlement.metadata or {}).get('slug') or '',
            'access_url': _access_url(entitlement.target_type, content.get('slug')),
        }

    @staticmethod
    def _readiness(*, items: list[dict[str, Any]], active_count: int) -> list[dict[str, Any]]:
        return [
            {
                'code': 'has_library_access',
                'label': 'Есть активные доступы',
                'is_ok': active_count > 0,
                'severity': 'success' if active_count > 0 else 'warning',
            },
            {
                'code': 'content_resolved',
                'label': 'Доступы связаны с опубликованным контентом',
                'is_ok': all((item['target_type'] == EntitlementTargetType.LIBRARY or bool(item.get('content'))) for item in items if item.get('is_available')),
                'severity': 'success',
            },
        ]


def _access_url(target_type: str, slug: str | None) -> str:
    if not slug:
        return '/customer/access'
    if target_type == EntitlementTargetType.VIDEO or target_type == 'video':
        return f'/catalog/videos/{slug}'
    if target_type == EntitlementTargetType.PROGRAM or target_type == 'program':
        return f'/catalog/programs/{slug}'
    if target_type == EntitlementTargetType.BUNDLE or target_type == 'bundle':
        return f'/catalog/bundles/{slug}'
    return '/customer/access'
