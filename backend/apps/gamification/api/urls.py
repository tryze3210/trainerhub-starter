from django.urls import path

from apps.gamification.api.views import (
    AdminGamificationOverviewAPIView,
    AdminRebuildLeaderboardsAPIView,
    AdminRewardRulesAPIView,
    MeGamificationDashboardAPIView,
    MeLeaderboardAPIView,
)

urlpatterns = [
    path('me/dashboard/', MeGamificationDashboardAPIView.as_view(), name='gamification-me-dashboard'),
    path('me/leaderboard/', MeLeaderboardAPIView.as_view(), name='gamification-me-leaderboard'),
    path('admin/overview/', AdminGamificationOverviewAPIView.as_view(), name='gamification-admin-overview'),
    path('admin/reward-rules/', AdminRewardRulesAPIView.as_view(), name='gamification-admin-reward-rules'),
    path('admin/leaderboards/rebuild/', AdminRebuildLeaderboardsAPIView.as_view(), name='gamification-admin-leaderboards-rebuild'),
]
