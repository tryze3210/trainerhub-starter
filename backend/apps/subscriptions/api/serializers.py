from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from apps.subscriptions.lifecycle import SubscriptionLifecycleService
from apps.subscriptions.models import Subscription, SubscriptionPlan, SubscriptionStatus


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'code', 'title', 'period_days', 'price', 'currency', 'is_active']


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    plan_name = serializers.CharField(source='plan.title', read_only=True)
    currency = serializers.CharField(source='plan.currency', read_only=True)
    amount = serializers.DecimalField(source='plan.price', max_digits=12, decimal_places=2, read_only=True)
    price_amount = serializers.DecimalField(source='plan.price', max_digits=12, decimal_places=2, read_only=True)
    started_at = serializers.DateTimeField(source='starts_at', read_only=True)
    current_period_start = serializers.DateTimeField(source='starts_at', read_only=True)
    current_period_end = serializers.DateTimeField(source='ends_at', read_only=True)
    cancel_at = serializers.DateTimeField(source='cancelled_at', read_only=True)
    canceled_at = serializers.DateTimeField(source='cancelled_at', read_only=True)
    is_active = serializers.SerializerMethodField()
    remaining_days = serializers.SerializerMethodField()
    entitlement_count = serializers.SerializerMethodField()
    lifecycle = serializers.SerializerMethodField()
    renewal_projection = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = [
            'id',
            'status',
            'starts_at',
            'ends_at',
            'cancelled_at',
            'auto_renew',
            'plan',
            'plan_name',
            'currency',
            'amount',
            'price_amount',
            'started_at',
            'created_at',
            'updated_at',
            'current_period_start',
            'current_period_end',
            'cancel_at',
            'canceled_at',
            'is_active',
            'remaining_days',
            'entitlement_count',
            'lifecycle',
            'renewal_projection',
        ]

    def get_is_active(self, obj):
        from django.utils import timezone

        now = timezone.now()
        return obj.status in {SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE} and (obj.ends_at is None or obj.ends_at > now)

    def get_remaining_days(self, obj):
        from django.utils import timezone

        if not obj.ends_at:
            return None
        return max(0, (obj.ends_at - timezone.now()).days)

    def get_entitlement_count(self, obj):
        try:
            return obj.granted_entitlements.count()
        except Exception:
            return 0

    def get_lifecycle(self, obj):
        now_active = self.get_is_active(obj)
        return {
            'can_cancel': obj.status in {SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE, SubscriptionStatus.PENDING},
            'can_resume': obj.status in {SubscriptionStatus.CANCELLED, SubscriptionStatus.PAST_DUE}
            and (obj.ends_at is None or obj.ends_at > timezone.now()),
            'can_sync_entitlements': True,
            'is_terminal': obj.status in {SubscriptionStatus.CANCELLED, SubscriptionStatus.EXPIRED},
            'is_access_active': now_active,
            'status_label': obj.get_status_display() if hasattr(obj, 'get_status_display') else obj.status,
        }

    def get_renewal_projection(self, obj):
        try:
            return SubscriptionLifecycleService.project_renewal(obj)
        except Exception:
            return None


class SubscriptionActionSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)


class AdminSubscriptionListQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(required=False, choices=SubscriptionStatus.choices)
    search = serializers.CharField(required=False, allow_blank=True, max_length=255)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=250, default=100)
