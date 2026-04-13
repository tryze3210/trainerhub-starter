from datetime import timedelta
from django.utils import timezone
from apps.live_sessions.models import ReminderDelivery, SessionAttendance


class ReminderOrchestrationService:
    DEFAULT_OFFSETS = (timedelta(hours=24), timedelta(hours=1), timedelta(minutes=15))

    @classmethod
    def schedule_for_attendance(cls, attendance: SessionAttendance) -> int:
        from apps.live_sessions.models import LiveSession
        session = LiveSession.objects.get(id=attendance.live_session_id)
        created = 0
        for offset in cls.DEFAULT_OFFSETS:
            scheduled_for = session.starts_at - offset
            if scheduled_for <= timezone.now():
                continue
            ReminderDelivery.objects.get_or_create(
                live_session_id=session.id,
                attendance_id=attendance.id,
                channel=ReminderDelivery.Channel.IN_APP,
                scheduled_for=scheduled_for,
            )
            created += 1
        return created
