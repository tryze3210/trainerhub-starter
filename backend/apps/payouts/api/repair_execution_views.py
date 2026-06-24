from __future__ import annotations

from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.payouts.repair_execution import PayoutRepairExecutionService


class AdminPayoutOpsRepairExecuteAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        payload = PayoutRepairExecutionService.execute(
            params=request.data or {},
            actor=request.user,
            request=request,
        )
        return Response(payload)
