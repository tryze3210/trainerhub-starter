from rest_framework import serializers


class WorkflowDefinitionSerializer(serializers.Serializer):
    workflow_key = serializers.CharField()
    trigger_event = serializers.CharField()
    steps = serializers.ListField(child=serializers.CharField())


class WorkflowRunSerializer(serializers.Serializer):
    id = serializers.CharField()
    workflow_key = serializers.CharField()
    subject_type = serializers.CharField()
    subject_id = serializers.CharField()
    status = serializers.CharField()
    current_step = serializers.CharField()
    tenant_id = serializers.CharField(allow_null=True)
    context = serializers.DictField()


class StartWorkflowSerializer(serializers.Serializer):
    workflow_key = serializers.CharField()
    subject_type = serializers.CharField()
    subject_id = serializers.CharField()
    tenant_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    context = serializers.DictField(required=False)
