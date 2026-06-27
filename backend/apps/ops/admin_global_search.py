from __future__ import annotations

from typing import Any
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db.models import Q, QuerySet
from django.utils import timezone

from apps.access_control.permissions import user_role_set
from apps.content.models import PublishedBundle, PublishedProgram, PublishedVideo
from apps.entitlements.models import Entitlement
from apps.orders.models import Order
from apps.payments.models import Payment
from apps.payouts.models import PayoutRequest
from apps.subscriptions.models import Subscription
from apps.tenancy.scoping import (
    accessible_tenant_owner_ids,
    is_global_operator,
    scope_entitlements_for_user,
    scope_orders_for_user,
    scope_payments_for_user,
    scope_payouts_for_user,
    trainer_scope_user_ids,
)
from apps.trainer_cms.models import TrainerBundleDraft, TrainerCourseDraft, TrainerProgramDraft, TrainerVideoDraft
from apps.trainer_profiles.models import TrainerPublicProfile
from apps.trainers.models import TrainerProfile


DEFAULT_CATEGORIES = ("users", "trainers", "orders", "payments", "payouts", "content", "subscriptions")


def _clean_query(query: str | None) -> str:
    return (query or "").strip()


def _string(value: Any) -> str:
    return "" if value is None else str(value)


def _uuid_q(field: str, query: str) -> Q:
    try:
        return Q(**{field: UUID(str(query))})
    except (TypeError, ValueError):
        return Q(pk__in=[])


def _href(entity_type: str, entity_id: str) -> str:
    return f"/admin/entities/{entity_type}/{entity_id}"


