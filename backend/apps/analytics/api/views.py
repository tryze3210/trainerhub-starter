from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone
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
    TrainerRevenueDashboardSerializer,
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


class TrainerRevenueDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        from apps.orders.models import OrderItem
        from apps.payments.models import Payment, PaymentStatus
        from apps.payouts.models import PayoutLedgerEntry, PayoutRequest
        from apps.payouts.services import PayoutService

        trainer_id = request.user.id
        today = timezone.localdate()
        start_date = today - timedelta(days=29)

        balance = PayoutService.get_or_create_balance(trainer_id=trainer_id)
        accrual_rows = (
            PayoutLedgerEntry.objects.filter(
                trainer_id=trainer_id,
                entry_type=PayoutLedgerEntry.EntryType.ACCRUAL,
                created_at__date__gte=start_date,
            )
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(accrual_amount=Coalesce(Sum('amount'), Decimal('0.00')))
            .order_by('day')
        )
        payout_rows = (
            PayoutLedgerEntry.objects.filter(
                trainer_id=trainer_id,
                entry_type=PayoutLedgerEntry.EntryType.PAYOUT,
                created_at__date__gte=start_date,
            )
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(payout_amount=Coalesce(Sum('amount'), Decimal('0.00')))
            .order_by('day')
        )
        order_rows = (
            Payment.objects.filter(
                status=PaymentStatus.SUCCEEDED,
                provider_payload__trainer_id=str(trainer_id),
                confirmed_at__date__gte=start_date,
            )
            .annotate(day=TruncDate('confirmed_at'))
            .values('day')
            .annotate(orders_count=Count('id'))
            .order_by('day')
        )

        accrual_map = {row['day']: row['accrual_amount'] for row in accrual_rows}
        payout_map = {row['day']: row['payout_amount'] for row in payout_rows}
        orders_map = {row['day']: row['orders_count'] for row in order_rows}

        revenue_series = []
        for offset in range(30):
            day = start_date + timedelta(days=offset)
            revenue_series.append({
                'date': day,
                'accrual_amount': accrual_map.get(day, Decimal('0.00')),
                'payout_amount': payout_map.get(day, Decimal('0.00')),
                'orders_count': orders_map.get(day, 0),
            })

        revenue_last_30_days = sum((item['accrual_amount'] for item in revenue_series), Decimal('0.00'))
        payouts_last_30_days = sum((item['payout_amount'] for item in revenue_series), Decimal('0.00'))
        paid_orders_qs = Payment.objects.filter(status=PaymentStatus.SUCCEEDED, provider_payload__trainer_id=str(trainer_id))
        paid_orders_count = paid_orders_qs.count()
        total_revenue = paid_orders_qs.aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
        avg_order_value = (total_revenue / paid_orders_count).quantize(Decimal('0.01')) if paid_orders_count else Decimal('0.00')

        top_products_qs = (
            OrderItem.objects.filter(order__payments__status=PaymentStatus.SUCCEEDED, metadata__trainer_id=str(trainer_id))
            .values('item_type', 'title_snapshot')
            .annotate(revenue=Coalesce(Sum('total_price'), Decimal('0.00')), orders_count=Count('id'))
            .order_by('-revenue', '-orders_count')[:5]
        )
        top_products = [
            {
                'item_type': row['item_type'],
                'title': row['title_snapshot'] or 'Untitled',
                'revenue': row['revenue'] or Decimal('0.00'),
                'orders_count': row['orders_count'] or 0,
            }
            for row in top_products_qs
        ]

        payout_requests = PayoutRequest.objects.filter(trainer_id=trainer_id)
        pending_statuses = [PayoutRequest.Status.PENDING, PayoutRequest.Status.APPROVED, PayoutRequest.Status.PROCESSING]
        payload = {
            'summary': {
                'currency': balance.currency,
                'available_amount': balance.available_amount,
                'reserved_amount': balance.reserved_amount,
                'lifetime_earned_amount': balance.lifetime_earned_amount,
                'revenue_last_30_days': revenue_last_30_days,
                'payouts_last_30_days': payouts_last_30_days,
                'paid_orders_count': paid_orders_count,
                'payout_requests_count': payout_requests.count(),
                'pending_payout_requests_count': payout_requests.filter(status__in=pending_statuses).count(),
                'avg_order_value': avg_order_value,
            },
            'revenue_series': revenue_series,
            'top_products': top_products,
        }
        return Response(TrainerRevenueDashboardSerializer(payload).data)
