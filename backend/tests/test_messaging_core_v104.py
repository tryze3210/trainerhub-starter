import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.events.models import DomainEvent
from apps.messaging.models import Conversation, ConversationParticipant, Message
from apps.notifications.models import Notification


pytestmark = pytest.mark.django_db


def make_user(email, *, role="customer", is_staff=False):
    return get_user_model().objects.create_user(email=email, password="pass12345", role=role, is_staff=is_staff)


def test_trainer_student_direct_message_creates_unread_notification_and_event():
    trainer = make_user("message-trainer@example.com", role="trainer")
    student = make_user("message-student@example.com")
    client = APIClient()
    client.force_authenticate(user=student)

    start_response = client.post(
        "/api/v1/messaging/conversations/start/",
        {
            "recipient_id": str(trainer.id),
            "subject": "Course question",
            "body": "Can I ask about lesson two?",
        },
        format="json",
    )

    assert start_response.status_code == 201, start_response.data
    conversation_id = start_response.data["id"]
    assert Conversation.objects.filter(id=conversation_id).exists()
    assert Message.objects.filter(conversation_id=conversation_id, message_type=Message.TYPE_SYSTEM).exists()
    assert Message.objects.filter(conversation_id=conversation_id, sender=student).exists()

    trainer_participant = ConversationParticipant.objects.get(conversation_id=conversation_id, user=trainer)
    assert trainer_participant.unread_count == 1
    assert Notification.objects.filter(user=trainer, metadata__source="messaging").exists()
    assert DomainEvent.objects.filter(event_type="messaging.message_sent", aggregate_id=conversation_id).exists()

    trainer_client = APIClient()
    trainer_client.force_authenticate(user=trainer)
    inbox_response = trainer_client.get("/api/v1/messaging/me/inbox/")
    assert inbox_response.status_code == 200, inbox_response.data
    assert inbox_response.data["unread_total"] == 1

    read_response = trainer_client.post(f"/api/v1/messaging/conversations/{conversation_id}/mark-read/")
    assert read_response.status_code == 200, read_response.data
    trainer_participant.refresh_from_db()
    assert trainer_participant.unread_count == 0


def test_non_participant_cannot_send_message_to_conversation():
    trainer = make_user("message-owner@example.com", role="trainer")
    student = make_user("message-owner-student@example.com")
    outsider = make_user("message-outsider@example.com")
    client = APIClient()
    client.force_authenticate(user=student)
    start_response = client.post(
        "/api/v1/messaging/conversations/start/",
        {"recipient_id": str(trainer.id), "body": "Hello"},
        format="json",
    )
    conversation_id = start_response.data["id"]

    outsider_client = APIClient()
    outsider_client.force_authenticate(user=outsider)
    response = outsider_client.post(
        f"/api/v1/messaging/conversations/{conversation_id}/send/",
        {"body": "I should not be here"},
        format="json",
    )

    assert response.status_code == 403, response.data
