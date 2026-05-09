from __future__ import annotations

from rest_framework import serializers

from apps.entitlements.models import Entitlement


class EntitlementSerializer(serializers.ModelSerializer):
    source_order_id = serializers.SerializerMethodField()
    source_subscription_id = serializers.SerializerMethodField()
    kind = serializers.CharField(source="target_type", read_only=True)
    object_id = serializers.CharField(source="target_id", read_only=True, allow_null=True)
    source = serializers.CharField(source="source_type", read_only=True)
    source_reference = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    trainer_name = serializers.SerializerMethodField()

    class Meta:
        model = Entitlement
        fields = [
            "id",
            "source_type",
            "source_order_id",
            "source_subscription_id",
            "target_type",
            "target_id",
            "kind",
            "object_id",
            "source",
            "source_reference",
            "is_active",
            "status",
            "starts_at",
            "ends_at",
            "metadata",
            "created_at",
            "updated_at",
            "is_available",
            "title",
            "trainer_name",
        ]

    def get_source_order_id(self, obj):
        if obj.source_order_id:
            return str(obj.source_order_id)
        if obj.source_type == "order":
            return (obj.metadata or {}).get("source_reference")
        return None

    def get_source_subscription_id(self, obj):
        if obj.source_subscription_id:
            return str(obj.source_subscription_id)
        if obj.source_type == "subscription":
            return (obj.metadata or {}).get("source_reference")
        return None

    def get_source_reference(self, obj):
        return obj.source_reference

    def get_is_active(self, obj):
        return obj.is_active

    def get_is_available(self, obj):
        from apps.entitlements.selectors import has_active_entitlement

        return has_active_entitlement(user=obj.user, target_type=obj.target_type, target_id=obj.target_id)

    def get_title(self, obj):
        return (obj.metadata or {}).get("title") or obj.target_type

    def get_trainer_name(self, obj):
        return (obj.metadata or {}).get("trainer_name") or ""


class AccessCheckRequestSerializer(serializers.Serializer):
    target_type = serializers.ChoiceField(choices=["video", "program", "bundle", "library"])
    target_id = serializers.CharField(required=False, allow_blank=True)


class AccessAuditQuerySerializer(serializers.Serializer):
    target_type = serializers.ChoiceField(choices=["video", "program", "bundle", "library"], required=False)
    content_type = serializers.ChoiceField(choices=["video", "program", "bundle", "library"], required=False)
    type = serializers.ChoiceField(choices=["video", "program", "bundle", "library"], required=False)
    target_id = serializers.CharField(required=False, allow_blank=True)
    object_id = serializers.CharField(required=False, allow_blank=True)
    id = serializers.CharField(required=False, allow_blank=True)
    admin_override = serializers.BooleanField(required=False, default=True)

    def validate(self, attrs):
        target_type = attrs.get("target_type") or attrs.get("content_type") or attrs.get("type")
        target_id = attrs.get("target_id") or attrs.get("object_id") or attrs.get("id")
        if not target_type:
            raise serializers.ValidationError({"target_type": "target_type/content_type is required"})
        if target_type != "library" and not target_id:
            raise serializers.ValidationError({"target_id": "target_id/object_id is required"})
        attrs["target_type"] = target_type
        attrs["target_id"] = target_id or ""
        return attrs


class AccessDecisionSerializer(serializers.Serializer):
    allowed = serializers.BooleanField()
    code = serializers.CharField()
    reason = serializers.CharField()
    target_type = serializers.CharField()
    target_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    content = serializers.DictField()
    entitlement_id = serializers.CharField(required=False, allow_null=True)
    source = serializers.CharField(required=False, allow_null=True)


class AccessAuditRuleSerializer(serializers.Serializer):
    code = serializers.CharField()
    label = serializers.CharField()
    passed = serializers.BooleanField()
    severity = serializers.CharField()
    reason = serializers.CharField()


class AccessAuditDecisionSerializer(AccessDecisionSerializer):
    requested_target_id = serializers.CharField(required=False, allow_blank=True)
    source_type = serializers.CharField(required=False, allow_null=True)
    source_reference = serializers.CharField(required=False, allow_null=True)
    evaluated_at = serializers.CharField()
    rules = AccessAuditRuleSerializer(many=True)
    audit = serializers.DictField()
