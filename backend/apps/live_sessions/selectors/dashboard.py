from django.db.models import Count
from apps.live_sessions.models import LiveSession, SessionAttendance


class LiveSessionDashboardSelector:
    @staticmethod
    def admin_overview():
        return {
            "total_sessions": LiveSession.objects.count(),
            "scheduled_sessions": LiveSession.objects.filter(status=LiveSession.SessionStatus.SCHEDULED).count(),
            "live_now": LiveSession.objects.filter(status=LiveSession.SessionStatus.LIVE).count(),
            "attendance_breakdown": list(
                SessionAttendance.objects.values("status").annotate(total=Count("id")).order_by("status")
            ),
        }
