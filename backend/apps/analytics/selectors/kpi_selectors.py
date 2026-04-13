from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.db.models import Max, Sum
from django.utils import timezone

from apps.analytics.models import (
    AnalyticsRefreshLog,
    DailyPlatformFunnel,
    DailyPlatformKPI,
    DailyTrafficSlice,
    DailyTrainerKPI,
    DailyUserCohortRetention,
)


class KPISelectors:
    @staticmethod
    def overview(days: int = 30) -> dict:
        today = timezone.localdate()
        start_date = today - timedelta(days=days - 1)
        qs = DailyPlatformKPI.objects.filter(date__gte=start_date, date__lte=today)

        revenue = qs.aggregate(total=Sum('paid_revenue')).get('total') or Decimal('0.00')
        gross_revenue = qs.aggregate(total=Sum('gross_revenue')).get('total') or Decimal('0.00')
        paid_orders = qs.aggregate(total=Sum('paid_orders')).get('total') or 0
        total_orders = qs.aggregate(total=Sum('total_orders')).get('total') or 0
        new_customers = qs.aggregate(total=Sum('total_new_customers')).get('total') or 0
        new_trainers = qs.aggregate(total=Sum('total_new_trainers')).get('total') or 0
        new_subscriptions = qs.aggregate(total=Sum('new_subscriptions')).get('total') or 0
        last_row = qs.order_by('-date').first()

        conversion_rate = Decimal('0.0000')
        if total_orders:
            conversion_rate = (Decimal(paid_orders) / Decimal(total_orders)).quantize(Decimal('0.0001'))

        return {
            'range_days': days,
            'revenue': revenue,
            'gross_revenue': gross_revenue,
            'paid_orders': paid_orders,
            'total_orders': total_orders,
            'new_customers': new_customers,
            'new_trainers': new_trainers,
            'new_subscriptions': new_subscriptions,
            'active_subscriptions': last_row.active_subscriptions if last_row else 0,
            'conversion_rate': conversion_rate,
            'arppu': last_row.arppu if last_row else Decimal('0.00'),
            'last_aggregated_date': last_row.date if last_row else None,
        }

    @staticmethod
    def revenue_timeseries(days: int = 30) -> list[dict]:
        today = timezone.localdate()
        start_date = today - timedelta(days=days - 1)
        rows = DailyPlatformKPI.objects.filter(date__gte=start_date, date__lte=today).order_by('date')
        return [
            {
                'date': row.date,
                'gross_revenue': row.gross_revenue,
                'paid_revenue': row.paid_revenue,
                'total_orders': row.total_orders,
                'paid_orders': row.paid_orders,
            }
            for row in rows
        ]

    @staticmethod
    def top_trainers(days: int = 30, limit: int = 10) -> list[dict]:
        today = timezone.localdate()
        start_date = today - timedelta(days=days - 1)
        rows = (
            DailyTrainerKPI.objects.filter(date__gte=start_date, date__lte=today)
            .values('trainer_id')
            .annotate(
                paid_revenue_sum=Sum('paid_revenue'),
                gross_revenue_sum=Sum('gross_revenue'),
                paid_orders_sum=Sum('paid_orders'),
                total_orders_sum=Sum('total_orders'),
                new_customers_sum=Sum('new_customers'),
                active_subscribers_max=Max('active_subscribers'),
            )
            .order_by('-paid_revenue_sum')[:limit]
        )
        return [
            {
                'trainer_id': row['trainer_id'],
                'paid_revenue': row['paid_revenue_sum'] or Decimal('0.00'),
                'gross_revenue': row['gross_revenue_sum'] or Decimal('0.00'),
                'paid_orders': row['paid_orders_sum'] or 0,
                'total_orders': row['total_orders_sum'] or 0,
                'new_customers': row['new_customers_sum'] or 0,
                'active_subscribers': row['active_subscribers_max'] or 0,
            }
            for row in rows
        ]

    @staticmethod
    def funnel_timeseries(days: int = 30) -> list[dict]:
        today = timezone.localdate()
        start_date = today - timedelta(days=days - 1)
        rows = DailyPlatformFunnel.objects.filter(date__gte=start_date, date__lte=today).order_by('date')
        return [
            {
                'date': row.date,
                'signups': row.signups,
                'ordering_customers': row.ordering_customers,
                'paid_customers': row.paid_customers,
                'new_subscribers': row.new_subscribers,
                'signup_to_order_rate': row.signup_to_order_rate,
                'order_to_paid_rate': row.order_to_paid_rate,
                'paid_to_subscription_rate': row.paid_to_subscription_rate,
            }
            for row in rows
        ]

    @staticmethod
    def retention_cohorts(days: int = 60) -> list[dict]:
        today = timezone.localdate()
        start_date = today - timedelta(days=days - 1)
        rows = DailyUserCohortRetention.objects.filter(cohort_date__gte=start_date, cohort_date__lte=today).order_by('cohort_date')
        return [
            {
                'cohort_date': row.cohort_date,
                'cohort_size': row.cohort_size,
                'retained_day_0': row.retained_day_0,
                'retained_day_1': row.retained_day_1,
                'retained_day_7': row.retained_day_7,
                'retained_day_30': row.retained_day_30,
                'retention_day_1_rate': row.retention_day_1_rate,
                'retention_day_7_rate': row.retention_day_7_rate,
                'retention_day_30_rate': row.retention_day_30_rate,
            }
            for row in rows
        ]

    @staticmethod
    def warehouse_health() -> dict:
        last_success = AnalyticsRefreshLog.objects.filter(status=AnalyticsRefreshLog.STATUS_SUCCEEDED).first()
        latest_failure = AnalyticsRefreshLog.objects.filter(status=AnalyticsRefreshLog.STATUS_FAILED).first()
        return {
            'status': 'healthy' if last_success else 'empty',
            'last_success_started_at': last_success.started_at if last_success else None,
            'last_success_finished_at': last_success.finished_at if last_success else None,
            'last_success_range_start': last_success.range_start if last_success else None,
            'last_success_range_end': last_success.range_end if last_success else None,
            'last_success_rows_written': last_success.rows_written if last_success else 0,
            'latest_failure_message': latest_failure.error_message if latest_failure else '',
        }


