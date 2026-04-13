from datetime import datetime


class ICSInviteBuilder:
    def build(self, reservation, trainer_name: str, attendee_email: str) -> str:
        start = reservation.starts_at.strftime("%Y%m%dT%H%M%SZ")
        end = reservation.ends_at.strftime("%Y%m%dT%H%M%SZ")
        uid = f"reservation-{reservation.id}@trainerhub"
        return "\r\n".join([
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//TrainerHub//Booking//EN",
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
            f"DTSTART:{start}",
            f"DTEND:{end}",
            f"SUMMARY:Session with {trainer_name}",
            f"ATTENDEE:MAILTO:{attendee_email}",
            "END:VEVENT",
            "END:VCALENDAR",
        ])