def _result(
    *,
    category: str,
    entity_type: str,
    entity_id: Any,
    title: str,
    subtitle: str = "",
    status: str = "",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entity_id_str = _string(entity_id)
    return {
        "category": category,
        "entity_type": entity_type,
        "entity_id": entity_id_str,
        "title": title,
        "subtitle": subtitle,
        "status": status,
        "href": _href(entity_type, entity_id_str),
        "metadata": metadata or {},
    }


def _bounded(queryset: QuerySet, limit: int) -> list:
    return list(queryset[:limit])


def _user_ids_for_visible_rows(user, query: str, limit: int) -> set[str]:
    ids: set[str] = set()
    for order in _bounded(scope_orders_for_user(Order.objects.filter(user__email__icontains=query), user), limit):
        ids.add(str(order.user_id))
    for entitlement in _bounded(
        scope_entitlements_for_user(Entitlement.objects.filter(user__email__icontains=query), user),
        limit,
    ):
        ids.add(str(entitlement.user_id))
    return ids


def _search_users(user, query: str, limit: int) -> list[dict[str, Any]]:
    User = get_user_model()
    base = User.objects.filter(
        Q(email__icontains=query)
        | Q(first_name__icontains=query)
        | Q(last_name__icontains=query)
        | _uuid_q("id", query)
    ).order_by("-created_at")
    if is_global_operator(user):
        rows = _bounded(base, limit)
    else:
        visible_ids = _user_ids_for_visible_rows(user, query, limit)
        rows = _bounded(base.filter(id__in=visible_ids), limit)
    return [
        _result(
            category="users",
            entity_type="user",
            entity_id=row.id,
            title=row.email,
            subtitle=" ".join(part for part in [row.first_name, row.last_name] if part),
            status=getattr(row, "role", ""),
            metadata={"is_active": row.is_active, "roles": sorted(user_role_set(row))},
        )
        for row in rows
    ]


def _trainer_user_ids_for_operator(user) -> list[str]:
    if is_global_operator(user):
        return []
    return trainer_scope_user_ids(user) or accessible_tenant_owner_ids(user)


def _search_trainers(user, query: str, limit: int) -> list[dict[str, Any]]:
    trainer_ids = _trainer_user_ids_for_operator(user)
    profiles = TrainerProfile.objects.select_related("user").filter(
        Q(user__email__icontains=query)
        | Q(display_name__icontains=query)
        | Q(slug__icontains=query)
        | _uuid_q("id", query)
        | _uuid_q("user_id", query)
    ).order_by("-created_at")
    public_profiles = TrainerPublicProfile.objects.select_related("user").filter(
        Q(user__email__icontains=query)
        | Q(display_name__icontains=query)
        | Q(slug__icontains=query)
        | _uuid_q("trainer_uuid", query)
        | _uuid_q("user_id", query)
    ).order_by("-created_at")
    if trainer_ids:
        profiles = profiles.filter(user_id__in=trainer_ids)
        public_profiles = public_profiles.filter(user_id__in=trainer_ids)
    elif not is_global_operator(user):
        profiles = profiles.none()
        public_profiles = public_profiles.none()

    results = [
        _result(
            category="trainers",
            entity_type="trainer",
            entity_id=row.user_id,
            title=row.display_name,
            subtitle=row.user.email,
            status=row.status,
            metadata={"profile_id": str(row.id), "slug": row.slug},
        )
        for row in _bounded(profiles, limit)
    ]
    seen = {item["entity_id"] for item in results}
    for row in _bounded(public_profiles, limit):
        if str(row.user_id) in seen:
            continue
        results.append(
            _result(
                category="trainers",
                entity_type="trainer",
                entity_id=row.user_id,
                title=row.display_name,
                subtitle=row.user.email,
                status="public" if row.is_public else "private",
                metadata={"profile_id": str(row.id), "slug": row.slug},
            )
        )
    return results[:limit]


def _search_orders(user, query: str, limit: int) -> list[dict[str, Any]]:
    queryset = scope_orders_for_user(
        Order.objects.select_related("user").prefetch_related("items").filter(
            _uuid_q("id", query)
            | Q(user__email__icontains=query)
            | Q(external_checkout_id__icontains=query)
            | Q(items__title_snapshot__icontains=query)
            | Q(items__metadata__trainer_id__icontains=query)
        ),
        user,
    ).order_by("-created_at").distinct()
    return [
        _result(
            category="orders",
            entity_type="order",
            entity_id=row.id,
            title=f"Order {row.id}",
            subtitle=row.user.email,
            status=row.status,
            metadata={"amount": str(row.total_amount), "currency": row.currency},
        )
        for row in _bounded(queryset, limit)
    ]


def _search_payments(user, query: str, limit: int) -> list[dict[str, Any]]:
    queryset = scope_payments_for_user(
        Payment.objects.select_related("order", "order__user").filter(
            _uuid_q("id", query)
            | _uuid_q("order__id", query)
            | Q(order__user__email__icontains=query)
            | Q(external_payment_id__icontains=query)
            | Q(provider__icontains=query)
            | Q(provider_payload__trainer_id__icontains=query)
        ),
        user,
    ).order_by("-created_at").distinct()
    return [
        _result(
            category="payments",
            entity_type="payment",
            entity_id=row.id,
            title=f"{row.provider} payment",
            subtitle=row.order.user.email,
            status=row.status,
            metadata={"amount": str(row.amount), "currency": row.currency, "order_id": str(row.order_id)},
        )
        for row in _bounded(queryset, limit)
    ]


def _search_payouts(user, query: str, limit: int) -> list[dict[str, Any]]:
    queryset = scope_payouts_for_user(
        PayoutRequest.objects.select_related("trainer", "trainer__user").filter(
            _uuid_q("id", query)
            | Q(trainer__display_name__icontains=query)
            | Q(trainer__slug__icontains=query)
            | Q(trainer__user__email__icontains=query)
            | _uuid_q("trainer__user_id", query)
            | Q(destination_json__external_reference__icontains=query)
        ),
        user,
    ).order_by("-created_at").distinct()
    return [
        _result(
            category="payouts",
            entity_type="payout",
            entity_id=row.id,
            title=f"Payout {row.id}",
            subtitle=row.trainer.user.email,
            status=row.status,
            metadata={"amount": str(row.amount), "currency": row.currency, "trainer_id": str(row.trainer.user_id)},
        )
        for row in _bounded(queryset, limit)
    ]


def _content_trainer_filter(user) -> Q:
    trainer_ids = _trainer_user_ids_for_operator(user)
    if is_global_operator(user):
        return Q()
    if not trainer_ids:
        return Q(pk__in=[])
    return Q(trainer_id__in=trainer_ids)


def _published_content_trainer_filter(user) -> Q:
    trainer_ids = _trainer_user_ids_for_operator(user)
    if is_global_operator(user):
        return Q()
    if not trainer_ids:
        return Q(pk__in=[])
    return Q(trainer_profile__user_id__in=trainer_ids)


def _search_content(user, query: str, limit: int) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    draft_models = [
        ("trainer_video_draft", TrainerVideoDraft),
        ("trainer_program_draft", TrainerProgramDraft),
        ("trainer_course_draft", TrainerCourseDraft),
        ("trainer_bundle_draft", TrainerBundleDraft),
    ]
    for entity_type, model in draft_models:
        queryset = model.objects.filter(
            _content_trainer_filter(user),
            _uuid_q("id", query)
            | Q(title__icontains=query)
            | Q(slug__icontains=query)
            | Q(description__icontains=query)
            | _uuid_q("trainer_id", query),
        ).order_by("-created_at")
        for row in _bounded(queryset, limit):
            results.append(
                _result(
                    category="content",
                    entity_type=entity_type,
                    entity_id=row.id,
                    title=row.title,
                    subtitle=row.slug,
                    status=row.status,
                    metadata={"trainer_id": str(row.trainer_id), "kind": "draft"},
                )
            )
    published_models = [
        ("published_video", PublishedVideo),
        ("published_program", PublishedProgram),
        ("published_bundle", PublishedBundle),
    ]
    for entity_type, model in published_models:
        queryset = model.objects.select_related("trainer_profile").filter(
            _published_content_trainer_filter(user),
            _uuid_q("id", query)
            | Q(title__icontains=query)
            | Q(slug__icontains=query)
            | Q(description__icontains=query)
            | Q(trainer_profile__display_name__icontains=query)
            | _uuid_q("trainer_profile__user_id", query),
        ).order_by("-created_at")
        for row in _bounded(queryset, limit):
            results.append(
                _result(
                    category="content",
                    entity_type=entity_type,
                    entity_id=row.id,
                    title=row.title,
                    subtitle=row.slug,
                    status=row.visibility,
                    metadata={"trainer_id": str(row.trainer_profile.user_id), "kind": "published"},
                )
            )
    return results[:limit]


def _scope_subscriptions_for_user(queryset: QuerySet, user) -> QuerySet:
    if is_global_operator(user):
        return queryset
    trainer_ids = trainer_scope_user_ids(user)
    if trainer_ids:
        return queryset.filter(Q(plan__trainer_id__in=trainer_ids) | Q(source_order__items__metadata__trainer_id__in=trainer_ids)).distinct()
    return queryset.filter(user=user)


def _search_subscriptions(user, query: str, limit: int) -> list[dict[str, Any]]:
    queryset = _scope_subscriptions_for_user(
        Subscription.objects.select_related("user", "plan").filter(
            _uuid_q("id", query)
            | Q(user__email__icontains=query)
            | Q(plan__title__icontains=query)
            | Q(plan__code__icontains=query)
            | Q(plan__trainer_id__icontains=query)
        ),
        user,
    ).order_by("-created_at").distinct()
    return [
        _result(
            category="subscriptions",
            entity_type="subscription",
            entity_id=row.id,
            title=row.plan.title,
            subtitle=row.user.email,
            status=row.status,
            metadata={"plan_id": str(row.plan_id), "trainer_id": row.plan.trainer_id},
        )
        for row in _bounded(queryset, limit)
    ]


SEARCHERS = {
    "users": _search_users,
    "trainers": _search_trainers,
    "orders": _search_orders,
    "payments": _search_payments,
    "payouts": _search_payouts,
    "content": _search_content,
    "subscriptions": _search_subscriptions,
}


def parse_categories(raw_categories: str | None) -> tuple[str, ...]:
    if not raw_categories:
        return DEFAULT_CATEGORIES
    selected = tuple(category.strip() for category in raw_categories.split(",") if category.strip())
    valid = tuple(category for category in selected if category in SEARCHERS)
    return valid or DEFAULT_CATEGORIES


def get_admin_global_search(*, user, query: str, categories: tuple[str, ...] | None = None, limit: int = 10) -> dict[str, Any]:
    query = _clean_query(query)
    categories = categories or DEFAULT_CATEGORIES
    limit = max(1, min(int(limit or 10), 25))
    results_by_category: dict[str, list[dict[str, Any]]] = {category: [] for category in categories}
    if query:
        for category in categories:
            searcher = SEARCHERS.get(category)
            if searcher:
                results_by_category[category] = searcher(user, query, limit)
    flat_results = [item for category in categories for item in results_by_category.get(category, [])]
    return {
        "query": query,
        "categories": list(categories),
        "limit": limit,
        "generated_at": timezone.now(),
        "total_count": len(flat_results),
        "results": flat_results,
        "results_by_category": results_by_category,
    }
