# Generated for TrainerHub v8 persistent domain events/outbox.

import uuid
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='DomainEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('event_type', models.CharField(db_index=True, max_length=128)),
                ('aggregate_type', models.CharField(db_index=True, max_length=96)),
                ('aggregate_id', models.CharField(db_index=True, max_length=128)),
                ('tenant_id', models.CharField(blank=True, db_index=True, max_length=128, null=True)),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('idempotency_key', models.CharField(blank=True, max_length=160, null=True, unique=True)),
                ('version', models.PositiveIntegerField(default=1)),
                ('occurred_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['-occurred_at', '-created_at']},
        ),
        migrations.CreateModel(
            name='InboxMessage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('consumer', models.CharField(max_length=128)),
                ('message_key', models.CharField(max_length=160)),
                ('status', models.CharField(choices=[('received', 'Received'), ('processing', 'Processing'), ('processed', 'Processed'), ('failed', 'Failed')], db_index=True, default='received', max_length=24)),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('received_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('last_error', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['-received_at', '-created_at']},
        ),
        migrations.CreateModel(
            name='OutboxMessage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('topic', models.CharField(db_index=True, max_length=128)),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('processed', 'Processed'), ('failed', 'Failed'), ('dead', 'Dead')], db_index=True, default='pending', max_length=24)),
                ('attempts', models.PositiveSmallIntegerField(default=0)),
                ('max_attempts', models.PositiveSmallIntegerField(default=10)),
                ('next_retry_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('locked_at', models.DateTimeField(blank=True, null=True)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('last_error', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('event', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='outbox_message', to='events.domainevent')),
            ],
            options={'ordering': ['created_at']},
        ),
        migrations.AddIndex(model_name='domainevent', index=models.Index(fields=['event_type', 'occurred_at'], name='events_type_occurred_idx')),
        migrations.AddIndex(model_name='domainevent', index=models.Index(fields=['aggregate_type', 'aggregate_id'], name='events_aggregate_idx')),
        migrations.AddIndex(model_name='domainevent', index=models.Index(fields=['tenant_id', 'occurred_at'], name='events_tenant_time_idx')),
        migrations.AddConstraint(model_name='inboxmessage', constraint=models.UniqueConstraint(fields=('consumer', 'message_key'), name='uniq_inbox_consumer_message')),
        migrations.AddIndex(model_name='inboxmessage', index=models.Index(fields=['consumer', 'status'], name='inbox_consumer_status_idx')),
        migrations.AddIndex(model_name='outboxmessage', index=models.Index(fields=['status', 'next_retry_at', 'created_at'], name='outbox_dispatch_idx')),
        migrations.AddIndex(model_name='outboxmessage', index=models.Index(fields=['topic', 'status'], name='outbox_topic_status_idx')),
    ]
