from rest_framework import serializers


class ProjectionStatusSerializer(serializers.Serializer):
    projection_key = serializers.CharField()
    status = serializers.CharField()
    last_event_id = serializers.CharField(allow_null=True)
    lag = serializers.IntegerField()
    failed_messages = serializers.IntegerField()
    updated_at = serializers.CharField()


class ProjectionRebuildSerializer(serializers.Serializer):
    projection_key = serializers.CharField()
