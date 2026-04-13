from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.api.serializers import (
    AnalyticsEventIngestSerializer,
    AttributionRowSerializer,
    CohortRetentionSerializer,
    FunnelPointSerializer,
    KPIOverviewSerializer,
    RevenueSeriesPointSerializer,
    TopPathSerializer,
    TopTrainerSerializer,
    TrafficBreakdownPointSerializer,
    WarehouseHealthSerializer,
)
from apps.analytics.selectors.kpi_selectors import KPISelectors, TrafficSelectors


class AdminAnalyticsBaseView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @staticmethod
    def _get_days(request, default: int = 30, max_days: int = 365) -> int:
        try:
            days = int(request.query_params.get('days', default))
        except (TypeError, ValueError):
            days = default
        return max(1, min(days, max_days))

    @staticmethod
    def _get_limit(request, default: int = 10, max_limit: int = 100) -> int:
        try:
            limit = int(request.query_params.get('limit', default))
        except (TypeError, ValueError):
            limit = default
        return max(1, min(limit, max_limit))

    def _traffic_filters(self, request) -> dict:
        return {
            'days': self._get_days(request, default=30, max_days=180),
            'source': request.query_params.get('source', '').strip(),
            'medium': request.query_params.get('medium', '').strip(),
            'campaign': request.query_params.get('campaign', '').strip(),
            'trainer_id': request.query_params.get('trainer_id', '').strip(),
            'path_prefix': request.query_params.get('path_prefix', '').strip(),
        }


class AnalyticsEventCollectView(generics.CreateAPIView):
    serializer_class = AnalyticsEventIngestSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response({'event_uuid': str(instance.event_uuid)}, status=status.HTTP_201_CREATED)


class KPIOverviewView(AdminAnalyticsBaseView):
    def get(self, request, *args, **kwargs):
        data = KPISelectors.overview(days=self._get_days(request, default=30, max_days=365))
        serializer = KPIOverviewSerializer(data)
        return Response(serializer.data)


class RevenueTimeSeriesView(AdminAnalyticsBaseView):
    def get(self, request, *args, **kwargs):
        data = KPISelectors.revenue_timeseries(days=self._get_days(request, default=30, max_days=365))
        serializer = RevenueSeriesPointSerializer(data, many=True)
        return Response(serializer.data)


class TopTrainersView(AdminAnalyticsBaseView):
    def get(self, request, *args, **kwargs):
        days = self._get_days(request, default=30, max_days=365)
        limit = self._get_limit(request, default=10, max_limit=100)
        data = KPISelectors.top_trainers(days=days, limit=limit)
        serializer = TopTrainerSerializer(data, many=True)
        return Response(serializer.data)


class FunnelTimeSeriesView(AdminAnalyticsBaseView):
    def get(self, request, *args, **kwargs):
        data = KPISelectors.funnel_timeseries(days=self._get_days(request, default=30, max_days=180))
        serializer = FunnelPointSerializer(data, many=True)
        return Response(serializer.data)


class RetentionCohortsView(AdminAnalyticsBaseView):
    def get(self, request, *args, **kwargs):
        data = KPISelectors.retention_cohorts(days=self._get_days(request, default=60, max_days=365))
        serializer = CohortRetentionSerializer(data, many=True)
        return Response(serializer.data)


class WarehouseHealthView(AdminAnalyticsBaseView):
    def get(self, request, *args, **kwargs):
        data = KPISelectors.warehouse_health()
        serializer = WarehouseHealthSerializer(data)
        return Response(serializer.data)


class TrafficTimeSeriesView(AdminAnalyticsBaseView):
    def get(self, request, *args, **kwargs):
        data = TrafficSelectors.timeseries(**self._traffic_filters(request))
        serializer = TrafficBreakdownPointSerializer(data, many=True)
        return Response(serializer.data)


class TrafficTopPathsView(AdminAnalyticsBaseView):
    def get(self, request, *args, **kwargs):
        filters = self._traffic_filters(request)
        limit = self._get_limit(request, default=10, max_limit=100)
        data = TrafficSelectors.top_paths(limit=limit, **filters)
        serializer = TopPathSerializer(data, many=True)
        return Response(serializer.data)


class TrafficAttributionView(AdminAnalyticsBaseView):
    def get(self, request, *args, **kwargs):
        filters = self._traffic_filters(request)
        limit = self._get_limit(request, default=10, max_limit=100)
        data = TrafficSelectors.attribution(limit=limit, **filters)
        serializer = AttributionRowSerializer(data, many=True)
        return Response(serializer.data)
