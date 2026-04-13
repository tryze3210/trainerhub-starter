from rest_framework import serializers

from apps.finance.models import ReconciliationDiscrepancy, ReconciliationSession, SettlementTransaction


class SettlementTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SettlementTransaction
        fields = (
            "id",
            "provider",
            "direction",
            "status",
            "amount",
            "currency",
            "provider_reference",
            "provider_batch_reference",
            "requested_at",
            "settled_at",
            "failed_at",
            "metadata",
        )


class ReconciliationDiscrepancySerializer(serializers.ModelSerializer):
    settlement_transaction = SettlementTransactionSerializer(read_only=True)

    class Meta:
        model = ReconciliationDiscrepancy
        fields = (
            "id",
            "session",
            "discrepancy_type",
            "status",
            "provider_reference",
            "internal_reference",
            "internal_amount",
            "provider_amount",
            "internal_status",
            "provider_status",
            "details",
            "resolution_notes",
            "resolved_at",
            "settlement_transaction",
        )


class ReconciliationSessionSerializer(serializers.ModelSerializer):
    discrepancies_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = ReconciliationSession
        fields = (
            "id",
            "provider",
            "status",
            "date_from",
            "date_to",
            "completed_at",
            "failed_at",
            "summary",
            "discrepancies_count",
            "created_at",
        )


class ReconciliationRunInputSerializer(serializers.Serializer):
    provider = serializers.CharField()
    date_from = serializers.DateTimeField()
    date_to = serializers.DateTimeField()


class DiscrepancyResolveInputSerializer(serializers.Serializer):
    notes = serializers.CharField()
    target_status = serializers.CharField(required=False)
