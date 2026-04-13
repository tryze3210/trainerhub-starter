from rest_framework.response import Response
from rest_framework.views import APIView

from apps.observability.api.serializers import (
    CorrelationViewSerializer,
    LogRecordSerializer,
    MetricSampleSerializer,
    ObservabilityOverviewSerializer,
    TraceSpanSerializer,
)
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
