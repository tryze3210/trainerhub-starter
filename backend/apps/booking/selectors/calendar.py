from django.db.models import Count

from apps.booking.models import BookingSlot, SessionReservation


class BookingSelectors:
    @staticmethod
    def trainer_calendar(trainer, start, end):
        return BookingSlot.objects.filter(trainer=trainer, starts_at__gte=start, starts_at__lt=end).order_by("starts_at")

    @staticmethod
    def admin_overview(start, end):
        return {
            "slots_total": BookingSlot.objects.filter(starts_at__gte=start, starts_at__lt=end).count(),
            "slots_open": BookingSlot.objects.filter(starts_at__gte=start, starts_at__lt=end, status=BookingSlot.STATUS_OPEN).count(),
            "reservations_total": SessionReservation.objects.filter(created_at__gte=start, created_at__lt=end).count(),
            "reservations_by_status": list(
                SessionReservation.objects.filter(created_at__gte=start, created_at__lt=end)
                .values("status")
                .annotate(total=Count("id"))
                .order_by("status")
            ),
        }
