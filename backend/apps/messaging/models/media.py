from django.db import models
import uuid

class MessageAttachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message_id = models.UUIDField(db_index=True)
    kind = models.CharField(max_length=32)  # image, video, file, voice_note
    status = models.CharField(max_length=32, default="pending")
    original_filename = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=128, blank=True)
    file_size = models.BigIntegerField(default=0)
    duration_seconds = models.IntegerField(null=True, blank=True)
    storage_key = models.CharField(max_length=512, blank=True)
    artifact_path = models.CharField(max_length=1024, blank=True)
    checksum = models.CharField(max_length=128, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class MessageUploadSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation_id = models.UUIDField(db_index=True)
    actor_id = models.UUIDField(db_index=True)
    kind = models.CharField(max_length=32)
    status = models.CharField(max_length=32, default="initiated")
    presigned_put_url = models.TextField(blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
