from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db.models import Q
from django.utils import timezone

from apps.entitlements.models import (
    Entitlement,
    EntitlementSourceType,
    EntitlementStatus,
    EntitlementTargetType,
)
from apps.entitlements.selectors import resolve_access_target
from apps.orders.models import OrderStatus
from apps.subscriptions.models import SubscriptionStatus


ACTIVE_ORDER_STATUSES = {OrderStatus.PAID, OrderStatus.COMPLETED}
INVALID_ORDER_STATUSES = {
    OrderStatus.CANCELLED,
    OrderStatus.FAILED,
    OrderStatus.REFUNDED,
    OrderStatus.DISPUTED,
    OrderStatus.CHARGED_BACK,
}
ACTIVE_SUBSCRIPTION_STATUSES = {SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE}
INVALID_SUBSCRIPTION_STATUSES = {
    SubscriptionStatus.PENDING,
    SubscriptionStatus.CANCELLED,
    SubscriptionStatus.EXPIRED,
}


@dataclass(frozen=True)
class AccessAuditTarget:
    target_type: str
    target_id: str
    original_target_id: str
    content: dict[str, Any]


def _iso(value: Any) -> str | None:
    return value.isoformat() if value else None


def _target_id_candidates(*values: Any) -> list[str]:
    candidates: list[str] = []
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text and text not in candidates:
            candidates.append(text)
    return candidates


def _active_entitlement_filter(now=None) -> Q:
    now = now or timezone.now()
    return (
        Q(status=EntitlementStatus.ACTIVE)
        & (Q(starts_at__isnull=True) | Q(starts_at__lte=now))
        & (Q(ends_at__isnull=True) | Q(ends_at__gte=now))
    )


def _resolve_target(*, target_type: str, target_id: Any) -> AccessAuditTarget:
    resolved = resolve_access_target(target_type=target_type, target_id=target_id)
    return AccessAuditTarget(
        target_type=str(resolved.get("target_type") or target_type),
        target_id=str(resolved.get("target_id") or target_id or ""),
        original_target_id=str(target_id or ""),
        content=dict(resolved.get("content") or {}),
    )


def _source_payload(entitlement: Entitlement) -> dict[str, Any]:
    source_order = entitlement.source_order
    source_subscription = entitlement.source_subscription
    return {
        "source_type": entitlement.source_type,
        "source_reference": entitlement.source_reference,
        "source_order_id": str(source_order.id) if source_order else None,
        "source_order_status": source_order.status if source_order else None,
        "source_subscription_id": str(source_subscription.id) if source_subscription else None,
        "source_subscription_status": source_subscription.status if source_subscription else None,
    }


def _entitlement_payload(entitlement: Entitlement | None, *, now=None) -> dict[str, Any] | None:
    if entitlement is None:
        return None
    now = now or timezone.now()
    starts_ok = not entitlement.starts_at or entitlement.starts_at <= now
    ends_ok = not entitlement.ends_at or entitlement.ends_at >= now
    return {
        "id": str(entitlement.id),
        "target_type": entitlement.target_type,
        "target_id": str(entitlement.target_id or ""),
        "status": entitlement.status,
        "starts_at": _iso(entitlement.starts_at),
        "ends_at": _iso(entitlement.ends_at),
        "created_at": _iso(entitlement.created_at),
        "updated_at": _iso(entitlement.updated_at),
        "metadata": entitlement.metadata or {},
        "date_window_active": bool(starts_ok and ends_ok),
        **_source_payload(entitlement),
    }


def _deny_rule(*, code: str, label: str, reason: str, severity: str = "error") -> dict[str, Any]:
    return {
        "code": code,
        "label": label,
        "passed": False,
        "severity": severity,
        "reason": reason,
    }


def _pass_rule(*, code: str, label: str, reason: str, severity: str = "success") -> dict[str, Any]:
    return {
        "code": code,
        "label": label,
        "passed": True,
        "severity": severity,
        "reason": reason,
    }


def _validate_source(entitlement: Entitlement, *, now=None) -> tuple[bool, list[dict[str, Any]], str | None]:
    now = now or timezone.now()
    rules: list[dict[str, Any]] = []

    if entitlement.source_type in {EntitlementSourceType.ORDER, "order"}:
        order = entitlement.source_order
        if order is None:
            # Legacy rows may only keep source_reference in metadata. Keep them valid if
            # the entitlement itself is active; repair/reconciliation will flag the missing FK.
            rules.append(
                _pass_rule(
                    code="legacy_order_source_reference",
                    label="Order source reference",
                    reason="entitlement uses legacy order source_reference without source_order FK",
                    severity="warning",
                )
            )
            return True, rules, None
        if order.status in ACTIVE_ORDER_STATUSES:
            rules.append(
                _pass_rule(
                    code="source_order_valid",
                    label="Order source is valid",
                    reason=f"order status is {order.status}",
                )
            )
            return True, rules, None
        if order.status in INVALID_ORDER_STATUSES:
            rules.append(
                _deny_rule(
                    code="source_order_invalid",
                    label="Order source invalidates access",
                    reason=f"order status is {order.status}",
                )
            )
            return False, rules, "source_order_invalid"
        rules.append(
            _deny_rule(
                code="source_order_not_completed",
                label="Order source is not completed",
                reason=f"order status is {order.status}",
                severity="warning",
            )
        )
        return False, rules, "source_order_not_completed"

    if entitlement.source_type in {EntitlementSourceType.SUBSCRIPTION, "subscription"}:
        subscription = entitlement.source_subscription
        if subscription is None:
            rules.append(
                _pass_rule(
                    code="legacy_subscription_source_reference",
                    label="Subscription source reference",
                    reason="entitlement uses legacy subscription source_reference without source_subscription FK",
                    severity="warning",
                )
            )
            return True, rules, None
        if subscription.status in ACTIVE_SUBSCRIPTION_STATUSES and (
            subscription.ends_at is None or subscription.ends_at >= now
        ):
            rules.append(
                _pass_rule(
                    code="source_subscription_valid",
                    label="Subscription source is valid",
                    reason="subscription is active and not expired",
                )
            )
            return True, rules, None
        if subscription.status in INVALID_SUBSCRIPTION_STATUSES:
            rules.append(
                _deny_rule(
                    code="source_subscription_invalid",
                    label="Subscription source invalidates access",
                    reason=f"subscription status is {subscription.status}",
                )
            )
            return False, rules, "source_subscription_invalid"
        rules.append(
            _deny_rule(
                code="source_subscription_expired",
                label="Subscription source is expired",
                reason="subscription end date is in the past",
            )
        )
        return False, rules, "source_subscription_expired"

    rules.append(
        _pass_rule(
            code="source_type_allows_access",
            label="Source type allows access",
            reason=f"source_type={entitlement.source_type}",
        )
    )
    return True, rules, None


