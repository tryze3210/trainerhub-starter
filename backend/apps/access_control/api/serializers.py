from rest_framework import serializers


class AccessSnapshotSerializer(serializers.Serializer):
    account = serializers.DictField()
    tenant = serializers.DictField()
    capabilities = serializers.ListField(child=serializers.CharField())
    completed_steps = serializers.ListField(child=serializers.CharField())
    feature_gates = serializers.DictField()


class FeatureCheckSerializer(serializers.Serializer):
    feature_key = serializers.CharField()
    capability = serializers.CharField(required=False, allow_blank=True)


class FeatureDecisionSerializer(serializers.Serializer):
    allowed = serializers.BooleanField()
    code = serializers.CharField()
    reason = serializers.CharField()
    required_capability = serializers.CharField(required=False, allow_null=True)
    feature_key = serializers.CharField(required=False, allow_null=True)
    context = serializers.DictField()


class ObjectCheckSerializer(serializers.Serializer):
    object_type = serializers.CharField()
    object_id = serializers.CharField()
    action = serializers.CharField()


class ObjectDecisionSerializer(serializers.Serializer):
    allowed = serializers.BooleanField()
    code = serializers.CharField()
    reason = serializers.CharField()
    object_type = serializers.CharField()
    object_id = serializers.CharField()
    action = serializers.CharField()
    tenant_id = serializers.CharField(required=False, allow_null=True)
    owner_account_id = serializers.CharField(required=False, allow_null=True)
    actor_account_id = serializers.CharField(required=False, allow_null=True)
    actor_role = serializers.CharField(required=False, allow_null=True)
    context = serializers.DictField()
