from rest_framework import serializers


class TrainerAnalyticsPeriodQuerySerializer(serializers.Serializer):
    days = serializers.IntegerField(min_value=1, max_value=365, default=30)


class TrainerContentAnalyticsQuerySerializer(TrainerAnalyticsPeriodQuerySerializer):
    type = serializers.ChoiceField(choices=["all", "video", "product"], default="all")
    limit = serializers.IntegerField(min_value=1, max_value=200, default=50)


class TrainerSalesAnalyticsQuerySerializer(TrainerAnalyticsPeriodQuerySerializer):
    limit = serializers.IntegerField(min_value=1, max_value=200, default=50)
