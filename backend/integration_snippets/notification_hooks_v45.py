"""Trigger in-app/email reminders via notifications bounded context."""


def enqueue_live_session_reminder(*, attendance, scheduled_for):
    # Replace with NotificationDispatcher / outbox integration from v32-v33.
    return {
        "attendance_id": str(attendance.id),
        "scheduled_for": scheduled_for.isoformat(),
        "status": "queued",
    }
