from django.conf import settings
from django.db import models
import uuid


class BookingPaymentLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reservation_id = models.UUIDField(db_index=True)
    order_id = models.UUIDField(null=True, blank=True, db_index=True)
    payment_id = models.UUIDField(null=True, blank=True, db_index=True)
    checkout_status = models.CharField(max_length=32, default="pending", db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=8, default="RUB")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "booking_payment_links"


class CancellationPolicy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trainer_id = models.UUIDField(db_index=True)
    title = models.CharField(max_length=255)
    refund_percent_before_24h = models.PositiveSmallIntegerField(default=100)
    refund_percent_before_3h = models.PositiveSmallIntegerField(default=50)
    refund_percent_after_window = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "booking_cancellation_policies"


class ReservationCancellation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reservation_id = models.UUIDField(db_index=True)
    cancelled_by_user_id = models.UUIDField(null=True, blank=True)
    reason = models.TextField(blank=True, default="")
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    refund_status = models.CharField(max_length=32, default="not_requested", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reservation_cancellations"


class CalendarInviteDelivery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reservation_id = models.UUIDField(db_index=True)
    recipient_email = models.EmailField()
    delivery_channel = models.CharField(max_length=32, default="email")
    delivery_status = models.CharField(max_length=32, default="pending", db_index=True)
    ics_artifact_path = models.CharField(max_length=1024, blank=True, default="")
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "calendar_invite_deliveries"
