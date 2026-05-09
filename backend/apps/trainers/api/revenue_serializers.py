from rest_framework import serializers


class TrainerRevenuePeriodQuerySerializer(serializers.Serializer):
    days = serializers.IntegerField(min_value=1, max_value=365, default=30, required=False)


class TrainerRevenueListQuerySerializer(serializers.Serializer):
    limit = serializers.IntegerField(min_value=1, max_value=500, default=100, required=False)
