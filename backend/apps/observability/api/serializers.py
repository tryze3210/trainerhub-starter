from rest_framework import serializers


class MetricSampleSerializer(serializers.Serializer):
    key = serializers.CharField()
    value = serializers.FloatField()
    unit = serializers.CharField()
    status = serializers.CharField()
    updated_at = serializers.CharField()
    labels = serializers.DictField(child=serializers.CharField(), required=False)


class LogRecordSerializer(serializers.Serializer):
    id = serializers.CharField()
    level = serializers.CharField()
    service = serializers.CharField()
    message = serializers.CharField()
    correlation_id = serializers.CharField(allow_null=True)
    occurred_at = serializers.CharField()
    context = serializers.DictField(required=False)


class TraceSpanSerializer(serializers.Serializer):
    trace_id = serializers.CharField()
    span_id = serializers.CharField()
    parent_span_id = serializers.CharField(allow_null=True)
    operation = serializers.CharField()
    service = serializers.CharField()
    status = serializers.CharField()
    duration_ms = serializers.IntegerField()
    correlation_id = serializers.CharField(allow_null=True)
    started_at = serializers.CharField()
    tags = serializers.DictField(required=False)


class ObservabilityOverviewSerializer(serializers.Serializer):
    generated_at = serializers.CharField(allow_null=True)
    platform_health = serializers.CharField()
    counters = serializers.DictField(child=serializers.IntegerField())
    error_budget = serializers.DictField()
    hot_correlations = serializers.ListField(child=serializers.CharField())


class CorrelationViewSerializer(serializers.Serializer):
    correlation_id = serializers.CharField()
    summary = serializers.DictField()
    related_events = serializers.ListField(child=serializers.DictField())
    related_workflows = serializers.ListField(child=serializers.DictField())
    related_projection_keys = serializers.ListField(child=serializers.CharField())
    logs = LogRecordSerializer(many=True)
    traces = TraceSpanSerializer(many=True)


class ObservabilityRuntimeQuerySerializer(serializers.Serializer):
    window_hours = serializers.IntegerField(required=False, min_value=1, max_value=720, default=24)


class ObservabilityRuntimeSnapshotSerializer(serializers.Serializer):
    generated_at = serializers.CharField()
    window_hours = serializers.IntegerField()
    overall_status = serializers.CharField()
    health_indicators = serializers.ListField(child=serializers.DictField())
    webhooks = serializers.DictField()
    payments = serializers.DictField()
    payout_repairs = serializers.DictField()
    background_jobs = serializers.DictField()
    alerts = serializers.ListField(child=serializers.DictField())
    admin_ops_alerts = serializers.DictField()
