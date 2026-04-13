from django.utils import timezone
from apps.live_sessions.models import SessionAttendance


class AttendanceService:
    @staticmethod
    def mark_joined(attendance: SessionAttendance) -> SessionAttendance:
        if not attendance.joined_at:
            attendance.joined_at = timezone.now()
        attendance.status = SessionAttendance.AttendanceStatus.JOINED
        attendance.save(update_fields=["joined_at", "status", "updated_at"])
        return attendance

    @staticmethod
    def mark_left(attendance: SessionAttendance) -> SessionAttendance:
        now = timezone.now()
        attendance.left_at = now
        if attendance.joined_at:
            attendance.duration_seconds = max(int((now - attendance.joined_at).total_seconds()), 0)
            attendance.status = SessionAttendance.AttendanceStatus.ATTENDED
        else:
            attendance.status = SessionAttendance.AttendanceStatus.LEFT
        attendance.save(update_fields=["left_at", "duration_seconds", "status", "updated_at"])
        return attendance
