from __future__ import annotations

from rest_framework import serializers

from apps.trainers.models import TrainerApplication


class TrainerOnboardingStateQuerySerializer(serializers.Serializer):
    include_profile = serializers.BooleanField(required=False, default=True)


class AdminTrainerApplicationListQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[choice[0] for choice in TrainerApplication.Status.choices],
        required=False,
        allow_blank=True,
    )
    search = serializers.CharField(required=False, allow_blank=True, max_length=255)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=250, default=100)


class AdminTrainerApplicationReviewSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(
        choices=(
            "approve",
            "approved",
            "reject",
            "rejected",
            "request_changes",
            "changes_requested",
            "needs_changes",
            "under_review",
        )
    )
    reviewer_note = serializers.CharField(required=False, allow_blank=True, max_length=4000)

    def validate(self, attrs):
        decision = attrs.get("decision")
        note = (attrs.get("reviewer_note") or "").strip()
        if decision in {"reject", "rejected", "request_changes", "changes_requested", "needs_changes"} and not note:
            raise serializers.ValidationError({"reviewer_note": "Reviewer note is required for rejection or changes request."})
        attrs["reviewer_note"] = note
        return attrs
