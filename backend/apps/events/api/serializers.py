from rest_framework import serializers


class DomainEventSerializer(serializers.Serializer):
    id = serializers.CharField()
    event_type = serializers.CharField()
    aggregate_type = serializers.CharField()
    aggregate_id = serializers.CharField()
    tenant_id = serializers.CharField(allow_null=True, required=False)
    payload = serializers.DictField(required=False)
    metadata = serializers.DictField(required=False)
    idempotency_key = serializers.CharField(allow_null=True, required=False)
    version = serializers.IntegerField(required=False)
    occurred_at = serializers.CharField(allow_null=True, required=False)
    created_at = serializers.CharField(allow_null=True, required=False)
    updated_at = serializers.CharField(allow_null=True, required=False)


class OutboxMessageSerializer(serializers.Serializer):
    id = serializers.CharField()
    event_id = serializers.CharField()
    event_type = serializers.CharField(allow_null=True, required=False)
    aggregate_type = serializers.CharField(allow_null=True, required=False)
    aggregate_id = serializers.CharField(allow_null=True, required=False)
    topic = serializers.CharField()
    status = serializers.CharField()
    attempts = serializers.IntegerField()
    max_attempts = serializers.IntegerField(required=False)
    payload = serializers.DictField()
    next_retry_at = serializers.CharField(allow_null=True)
    locked_at = serializers.CharField(allow_null=True, required=False)
    processed_at = serializers.CharField(allow_null=True, required=False)
    last_error = serializers.CharField(allow_blank=True, required=False)
    created_at = serializers.CharField(allow_null=True, required=False)
    updated_at = serializers.CharField(allow_null=True, required=False)


class InboxMessageSerializer(serializers.Serializer):
    id = serializers.CharField()
    consumer = serializers.CharField()
    message_key = serializers.CharField()
    status = serializers.CharField()
    payload = serializers.DictField(required=False)
    received_at = serializers.CharField(allow_null=True, required=False)
    processed_at = serializers.CharField(allow_null=True)
    last_error = serializers.CharField(allow_blank=True, required=False)
    created_at = serializers.CharField(allow_null=True, required=False)
    updated_at = serializers.CharField(allow_null=True, required=False)


class EmitEventSerializer(serializers.Serializer):
    event_type = serializers.CharField()
    aggregate_type = serializers.CharField()
    aggregate_id = serializers.CharField()
    tenant_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    payload = serializers.DictField(required=False, default=dict)
    metadata = serializers.DictField(required=False, default=dict)
    idempotency_key = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class DispatchOutboxSerializer(serializers.Serializer):
    batch_size = serializers.IntegerField(required=False, min_value=1, max_value=500, default=100)


class RetryOutboxSerializer(serializers.Serializer):
    force = serializers.BooleanField(required=False, default=False)
    reset_attempts = serializers.BooleanField(required=False, default=False)


class MarkOutboxDeadSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default='Marked dead manually by operator.')


class RequeueStuckOutboxSerializer(serializers.Serializer):
    older_than_minutes = serializers.IntegerField(required=False, min_value=1, max_value=1440, default=15)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=500, default=100)


class EventHandlerSerializer(serializers.Serializer):
    key = serializers.CharField()
    consumer = serializers.CharField()
    matcher = serializers.CharField()
    pattern = serializers.CharField()
    handler = serializers.CharField()


class OutboxHealthQuerySerializer(serializers.Serializer):
    max_pending_age_minutes = serializers.IntegerField(required=False, min_value=1, max_value=1440, default=15)
    max_processing_age_minutes = serializers.IntegerField(required=False, min_value=1, max_value=1440, default=15)
    max_dead_messages = serializers.IntegerField(required=False, min_value=0, max_value=100000, default=0)
    max_failed_messages = serializers.IntegerField(required=False, min_value=0, max_value=100000, default=50)
