from celery.schedules import crontab

CELERY_BEAT_SCHEDULE.update({
    'gamification-rebuild-weekly-leaderboard-hourly': {
        'task': 'gamification.rebuild_weekly_leaderboard',
        'schedule': crontab(minute=10),
    },
    'gamification-rebuild-monthly-leaderboard-nightly': {
        'task': 'gamification.rebuild_monthly_leaderboard',
        'schedule': crontab(minute=30, hour=2),
    },
})
