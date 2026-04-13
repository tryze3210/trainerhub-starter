from rest_framework import serializers


class ReviewSerializer(serializers.Serializer):
    id = serializers.CharField()
    target_type = serializers.CharField()
    target_id = serializers.CharField()
    author_name = serializers.CharField()
    rating = serializers.IntegerField()
    title = serializers.CharField()
    body = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.CharField()


class ReviewSummarySerializer(serializers.Serializer):
    target_type = serializers.CharField()
    target_id = serializers.CharField()
    reviews_count = serializers.IntegerField()
    average_rating = serializers.FloatField()


class TargetReviewPayloadSerializer(serializers.Serializer):
    summary = ReviewSummarySerializer()
    items = ReviewSerializer(many=True)
