from rest_framework import serializers
from apps.subscriptions.models import Subscription, SubscriptionPlan


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'code', 'title', 'period_days', 'price', 'currency', 'is_active']


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = ['id', 'status', 'starts_at', 'ends_at', 'cancelled_at', 'auto_renew', 'plan']
