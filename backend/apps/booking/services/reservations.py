from django.db import transaction
from django.utils import timezone

from apps.booking.models import BookingEvent, BookingSlot, SessionReservation


class ReservationService:
    @transaction.atomic
    def create_reservation(self, *, slot: BookingSlot, customer, title: str, notes: str = "") -> SessionReservation:
        if slot.status != BookingSlot.STATUS_OPEN:
            raise ValueError("Slot is not open")
        slot.status = BookingSlot.STATUS_RESERVED
        slot.save(update_fields=["status", "updated_at"])
        reservation = SessionReservation.objects.create(
            slot=slot,
            trainer=slot.trainer,
            customer=customer,
            status=SessionReservation.STATUS_CONFIRMED,
            title=title,
            notes=notes,
        )
        BookingEvent.objects.create(
            reservation=reservation,
            event_type="reservation_confirmed",
            actor=customer,
            payload={"starts_at": slot.starts_at.isoformat(), "created_at": timezone.now().isoformat()},
        )
        return reservation

    @transaction.atomic
    def cancel_reservation(self, *, reservation: SessionReservation, actor=None, reason: str = "") -> SessionReservation:
        reservation.status = SessionReservation.STATUS_CANCELLED
        reservation.save(update_fields=["status", "updated_at"])
        slot = reservation.slot
        slot.status = BookingSlot.STATUS_OPEN
        slot.save(update_fields=["status", "updated_at"])
        BookingEvent.objects.create(
            reservation=reservation,
            event_type="reservation_cancelled",
            actor=actor,
            payload={"reason": reason},
        )
        return reservation
