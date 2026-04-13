from django.utils import timezone
from apps.entitlements.models import Entitlement


def has_active_entitlement(*, user, kind: str, object_id: str) -> bool:
    now = timezone.now()
    return Entitlement.objects.filter(
        user=user,
        kind=kind,
        object_id=object_id,
        is_active=True,
        starts_at__lte=now,
    ).filter(ends_at__isnull=True).exists() or Entitlement.objects.filter(
        user=user,
        kind=kind,
        object_id=object_id,
        is_active=True,
        starts_at__lte=now,
        ends_at__gte=now,
    ).exists()


def get_user_active_entitlements(*, user):
    now = timezone.now()
    return Entitlement.objects.filter(user=user, is_active=True, starts_at__lte=now).filter(ends_at__isnull=True) | Entitlement.objects.filter(user=user, is_active=True, starts_at__lte=now, ends_at__gte=now)
