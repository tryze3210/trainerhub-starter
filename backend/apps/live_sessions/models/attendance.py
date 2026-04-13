import uuid
from django.conf import settings
from django.db import models


class SessionAttendance(models.Model):
    class AttendanceStatus(models.TextChoices):
        REGISTERED = "registered", "Registered"
        JOINED = "joined", "Joined"
        LEFT = "left", "Left"
        ATTENDED = "attended", "Attended"
        NO_SHOW = "no_show", "No show"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    live_session_id = models.UUIDField(db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="session_attendances")
    reservation_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=AttendanceStatus.choices, default=AttendanceStatus.REGISTERED)
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "live_sessions_session_attendance"
        unique_together = [("live_session_id", "user")]
