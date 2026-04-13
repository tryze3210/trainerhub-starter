from rest_framework import serializers

from apps.booking.models import AvailabilityRule, BookingProfile, BookingSlot, SessionReservation


class BookingProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingProfile
        fields = [
            "id", "timezone", "session_buffer_minutes", "min_notice_hours", "max_future_days", "is_active"
        ]


class AvailabilityRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilityRule
        fields = ["id", "weekday", "start_minute", "end_minute", "slot_size_minutes", "is_active"]


class BookingSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingSlot
        fields = ["id", "trainer", "starts_at", "ends_at", "status", "source"]


class CreateReservationSerializer(serializers.Serializer):
    slot_id = serializers.UUIDField()
    title = serializers.CharField(max_length=255)
    notes = serializers.CharField(required=False, allow_blank=True)


class SessionReservationSerializer(serializers.ModelSerializer):
    slot = BookingSlotSerializer()

    class Meta:
        model = SessionReservation
        fields = ["id", "status", "title", "notes", "slot", "created_at"]
