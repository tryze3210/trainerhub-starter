from rest_framework import serializers

from apps.analytics.models import AnalyticsEvent


class KPIOverviewSerializer(serializers.Serializer):
    range_days = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    gross_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    paid_orders = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    new_customers = serializers.IntegerField()
    new_trainers = serializers.IntegerField()
    new_subscriptions = serializers.IntegerField()
    active_subscriptions = serializers.IntegerField()
    conversion_rate = serializers.DecimalField(max_digits=7, decimal_places=4)
    arppu = serializers.DecimalField(max_digits=14, decimal_places=2)
    last_aggregated_date = serializers.DateField(allow_null=True)


class RevenueSeriesPointSerializer(serializers.Serializer):
    date = serializers.DateField()
    gross_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    paid_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_orders = serializers.IntegerField()
    paid_orders = serializers.IntegerField()


class TopTrainerSerializer(serializers.Serializer):
    trainer_id = serializers.UUIDField()
    paid_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    gross_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    paid_orders = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    new_customers = serializers.IntegerField()
    active_subscribers = serializers.IntegerField()


class FunnelPointSerializer(serializers.Serializer):
    date = serializers.DateField()
    signups = serializers.IntegerField()
    ordering_customers = serializers.IntegerField()
    paid_customers = serializers.IntegerField()
    new_subscribers = serializers.IntegerField()
    signup_to_order_rate = serializers.DecimalField(max_digits=7, decimal_places=4)
    order_to_paid_rate = serializers.DecimalField(max_digits=7, decimal_places=4)
    paid_to_subscription_rate = serializers.DecimalField(max_digits=7, decimal_places=4)


class CohortRetentionSerializer(serializers.Serializer):
    cohort_date = serializers.DateField()
    cohort_size = serializers.IntegerField()
    retained_day_0 = serializers.IntegerField()
    retained_day_1 = serializers.IntegerField()
    retained_day_7 = serializers.IntegerField()
    retained_day_30 = serializers.IntegerField()
    retention_day_1_rate = serializers.DecimalField(max_digits=7, decimal_places=4)
    retention_day_7_rate = serializers.DecimalField(max_digits=7, decimal_places=4)
    retention_day_30_rate = serializers.DecimalField(max_digits=7, decimal_places=4)


class WarehouseHealthSerializer(serializers.Serializer):
    status = serializers.CharField()
    last_success_started_at = serializers.DateTimeField(allow_null=True)
    last_success_finished_at = serializers.DateTimeField(allow_null=True)
    last_success_range_start = serializers.DateField(allow_null=True)
    last_success_range_end = serializers.DateField(allow_null=True)
    last_success_rows_written = serializers.IntegerField()
    latest_failure_message = serializers.CharField(allow_blank=True)


class AnalyticsEventIngestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsEvent
        fields = [
            'event_uuid',
            'event_name',
            'occurred_at',
            'session_id',
            'anonymous_id',
            'user_id',
            'trainer_id',
            'order_id',
            'path',
            'referrer',
            'utm_source',
            'utm_medium',
            'utm_campaign',
            'country_code',
            'device_type',
            'metadata',
        ]
        extra_kwargs = {
            'event_uuid': {'required': False},
            'anonymous_id': {'required': False, 'allow_blank': True},
            'user_id': {'required': False, 'allow_null': True},
            'trainer_id': {'required': False, 'allow_null': True},
            'order_id': {'required': False, 'allow_null': True},
            'path': {'required': False, 'allow_blank': True},
            'referrer': {'required': False, 'allow_blank': True},
            'utm_source': {'required': False, 'allow_blank': True},
            'utm_medium': {'required': False, 'allow_blank': True},
            'utm_campaign': {'required': False, 'allow_blank': True},
            'country_code': {'required': False, 'allow_blank': True},
            'device_type': {'required': False, 'allow_blank': True},
            'metadata': {'required': False},
        }

    def create(self, validated_data):
        validated_data['event_date'] = validated_data['occurred_at'].date()
        return super().create(validated_data)


class TrafficBreakdownPointSerializer(serializers.Serializer):
    date = serializers.DateField()
    sessions = serializers.IntegerField()
    unique_users = serializers.IntegerField()
    page_views = serializers.IntegerField()
    video_views = serializers.IntegerField()
    checkout_starts = serializers.IntegerField()
    purchases = serializers.IntegerField()


class TopPathSerializer(serializers.Serializer):
    path = serializers.CharField()
    sessions = serializers.IntegerField()
    page_views = serializers.IntegerField()
    video_views = serializers.IntegerField()
    checkout_starts = serializers.IntegerField()
    purchases = serializers.IntegerField()


class AttributionRowSerializer(serializers.Serializer):
    utm_source = serializers.CharField()
    utm_medium = serializers.CharField()
    utm_campaign = serializers.CharField()
    sessions = serializers.IntegerField()
    page_views = serializers.IntegerField()
    purchases = serializers.IntegerField()


class TrainerRevenueSeriesPointSerializer(serializers.Serializer):
    date = serializers.DateField()
    accrual_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    payout_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    orders_count = serializers.IntegerField()


class TrainerTopProductSerializer(serializers.Serializer):
    item_type = serializers.CharField()
    title = serializers.CharField()
    revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    orders_count = serializers.IntegerField()


class TrainerRevenueSummarySerializer(serializers.Serializer):
    currency = serializers.CharField()
    available_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    reserved_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    lifetime_earned_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    revenue_last_30_days = serializers.DecimalField(max_digits=14, decimal_places=2)
    payouts_last_30_days = serializers.DecimalField(max_digits=14, decimal_places=2)
    paid_orders_count = serializers.IntegerField()
    payout_requests_count = serializers.IntegerField()
    pending_payout_requests_count = serializers.IntegerField()
    avg_order_value = serializers.DecimalField(max_digits=14, decimal_places=2)


class TrainerRevenueDashboardSerializer(serializers.Serializer):
    summary = TrainerRevenueSummarySerializer()
    revenue_series = TrainerRevenueSeriesPointSerializer(many=True)
    top_products = TrainerTopProductSerializer(many=True)
