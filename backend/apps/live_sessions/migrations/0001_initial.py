# Generated manually for live_sessions initial schema.

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
            name="LiveSession",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                (
                    "session_type",
                    models.CharField(
                        choices=[
                            ("webinar", "Webinar"),
                            ("group_class", "Group class"),
                            ("workshop", "Workshop"),
                        ],
                        default="webinar",
                        max_length=32,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("scheduled", "Scheduled"),
                            ("live", "Live"),
                            ("completed", "Completed"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="draft",
                        max_length=32,
                    ),
                ),
                ("starts_at", models.DateTimeField()),
                ("ends_at", models.DateTimeField()),
                ("capacity", models.PositiveIntegerField(default=100)),
                ("booking_reservation_id", models.UUIDField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "trainer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="live_sessions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "live_sessions_live_session",
                "ordering": ["starts_at"],
            },
        ),
        migrations.CreateModel(
            name="SessionRoom",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("live_session_id", models.UUIDField(unique=True)),
                (
                    "provider",
                    models.CharField(
                        choices=[
                            ("internal", "Internal"),
                            ("jitsi", "Jitsi"),
                            ("zoom", "Zoom"),
                            ("youtube", "YouTube"),
                        ],
                        default="internal",
                        max_length=32,
                    ),
                ),
                ("room_key", models.CharField(max_length=255, unique=True)),
                ("join_url", models.URLField(blank=True)),
                ("host_url", models.URLField(blank=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "live_sessions_session_room",
            },
        ),
        migrations.CreateModel(
            name="SessionAttendance",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("live_session_id", models.UUIDField(db_index=True)),
                ("reservation_id", models.UUIDField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("registered", "Registered"),
                            ("joined", "Joined"),
                            ("left", "Left"),
                            ("attended", "Attended"),
                            ("no_show", "No show"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="registered",
                        max_length=32,
                    ),
                ),
                ("joined_at", models.DateTimeField(blank=True, null=True)),
                ("left_at", models.DateTimeField(blank=True, null=True)),
                ("duration_seconds", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="session_attendances",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "live_sessions_session_attendance",
                "unique_together": {("live_session_id", "user")},
            },
        ),
        migrations.CreateModel(
            name="ReminderDelivery",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("live_session_id", models.UUIDField(db_index=True)),
                ("attendance_id", models.UUIDField(db_index=True)),
                (
                    "channel",
                    models.CharField(
                        choices=[
                            ("email", "Email"),
                            ("in_app", "In-app"),
                            ("push", "Push"),
                        ],
                        max_length=32,
                    ),
                ),
                ("scheduled_for", models.DateTimeField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("sent", "Sent"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=32,
                    ),
                ),
                ("provider_message_id", models.CharField(blank=True, max_length=255)),
                ("failure_reason", models.TextField(blank=True)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "live_sessions_reminder_delivery",
            },
        ),
    ]