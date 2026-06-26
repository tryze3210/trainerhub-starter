from django.conf import settings
from django.db import models
import uuid


class Conversation(models.Model):
    KIND_DIRECT = "direct"
    KIND_BOOKING = "booking"
    KIND_SUPPORT = "support"
    KIND_CHOICES = [
        (KIND_DIRECT, "Direct"),
        (KIND_BOOKING, "Booking"),
        (KIND_SUPPORT, "Support"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kind = models.CharField(max_length=32, choices=KIND_CHOICES, default=KIND_DIRECT)
    booking_reservation_id = models.UUIDField(null=True, blank=True)
    trainer_id = models.UUIDField(null=True, blank=True)
    client_id = models.UUIDField(null=True, blank=True)
    subject = models.CharField(max_length=255, blank=True, default="")
    last_message_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_message_at", "-created_at"]
        indexes = [
            models.Index(fields=["trainer_id", "client_id"], name="msg_conv_trainer_client_idx"),
            models.Index(fields=["kind", "last_message_at"], name="msg_conv_kind_last_idx"),
        ]


class ConversationParticipant(models.Model):
    ROLE_TRAINER = "trainer"
    ROLE_CLIENT = "client"
    ROLE_MEMBER = "member"
    ROLE_SYSTEM = "system"
    ROLE_CHOICES = [
        (ROLE_TRAINER, "Trainer"),
        (ROLE_CLIENT, "Client"),
        (ROLE_MEMBER, "Member"),
        (ROLE_SYSTEM, "System"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    unread_count = models.PositiveIntegerField(default=0)
    last_read_message_id = models.UUIDField(null=True, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["conversation", "user"], name="uq_message_participant_user"),
        ]
        indexes = [
            models.Index(fields=["user", "unread_count"], name="msg_part_user_unread_idx"),
        ]


class Message(models.Model):
    TYPE_USER = "user"
    TYPE_SYSTEM = "system"
    TYPE_CHOICES = [
        (TYPE_USER, "User"),
        (TYPE_SYSTEM, "System"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    message_type = models.CharField(max_length=32, choices=TYPE_CHOICES, default=TYPE_USER)
    body = models.TextField()
    delivery_status = models.CharField(max_length=32, default="sent")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"], name="msg_message_conversation_idx"),
            models.Index(fields=["sender", "created_at"], name="msg_message_sender_idx"),
        ]


class MessageEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=32)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["event_type", "created_at"], name="msg_event_type_created_idx"),
        ]
