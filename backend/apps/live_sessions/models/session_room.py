import uuid
from django.db import models


class SessionRoom(models.Model):
    class Provider(models.TextChoices):
        INTERNAL = "internal", "Internal"
        JITSI = "jitsi", "Jitsi"
        ZOOM = "zoom", "Zoom"
        YOUTUBE = "youtube", "YouTube"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    live_session_id = models.UUIDField(unique=True)
    provider = models.CharField(max_length=32, choices=Provider.choices, default=Provider.INTERNAL)
    room_key = models.CharField(max_length=255, unique=True)
    join_url = models.URLField(blank=True)
    host_url = models.URLField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "live_sessions_session_room"
