from rest_framework import serializers


class DiagnosticsCheckSerializer(serializers.Serializer):
    key = serializers.CharField()
    title = serializers.CharField()
    status = serializers.CharField()
    severity = serializers.CharField()
    message = serializers.CharField()
    owner = serializers.CharField()
    updated_at = serializers.CharField()


class DiagnosticsRunSerializer(serializers.Serializer):
    id = serializers.CharField()
    suite_key = serializers.CharField()
    triggered_by = serializers.CharField()
    status = serializers.CharField()
    started_at = serializers.CharField()
    completed_at = serializers.CharField(allow_null=True)
    checks = serializers.ListField(child=serializers.DictField())


class DiagnosticsSnapshotSerializer(serializers.Serializer):
    overall_status = serializers.CharField()
    checks = DiagnosticsCheckSerializer(many=True)
    recent_runs = DiagnosticsRunSerializer(many=True)


class RunDiagnosticsSerializer(serializers.Serializer):
    suite_key = serializers.CharField()
    triggered_by = serializers.CharField(required=False, default='admin_console')
