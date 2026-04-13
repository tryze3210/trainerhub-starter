from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, response, status, views

from apps.booking.api.serializers import (
    BookingProfileSerializer,
    BookingSlotSerializer,
    CreateReservationSerializer,
    SessionReservationSerializer,
)
from apps.booking.models import BookingProfile, BookingSlot, SessionReservation
from apps.booking.selectors.calendar import BookingSelectors
from apps.booking.services.reservations import ReservationService


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


class CreateReservationView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CreateReservationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        slot = get_object_or_404(BookingSlot, id=serializer.validated_data["slot_id"])
        reservation = ReservationService().create_reservation(
            slot=slot,
            customer=request.user,
            title=serializer.validated_data["title"],
            notes=serializer.validated_data.get("notes", ""),
        )
        return response.Response(SessionReservationSerializer(reservation).data, status=status.HTTP_201_CREATED)


class MyReservationsView(generics.ListAPIView):
    serializer_class = SessionReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SessionReservation.objects.filter(customer=self.request.user).select_related("slot").order_by("-created_at")


class AdminBookingOverviewView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        end = timezone.now()
        start = end - timedelta(days=30)
        return response.Response(BookingSelectors.admin_overview(start, end))
