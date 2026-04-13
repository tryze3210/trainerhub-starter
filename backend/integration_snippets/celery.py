from celery.schedules import crontab

app.conf.beat_schedule.update({
    "finance-documents-build-trainer-statements": {
        "task": "apps.finance_documents.tasks.build_monthly_trainer_statements",
        "schedule": crontab(hour=3, minute=20),
    },
})
