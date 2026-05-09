from __future__ import annotations

from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.payouts.api.readiness_serializers import (
    AdminPayoutReadinessQuerySerializer,
    AdminPayoutReadinessSerializer,
)
from apps.payouts.readiness import PayoutReadinessOptions, build_admin_payout_readiness


class AdminPayoutReadinessAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        query = AdminPayoutReadinessQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        payload = build_admin_payout_readiness(
            options=PayoutReadinessOptions(
                include_projection=query.validated_data["include_projection"],
                include_reconciliation=query.validated_data["include_reconciliation"],
                include_recommendations=query.validated_data["include_recommendations"],
            )
        )
        return Response(AdminPayoutReadinessSerializer(payload).data)
