from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "booking-remind-upcoming-sessions": {
        "task": "apps.booking.tasks.send_upcoming_session_reminders",
        "schedule": crontab(minute="*/15"),
    },
    "booking-expire-pending-checkouts": {
        "task": "apps.booking.tasks.expire_pending_booking_checkouts",
        "schedule": crontab(minute="*/10"),
    },
}
