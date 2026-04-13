from __future__ import annotations

from dataclasses import dataclass
from string import Template
from typing import Iterable, Sequence

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from apps.notifications.models import (
    AdminAnnouncement,
    AudienceType,
    DeliveryStatus,
    Notification,
    NotificationChannel,
    NotificationPreference,
    NotificationTemplate,
    NotificationType,
)

User = get_user_model()


@dataclass
class NotificationPayload:
    title: str
    body: str
    notification_type: str = NotificationType.SYSTEM
    channel: str = NotificationChannel.IN_APP
    cta_label: str = ''
    cta_url: str = ''
    metadata: dict | None = None


class NotificationDispatcher:
    @staticmethod
    def _ensure_preferences(user_ids: Sequence[int]) -> None:
        existing = set(NotificationPreference.objects.filter(user_id__in=user_ids).values_list('user_id', flat=True))
        missing = [NotificationPreference(user_id=user_id) for user_id in user_ids if user_id not in existing]
        if missing:
            NotificationPreference.objects.bulk_create(missing, ignore_conflicts=True)

    @staticmethod
    def render_template(template_code: str, context: dict) -> NotificationPayload:
        template = NotificationTemplate.objects.get(code=template_code, is_active=True)
        return NotificationPayload(
            title=Template(template.title_template).safe_substitute(**context),
            body=Template(template.body_template).safe_substitute(**context),
            notification_type=template.notification_type,
            channel=template.channel,
        )

    @classmethod
    @transaction.atomic
    def send_to_users(cls, user_ids: Sequence[int], payload: NotificationPayload, announcement: AdminAnnouncement | None = None) -> int:
        if not user_ids:
            return 0
        cls._ensure_preferences(user_ids)
        notifications = [
            Notification(
                user_id=user_id,
                announcement=announcement,
                notification_type=payload.notification_type,
                channel=payload.channel,
                title=payload.title,
                body=payload.body,
                cta_label=payload.cta_label,
                cta_url=payload.cta_url,
                metadata=payload.metadata or {},
                status=DeliveryStatus.SENT if payload.channel == NotificationChannel.IN_APP else DeliveryStatus.PENDING,
                sent_at=timezone.now() if payload.channel == NotificationChannel.IN_APP else None,
            )
            for user_id in user_ids
        ]
        created = Notification.objects.bulk_create(notifications, batch_size=1000)
        return len(created)

    @classmethod
    def publish_announcement(cls, announcement: AdminAnnouncement, specific_user_ids: Sequence[int] | None = None) -> int:
        qs = User.objects.all().order_by('id')
        if announcement.audience_type == AudienceType.ALL_TRAINERS:
            qs = qs.filter(is_staff=False).filter(groups__name__iexact='trainers').distinct()
        elif announcement.audience_type == AudienceType.SPECIFIC_USERS:
            qs = qs.filter(id__in=list(specific_user_ids or []))
        user_ids = list(qs.values_list('id', flat=True))
        payload = NotificationPayload(
            title=announcement.title,
            body=announcement.body,
            notification_type=NotificationType.ANNOUNCEMENT,
            channel=NotificationChannel.IN_APP,
            cta_label=announcement.cta_label,
            cta_url=announcement.cta_url,
            metadata={'announcement_uuid': str(announcement.announcement_uuid)},
        )
        created = cls.send_to_users(user_ids=user_ids, payload=payload, announcement=announcement)
        announcement.is_published = True
        announcement.published_at = timezone.now()
        announcement.save(update_fields=['is_published', 'published_at', 'updated_at'])
        return created
