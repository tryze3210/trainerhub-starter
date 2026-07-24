import logging

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models, transaction
from django.utils import timezone

from apps.access_control.permissions import ROLE_TRAINER, user_role_set
from apps.messaging.models import Conversation, ConversationParticipant, Message, MessageEvent


logger = logging.getLogger('apps.messaging')


def _has_trainer_role(user) -> bool:
    return ROLE_TRAINER in user_role_set(user)


def _role_for_user(user) -> str:
    if _has_trainer_role(user):
        return ConversationParticipant.ROLE_TRAINER
    return ConversationParticipant.ROLE_CLIENT


def _is_participant(*, conversation, user) -> bool:
    return ConversationParticipant.objects.filter(conversation=conversation, user=user).exists()


def _emit_message_event(*, message: Message, event_type: str, actor=None, payload=None) -> None:
    MessageEvent.objects.create(
        message=message,
        event_type=event_type,
        actor=actor,
        payload=payload or {},
    )


def _notify_recipient(*, recipient, sender, conversation: Conversation, message: Message) -> None:
    try:
        from apps.notifications.models import NotificationType
        from apps.notifications.services.delivery_service import NotificationDeliveryService

        sender_name = getattr(sender, "email", "") if sender else "System"
        NotificationDeliveryService().create_in_app(
            user=recipient,
            type=NotificationType.SYSTEM,
            title="New message",
            body=f"{sender_name}: {message.body[:120]}",
            event_key=f"message:{message.id}:recipient:{recipient.id}",
            metadata={
                "source": "messaging",
                "conversation_id": str(conversation.id),
                "message_id": str(message.id),
                "sender_id": str(getattr(sender, "id", "") or ""),
            },
            cta_label="Open messages",
            cta_url="/messages",
        )
    except Exception:
        logger.exception('messaging.notification_side_effect_failed message_id=%s recipient_id=%s', message.id, recipient.id)


def _emit_domain_event(*, conversation: Conversation, message: Message, sender=None) -> None:
    try:
        from apps.events.services import DomainEventService

        DomainEventService().emit(
            event_type="messaging.message_sent",
            aggregate_type="conversation",
            aggregate_id=str(conversation.id),
            idempotency_key=f"messaging.message:{message.id}",
            payload={
                "conversation_id": str(conversation.id),
                "message_id": str(message.id),
                "message_type": message.message_type,
                "sender_id": str(getattr(sender, "id", "") or ""),
                "recipient_ids": [
                    str(participant.user_id)
                    for participant in ConversationParticipant.objects.filter(conversation=conversation).exclude(user=sender)
                ],
            },
            metadata={"source": "messaging"},
        )
    except Exception:
        logger.exception('messaging.domain_event_side_effect_failed message_id=%s conversation_id=%s', message.id, conversation.id)


class ConversationService:
    @transaction.atomic
    def start_direct_thread(self, *, sender, recipient_id, subject="", body=""):
        recipient = get_user_model().objects.filter(id=recipient_id).first()
        if not recipient:
            raise ValidationError({"recipient_id": "Recipient not found."})
        if recipient.id == sender.id:
            raise ValidationError({"recipient_id": "Cannot start a conversation with yourself."})
        trainer_id = sender.id if _has_trainer_role(sender) else recipient.id if _has_trainer_role(recipient) else None
        client_id = recipient.id if trainer_id == sender.id else sender.id

        conversation = (
            Conversation.objects.filter(kind=Conversation.KIND_DIRECT)
            .filter(participants__user=sender)
            .filter(participants__user=recipient)
            .distinct()
            .first()
        )
        if conversation is None:
            conversation = Conversation.objects.create(
                kind=Conversation.KIND_DIRECT,
                trainer_id=trainer_id,
                client_id=client_id,
                subject=(subject or "").strip(),
                last_message_at=timezone.now(),
            )
            ConversationParticipant.objects.bulk_create(
                [
                    ConversationParticipant(conversation=conversation, user=sender, role=_role_for_user(sender)),
                    ConversationParticipant(conversation=conversation, user=recipient, role=_role_for_user(recipient)),
                ]
            )
            self.create_system_message(
                conversation=conversation,
                body="Conversation started.",
                metadata={"source": "messaging_core"},
            )
        elif subject and not conversation.subject:
            conversation.subject = subject.strip()
            conversation.save(update_fields=["subject", "updated_at"])

        message = None
        if body and body.strip():
            message = self.send_message(conversation=conversation, sender=sender, body=body)
        return conversation, message

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
        self.create_system_message(
            conversation=conversation,
            body="Booking conversation started.",
            metadata={"reservation_id": str(reservation_id), "source": "booking"},
        )
        return conversation

    @transaction.atomic
    def send_message(self, *, conversation, sender, body):
        if not _is_participant(conversation=conversation, user=sender):
            raise PermissionDenied("Conversation participant required.")
        text = (body or "").strip()
        if not text:
            raise ValidationError({"body": "Message body is required."})
        message = Message.objects.create(conversation=conversation, sender=sender, body=text)
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=["last_message_at", "updated_at"])
        recipients = list(ConversationParticipant.objects.filter(conversation=conversation).exclude(user=sender).select_related("user"))
        ConversationParticipant.objects.filter(id__in=[participant.id for participant in recipients]).update(
            unread_count=models.F("unread_count") + 1
        )
        _emit_message_event(message=message, event_type="sent", actor=sender)
        for participant in recipients:
            _notify_recipient(recipient=participant.user, sender=sender, conversation=conversation, message=message)
        _emit_domain_event(conversation=conversation, message=message, sender=sender)
        return message

    @transaction.atomic
    def create_system_message(self, *, conversation, body, metadata=None):
        text = (body or "").strip()
        if not text:
            raise ValidationError({"body": "System message body is required."})
        message = Message.objects.create(
            conversation=conversation,
            sender=None,
            message_type=Message.TYPE_SYSTEM,
            body=text,
            metadata=metadata or {},
        )
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=["last_message_at", "updated_at"])
        _emit_message_event(message=message, event_type="system", actor=None, payload=metadata or {})
        return message
