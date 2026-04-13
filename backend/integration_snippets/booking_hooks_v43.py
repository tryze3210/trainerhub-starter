"""
Call this from booking reservation confirmed flow to create booking-linked thread.
"""

from apps.messaging.services.conversations import ConversationService


def create_booking_conversation(*, reservation, trainer_user, client_user):
    return ConversationService().create_booking_thread(
        reservation_id=reservation.id,
        trainer_user=trainer_user,
        client_user=client_user,
        subject=f"Session {reservation.id}",
    )