class AccessControlAuditService:
    """Read-only access decision service for buyer/admin content access checks.

    The service is intentionally strict around money-backed sources: an active
    entitlement from a refunded order or cancelled/expired subscription must not
    silently grant access. Reconciliation can still detect and repair those bad
    rows, while this service prevents the runtime leak.
    """

    @staticmethod
    def check(
        *,
        user,
        target_type: str,
        target_id: Any,
        include_admin_override: bool = True,
    ) -> dict[str, Any]:
        now = timezone.now()
        target = _resolve_target(target_type=target_type, target_id=target_id)
        target_ids = _target_id_candidates(target.target_id, target.original_target_id)

        base_queryset = (
            Entitlement.objects.filter(user=user, target_type=target.target_type)
            .select_related("source_order", "source_subscription")
            .order_by("-created_at")
        )
        direct_queryset = base_queryset.filter(target_id__in=target_ids) if target_ids else base_queryset.none()
        direct_active = direct_queryset.filter(_active_entitlement_filter(now)).first()
        direct_latest = direct_queryset.first()

        library_queryset = (
            Entitlement.objects.filter(user=user, target_type=EntitlementTargetType.LIBRARY)
            .select_related("source_order", "source_subscription")
            .order_by("-created_at")
        )
        library_active = library_queryset.filter(_active_entitlement_filter(now)).first()
        library_latest = library_queryset.first()

        rules: list[dict[str, Any]] = []
        selected: Entitlement | None = None
        source_kind: str | None = None
        code = "access_required"
        reason = "no_active_entitlement"
        allowed = False

        if direct_active is not None:
            selected = direct_active
            source_kind = "direct"
            rules.append(
                _pass_rule(
                    code="direct_entitlement_active",
                    label="Direct entitlement is active",
                    reason="matching active entitlement exists",
                )
            )
        elif library_active is not None:
            selected = library_active
            source_kind = "library"
            rules.append(
                _pass_rule(
                    code="library_entitlement_active",
                    label="Library entitlement is active",
                    reason="active library entitlement covers this target",
                )
            )
        else:
            if direct_latest is not None:
                reason = f"direct_entitlement_{direct_latest.status}"
                rules.append(
                    _deny_rule(
                        code="direct_entitlement_not_active",
                        label="Direct entitlement is not active",
                        reason=f"latest matching entitlement status is {direct_latest.status}",
                    )
                )
            elif library_latest is not None:
                reason = f"library_entitlement_{library_latest.status}"
                rules.append(
                    _deny_rule(
                        code="library_entitlement_not_active",
                        label="Library entitlement is not active",
                        reason=f"latest library entitlement status is {library_latest.status}",
                    )
                )
            else:
                rules.append(
                    _deny_rule(
                        code="no_entitlement_found",
                        label="No entitlement found",
                        reason="user has no direct or library entitlement for the target",
                    )
                )

        if selected is not None:
            source_ok, source_rules, source_code = _validate_source(selected, now=now)
            rules.extend(source_rules)
            if source_ok:
                allowed = True
                code = "access_granted"
                reason = "active_entitlement" if source_kind == "direct" else "active_library_entitlement"
            else:
                allowed = False
                code = source_code or "source_invalid"
                reason = source_code or "source_invalid"

        if not allowed and include_admin_override and (getattr(user, "is_staff", False) or getattr(user, "is_superuser", False)):
            allowed = True
            code = "admin_override"
            reason = "staff_user_override"
            source_kind = "admin_override"
            rules.append(
                _pass_rule(
                    code="admin_override",
                    label="Admin override",
                    reason="staff/superuser may inspect protected content for operations",
                    severity="warning",
                )
            )

        decision = {
            "allowed": allowed,
            "code": code,
            "reason": reason,
            "target_type": target.target_type,
            "target_id": target.target_id,
            "requested_target_id": target.original_target_id,
            "content": target.content,
            "entitlement_id": str(selected.id) if selected else None,
            "source": source_kind,
            "source_type": selected.source_type if selected else None,
            "source_reference": selected.source_reference if selected else None,
            "evaluated_at": now.isoformat(),
            "rules": rules,
            "audit": {
                "direct_entitlement": _entitlement_payload(direct_latest, now=now),
                "library_entitlement": _entitlement_payload(library_latest, now=now),
                "selected_entitlement": _entitlement_payload(selected, now=now),
                "candidate_target_ids": target_ids,
                "admin_override_enabled": bool(include_admin_override),
            },
        }
        return decision
