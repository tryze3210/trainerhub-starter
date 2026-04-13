from rest_framework import serializers

from apps.moderation.domain.models import ModerationCase, ModerationReviewDecision, TrainerRiskFlag


class ModerationCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModerationCase
        fields = [
            "id", "target_type", "target_id", "title", "summary", "status", "priority", "queue",
            "latest_decision", "trainer", "assigned_to", "opened_at", "updated_at", "resolved_at",
        ]


class ModerationDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModerationReviewDecision
        fields = ["id", "case", "reviewer", "decision", "reason", "metadata", "created_at"]


class TrainerRiskFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerRiskFlag
        fields = ["id", "trainer", "code", "label", "risk_level", "is_active", "source", "details", "created_at", "resolved_at"]
