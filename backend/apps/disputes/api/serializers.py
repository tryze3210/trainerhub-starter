from rest_framework import serializers

from apps.disputes.models import DisputeCase, DisputeEvent, RefundReview, ChargebackOperation


class DisputeEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisputeEvent
        fields = ["id", "event_type", "body", "payload", "created_at", "actor_id"]


class DisputeCaseSerializer(serializers.ModelSerializer):
    events = DisputeEventSerializer(many=True, read_only=True)

    class Meta:
        model = DisputeCase
        fields = [
            "id", "public_id", "dispute_type", "status", "subject", "reason_code", "summary",
            "resolution_note", "opened_at", "resolved_at", "trainer_id", "order_id", "payment_id",
            "opened_by_id", "assigned_to_id", "metadata", "events",
        ]


class CreateDisputeCaseSerializer(serializers.Serializer):
    dispute_type = serializers.ChoiceField(choices=DisputeCase.TYPE_CHOICES)
    subject = serializers.CharField(max_length=255)
    summary = serializers.CharField(required=False, allow_blank=True)
    reason_code = serializers.CharField(required=False, allow_blank=True)
    trainer_id = serializers.UUIDField(required=False)
    order_id = serializers.UUIDField(required=False)
    payment_id = serializers.UUIDField(required=False)


class RefundReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefundReview
        fields = ["id", "requested_amount", "approved_amount", "currency", "decision", "reviewed_by_id", "reviewed_at", "rationale"]


class ChargebackOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChargebackOperation
        fields = ["id", "provider_case_id", "network", "amount", "currency", "status", "evidence_due_at", "evidence_payload", "provider_payload"]
