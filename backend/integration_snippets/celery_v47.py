from celery.schedules import crontab

CELERY_BEAT_SCHEDULE |= {
    "habits-rebuild-snapshots-hourly": {
        "task": "habits.rebuild_snapshots",
        "schedule": crontab(minute=10, hour="*"),
    },
    "habits-schedule-due-reminders-every-15m": {
        "task": "habits.schedule_due_reminders",
        "schedule": crontab(minute="*/15"),
    },
    "habits-expire-missed-checkins-nightly": {
        "task": "habits.expire_missed_checkins",
        "schedule": crontab(minute=20, hour=1),
    },
}
