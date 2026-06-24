from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.booking.models import BookingAttendance, BookingEvent, SessionReservation


class BookingAttendanceService:
    @staticmethod
    def ensure_for_reservation(reservation: SessionReservation) -> BookingAttendance:
        attendance, _ = BookingAttendance.objects.get_or_create(
            reservation=reservation,
            defaults={
                "trainer": reservation.trainer,
                "customer": reservation.customer,
                "status": BookingAttendance.STATUS_EXPECTED,
            },
        )
        return attendance

    @classmethod
    @transaction.atomic
    def check_in(
        cls,
        *,
        reservation: SessionReservation | None = None,
        token: str = "",
        external_identifier: str = "",
        method: str = BookingAttendance.METHOD_MANUAL,
        actor=None,
        metadata: dict | None = None,
    ) -> BookingAttendance:
        attendance = cls._resolve_attendance(
            reservation=reservation,
            token=token,
            external_identifier=external_identifier,
        )
        if attendance.status in {BookingAttendance.STATUS_NO_SHOW, BookingAttendance.STATUS_CANCELLED}:
            raise ValueError("Cannot check in cancelled or no-show attendance.")
        if not attendance.checked_in_at:
            attendance.checked_in_at = timezone.now()
        attendance.status = BookingAttendance.STATUS_CHECKED_IN
        attendance.checkin_method = method or BookingAttendance.METHOD_MANUAL
        if external_identifier:
            attendance.external_identifier = str(external_identifier).strip()
        attendance.metadata = {**(attendance.metadata or {}), **(metadata or {})}
        attendance.save(update_fields=[
            "status",
            "checkin_method",
            "external_identifier",
            "checked_in_at",
            "metadata",
            "updated_at",
        ])
        BookingEvent.objects.create(
            reservation=attendance.reservation,
            event_type="attendance_checked_in",
            actor=actor,
            payload={
                "attendance_id": str(attendance.id),
                "method": attendance.checkin_method,
                "checked_in_at": attendance.checked_in_at.isoformat() if attendance.checked_in_at else None,
            },
        )
        return attendance

    @classmethod
    @transaction.atomic
    def check_out(cls, *, attendance: BookingAttendance, actor=None) -> BookingAttendance:
        attendance = BookingAttendance.objects.select_for_update().select_related("reservation").get(pk=attendance.pk)
        now = timezone.now()
        attendance.checked_out_at = now
        if attendance.checked_in_at:
            attendance.duration_seconds = max(int((now - attendance.checked_in_at).total_seconds()), 0)
            attendance.status = BookingAttendance.STATUS_ATTENDED
        attendance.save(update_fields=["status", "checked_out_at", "duration_seconds", "updated_at"])
        BookingEvent.objects.create(
            reservation=attendance.reservation,
            event_type="attendance_checked_out",
            actor=actor,
            payload={"attendance_id": str(attendance.id), "duration_seconds": attendance.duration_seconds},
        )
        return attendance

    @classmethod
    @transaction.atomic
    def mark_no_show(cls, *, reservation: SessionReservation, actor=None, reason: str = "") -> BookingAttendance:
        attendance = cls.ensure_for_reservation(reservation)
        attendance = BookingAttendance.objects.select_for_update().select_related("reservation").get(pk=attendance.pk)
        if attendance.status == BookingAttendance.STATUS_ATTENDED:
            raise ValueError("Attended reservation cannot be marked no-show.")
        attendance.status = BookingAttendance.STATUS_NO_SHOW
        attendance.metadata = {**(attendance.metadata or {}), "no_show_reason": reason}
        attendance.save(update_fields=["status", "metadata", "updated_at"])
        BookingEvent.objects.create(
            reservation=attendance.reservation,
            event_type="attendance_no_show",
            actor=actor,
            payload={"attendance_id": str(attendance.id), "reason": reason},
        )
        return attendance

    @classmethod
    def _resolve_attendance(
        cls,
        *,
        reservation: SessionReservation | None = None,
        token: str = "",
        external_identifier: str = "",
    ) -> BookingAttendance:
        if reservation is not None:
            return cls.ensure_for_reservation(reservation)
        if token:
            return BookingAttendance.objects.select_for_update().select_related("reservation").get(checkin_token=token)
        if external_identifier:
            return BookingAttendance.objects.select_for_update().select_related("reservation").get(external_identifier=str(external_identifier).strip())
        raise ValueError("reservation, token or external_identifier is required.")
