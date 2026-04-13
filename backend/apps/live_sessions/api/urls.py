from django.urls import path
from apps.live_sessions.api.views import (
    AdminLiveOverviewView,
    MyAttendanceView,
    MyLiveSessionsView,
    ScheduleAttendanceRemindersView,
    SessionRoomEnsureView,
)

urlpatterns = [
    path("me/sessions/", MyLiveSessionsView.as_view(), name="live-me-sessions"),
    path("me/attendance/", MyAttendanceView.as_view(), name="live-me-attendance"),
    path("me/attendance/<uuid:attendance_id>/schedule-reminders/", ScheduleAttendanceRemindersView.as_view(), name="live-attendance-reminders"),
    path("me/sessions/<uuid:session_id>/ensure-room/", SessionRoomEnsureView.as_view(), name="live-ensure-room"),
    path("admin/overview/", AdminLiveOverviewView.as_view(), name="live-admin-overview"),
]
