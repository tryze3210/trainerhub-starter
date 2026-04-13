from celery import shared_task


@shared_task(name="habits.rebuild_snapshots")
def rebuild_snapshots():
    return {"status": "ok"}


@shared_task(name="habits.schedule_due_reminders")
def schedule_due_reminders():
    return {"status": "ok"}


@shared_task(name="habits.expire_missed_checkins")
def expire_missed_checkins():
    return {"status": "ok"}
