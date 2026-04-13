from django.db import transaction
from django.utils import timezone
from apps.messaging.models import Conversation, ConversationParticipant, Message


class ConversationService:
    @transaction.atomic
    def create_booking_thread(self, *, reservation_id, trainer_user, client_user, subject=""):
        conversation = Conversation.objects.create(
            kind="booking",
            booking_reservation_id=reservation_id,
            trainer_id=getattr(trainer_user, "id", None),
            client_id=getattr(client_user, "id", None),
            subject=subject,
        )
        ConversationParticipant.objects.bulk_create([
            ConversationParticipant(conversation=conversation, user=trainer_user, role="trainer"),
            ConversationParticipant(conversation=conversation, user=client_user, role="client"),
        ])
        return conversation

    @transaction.atomic
    def send_message(self, *, conversation, sender, body):
        message = Message.objects.create(conversation=conversation, sender=sender, body=body)
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=["last_message_at"])
        ConversationParticipant.objects.filter(conversation=conversation).exclude(user=sender).update(
            unread_count=models.F("unread_count") + 1
        )
        return message
