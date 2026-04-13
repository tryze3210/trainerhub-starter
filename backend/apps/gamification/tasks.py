from celery import shared_task

from apps.gamification.services.leaderboards import LeaderboardSnapshotBuilder


@shared_task(name='gamification.rebuild_weekly_leaderboard')
def rebuild_weekly_leaderboard():
    return LeaderboardSnapshotBuilder().rebuild(period='weekly')


@shared_task(name='gamification.rebuild_monthly_leaderboard')
def rebuild_monthly_leaderboard():
    return LeaderboardSnapshotBuilder().rebuild(period='monthly')
