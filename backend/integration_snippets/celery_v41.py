from celery.schedules import crontab

CELERY_BEAT_SCHEDULE.update({
    "booking-generate-rolling-slots-nightly": {
        "task": "apps.booking.tasks.generate_rolling_slots",
        "schedule": crontab(minute=10, hour=2),
    },
})
