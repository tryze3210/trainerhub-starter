from django.db.models import Count, Q
from django.utils import timezone

from apps.notifications.models import AdminAnnouncement, Notification


class NotificationSelectors:
    @staticmethod
    def inbox(user, limit: int = 20):
        return Notification.objects.filter(user=user, channel='in_app').order_by('-created_at')[:limit]

    @staticmethod
    def unread_count(user) -> int:
        return Notification.objects.filter(user=user, channel='in_app', is_read=False).count()

    @staticmethod
    def admin_overview() -> dict:
        now = timezone.now()
        return {
            'published_announcements': AdminAnnouncement.objects.filter(is_published=True).count(),
            'active_announcements': AdminAnnouncement.objects.filter(is_published=True, starts_at__lte=now).filter(Q(ends_at__isnull=True) | Q(ends_at__gte=now)).count(),
            'total_notifications': Notification.objects.count(),
            'unread_notifications': Notification.objects.filter(is_read=False).count(),
            'failed_notifications': Notification.objects.filter(status='failed').count(),
        }

    @staticmethod
    def latest_announcements(limit: int = 20):
        return AdminAnnouncement.objects.order_by('-created_at')[:limit]

    @staticmethod
    def delivery_breakdown(limit: int = 10):
        rows = (
            Notification.objects.values('notification_type', 'status')
            .annotate(total=Count('id'))
            .order_by('-total', 'notification_type', 'status')[:limit]
        )
        return list(rows)
