from rest_framework import serializers
from apps.live_sessions.models import LiveSession, SessionAttendance


class LiveSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveSession
        fields = [
            "id", "title", "description", "session_type", "status",
            "starts_at", "ends_at", "capacity", "booking_reservation_id",
        ]


class SessionAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionAttendance
        fields = [
            "id", "live_session_id", "user", "reservation_id", "status",
            "joined_at", "left_at", "duration_seconds",
        ]
        read_only_fields = fields
