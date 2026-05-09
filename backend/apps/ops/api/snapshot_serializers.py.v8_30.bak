from __future__ import annotations

from rest_framework import serializers


class AdminReconciliationSnapshotListSerializer(serializers.Serializer):
    limit = serializers.IntegerField(required=False, min_value=1, max_value=250, default=20)
    source = serializers.ChoiceField(
        required=False,
        allow_blank=True,
        choices=(('', 'Any'), ('manual', 'Manual'), ('scheduled', 'Scheduled'), ('repair', 'Repair'), ('ci', 'CI')),
        default='',
    )
    status = serializers.ChoiceField(
        required=False,
        allow_blank=True,
        choices=(('', 'Any'), ('ok', 'OK'), ('degraded', 'Degraded'), ('critical', 'Critical')),
        default='',
    )
    include_report = serializers.BooleanField(required=False, default=False)


class AdminReconciliationSnapshotCaptureSerializer(serializers.Serializer):
    limit = serializers.IntegerField(required=False, min_value=1, max_value=500, default=100)
    source = serializers.ChoiceField(
        required=False,
        choices=(('manual', 'Manual'), ('scheduled', 'Scheduled'), ('repair', 'Repair'), ('ci', 'CI')),
        default='manual',
    )
    correlation_id = serializers.CharField(required=False, allow_blank=True, max_length=128)


class AdminReconciliationSnapshotTrendSerializer(serializers.Serializer):
    limit = serializers.IntegerField(required=False, min_value=2, max_value=250, default=30)
