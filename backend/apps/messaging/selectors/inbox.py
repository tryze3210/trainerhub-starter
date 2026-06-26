from apps.messaging.models import ConversationParticipant


def get_user_inbox(user):
    return (
        ConversationParticipant.objects
        .select_related("conversation", "user")
        .filter(user=user)
        .order_by("-conversation__last_message_at", "-conversation__created_at")
    )


def conversation_to_dict(participant: ConversationParticipant) -> dict:
    conversation = participant.conversation
    last_message = conversation.messages.select_related("sender").order_by("-created_at").first()
    return {
        "id": str(conversation.id),
        "kind": conversation.kind,
        "booking_reservation_id": str(conversation.booking_reservation_id) if conversation.booking_reservation_id else None,
        "trainer_id": str(conversation.trainer_id) if conversation.trainer_id else None,
        "client_id": str(conversation.client_id) if conversation.client_id else None,
        "subject": conversation.subject,
        "unread_count": participant.unread_count,
        "last_message_at": conversation.last_message_at.isoformat() if conversation.last_message_at else None,
        "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
        "updated_at": conversation.updated_at.isoformat() if getattr(conversation, "updated_at", None) else None,
        "last_message": message_to_dict(last_message) if last_message else None,
        "participants": [
            {
                "user_id": str(item.user_id),
                "email": getattr(item.user, "email", ""),
                "role": item.role,
                "unread_count": item.unread_count,
            }
            for item in conversation.participants.select_related("user").order_by("joined_at")
        ],
    }


def message_to_dict(message) -> dict:
    return {
        "id": str(message.id),
        "conversation": str(message.conversation_id),
        "sender": str(message.sender_id) if message.sender_id else None,
        "sender_email": getattr(message.sender, "email", "") if message.sender_id else "System",
        "message_type": message.message_type,
        "body": message.body,
        "delivery_status": message.delivery_status,
        "metadata": message.metadata or {},
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }
