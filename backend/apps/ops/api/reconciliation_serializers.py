from __future__ import annotations

from rest_framework import serializers


class AdminReconciliationQuerySerializer(serializers.Serializer):
    limit = serializers.IntegerField(required=False, min_value=1, max_value=500, default=100)
