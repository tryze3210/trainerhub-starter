from apps.messaging.models import ConversationParticipant


def get_user_inbox(user):
    return (
        ConversationParticipant.objects
        .select_related("conversation", "user")
        .filter(user=user)
        .order_by("-conversation__last_message_at", "-conversation__created_at")
    )
