from rest_framework import serializers


class ActiveTenantSerializer(serializers.Serializer):
    id = serializers.CharField()
    code = serializers.CharField()
    name = serializers.CharField()
    kind = serializers.CharField()
    membership_role = serializers.CharField()
    permissions = serializers.ListField(child=serializers.CharField())


class MembershipSerializer(serializers.Serializer):
    tenant_id = serializers.CharField()
    tenant_code = serializers.CharField()
    tenant_name = serializers.CharField()
    tenant_kind = serializers.CharField()
    membership_role = serializers.CharField()
    status = serializers.CharField()
    permissions = serializers.ListField(child=serializers.CharField())


class TenantContextSerializer(serializers.Serializer):
    active_tenant = ActiveTenantSerializer()
    memberships = MembershipSerializer(many=True)
    accessible_tenant_ids = serializers.ListField(child=serializers.CharField())


class TenantSwitchSerializer(serializers.Serializer):
    tenant_code = serializers.CharField()
