from rest_framework import serializers


class OutboxMessageSerializer(serializers.Serializer):
    id = serializers.CharField()
    event_id = serializers.CharField()
    topic = serializers.CharField()
    status = serializers.CharField()
    attempts = serializers.IntegerField()
    payload = serializers.DictField()
    next_retry_at = serializers.CharField(allow_null=True)


class InboxMessageSerializer(serializers.Serializer):
    id = serializers.CharField()
    consumer = serializers.CharField()
    message_key = serializers.CharField()
    status = serializers.CharField()
    processed_at = serializers.CharField(allow_null=True)


class EmitEventSerializer(serializers.Serializer):
    event_type = serializers.CharField()
    aggregate_type = serializers.CharField()
    aggregate_id = serializers.CharField()
    tenant_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    payload = serializers.DictField()
