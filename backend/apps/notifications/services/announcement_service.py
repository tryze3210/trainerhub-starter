from __future__ import annotations

from typing import Iterable

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from apps.notifications.models import (
    AdminAnnouncement,
    AudienceType,
    DeliveryStatus,
    Notification,
    NotificationChannel,
    NotificationType,
)


class AdminAnnouncementService:
    @staticmethod
    def _resolve_users(*, audience_type: str, user_ids: Iterable[str] | None = None):
        User = get_user_model()
        qs = User.objects.filter(is_active=True)

        if audience_type == AudienceType.ALL_TRAINERS:
            field_names = {field.name for field in User._meta.get_fields()}
            if 'role' in field_names:
                qs = qs.filter(role='trainer')
            else:
                qs = qs.none()
        elif audience_type == AudienceType.SPECIFIC_USERS:
            ids = [value for value in (user_ids or []) if value]
            qs = qs.filter(id__in=ids) if ids else qs.none()

        return qs.order_by('id')

    @classmethod
    @transaction.atomic
    def create_announcement(
        cls,
        *,
        actor,
        title: str,
        body: str,
        audience_type: str = AudienceType.ALL_USERS,
        cta_label: str = '',
        cta_url: str = '',
        starts_at=None,
        ends_at=None,
        publish_now: bool = False,
        user_ids: list[str] | None = None,
    ) -> tuple[AdminAnnouncement, int]:
        announcement = AdminAnnouncement.objects.create(
            title=title.strip(),
            body=body.strip(),
            audience_type=audience_type,
            cta_label=(cta_label or '').strip(),
            cta_url=(cta_url or '').strip(),
            starts_at=starts_at or timezone.now(),
            ends_at=ends_at,
            is_published=False,
            created_by=actor if getattr(actor, 'is_authenticated', False) else None,
        )
        created_count = 0
        if publish_now:
            created_count = cls.publish(announcement=announcement, actor=actor, user_ids=user_ids)
        return announcement, created_count

    @classmethod
    @transaction.atomic
    def publish(cls, *, announcement: AdminAnnouncement, actor=None, user_ids: list[str] | None = None) -> int:
        users = cls._resolve_users(audience_type=announcement.audience_type, user_ids=user_ids)
        notifications = []
        now = timezone.now()
        for user in users.iterator(chunk_size=500):
            preferences = getattr(user, 'notification_preferences', None)
            if preferences and not preferences.in_app_enabled:
                continue
            notifications.append(
                Notification(
                    user=user,
                    announcement=announcement,
                    notification_type=NotificationType.ANNOUNCEMENT,
                    channel=NotificationChannel.IN_APP,
                    title=announcement.title,
                    body=announcement.body,
                    cta_label=announcement.cta_label,
                    cta_url=announcement.cta_url,
                    status=DeliveryStatus.SENT,
                    sent_at=now,
                    metadata={'announcement_id': str(announcement.announcement_uuid)},
                )
            )

        if notifications:
            Notification.objects.bulk_create(notifications, batch_size=500)

        if not announcement.is_published:
            announcement.is_published = True
            announcement.published_at = now
            announcement.save(update_fields=['is_published', 'published_at', 'updated_at'])

        return len(notifications)
