from django.db import models
import uuid

class ConversationEscalation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation_id = models.UUIDField(db_index=True)
    source_message_id = models.UUIDField(null=True, blank=True)
    target_queue = models.CharField(max_length=64, default="support")
    status = models.CharField(max_length=32, default="open")
    reason_code = models.CharField(max_length=64, blank=True)
    summary = models.TextField(blank=True)
    support_inbox_item_id = models.UUIDField(null=True, blank=True)
    created_by_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
