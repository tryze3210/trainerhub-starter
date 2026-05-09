from __future__ import annotations

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.trainers.api.readiness_serializers import AdminTrainerApplicationReadinessQuerySerializer
from apps.trainers.application_readiness import build_trainer_application_readiness


class AdminTrainerApplicationReadinessApi(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        serializer = AdminTrainerApplicationReadinessQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = build_trainer_application_readiness(**serializer.validated_data)
        return Response(payload)
