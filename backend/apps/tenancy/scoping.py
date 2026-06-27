from __future__ import annotations

from django.db.models import Q, QuerySet

from apps.access_control.permissions import (
    ROLE_ADMIN,
    ROLE_FINANCE,
    ROLE_READONLY_AUDITOR,
    ROLE_STUDENT,
    ROLE_SUPPORT,
    ROLE_TRAINER,
    ROLE_USER,
    user_role_set,
)
from apps.tenancy.models import Tenant, TenantMembership


OPERATOR_ROLES = {ROLE_SUPPORT, ROLE_FINANCE, ROLE_READONLY_AUDITOR}


def _string_ids(values) -> list[str]:
    return [str(value) for value in values if value is not None and str(value)]


def is_global_operator(user) -> bool:
    roles = user_role_set(user)
    return ROLE_ADMIN in roles or bool(getattr(user, "is_staff", False) or getattr(user, "is_superuser", False))


def accessible_tenant_owner_ids(user) -> list[str]:
    if not user or not getattr(user, "is_authenticated", False):
        return []
    tenant_ids = list(
        TenantMembership.objects.filter(account_id=str(user.id), status="active").values_list("tenant_id", flat=True)
    )
    if not tenant_ids:
        return []
    return _string_ids(
        Tenant.objects.filter(id__in=tenant_ids, status="active").values_list("owner_account_id", flat=True)
    )


def trainer_scope_user_ids(user) -> list[str]:
    roles = user_role_set(user)
    trainer_ids = set(accessible_tenant_owner_ids(user))
    if ROLE_TRAINER in roles:
        trainer_ids.add(str(user.id))
    return sorted(trainer_ids)


def _none_when_empty(queryset: QuerySet, ids: list[str]) -> QuerySet:
    return queryset if ids else queryset.none()


def scope_orders_for_user(queryset: QuerySet, user) -> QuerySet:
    if is_global_operator(user):
        return queryset
    roles = user_role_set(user)
    if roles.intersection({ROLE_USER, ROLE_STUDENT}) and not roles.intersection({ROLE_TRAINER, *OPERATOR_ROLES}):
        return queryset.filter(user=user)
    trainer_ids = trainer_scope_user_ids(user)
    queryset = _none_when_empty(queryset, trainer_ids)
    if not trainer_ids:
        return queryset
    return queryset.filter(
        Q(items__metadata__trainer_id__in=trainer_ids)
        | Q(payments__provider_payload__trainer_id__in=trainer_ids)
    ).distinct()


def scope_payments_for_user(queryset: QuerySet, user) -> QuerySet:
    if is_global_operator(user):
        return queryset
    roles = user_role_set(user)
    if roles.intersection({ROLE_USER, ROLE_STUDENT}) and not roles.intersection({ROLE_TRAINER, *OPERATOR_ROLES}):
        return queryset.filter(order__user=user)
    trainer_ids = trainer_scope_user_ids(user)
    queryset = _none_when_empty(queryset, trainer_ids)
    if not trainer_ids:
        return queryset
    return queryset.filter(
        Q(order__items__metadata__trainer_id__in=trainer_ids)
        | Q(provider_payload__trainer_id__in=trainer_ids)
    ).distinct()


def scope_payment_webhooks_for_user(queryset: QuerySet, user) -> QuerySet:
    if is_global_operator(user):
        return queryset
    trainer_ids = trainer_scope_user_ids(user)
    queryset = _none_when_empty(queryset, trainer_ids)
    if not trainer_ids:
        return queryset
    return queryset.filter(
        Q(payment__order__items__metadata__trainer_id__in=trainer_ids)
        | Q(payment__provider_payload__trainer_id__in=trainer_ids)
    ).distinct()


def scope_entitlements_for_user(queryset: QuerySet, user) -> QuerySet:
    if is_global_operator(user):
        return queryset
    roles = user_role_set(user)
    if roles.intersection({ROLE_USER, ROLE_STUDENT}) and not roles.intersection({ROLE_TRAINER, *OPERATOR_ROLES}):
        return queryset.filter(user=user)
    trainer_ids = trainer_scope_user_ids(user)
    queryset = _none_when_empty(queryset, trainer_ids)
    if not trainer_ids:
        return queryset
    return queryset.filter(
        Q(metadata__trainer_id__in=trainer_ids)
        | Q(source_order__items__metadata__trainer_id__in=trainer_ids)
    ).distinct()


def scope_payouts_for_user(queryset: QuerySet, user) -> QuerySet:
    if is_global_operator(user):
        return queryset
    trainer_ids = trainer_scope_user_ids(user)
    queryset = _none_when_empty(queryset, trainer_ids)
    if not trainer_ids:
        return queryset
    return queryset.filter(trainer__user_id__in=trainer_ids)


def scope_balance_entries_for_user(queryset: QuerySet, user) -> QuerySet:
    if is_global_operator(user):
        return queryset
    trainer_ids = trainer_scope_user_ids(user)
    queryset = _none_when_empty(queryset, trainer_ids)
    if not trainer_ids:
        return queryset
    return queryset.filter(wallet__trainer__user_id__in=trainer_ids)
