import uuid
from django.conf import settings
from django.db import models


class LiveSession(models.Model):
    class SessionType(models.TextChoices):
        WEBINAR = "webinar", "Webinar"
        GROUP_CLASS = "group_class", "Group class"
        WORKSHOP = "workshop", "Workshop"

    class SessionStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        SCHEDULED = "scheduled", "Scheduled"
        LIVE = "live", "Live"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trainer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="live_sessions")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    session_type = models.CharField(max_length=32, choices=SessionType.choices, default=SessionType.WEBINAR)
    status = models.CharField(max_length=32, choices=SessionStatus.choices, default=SessionStatus.DRAFT)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    capacity = models.PositiveIntegerField(default=100)
    booking_reservation_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "live_sessions_live_session"
        ordering = ["starts_at"]
