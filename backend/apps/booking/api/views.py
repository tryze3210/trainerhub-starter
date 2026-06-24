from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, response, status, views

from apps.booking.api.serializers import (
    AvailabilityRuleSerializer,
    AttendanceCheckInSerializer,
    AttendanceNoShowSerializer,
    BookingAttendanceSerializer,
    BookingProfileSerializer,
    BookingSlotSerializer,
    BookingWaitlistEntrySerializer,
    CancelReservationSerializer,
    CreateReservationSerializer,
    GenerateSlotsSerializer,
    SessionReservationSerializer,
    WaitlistJoinSerializer,
)
from apps.booking.models import AvailabilityRule, BookingAttendance, BookingProfile, BookingSlot, BookingWaitlistEntry, SessionReservation
from apps.booking.selectors.calendar import BookingSelectors
from apps.booking.services.attendance import BookingAttendanceService
from apps.booking.services.reservations import ReservationService
from apps.booking.services.slot_generator import SlotGenerationService


class MyBookingProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = BookingProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj, _ = BookingProfile.objects.get_or_create(trainer=self.request.user)
        return obj


class MyCalendarView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        start = timezone.now()
        end = start + timedelta(days=14)
        slots = BookingSelectors.trainer_calendar(request.user, start, end)
        return response.Response(BookingSlotSerializer(slots, many=True).data)


class MyAvailabilityRulesView(generics.ListCreateAPIView):
    serializer_class = AvailabilityRuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AvailabilityRule.objects.filter(trainer=self.request.user).order_by("weekday", "start_minute")

    def perform_create(self, serializer):
        serializer.save(trainer=self.request.user)


class GenerateSlotsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = GenerateSlotsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        BookingProfile.objects.get_or_create(trainer=request.user)
        result = SlotGenerationService(request.user).generate_range(
            serializer.validated_data["start_date"],
            serializer.validated_data["end_date"],
        )
        return response.Response({"created": result.created, "existing": result.existing})


class TrainerScheduleView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        start = timezone.now()
        end = start + timedelta(days=int(request.query_params.get("days", 30) or 30))
        slots = BookingSelectors.trainer_calendar(request.user, start, end)
        reservations = (
            SessionReservation.objects
            .filter(trainer=request.user, slot__starts_at__gte=start, slot__starts_at__lt=end)
            .select_related("slot", "customer", "attendance")
            .order_by("slot__starts_at")
        )
        waitlist = (
            BookingWaitlistEntry.objects
            .filter(trainer=request.user, slot__starts_at__gte=start, slot__starts_at__lt=end)
            .select_related("slot", "customer")
            .order_by("slot__starts_at", "created_at")
        )
        attendance = (
            BookingAttendance.objects
            .filter(trainer=request.user, reservation__slot__starts_at__gte=start, reservation__slot__starts_at__lt=end)
            .select_related("reservation", "reservation__slot", "customer")
            .order_by("reservation__slot__starts_at")
        )
        profile, _ = BookingProfile.objects.get_or_create(trainer=request.user)
        return response.Response({
            "profile": BookingProfileSerializer(profile).data,
            "slots": BookingSlotSerializer(slots, many=True).data,
            "reservations": SessionReservationSerializer(reservations, many=True).data,
            "attendance": BookingAttendanceSerializer(attendance, many=True).data,
            "waitlist": BookingWaitlistEntrySerializer(waitlist, many=True).data,
            "summary": {
                "slots_total": slots.count(),
                "slots_open": slots.filter(status=BookingSlot.STATUS_OPEN).count(),
                "reservations_confirmed": reservations.filter(status=SessionReservation.STATUS_CONFIRMED).count(),
                "attendance_checked_in": attendance.filter(status__in=[BookingAttendance.STATUS_CHECKED_IN, BookingAttendance.STATUS_ATTENDED]).count(),
                "attendance_no_show": attendance.filter(status=BookingAttendance.STATUS_NO_SHOW).count(),
                "waitlist_waiting": waitlist.filter(status=BookingWaitlistEntry.STATUS_WAITING).count(),
            },
        })


class PublicOpenSlotsView(generics.ListAPIView):
    serializer_class = BookingSlotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = BookingSlot.objects.filter(starts_at__gte=timezone.now(), status=BookingSlot.STATUS_OPEN).order_by("starts_at")
        trainer_id = self.request.query_params.get("trainer_id")
        if trainer_id:
            queryset = queryset.filter(trainer_id=trainer_id)
        return queryset[:100]


