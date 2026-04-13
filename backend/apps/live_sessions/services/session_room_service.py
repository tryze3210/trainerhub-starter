import secrets
from apps.live_sessions.models import LiveSession, SessionRoom


class SessionRoomService:
    @staticmethod
    def ensure_room(session: LiveSession) -> SessionRoom:
        room, _ = SessionRoom.objects.get_or_create(
            live_session_id=session.id,
            defaults={
                "provider": SessionRoom.Provider.INTERNAL,
                "room_key": secrets.token_urlsafe(12),
                "join_url": f"https://app.example.com/live/{session.id}",
                "host_url": f"https://app.example.com/live/{session.id}?host=1",
            },
        )
        return room
