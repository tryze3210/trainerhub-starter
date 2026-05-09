from __future__ import annotations

from rest_framework import serializers


class AdminPayoutReadinessQuerySerializer(serializers.Serializer):
    include_projection = serializers.BooleanField(required=False, default=True)
    include_reconciliation = serializers.BooleanField(required=False, default=True)
    include_recommendations = serializers.BooleanField(required=False, default=True)


class AdminPayoutReadinessSerializer(serializers.Serializer):
    """Flexible response serializer for the payout readiness payload.

    The payload intentionally contains nested diagnostic maps from several payout
    subsystems. DictField/ListField keeps this endpoint stable while the
    internal checks evolve.
    """

    status = serializers.CharField()
    generated_at = serializers.CharField()
    summary = serializers.DictField()
    api_surface = serializers.DictField()
    workflow = serializers.DictField()
    checks = serializers.ListField(child=serializers.DictField())
    status_buckets = serializers.ListField(child=serializers.DictField())
    ledger_buckets = serializers.ListField(child=serializers.DictField())
    projection = serializers.DictField()
    reconciliation = serializers.DictField()
    recommendations = serializers.ListField(child=serializers.CharField(), required=False)
