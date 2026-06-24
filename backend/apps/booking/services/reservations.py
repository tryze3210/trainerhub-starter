from django.db import transaction
from django.utils import timezone

from apps.booking.models import BookingEvent, BookingSlot, BookingWaitlistEntry, SessionReservation
from apps.booking.services.attendance import BookingAttendanceService


class ReservationService:
    @staticmethod
    def _confirmed_count(slot: BookingSlot) -> int:
        return slot.reservations.filter(status=SessionReservation.STATUS_CONFIRMED).count()

    @classmethod
    def _has_capacity(cls, slot: BookingSlot) -> bool:
        return cls._confirmed_count(slot) < max(1, slot.capacity)

    @staticmethod
    def _sync_slot_status(slot: BookingSlot) -> None:
        confirmed = slot.reservations.filter(status=SessionReservation.STATUS_CONFIRMED).count()
        next_status = BookingSlot.STATUS_RESERVED if confirmed >= max(1, slot.capacity) else BookingSlot.STATUS_OPEN
        if slot.status != next_status:
            slot.status = next_status
            slot.save(update_fields=["status", "updated_at"])

    @transaction.atomic
    def create_reservation(self, *, slot: BookingSlot, customer, title: str, notes: str = "") -> SessionReservation:
        slot = BookingSlot.objects.select_for_update().get(pk=slot.pk)
        if slot.status == BookingSlot.STATUS_CANCELLED:
            raise ValueError("Slot is cancelled")
        if not self._has_capacity(slot):
            raise ValueError("Slot is full")
        existing = SessionReservation.objects.filter(
            slot=slot,
            customer=customer,
            status__in=[SessionReservation.STATUS_PENDING, SessionReservation.STATUS_CONFIRMED],
        ).first()
        if existing:
            return existing
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
        BookingAttendanceService.ensure_for_reservation(reservation)
        self._sync_slot_status(slot)
        return reservation

    @transaction.atomic
    def join_waitlist(self, *, slot: BookingSlot, customer, title: str = "", notes: str = "") -> BookingWaitlistEntry:
        slot = BookingSlot.objects.select_for_update().get(pk=slot.pk)
        if self._has_capacity(slot):
            raise ValueError("Slot still has capacity. Create a reservation instead.")
        entry, _ = BookingWaitlistEntry.objects.get_or_create(
            slot=slot,
            customer=customer,
            status=BookingWaitlistEntry.STATUS_WAITING,
            defaults={
                "trainer": slot.trainer,
                "title": title,
                "notes": notes,
            },
        )
        return entry

    @transaction.atomic
    def cancel_reservation(self, *, reservation: SessionReservation, actor=None, reason: str = "") -> SessionReservation:
        reservation = SessionReservation.objects.select_for_update().select_related("slot").get(pk=reservation.pk)
        if reservation.status == SessionReservation.STATUS_CANCELLED:
            return reservation
        reservation.status = SessionReservation.STATUS_CANCELLED
        reservation.save(update_fields=["status", "updated_at"])
        attendance = BookingAttendanceService.ensure_for_reservation(reservation)
        attendance.status = "cancelled"
        attendance.save(update_fields=["status", "updated_at"])
        slot = reservation.slot
        BookingEvent.objects.create(
            reservation=reservation,
            event_type="reservation_cancelled",
            actor=actor,
            payload={"reason": reason},
        )
        promoted = self.promote_next_waitlist(slot=slot, actor=actor)
        if not promoted:
            self._sync_slot_status(slot)
        return reservation

    @transaction.atomic
    def promote_next_waitlist(self, *, slot: BookingSlot, actor=None) -> SessionReservation | None:
        slot = BookingSlot.objects.select_for_update().get(pk=slot.pk)
        if not self._has_capacity(slot):
            return None
        entry = (
            BookingWaitlistEntry.objects
            .select_for_update()
            .filter(slot=slot, status=BookingWaitlistEntry.STATUS_WAITING)
            .order_by("created_at")
            .first()
        )
        if not entry:
            return None
        reservation = SessionReservation.objects.create(
            slot=slot,
            trainer=slot.trainer,
            customer=entry.customer,
            status=SessionReservation.STATUS_CONFIRMED,
            title=entry.title or "Promoted from waitlist",
            notes=entry.notes,
        )
        entry.status = BookingWaitlistEntry.STATUS_PROMOTED
        entry.promoted_reservation = reservation
        entry.save(update_fields=["status", "promoted_reservation", "updated_at"])
        BookingEvent.objects.create(
            reservation=reservation,
            event_type="reservation_promoted_from_waitlist",
            actor=actor,
            payload={"waitlist_entry_id": str(entry.id), "starts_at": slot.starts_at.isoformat()},
        )
        BookingAttendanceService.ensure_for_reservation(reservation)
        self._sync_slot_status(slot)
        return reservation
