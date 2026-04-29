from rest_framework import serializers
from apps.entitlements.models import Entitlement


class EntitlementSerializer(serializers.ModelSerializer):
    source_order_id = serializers.SerializerMethodField()
    source_subscription_id = serializers.SerializerMethodField()
    kind = serializers.CharField(source='target_type', read_only=True)
    object_id = serializers.CharField(source='target_id', read_only=True, allow_null=True)
    source = serializers.CharField(source='source_type', read_only=True)
    source_reference = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    trainer_name = serializers.SerializerMethodField()

    class Meta:
        model = Entitlement
        fields = [
            'id',
            'source_type',
            'source_order_id',
            'source_subscription_id',
            'target_type',
            'target_id',
            'kind',
            'object_id',
            'source',
            'source_reference',
            'is_active',
            'status',
            'starts_at',
            'ends_at',
            'metadata',
            'created_at',
            'updated_at',
            'is_available',
            'title',
            'trainer_name',
        ]

    def get_source_order_id(self, obj):
        if obj.source_order_id:
            return str(obj.source_order_id)
        if obj.source_type == 'order':
            return (obj.metadata or {}).get('source_reference')
        return None

    def get_source_subscription_id(self, obj):
        if obj.source_subscription_id:
            return str(obj.source_subscription_id)
        if obj.source_type == 'subscription':
            return (obj.metadata or {}).get('source_reference')
        return None

    def get_source_reference(self, obj):
        return obj.source_reference

    def get_is_active(self, obj):
        return obj.is_active

    def get_is_available(self, obj):
        from apps.entitlements.selectors import has_active_entitlement
        return has_active_entitlement(user=obj.user, target_type=obj.target_type, target_id=obj.target_id)

    def get_title(self, obj):
        return (obj.metadata or {}).get('title') or obj.target_type

    def get_trainer_name(self, obj):
        return (obj.metadata or {}).get('trainer_name') or ''


class AccessCheckRequestSerializer(serializers.Serializer):
    target_type = serializers.ChoiceField(choices=['video', 'program', 'bundle', 'library'])
    target_id = serializers.CharField(required=False, allow_blank=True)


class AccessDecisionSerializer(serializers.Serializer):
    allowed = serializers.BooleanField()
    code = serializers.CharField()
    reason = serializers.CharField()
    target_type = serializers.CharField()
    target_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    content = serializers.DictField()
    entitlement_id = serializers.CharField(required=False, allow_null=True)
    source = serializers.CharField(required=False, allow_null=True)
