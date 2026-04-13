from rest_framework import generics, permissions, response, status, views
from apps.live_sessions.api.serializers import LiveSessionSerializer, SessionAttendanceSerializer
from apps.live_sessions.models import LiveSession, SessionAttendance
from apps.live_sessions.selectors.dashboard import LiveSessionDashboardSelector
from apps.live_sessions.services.reminder_service import ReminderOrchestrationService
from apps.live_sessions.services.session_room_service import SessionRoomService


class MyLiveSessionsView(generics.ListAPIView):
    serializer_class = LiveSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LiveSession.objects.filter(trainer=self.request.user).order_by("starts_at")


class AdminLiveOverviewView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        return response.Response(LiveSessionDashboardSelector.admin_overview())


class SessionRoomEnsureView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, session_id):
        session = LiveSession.objects.get(id=session_id, trainer=request.user)
        room = SessionRoomService.ensure_room(session)
        return response.Response({
            "session_id": str(session.id),
            "room_id": str(room.id),
            "provider": room.provider,
            "join_url": room.join_url,
            "host_url": room.host_url,
        })


class MyAttendanceView(generics.ListAPIView):
    serializer_class = SessionAttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SessionAttendance.objects.filter(user=self.request.user).order_by("-created_at")


class ScheduleAttendanceRemindersView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, attendance_id):
        attendance = SessionAttendance.objects.get(id=attendance_id, user=request.user)
        created = ReminderOrchestrationService.schedule_for_attendance(attendance)
        return response.Response({"scheduled": created}, status=status.HTTP_200_OK)
