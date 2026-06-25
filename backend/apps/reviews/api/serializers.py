from rest_framework import serializers


class ReviewSerializer(serializers.Serializer):
    id = serializers.CharField()
    target_type = serializers.CharField()
    target_id = serializers.CharField()
    target_title = serializers.CharField(required=False, allow_blank=True)
    target_slug = serializers.CharField(required=False, allow_blank=True)
    trainer_id = serializers.CharField(required=False, allow_blank=True)
    author_name = serializers.CharField()
    rating = serializers.IntegerField()
    title = serializers.CharField()
    body = serializers.CharField()
    status = serializers.CharField()
    verified_purchase = serializers.BooleanField(required=False)
    quality_flags = serializers.ListField(child=serializers.CharField(), required=False)
    moderation_note = serializers.CharField(required=False, allow_blank=True)
    moderated_by_id = serializers.CharField(required=False, allow_blank=True)
    moderated_at = serializers.CharField(required=False, allow_null=True)
    trainer_reply = serializers.CharField(required=False, allow_blank=True)
    trainer_reply_by_id = serializers.CharField(required=False, allow_blank=True)
    trainer_replied_at = serializers.CharField(required=False, allow_null=True)
    created_at = serializers.CharField(allow_null=True)
    updated_at = serializers.CharField(required=False, allow_null=True)


class ReviewSummarySerializer(serializers.Serializer):
    target_type = serializers.CharField()
    target_id = serializers.CharField()
    reviews_count = serializers.IntegerField()
    average_rating = serializers.FloatField()
    rating_distribution = serializers.DictField(child=serializers.IntegerField(), required=False)


class ReviewEligibilitySerializer(serializers.Serializer):
    can_review = serializers.BooleanField()
    code = serializers.CharField()
    reason = serializers.CharField()
    entitlement_id = serializers.CharField(required=False, allow_null=True)
    verified_purchase = serializers.BooleanField(required=False)
    target = serializers.DictField(required=False)


class ReviewCreateSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    title = serializers.CharField(max_length=160)
    body = serializers.CharField()


class ReviewModerationSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=['publish', 'reject', 'flag'])
    note = serializers.CharField(required=False, allow_blank=True)


class ReviewReplySerializer(serializers.Serializer):
    reply = serializers.CharField()


class TargetReviewPayloadSerializer(serializers.Serializer):
    summary = ReviewSummarySerializer()
    items = ReviewSerializer(many=True)
    viewer_review = ReviewSerializer(allow_null=True, required=False)
    eligibility = ReviewEligibilitySerializer(required=False)
