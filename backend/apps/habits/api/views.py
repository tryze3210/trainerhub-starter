from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class MyHabitPlansView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"results": []})


class MyHabitDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "active_habits": 0,
            "completion_rate_7d": "0.00",
            "aggregate_current_streak": 0,
        })


class SubmitDailyCheckInView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({"status": "accepted"})


class MyJournalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"results": []})

    def post(self, request):
        return Response({"status": "created"})


class AdminHabitOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "tracked_users": 0,
            "active_habit_plans": 0,
            "avg_completion_rate_7d": "0.00",
        })
