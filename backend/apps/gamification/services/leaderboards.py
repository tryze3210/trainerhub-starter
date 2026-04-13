from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.utils import timezone

from apps.gamification.models import AchievementLedger, LeaderboardSnapshot, UserBadge

User = get_user_model()


class LeaderboardSnapshotBuilder:
    def rebuild(self, *, period: str = 'weekly', cohort_id: str = '', limit: int = 50) -> int:
        today = timezone.now().date()
        if period == 'weekly':
            start = today - timedelta(days=7)
        elif period == 'monthly':
            start = today - timedelta(days=30)
        else:
            start = date(2000, 1, 1)

        LeaderboardSnapshot.objects.filter(period=period, snapshot_date=today, cohort_id=cohort_id).delete()
        rows = (
            AchievementLedger.objects.filter(created_at__date__gte=start)
            .values('user')
            .annotate(points=Sum('points_delta'))
            .order_by('-points', 'user')[:limit]
        )
        count = 0
        for idx, row in enumerate(rows, start=1):
            user_id = row['user']
            badge_count = UserBadge.objects.filter(user_id=user_id).count()
            LeaderboardSnapshot.objects.create(
                period=period,
                snapshot_date=today,
                rank=idx,
                user_id=user_id,
                points=row['points'] or 0,
                streak_days=0,
                badge_count=badge_count,
                cohort_id=cohort_id,
            )
            count += 1
        return count
