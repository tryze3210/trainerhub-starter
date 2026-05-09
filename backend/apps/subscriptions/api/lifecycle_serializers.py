from __future__ import annotations

from rest_framework import serializers

from apps.subscriptions.models import SubscriptionStatus


class SubscriptionLifecycleActionSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)
    sync_entitlements = serializers.BooleanField(required=False, default=True)


class SubscriptionLifecycleReconcileSerializer(serializers.Serializer):
    subscription_id = serializers.UUIDField(required=False)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=500, default=100)


class SubscriptionLifecycleSummaryQuerySerializer(serializers.Serializer):
    days = serializers.IntegerField(required=False, min_value=1, max_value=365, default=30)


class AdminSubscriptionLifecycleListQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(required=False, choices=SubscriptionStatus.choices)
    search = serializers.CharField(required=False, allow_blank=True, max_length=255)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=250, default=100)
