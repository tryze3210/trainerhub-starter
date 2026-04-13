from celery.schedules import crontab

CELERY_BEAT_SCHEDULE.update(
    {
        "referrals-process-pending-rewards": {
            "task": "apps.referrals.tasks.process_pending_rewards",
            "schedule": crontab(minute="*/30"),
        },
        "referrals-expire-invites": {
            "task": "apps.referrals.tasks.expire_invites",
            "schedule": crontab(minute=15, hour=2),
        },
    }
)
