from rest_framework import serializers

from apps.booking.models import AvailabilityRule, BookingAttendance, BookingProfile, BookingSlot, BookingWaitlistEntry, SessionReservation


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
    reservations_count = serializers.SerializerMethodField()
    waitlist_count = serializers.SerializerMethodField()

    class Meta:
        model = BookingSlot
        fields = ["id", "trainer", "starts_at", "ends_at", "status", "capacity", "source", "reservations_count", "waitlist_count"]

    def get_reservations_count(self, obj):
        return obj.reservations.filter(status=SessionReservation.STATUS_CONFIRMED).count()

    def get_waitlist_count(self, obj):
        return obj.waitlist_entries.filter(status=BookingWaitlistEntry.STATUS_WAITING).count()


class CreateReservationSerializer(serializers.Serializer):
    slot_id = serializers.UUIDField()
    title = serializers.CharField(max_length=255)
    notes = serializers.CharField(required=False, allow_blank=True)


class CancelReservationSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=1000)


class AttendanceCheckInSerializer(serializers.Serializer):
    reservation_id = serializers.UUIDField(required=False)
    token = serializers.UUIDField(required=False)
    external_identifier = serializers.CharField(required=False, allow_blank=True, max_length=128)
    method = serializers.ChoiceField(required=False, choices=BookingAttendance.METHOD_CHOICES, default=BookingAttendance.METHOD_MANUAL)

    def validate(self, attrs):
        if not attrs.get("reservation_id") and not attrs.get("token") and not attrs.get("external_identifier"):
            raise serializers.ValidationError("reservation_id, token or external_identifier is required.")
        return attrs


class AttendanceNoShowSerializer(serializers.Serializer):
    reservation_id = serializers.UUIDField()
    reason = serializers.CharField(required=False, allow_blank=True, max_length=1000)


class GenerateSlotsSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()


class WaitlistJoinSerializer(serializers.Serializer):
    slot_id = serializers.UUIDField()
    title = serializers.CharField(required=False, allow_blank=True, max_length=255)
    notes = serializers.CharField(required=False, allow_blank=True)


class SessionReservationSerializer(serializers.ModelSerializer):
    slot = BookingSlotSerializer()
    customer_email = serializers.EmailField(source="customer.email", read_only=True)
    customer_name = serializers.SerializerMethodField()
    attendance = serializers.SerializerMethodField()

    class Meta:
        model = SessionReservation
        fields = ["id", "status", "title", "notes", "slot", "customer_email", "customer_name", "attendance", "created_at"]

    def get_customer_name(self, obj):
        return obj.customer.get_full_name() or obj.customer.email

    def get_attendance(self, obj):
        attendance = getattr(obj, "attendance", None)
        if not attendance:
            return None
        return BookingAttendanceSerializer(attendance).data


class BookingAttendanceSerializer(serializers.ModelSerializer):
    reservation_id = serializers.UUIDField(source="reservation.id", read_only=True)
    customer_email = serializers.EmailField(source="customer.email", read_only=True)
    customer_name = serializers.SerializerMethodField()
    slot_starts_at = serializers.DateTimeField(source="reservation.slot.starts_at", read_only=True)
    slot_ends_at = serializers.DateTimeField(source="reservation.slot.ends_at", read_only=True)

    class Meta:
        model = BookingAttendance
        fields = [
            "id",
            "reservation_id",
            "customer_email",
            "customer_name",
            "checkin_token",
            "external_identifier",
            "status",
            "checkin_method",
            "checked_in_at",
            "checked_out_at",
            "duration_seconds",
            "slot_starts_at",
            "slot_ends_at",
            "metadata",
            "created_at",
            "updated_at",
        ]

    def get_customer_name(self, obj):
        return obj.customer.get_full_name() or obj.customer.email


class BookingWaitlistEntrySerializer(serializers.ModelSerializer):
    slot = BookingSlotSerializer()
    customer_email = serializers.EmailField(source="customer.email", read_only=True)
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = BookingWaitlistEntry
        fields = ["id", "status", "title", "notes", "slot", "customer_email", "customer_name", "created_at", "updated_at"]

    def get_customer_name(self, obj):
        return obj.customer.get_full_name() or obj.customer.email
