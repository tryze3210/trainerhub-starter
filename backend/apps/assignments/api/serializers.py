from rest_framework import serializers

from apps.assignments.models import AssignmentContentType, AssignmentStatus, SubmissionStatus


class AssignmentCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    content_type = serializers.ChoiceField(choices=AssignmentContentType.choices)
    content_id = serializers.CharField(max_length=80)
    lesson_id = serializers.CharField(max_length=80, required=False, allow_blank=True)
    due_at = serializers.DateTimeField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=AssignmentStatus.choices, required=False)
    metadata = serializers.JSONField(required=False)


class AssignmentSubmitSerializer(serializers.Serializer):
    answer_text = serializers.CharField(required=False, allow_blank=True)
    attachments = serializers.ListField(child=serializers.DictField(), required=False)


class AssignmentReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[
            (SubmissionStatus.REVIEWED, "Reviewed"),
            (SubmissionStatus.NEEDS_REVISION, "Needs revision"),
            (SubmissionStatus.APPROVED, "Approved"),
        ],
        required=False,
    )
    review_comment = serializers.CharField(required=False, allow_blank=True)
    score = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
