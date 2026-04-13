from django.db.models import Q
from django.utils import timezone

from .constants import DeliveryStatus, TemplateStatus
from .models import NotificationMessage, NotificationTemplate, SuppressionRule


def get_active_template(*, key: str, channel: str, locale: str = "en"):
    return (
        NotificationTemplate.objects.filter(
            key=key,
            channel=channel,
            locale=locale,
            status=TemplateStatus.ACTIVE,
        )
        .order_by("-version")
        .first()
    )


def get_due_messages(limit: int = 100):
    now = timezone.now()
    return NotificationMessage.objects.filter(
        status=DeliveryStatus.PENDING,
    ).filter(Q(scheduled_for__isnull=True) | Q(scheduled_for__lte=now)).order_by("created_at")[:limit]


def get_active_suppression_rules(*, category: str, channel: str):
    now = timezone.now()
    return SuppressionRule.objects.filter(
        is_active=True,
    ).filter(
        Q(category="") | Q(category=category),
        Q(channel="") | Q(channel=channel),
    ).filter(
        Q(starts_at__isnull=True) | Q(starts_at__lte=now),
        Q(ends_at__isnull=True) | Q(ends_at__gte=now),
    )
