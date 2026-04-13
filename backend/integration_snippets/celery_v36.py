from celery.schedules import crontab

CELERY_BEAT_SCHEDULE.update({
    "build-monthly-trainer-statements": {
        "task": "apps.finance_documents.tasks.build_monthly_trainer_statements",
        "schedule": crontab(hour=2, minute=10, day_of_month=1),
    },
})
