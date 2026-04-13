from rest_framework import serializers

from apps.finance_reporting.models import FinanceReconciliationSnapshot, SettlementReport, TrainerSettlementLine


class FinanceReconciliationSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinanceReconciliationSnapshot
        fields = "__all__"


class TrainerSettlementLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerSettlementLine
        fields = "__all__"


class SettlementReportSerializer(serializers.ModelSerializer):
    lines = TrainerSettlementLineSerializer(many=True, read_only=True)

    class Meta:
        model = SettlementReport
        fields = "__all__"
