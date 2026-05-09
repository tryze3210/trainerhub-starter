from __future__ import annotations

from rest_framework import serializers


class AdminTrainerApplicationReadinessQuerySerializer(serializers.Serializer):
    limit = serializers.IntegerField(required=False, min_value=1, max_value=250, default=50)
    stale_after_days = serializers.IntegerField(required=False, min_value=1, max_value=90, default=7)
    include_samples = serializers.BooleanField(required=False, default=True)
    include_recommendations = serializers.BooleanField(required=False, default=True)


class AdminTrainerApplicationReadinessResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    generated_at = serializers.CharField()
    summary = serializers.JSONField()
    checks = serializers.JSONField()
    issues = serializers.JSONField()
    api_surface = serializers.JSONField()
    recommendations = serializers.JSONField()
    commands = serializers.JSONField()
