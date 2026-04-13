"""Bridge paid/group booking reservations into live session attendance creation.

Call from booking application service after reservation confirmation.
"""


def on_booking_confirmed_create_attendance(*, reservation, user, live_session_id):
    # TODO: replace with real import path inside your project.
    from apps.live_sessions.models import SessionAttendance

    return SessionAttendance.objects.get_or_create(
        live_session_id=live_session_id,
        user=user,
        defaults={
            "reservation_id": reservation.id,
            "status": SessionAttendance.AttendanceStatus.REGISTERED,
        },
    )
