from django.urls import path

from apps.booking.api.views import (
    AdminBookingOverviewView,
    CreateReservationView,
    MyBookingProfileView,
    MyCalendarView,
    MyReservationsView,
)

urlpatterns = [
    path("me/profile/", MyBookingProfileView.as_view(), name="booking-me-profile"),
    path("me/calendar/", MyCalendarView.as_view(), name="booking-me-calendar"),
    path("me/reservations/", MyReservationsView.as_view(), name="booking-me-reservations"),
    path("reservations/create/", CreateReservationView.as_view(), name="booking-create-reservation"),
    path("admin/overview/", AdminBookingOverviewView.as_view(), name="booking-admin-overview"),
]
