from rest_framework import serializers


class OnboardingStepSerializer(serializers.Serializer):
    code = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    role_scope = serializers.CharField()
    is_completed = serializers.BooleanField()
    sort_order = serializers.IntegerField()


class OnboardingSummarySerializer(serializers.Serializer):
    completed_steps = serializers.IntegerField()
    total_steps = serializers.IntegerField()
    completion_percent = serializers.IntegerField()
    next_step = serializers.CharField(allow_null=True)


class OnboardingStatusSerializer(serializers.Serializer):
    steps = OnboardingStepSerializer(many=True)
    summary = OnboardingSummarySerializer()


class CompleteStepSerializer(serializers.Serializer):
    step_code = serializers.CharField()
    payload = serializers.DictField(required=False)
