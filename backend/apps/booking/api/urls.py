from django.urls import path

from apps.booking.api.views import (
    AdminBookingOverviewView,
    AttendanceCheckInView,
    AttendanceCheckOutView,
    AttendanceHistoryView,
    AttendanceNoShowView,
    CancelReservationView,
    CreateReservationView,
    GenerateSlotsView,
    JoinWaitlistView,
    MyAvailabilityRulesView,
    MyBookingProfileView,
    MyCalendarView,
    MyReservationsView,
    PublicOpenSlotsView,
    TrainerScheduleView,
)

urlpatterns = [
    path("me/profile/", MyBookingProfileView.as_view(), name="booking-me-profile"),
    path("me/availability-rules/", MyAvailabilityRulesView.as_view(), name="booking-me-availability-rules"),
    path("me/calendar/", MyCalendarView.as_view(), name="booking-me-calendar"),
    path("me/generate-slots/", GenerateSlotsView.as_view(), name="booking-me-generate-slots"),
    path("me/schedule/", TrainerScheduleView.as_view(), name="booking-me-schedule"),
    path("me/reservations/", MyReservationsView.as_view(), name="booking-me-reservations"),
    path("slots/open/", PublicOpenSlotsView.as_view(), name="booking-open-slots"),
    path("reservations/create/", CreateReservationView.as_view(), name="booking-create-reservation"),
    path("reservations/waitlist/", JoinWaitlistView.as_view(), name="booking-join-waitlist"),
    path("reservations/<uuid:reservation_id>/cancel/", CancelReservationView.as_view(), name="booking-cancel-reservation"),
    path("attendance/", AttendanceHistoryView.as_view(), name="booking-attendance-history"),
    path("attendance/check-in/", AttendanceCheckInView.as_view(), name="booking-attendance-check-in"),
    path("attendance/check-out/<uuid:attendance_id>/", AttendanceCheckOutView.as_view(), name="booking-attendance-check-out"),
    path("attendance/no-show/", AttendanceNoShowView.as_view(), name="booking-attendance-no-show"),
    path("admin/overview/", AdminBookingOverviewView.as_view(), name="booking-admin-overview"),
]
