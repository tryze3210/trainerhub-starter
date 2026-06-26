# Generated for TrainerHub v104 messaging core.

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Conversation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("kind", models.CharField(choices=[("direct", "Direct"), ("booking", "Booking"), ("support", "Support")], default="direct", max_length=32)),
                ("booking_reservation_id", models.UUIDField(blank=True, null=True)),
                ("trainer_id", models.UUIDField(blank=True, null=True)),
                ("client_id", models.UUIDField(blank=True, null=True)),
                ("subject", models.CharField(blank=True, default="", max_length=255)),
                ("last_message_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-last_message_at", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Message",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("message_type", models.CharField(choices=[("user", "User"), ("system", "System")], default="user", max_length=32)),
                ("body", models.TextField()),
                ("delivery_status", models.CharField(default="sent", max_length=32)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("conversation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="messaging.conversation")),
                ("sender", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
        migrations.CreateModel(
            name="MessageEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("event_type", models.CharField(max_length=32)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("message", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="events", to="messaging.message")),
            ],
        ),
        migrations.CreateModel(
            name="ConversationParticipant",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("role", models.CharField(choices=[("trainer", "Trainer"), ("client", "Client"), ("member", "Member"), ("system", "System")], default="member", max_length=32)),
                ("unread_count", models.PositiveIntegerField(default=0)),
                ("last_read_message_id", models.UUIDField(blank=True, null=True)),
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                ("conversation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="participants", to="messaging.conversation")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddIndex(
            model_name="conversation",
            index=models.Index(fields=["trainer_id", "client_id"], name="msg_conv_trainer_client_idx"),
        ),
        migrations.AddIndex(
            model_name="conversation",
            index=models.Index(fields=["kind", "last_message_at"], name="msg_conv_kind_last_idx"),
        ),
        migrations.AddIndex(
            model_name="message",
            index=models.Index(fields=["conversation", "created_at"], name="msg_message_conversation_idx"),
        ),
        migrations.AddIndex(
            model_name="message",
            index=models.Index(fields=["sender", "created_at"], name="msg_message_sender_idx"),
        ),
        migrations.AddIndex(
            model_name="messageevent",
            index=models.Index(fields=["event_type", "created_at"], name="msg_event_type_created_idx"),
        ),
        migrations.AddIndex(
            model_name="conversationparticipant",
            index=models.Index(fields=["user", "unread_count"], name="msg_part_user_unread_idx"),
        ),
        migrations.AddConstraint(
            model_name="conversationparticipant",
            constraint=models.UniqueConstraint(fields=("conversation", "user"), name="uq_message_participant_user"),
        ),
    ]
