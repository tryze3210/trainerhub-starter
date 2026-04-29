from rest_framework import serializers

from apps.moderation.domain.models import (
    ModerationCase,
    ModerationCaseEvent,
    ModerationReviewDecision,
    TrainerRiskFlag,
)


class ModerationCaseEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModerationCaseEvent
        fields = ["id", "actor", "event_type", "payload", "created_at"]


class ModerationDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModerationReviewDecision
        fields = ["id", "case", "reviewer", "decision", "reason", "metadata", "created_at"]


class ModerationCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModerationCase
        fields = [
            "id", "target_type", "target_id", "title", "summary", "status", "priority", "queue",
            "latest_decision", "trainer", "assigned_to", "opened_at", "updated_at", "resolved_at",
        ]


class ModerationCaseDetailSerializer(ModerationCaseSerializer):
    events = ModerationCaseEventSerializer(many=True, read_only=True)
    decisions = ModerationDecisionSerializer(many=True, read_only=True)

    class Meta(ModerationCaseSerializer.Meta):
        fields = ModerationCaseSerializer.Meta.fields + ["events", "decisions"]


class ModerationDecisionInputSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["approved", "rejected", "needs_changes", "escalated"])
    reason = serializers.CharField(required=False, allow_blank=True, default="")
    metadata = serializers.JSONField(required=False, default=dict)


class ModerationAssignSerializer(serializers.Serializer):
    assignee_id = serializers.UUIDField(required=False, allow_null=True)


class TrainerRiskFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerRiskFlag
        fields = ["id", "trainer", "code", "label", "risk_level", "is_active", "source", "details", "created_at", "resolved_at"]


class TrainerRiskFlagCreateSerializer(serializers.Serializer):
    trainer_id = serializers.UUIDField()
    code = serializers.CharField(max_length=64)
    label = serializers.CharField(max_length=255)
    risk_level = serializers.ChoiceField(choices=["low", "medium", "high", "critical"])
    details = serializers.JSONField(required=False, default=dict)
