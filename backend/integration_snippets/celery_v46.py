from celery.schedules import crontab

CELERY_BEAT_SCHEDULE.update(
    {
        "cohorts-rebuild-dashboards-nightly": {
            "task": "cohorts.rebuild_all_dashboards",
            "schedule": crontab(hour=2, minute=25),
        }
    }
)
