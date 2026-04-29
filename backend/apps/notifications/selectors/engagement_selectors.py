from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.db.models import Count, Q
from django.utils import timezone

from apps.notifications.models import (
    AdminAnnouncement,
    DeliveryStatus,
    Notification,
    NotificationChannel,
    NotificationDelivery,
    NotificationPreference,
    NotificationStatus,
)


def _iso(value):
    return value.isoformat() if value else None


class NotificationEngagementSelectors:
    @staticmethod
    def get_or_create_preferences(user):
        preferences, _ = NotificationPreference.objects.get_or_create(user=user)
        return preferences

    @staticmethod
    def user_inbox(*, user, unread_only: bool = False, limit: int = 50) -> dict[str, Any]:
        limit = max(1, min(int(limit or 50), 100))
        qs = Notification.objects.filter(user=user, channel=NotificationChannel.IN_APP).order_by('-created_at')
        if unread_only:
            qs = qs.filter(is_read=False)

        total = Notification.objects.filter(user=user, channel=NotificationChannel.IN_APP).count()
        unread = Notification.objects.filter(user=user, channel=NotificationChannel.IN_APP, is_read=False).count()
        by_type = dict(
            Notification.objects.filter(user=user, channel=NotificationChannel.IN_APP)
            .values_list('notification_type')
            .annotate(count=Count('id'))
        )

        return {
            'summary': {
                'total': total,
                'unread': unread,
                'read': max(total - unread, 0),
                'by_type': by_type,
            },
            'preferences': NotificationEngagementSelectors.serialize_preferences(
                NotificationEngagementSelectors.get_or_create_preferences(user)
            ),
            'results': [NotificationEngagementSelectors.serialize_notification(item) for item in qs[:limit]],
        }

    @staticmethod
    def admin_center(*, days: int = 30) -> dict[str, Any]:
        days = max(1, min(int(days or 30), 365))
        since = timezone.now() - timedelta(days=days)

        notifications = Notification.objects.filter(created_at__gte=since)
        deliveries = NotificationDelivery.objects.filter(created_at__gte=since)
        announcements = AdminAnnouncement.objects.filter(created_at__gte=since)

        return {
            'period': {
                'days': days,
                'since': _iso(since),
                'generated_at': _iso(timezone.now()),
            },
            'summary': {
                'notifications_total': notifications.count(),
                'notifications_unread': notifications.filter(is_read=False).count(),
                'notifications_read': notifications.filter(is_read=True).count(),
                'deliveries_total': deliveries.count(),
                'deliveries_pending': deliveries.filter(status=NotificationStatus.PENDING).count(),
                'deliveries_sent': deliveries.filter(status=NotificationStatus.SENT).count(),
                'deliveries_failed': deliveries.filter(status=NotificationStatus.FAILED).count(),
                'announcements_total': announcements.count(),
                'announcements_published': announcements.filter(is_published=True).count(),
                'announcements_draft': announcements.filter(is_published=False).count(),
            },
            'channels': list(
                notifications.values('channel')
                .annotate(count=Count('id'), unread=Count('id', filter=Q(is_read=False)))
                .order_by('channel')
            ),
            'types': list(
                notifications.values('notification_type')
                .annotate(count=Count('id'), unread=Count('id', filter=Q(is_read=False)))
                .order_by('notification_type')
            ),
            'recent_announcements': [
                NotificationEngagementSelectors.serialize_announcement(item)
                for item in AdminAnnouncement.objects.select_related('created_by').order_by('-created_at')[:10]
            ],
            'recent_failed_deliveries': [
                NotificationEngagementSelectors.serialize_delivery(item)
                for item in NotificationDelivery.objects.select_related('user')
                .filter(status=NotificationStatus.FAILED)
                .order_by('-created_at')[:20]
            ],
            'recent_notifications': [
                NotificationEngagementSelectors.serialize_notification(item)
                for item in Notification.objects.select_related('user').order_by('-created_at')[:20]
            ],
            'health': NotificationEngagementSelectors._health(deliveries=deliveries, announcements=announcements),
        }

    @staticmethod
    def _health(*, deliveries, announcements) -> dict[str, Any]:
        failed = deliveries.filter(status=NotificationStatus.FAILED).count()
        pending = deliveries.filter(status=NotificationStatus.PENDING).count()
        draft_announcements = announcements.filter(is_published=False).count()
        checks = [
            {
                'code': 'failed_deliveries',
                'title': 'Failed notification deliveries',
                'status': 'attention' if failed else 'ok',
                'value': failed,
            },
            {
                'code': 'pending_deliveries',
                'title': 'Pending delivery backlog',
                'status': 'attention' if pending > 25 else 'ok',
                'value': pending,
            },
            {
                'code': 'draft_announcements',
                'title': 'Draft announcements waiting for publish',
                'status': 'attention' if draft_announcements else 'ok',
                'value': draft_announcements,
            },
        ]
        return {
            'status': 'attention' if any(item['status'] == 'attention' for item in checks) else 'ok',
            'checks': checks,
        }

    @staticmethod
    def serialize_preferences(preferences: NotificationPreference) -> dict[str, Any]:
        return {
            'in_app_enabled': preferences.in_app_enabled,
            'email_enabled': preferences.email_enabled,
            'marketing_enabled': preferences.marketing_enabled,
            'product_updates_enabled': preferences.product_updates_enabled,
            'quiet_hours_start': preferences.quiet_hours_start.isoformat() if preferences.quiet_hours_start else None,
            'quiet_hours_end': preferences.quiet_hours_end.isoformat() if preferences.quiet_hours_end else None,
            'created_at': _iso(preferences.created_at),
            'updated_at': _iso(preferences.updated_at),
        }

    @staticmethod
    def serialize_notification(notification: Notification) -> dict[str, Any]:
        user = getattr(notification, 'user', None)
        return {
            'id': str(notification.notification_uuid),
            'db_id': notification.id,
            'user_id': str(user.id) if user else None,
            'user_email': getattr(user, 'email', '') if user else '',
            'notification_type': notification.notification_type,
            'channel': notification.channel,
            'title': notification.title,
            'body': notification.body,
            'cta_label': notification.cta_label,
            'cta_url': notification.cta_url,
            'metadata': notification.metadata or {},
            'status': notification.status,
            'is_read': notification.is_read,
            'read_at': _iso(notification.read_at),
            'sent_at': _iso(notification.sent_at),
            'created_at': _iso(notification.created_at),
        }

    @staticmethod
    def serialize_announcement(announcement: AdminAnnouncement) -> dict[str, Any]:
        return {
            'id': str(announcement.announcement_uuid),
            'db_id': announcement.id,
            'title': announcement.title,
            'body': announcement.body,
            'cta_label': announcement.cta_label,
            'cta_url': announcement.cta_url,
            'audience_type': announcement.audience_type,
            'is_published': announcement.is_published,
            'starts_at': _iso(announcement.starts_at),
            'ends_at': _iso(announcement.ends_at),
            'published_at': _iso(announcement.published_at),
            'created_at': _iso(announcement.created_at),
            'created_by': getattr(announcement.created_by, 'email', '') if announcement.created_by else '',
            'notifications_count': getattr(announcement, 'notifications_count', None),
        }

    @staticmethod
    def serialize_delivery(delivery: NotificationDelivery) -> dict[str, Any]:
        return {
            'id': str(delivery.id),
            'user_id': str(delivery.user_id),
            'user_email': getattr(delivery.user, 'email', ''),
            'channel': delivery.channel,
            'type': delivery.type,
            'template_code': delivery.template_code,
            'subject': delivery.subject,
            'status': delivery.status,
            'error_message': delivery.error_message,
            'provider': delivery.provider,
            'provider_message_id': delivery.provider_message_id,
            'sent_at': _iso(delivery.sent_at),
            'created_at': _iso(delivery.created_at),
        }
