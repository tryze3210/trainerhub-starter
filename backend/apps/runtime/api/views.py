from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.runtime.api.serializers import (
    CachePingSerializer,
    RuntimeConfigSerializer,
    RuntimeHealthSerializer,
    RuntimeReadinessSerializer,
)
from apps.runtime.services import RuntimeService


class RuntimeHealthView(APIView):
    service = RuntimeService()

    def get(self, request):
        return Response(RuntimeHealthSerializer(self.service.health()).data)


class RuntimeReadinessView(APIView):
    service = RuntimeService()

    def get(self, request):
        return Response(RuntimeReadinessSerializer(self.service.readiness()).data)


class RuntimeConfigView(APIView):
    service = RuntimeService()

    def get(self, request):
        return Response(RuntimeConfigSerializer(self.service.config()).data)


class CachePingView(APIView):
    service = RuntimeService()

    def post(self, request):
        return Response(CachePingSerializer(self.service.cache_ping()).data, status=status.HTTP_202_ACCEPTED)
