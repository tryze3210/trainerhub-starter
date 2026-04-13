from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=100, unique=True)),
                ('title_template', models.CharField(max_length=255)),
                ('body_template', models.TextField()),
                ('notification_type', models.CharField(choices=[('system', 'System'), ('order', 'Order'), ('payment', 'Payment'), ('subscription', 'Subscription'), ('announcement', 'Announcement')], default='system', max_length=32)),
                ('channel', models.CharField(choices=[('in_app', 'In-app'), ('email', 'Email'), ('push', 'Push')], default='in_app', max_length=16)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'notifications_template', 'ordering': ['code']},
        ),
        migrations.CreateModel(
            name='AdminAnnouncement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('announcement_uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('title', models.CharField(max_length=255)),
                ('body', models.TextField()),
                ('cta_label', models.CharField(blank=True, max_length=100)),
                ('cta_url', models.CharField(blank=True, max_length=500)),
                ('audience_type', models.CharField(choices=[('all_users', 'All users'), ('all_trainers', 'All trainers'), ('specific_users', 'Specific users')], default='all_users', max_length=32)),
                ('starts_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('ends_at', models.DateTimeField(blank=True, null=True)),
                ('is_published', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_admin_announcements', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'notifications_admin_announcement', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='NotificationPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('in_app_enabled', models.BooleanField(default=True)),
                ('email_enabled', models.BooleanField(default=True)),
                ('marketing_enabled', models.BooleanField(default=True)),
                ('product_updates_enabled', models.BooleanField(default=True)),
                ('quiet_hours_start', models.TimeField(blank=True, null=True)),
                ('quiet_hours_end', models.TimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='notification_preferences', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'notifications_preference'},
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('notification_type', models.CharField(choices=[('system', 'System'), ('order', 'Order'), ('payment', 'Payment'), ('subscription', 'Subscription'), ('announcement', 'Announcement')], default='system', max_length=32)),
                ('channel', models.CharField(choices=[('in_app', 'In-app'), ('email', 'Email'), ('push', 'Push')], default='in_app', max_length=16)),
                ('title', models.CharField(max_length=255)),
                ('body', models.TextField()),
                ('cta_label', models.CharField(blank=True, max_length=100)),
                ('cta_url', models.CharField(blank=True, max_length=500)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed'), ('read', 'Read')], default='pending', max_length=16)),
                ('is_read', models.BooleanField(default=False)),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('announcement', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notifications', to='notifications.adminannouncement')),
                ('template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notifications', to='notifications.notificationtemplate')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'notifications_notification', 'ordering': ['-created_at']},
        ),
        migrations.AddIndex(
            model_name='adminannouncement',
            index=models.Index(fields=['is_published', 'starts_at'], name='notif_ann_publish_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['user', 'is_read', '-created_at'], name='notif_user_unread_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['notification_type', 'created_at'], name='notif_type_created_idx'),
        ),
    ]
