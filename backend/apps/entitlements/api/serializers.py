from rest_framework import serializers
from apps.entitlements.models import Entitlement


class EntitlementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entitlement
        fields = ['id', 'source_type', 'source_order_id', 'source_subscription_id', 'target_type', 'target_id', 'status', 'starts_at', 'ends_at', 'metadata']
