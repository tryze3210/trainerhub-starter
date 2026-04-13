from django.db.models import Count

from apps.gamification.models import AchievementLedger, LeaderboardSnapshot, UserBadge, UserRewardBalance


class GamificationDashboardSelector:
    def user_dashboard(self, *, user):
        balance = UserRewardBalance.objects.filter(user=user).first()
        badges = UserBadge.objects.filter(user=user).select_related('badge')[:12]
        recent = AchievementLedger.objects.filter(user=user).select_related('reward_rule')[:20]
        rank_row = LeaderboardSnapshot.objects.filter(user=user, period='weekly').order_by('-snapshot_date').first()
        return {
            'balance': {
                'total_points': getattr(balance, 'total_points', 0),
                'lifetime_points': getattr(balance, 'lifetime_points', 0),
                'level': getattr(balance, 'level', 1),
                'weekly_rank': getattr(rank_row, 'rank', None),
            },
            'badges': [
                {'code': item.badge.code, 'title': item.badge.title, 'awarded_at': item.awarded_at}
                for item in badges
            ],
            'recent_activity': [
                {
                    'event_type': item.event_type,
                    'points_delta': item.points_delta,
                    'created_at': item.created_at,
                    'reward_rule': getattr(item.reward_rule, 'code', None),
                }
                for item in recent
            ],
        }

    def admin_overview(self):
        return {
            'ledger_entries': AchievementLedger.objects.count(),
            'awarded_badges': UserBadge.objects.count(),
            'active_players': UserRewardBalance.objects.count(),
            'latest_weekly_rows': LeaderboardSnapshot.objects.filter(period='weekly').count(),
        }
