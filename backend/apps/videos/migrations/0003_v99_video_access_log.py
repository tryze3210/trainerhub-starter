import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("videos", "0002_marketplace_core_v6_10_safe_schema"),
    ]

    operations = [
        migrations.CreateModel(
            name="VideoAccessLog",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "decision",
                    models.CharField(choices=[("granted", "Granted"), ("denied", "Denied")], max_length=32),
                ),
                (
                    "reason",
                    models.CharField(
                        choices=[
                            ("admin", "Admin"),
                            ("trainer_owner", "Trainer owner"),
                            ("free_video", "Free video"),
                            ("entitlement", "Entitlement"),
                            ("denied", "Denied"),
                        ],
                        max_length=64,
                    ),
                ),
                ("access_token_hash", models.CharField(blank=True, max_length=64)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True)),
                ("referer", models.TextField(blank=True)),
                ("origin", models.TextField(blank=True)),
                ("anti_leech", models.JSONField(blank=True, default=dict)),
                ("entitlement_decision", models.JSONField(blank=True, default=dict)),
                (
                    "media_asset",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="access_logs",
                        to="videos.mediaasset",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="video_access_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "video",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="access_logs",
                        to="videos.video",
                    ),
                ),
            ],
        ),
    ]
