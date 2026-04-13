from celery.schedules import crontab

CELERY_BEAT_SCHEDULE.update(
    {
        "disputes-sync-open-chargebacks-hourly": {
            "task": "disputes.sync_open_chargebacks",
            "schedule": crontab(minute=15),
        },
        "disputes-sla-escalation-sweep-every-30-min": {
            "task": "disputes.sla_escalation_sweep",
            "schedule": crontab(minute="*/30"),
        },
    }
)
