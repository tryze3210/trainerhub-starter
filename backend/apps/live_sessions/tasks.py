from celery import shared_task


@shared_task(name="live_sessions.generate_upcoming_reminders")
def generate_upcoming_reminders():
    return {"ok": True, "task": "generate_upcoming_reminders"}


@shared_task(name="live_sessions.mark_no_shows")
def mark_no_shows():
    return {"ok": True, "task": "mark_no_shows"}
