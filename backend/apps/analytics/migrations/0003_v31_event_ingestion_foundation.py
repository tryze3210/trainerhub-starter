from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ('analytics', '0002_v30_warehouse_extensions'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnalyticsEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('event_name', models.CharField(choices=[('page_view', 'Page view'), ('session_start', 'Session start'), ('video_view', 'Video view'), ('checkout_started', 'Checkout started'), ('purchase_completed', 'Purchase completed')], max_length=32)),
                ('occurred_at', models.DateTimeField()),
                ('event_date', models.DateField(db_index=True)),
                ('session_id', models.CharField(db_index=True, max_length=128)),
                ('anonymous_id', models.CharField(blank=True, db_index=True, max_length=128)),
                ('user_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('trainer_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('order_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('path', models.CharField(blank=True, max_length=512)),
                ('referrer', models.CharField(blank=True, max_length=1024)),
                ('utm_source', models.CharField(blank=True, max_length=128)),
                ('utm_medium', models.CharField(blank=True, max_length=128)),
                ('utm_campaign', models.CharField(blank=True, max_length=128)),
                ('country_code', models.CharField(blank=True, max_length=8)),
                ('device_type', models.CharField(blank=True, max_length=32)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'analytics_event',
                'ordering': ['-occurred_at'],
                'indexes': [models.Index(fields=['event_date', 'event_name'], name='analytics_event_date_name_idx'), models.Index(fields=['session_id', 'occurred_at'], name='analytics_event_session_idx'), models.Index(fields=['utm_source', 'utm_medium', 'event_date'], name='analytics_event_utm_idx'), models.Index(fields=['trainer_id', 'event_date'], name='analytics_event_trainer_idx')],
            },
        ),
        migrations.CreateModel(
            name='DailyTrafficSlice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('path', models.CharField(blank=True, max_length=512)),
                ('utm_source', models.CharField(blank=True, max_length=128)),
                ('utm_medium', models.CharField(blank=True, max_length=128)),
                ('utm_campaign', models.CharField(blank=True, max_length=128)),
                ('trainer_id', models.UUIDField(blank=True, null=True)),
                ('sessions', models.PositiveIntegerField(default=0)),
                ('unique_users', models.PositiveIntegerField(default=0)),
                ('page_views', models.PositiveIntegerField(default=0)),
                ('video_views', models.PositiveIntegerField(default=0)),
                ('checkout_starts', models.PositiveIntegerField(default=0)),
                ('purchases', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'analytics_daily_traffic_slice',
                'ordering': ['-date', 'path'],
                'indexes': [models.Index(fields=['date', 'path'], name='analytics_slice_date_path_idx'), models.Index(fields=['date', 'utm_source', 'utm_medium'], name='analytics_slice_date_utm_idx'), models.Index(fields=['trainer_id', 'date'], name='analytics_slice_trainer_idx')],
                'unique_together': {('date', 'path', 'utm_source', 'utm_medium', 'utm_campaign', 'trainer_id')},
            },
        ),
    ]