class TrafficSelectors:
    @staticmethod
    def _filtered_queryset(days: int = 30, source: str = '', medium: str = '', campaign: str = '', trainer_id: str = '', path_prefix: str = ''):
        today = timezone.localdate()
        start_date = today - timedelta(days=days - 1)
        qs = DailyTrafficSlice.objects.filter(date__gte=start_date, date__lte=today)
        if source:
            qs = qs.filter(utm_source=source)
        if medium:
            qs = qs.filter(utm_medium=medium)
        if campaign:
            qs = qs.filter(utm_campaign=campaign)
        if trainer_id:
            qs = qs.filter(trainer_id=trainer_id)
        if path_prefix:
            qs = qs.filter(path__startswith=path_prefix)
        return qs

    @classmethod
    def timeseries(cls, **filters) -> list[dict]:
        rows = (
            cls._filtered_queryset(**filters)
            .values('date')
            .annotate(
                sessions_sum=Sum('sessions'),
                users_sum=Sum('unique_users'),
                page_views_sum=Sum('page_views'),
                video_views_sum=Sum('video_views'),
                checkout_starts_sum=Sum('checkout_starts'),
                purchases_sum=Sum('purchases'),
            )
            .order_by('date')
        )
        return [
            {
                'date': row['date'],
                'sessions': row['sessions_sum'] or 0,
                'unique_users': row['users_sum'] or 0,
                'page_views': row['page_views_sum'] or 0,
                'video_views': row['video_views_sum'] or 0,
                'checkout_starts': row['checkout_starts_sum'] or 0,
                'purchases': row['purchases_sum'] or 0,
            }
            for row in rows
        ]

    @classmethod
    def top_paths(cls, limit: int = 10, **filters) -> list[dict]:
        rows = (
            cls._filtered_queryset(**filters)
            .values('path')
            .annotate(
                sessions_sum=Sum('sessions'),
                page_views_sum=Sum('page_views'),
                video_views_sum=Sum('video_views'),
                checkout_starts_sum=Sum('checkout_starts'),
                purchases_sum=Sum('purchases'),
            )
            .order_by('-page_views_sum', '-sessions_sum')[:limit]
        )
        return [
            {
                'path': row['path'] or '/',
                'sessions': row['sessions_sum'] or 0,
                'page_views': row['page_views_sum'] or 0,
                'video_views': row['video_views_sum'] or 0,
                'checkout_starts': row['checkout_starts_sum'] or 0,
                'purchases': row['purchases_sum'] or 0,
            }
            for row in rows
        ]

    @classmethod
    def attribution(cls, limit: int = 10, **filters) -> list[dict]:
        rows = (
            cls._filtered_queryset(**filters)
            .values('utm_source', 'utm_medium', 'utm_campaign')
            .annotate(
                sessions_sum=Sum('sessions'),
                page_views_sum=Sum('page_views'),
                purchases_sum=Sum('purchases'),
            )
            .order_by('-sessions_sum', '-purchases_sum')[:limit]
        )
        return [
            {
                'utm_source': row['utm_source'] or '(direct)',
                'utm_medium': row['utm_medium'] or '(none)',
                'utm_campaign': row['utm_campaign'] or '-',
                'sessions': row['sessions_sum'] or 0,
                'page_views': row['page_views_sum'] or 0,
                'purchases': row['purchases_sum'] or 0,
            }
            for row in rows
        ]
