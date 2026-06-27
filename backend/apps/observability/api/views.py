from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access_control.permissions import IsAdminSupportFinanceReadonly
from apps.observability.api.serializers import (
    CorrelationViewSerializer,
    LogRecordSerializer,
    MetricSampleSerializer,
    ObservabilityOverviewSerializer,
    ObservabilityRuntimeQuerySerializer,
    ObservabilityRuntimeSnapshotSerializer,
    TraceSpanSerializer,
)
from apps.observability.runtime import get_observability_runtime_snapshot
from apps.observability.services import ObservabilityService


class ObservabilityOverviewView(APIView):
    service = ObservabilityService()

    def get(self, request):
        return Response(ObservabilityOverviewSerializer(self.service.overview()).data)


class MetricListView(APIView):
    service = ObservabilityService()

    def get(self, request):
        return Response(MetricSampleSerializer(self.service.metrics(), many=True).data)


class LogRecordListView(APIView):
    service = ObservabilityService()

    def get(self, request):
        return Response(LogRecordSerializer(self.service.logs(), many=True).data)


class TraceSpanListView(APIView):
    service = ObservabilityService()

    def get(self, request):
        return Response(TraceSpanSerializer(self.service.traces(), many=True).data)


class CorrelationDetailView(APIView):
    service = ObservabilityService()

    def get(self, request, correlation_id: str):
        return Response(CorrelationViewSerializer(self.service.correlation(correlation_id)).data)


class ObservabilityRuntimeView(APIView):
    permission_classes = [IsAdminSupportFinanceReadonly]

    def get(self, request):
        serializer = ObservabilityRuntimeQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = get_observability_runtime_snapshot(**serializer.validated_data)
        return Response(ObservabilityRuntimeSnapshotSerializer(payload).data)
