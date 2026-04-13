from celery.schedules import crontab

CELERY_BEAT_SCHEDULE.update({
    "live-generate-upcoming-reminders": {
        "task": "live_sessions.generate_upcoming_reminders",
        "schedule": crontab(minute="*/15"),
    },
    "live-mark-no-shows": {
        "task": "live_sessions.mark_no_shows",
        "schedule": crontab(minute=10, hour="*"),
    },
})
