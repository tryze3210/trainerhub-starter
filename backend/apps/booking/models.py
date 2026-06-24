import uuid
from django.conf import settings
from django.db import models


class BookingProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trainer = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="booking_profile")
    timezone = models.CharField(max_length=64, default="Europe/Berlin")
    session_buffer_minutes = models.PositiveIntegerField(default=15)
    min_notice_hours = models.PositiveIntegerField(default=12)
    max_future_days = models.PositiveIntegerField(default=45)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AvailabilityRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trainer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="availability_rules")
    weekday = models.PositiveSmallIntegerField()
    start_minute = models.PositiveIntegerField()
    end_minute = models.PositiveIntegerField()
    slot_size_minutes = models.PositiveIntegerField(default=60)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AvailabilityException(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trainer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="availability_exceptions")
    date = models.DateField()
    is_blocked = models.BooleanField(default=True)
    start_minute = models.PositiveIntegerField(null=True, blank=True)
    end_minute = models.PositiveIntegerField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class BookingSlot(models.Model):
    STATUS_OPEN = "open"
    STATUS_HELD = "held"
    STATUS_RESERVED = "reserved"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_HELD, "Held"),
        (STATUS_RESERVED, "Reserved"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trainer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="booking_slots")
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_OPEN, db_index=True)
    capacity = models.PositiveIntegerField(default=1)
    source = models.CharField(max_length=32, default="generated")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["trainer", "starts_at", "status"])]
        constraints = [
            models.UniqueConstraint(fields=["trainer", "starts_at"], name="uniq_booking_slot_per_trainer_start")
        ]


class SessionReservation(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_CANCELLED = "cancelled"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_COMPLETED, "Completed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slot = models.ForeignKey(BookingSlot, on_delete=models.PROTECT, related_name="reservations")
    trainer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="session_reservations_as_trainer")
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="session_reservations_as_customer")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    title = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    external_ref = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class BookingEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reservation = models.ForeignKey(SessionReservation, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=64)
    payload = models.JSONField(default=dict, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class BookingWaitlistEntry(models.Model):
    STATUS_WAITING = "waiting"
    STATUS_PROMOTED = "promoted"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_WAITING, "Waiting"),
        (STATUS_PROMOTED, "Promoted"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slot = models.ForeignKey(BookingSlot, on_delete=models.CASCADE, related_name="waitlist_entries")
    trainer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="booking_waitlist_as_trainer")
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="booking_waitlist_as_customer")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_WAITING, db_index=True)
    title = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    promoted_reservation = models.ForeignKey(SessionReservation, on_delete=models.SET_NULL, null=True, blank=True, related_name="waitlist_source")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["slot", "status", "created_at"])]
        constraints = [
            models.UniqueConstraint(fields=["slot", "customer", "status"], name="uniq_waiting_customer_per_slot")
        ]


class BookingAttendance(models.Model):
    STATUS_EXPECTED = "expected"
    STATUS_CHECKED_IN = "checked_in"
    STATUS_ATTENDED = "attended"
    STATUS_NO_SHOW = "no_show"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_EXPECTED, "Expected"),
        (STATUS_CHECKED_IN, "Checked in"),
        (STATUS_ATTENDED, "Attended"),
        (STATUS_NO_SHOW, "No show"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    METHOD_MANUAL = "manual"
    METHOD_QR = "qr"
    METHOD_MIFARE = "mifare"
    METHOD_EXTERNAL = "external"
    METHOD_CHOICES = [
        (METHOD_MANUAL, "Manual"),
        (METHOD_QR, "QR"),
        (METHOD_MIFARE, "Mifare"),
        (METHOD_EXTERNAL, "External"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reservation = models.OneToOneField(SessionReservation, on_delete=models.CASCADE, related_name="attendance")
    trainer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="booking_attendance_as_trainer")
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="booking_attendance_as_customer")
    checkin_token = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    external_identifier = models.CharField(max_length=128, blank=True, db_index=True)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_EXPECTED, db_index=True)
    checkin_method = models.CharField(max_length=24, choices=METHOD_CHOICES, default=METHOD_MANUAL)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["trainer", "status", "checked_in_at"], name="booking_att_trainer_status_idx"),
            models.Index(fields=["customer", "created_at"], name="booking_att_customer_idx"),
        ]
