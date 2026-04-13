import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='MediaAsset',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('trainer_id', models.UUIDField(db_index=True)),
                ('asset_type', models.CharField(choices=[('video', 'Video'), ('thumbnail', 'Thumbnail'), ('preview', 'Preview')], max_length=32)),
                ('title', models.CharField(max_length=255)),
                ('storage_bucket', models.CharField(max_length=255)),
                ('storage_key', models.CharField(max_length=1024, unique=True)),
                ('upload_status', models.CharField(choices=[('created', 'Created'), ('uploading', 'Uploading'), ('uploaded', 'Uploaded'), ('processing', 'Processing'), ('ready', 'Ready'), ('failed', 'Failed')], default='created', max_length=32)),
                ('moderation_status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=32)),
                ('mime_type', models.CharField(blank=True, max_length=128)),
                ('size_bytes', models.BigIntegerField(default=0)),
                ('duration_seconds', models.PositiveIntegerField(blank=True, null=True)),
                ('width', models.PositiveIntegerField(blank=True, null=True)),
                ('height', models.PositiveIntegerField(blank=True, null=True)),
                ('error_message', models.TextField(blank=True)),
            ],
        ),
    ]
