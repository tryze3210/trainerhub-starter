from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="NotificationDelivery",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("channel", models.CharField(max_length=20, choices=[("in_app", "In-app"), ("email", "Email")])),
                ("type", models.CharField(max_length=50, choices=[("order_paid", "Order paid"), ("payment_failed", "Payment failed"), ("subscription_activated", "Subscription activated"), ("admin_announcement", "Admin announcement")],)),
                ("template_code", models.CharField(max_length=100, blank=True)),
                ("subject", models.CharField(max_length=255, blank=True)),
                ("rendered_body", models.TextField(blank=True)),
                ("status", models.CharField(max_length=20, default="pending", choices=[("pending", "Pending"), ("sent", "Sent"), ("failed", "Failed"), ("skipped", "Skipped")],)),
                ("error_message", models.TextField(blank=True)),
                ("provider", models.CharField(max_length=100, blank=True)),
                ("provider_message_id", models.CharField(max_length=255, blank=True)),
                ("sent_at", models.DateTimeField(null=True, blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("notification", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="deliveries", to="notifications.notification")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notification_deliveries", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name="notificationtemplate",
            name="subject_template",
            field=models.CharField(max_length=255, blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AddIndex(
            model_name="notificationdelivery",
            index=models.Index(fields=["channel", "status", "created_at"], name="notif_deliv_ch_status_idx"),
        ),
        migrations.AddIndex(
            model_name="notificationdelivery",
            index=models.Index(fields=["user", "created_at"], name="notif_deliv_user_created_idx"),
        ),
        migrations.AddIndex(
            model_name="notificationdelivery",
            index=models.Index(fields=["type", "created_at"], name="notif_deliv_type_created_idx"),
        ),
    ]