class CreateReservationView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CreateReservationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        slot = get_object_or_404(BookingSlot, id=serializer.validated_data["slot_id"])
        try:
            reservation = ReservationService().create_reservation(
                slot=slot,
                customer=request.user,
                title=serializer.validated_data["title"],
                notes=serializer.validated_data.get("notes", ""),
            )
        except ValueError as exc:
            return response.Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return response.Response(SessionReservationSerializer(reservation).data, status=status.HTTP_201_CREATED)


class JoinWaitlistView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = WaitlistJoinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        slot = get_object_or_404(BookingSlot, id=serializer.validated_data["slot_id"])
        try:
            entry = ReservationService().join_waitlist(
                slot=slot,
                customer=request.user,
                title=serializer.validated_data.get("title", ""),
                notes=serializer.validated_data.get("notes", ""),
            )
        except ValueError as exc:
            return response.Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return response.Response(BookingWaitlistEntrySerializer(entry).data, status=status.HTTP_201_CREATED)


class MyReservationsView(generics.ListAPIView):
    serializer_class = SessionReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SessionReservation.objects.filter(customer=self.request.user).select_related("slot").order_by("-created_at")


class CancelReservationView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, reservation_id):
        serializer = CancelReservationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reservation = get_object_or_404(SessionReservation, id=reservation_id)
        if reservation.customer_id != request.user.id and reservation.trainer_id != request.user.id and not request.user.is_staff:
            return response.Response({"detail": "You do not have access to this reservation."}, status=status.HTTP_403_FORBIDDEN)
        reservation = ReservationService().cancel_reservation(
            reservation=reservation,
            actor=request.user,
            reason=serializer.validated_data.get("reason", ""),
        )
        return response.Response(SessionReservationSerializer(reservation).data)


class AttendanceHistoryView(generics.ListAPIView):
    serializer_class = BookingAttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = (
            BookingAttendance.objects
            .select_related("reservation", "reservation__slot", "customer", "trainer")
            .order_by("-created_at")
        )
        if self.request.user.is_staff:
            return queryset[:200]
        return queryset.filter(trainer=self.request.user)[:200]


class AttendanceCheckInView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AttendanceCheckInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reservation = None
        reservation_id = serializer.validated_data.get("reservation_id")
        if reservation_id:
            reservation = get_object_or_404(SessionReservation, id=reservation_id)
            if reservation.trainer_id != request.user.id and reservation.customer_id != request.user.id and not request.user.is_staff:
                return response.Response({"detail": "You do not have access to this reservation."}, status=status.HTTP_403_FORBIDDEN)
        try:
            attendance = BookingAttendanceService.check_in(
                reservation=reservation,
                token=str(serializer.validated_data.get("token") or ""),
                external_identifier=serializer.validated_data.get("external_identifier", ""),
                method=serializer.validated_data.get("method", BookingAttendance.METHOD_MANUAL),
                actor=request.user,
            )
        except (BookingAttendance.DoesNotExist, ValueError) as exc:
            return response.Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if attendance.trainer_id != request.user.id and attendance.customer_id != request.user.id and not request.user.is_staff:
            return response.Response({"detail": "You do not have access to this attendance."}, status=status.HTTP_403_FORBIDDEN)
        return response.Response(BookingAttendanceSerializer(attendance).data)


class AttendanceCheckOutView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, attendance_id):
        attendance = get_object_or_404(BookingAttendance, id=attendance_id)
        if attendance.trainer_id != request.user.id and not request.user.is_staff:
            return response.Response({"detail": "Only the trainer can check out attendance."}, status=status.HTTP_403_FORBIDDEN)
        attendance = BookingAttendanceService.check_out(attendance=attendance, actor=request.user)
        return response.Response(BookingAttendanceSerializer(attendance).data)


class AttendanceNoShowView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AttendanceNoShowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reservation = get_object_or_404(SessionReservation, id=serializer.validated_data["reservation_id"])
        if reservation.trainer_id != request.user.id and not request.user.is_staff:
            return response.Response({"detail": "Only the trainer can mark no-show."}, status=status.HTTP_403_FORBIDDEN)
        try:
            attendance = BookingAttendanceService.mark_no_show(
                reservation=reservation,
                actor=request.user,
                reason=serializer.validated_data.get("reason", ""),
            )
        except ValueError as exc:
            return response.Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return response.Response(BookingAttendanceSerializer(attendance).data)


class AdminBookingOverviewView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        end = timezone.now()
        start = end - timedelta(days=30)
        return response.Response(BookingSelectors.admin_overview(start, end))
