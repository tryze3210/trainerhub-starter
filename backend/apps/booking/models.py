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
    slot = models.OneToOneField(BookingSlot, on_delete=models.PROTECT, related_name="reservation")
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
