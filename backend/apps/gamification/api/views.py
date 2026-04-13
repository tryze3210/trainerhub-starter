from rest_framework import permissions, response, status, views

from apps.gamification.api.serializers import LeaderboardSnapshotSerializer, RewardRuleSerializer
from apps.gamification.models import LeaderboardSnapshot, RewardRule
from apps.gamification.selectors.dashboard import GamificationDashboardSelector
from apps.gamification.services.leaderboards import LeaderboardSnapshotBuilder


class MeGamificationDashboardAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = GamificationDashboardSelector().user_dashboard(user=request.user)
        return response.Response(data)


class MeLeaderboardAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        period = request.query_params.get('period', 'weekly')
        qs = LeaderboardSnapshot.objects.filter(period=period).select_related('user').order_by('-snapshot_date', 'rank')[:50]
        return response.Response(LeaderboardSnapshotSerializer(qs, many=True).data)


class AdminGamificationOverviewAPIView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        return response.Response(GamificationDashboardSelector().admin_overview())


class AdminRewardRulesAPIView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        return response.Response(RewardRuleSerializer(RewardRule.objects.all(), many=True).data)


class AdminRebuildLeaderboardsAPIView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        period = request.data.get('period', 'weekly')
        rebuilt = LeaderboardSnapshotBuilder().rebuild(period=period)
        return response.Response({'status': 'ok', 'period': period, 'rebuilt_rows': rebuilt}, status=status.HTTP_202_ACCEPTED)
