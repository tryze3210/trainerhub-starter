from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Iterable

from django.apps import apps
from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone

from apps.analytics.models import (
    AnalyticsEvent,
    AnalyticsRefreshLog,
    DailyPlatformFunnel,
    DailyPlatformKPI,
    DailyTrafficSlice,
    DailyTrainerKPI,
    DailyUserCohortRetention,
)


PAID_PAYMENT_STATUSES = {'paid', 'captured', 'succeeded'}
ACTIVE_SUBSCRIPTION_STATUSES = {'active', 'trialing'}
NEW_SUBSCRIPTION_STATUSES = {'active', 'trialing', 'pending_activation'}


@dataclass(slots=True)
class DateRange:
    start_date: date
    end_date: date

    def iter_days(self) -> Iterable[date]:
        current = self.start_date
        while current <= self.end_date:
            yield current
            current += timedelta(days=1)


class AnalyticsWarehouseBuilder:
    def __init__(self) -> None:
        self.User = apps.get_model('users', 'User')
        self.TrainerProfile = apps.get_model('trainer_profiles', 'TrainerProfile')
        self.Order = apps.get_model('orders', 'Order')
        self.Payment = apps.get_model('payments', 'Payment')
        self.Subscription = apps.get_model('subscriptions', 'Subscription')

    def rebuild(self, start_date: date, end_date: date, trigger: str = 'manual') -> int:
        date_range = DateRange(start_date=start_date, end_date=end_date)
        refresh_log = AnalyticsRefreshLog.objects.create(
            trigger=trigger,
            range_start=start_date,
            range_end=end_date,
            status=AnalyticsRefreshLog.STATUS_RUNNING,
        )
        rows_written = 0
        try:
            for target_date in date_range.iter_days():
                with transaction.atomic():
                    self._rebuild_platform_day(target_date)
                    self._rebuild_trainer_day(target_date)
                    self._rebuild_funnel_day(target_date)
                    self._rebuild_traffic_slice_day(target_date)
                    rows_written += 4
            self._rebuild_retention_cohorts(start_date=start_date, end_date=end_date)
            rows_written += (end_date - start_date).days + 1
            refresh_log.status = AnalyticsRefreshLog.STATUS_SUCCEEDED
            refresh_log.rows_written = rows_written
            refresh_log.finished_at = timezone.now()
            refresh_log.save(update_fields=['status', 'rows_written', 'finished_at'])
            return rows_written
        except Exception as exc:
            refresh_log.status = AnalyticsRefreshLog.STATUS_FAILED
            refresh_log.error_message = str(exc)
            refresh_log.finished_at = timezone.now()
            refresh_log.save(update_fields=['status', 'error_message', 'finished_at'])
            raise

    def rebuild_last_n_days(self, days: int = 30, trigger: str = 'manual') -> int:
        today = timezone.localdate()
        start_date = today - timedelta(days=days - 1)
        return self.rebuild(start_date=start_date, end_date=today, trigger=trigger)

    def rebuild_full(self, trigger: str = 'manual') -> int:
        earliest_order = self.Order.objects.order_by('created_at').values_list('created_at', flat=True).first()
        earliest_payment = self.Payment.objects.order_by('paid_at').values_list('paid_at', flat=True).first()
        earliest_subscription = self.Subscription.objects.order_by('started_at').values_list('started_at', flat=True).first()
        earliest_user = self.User.objects.order_by('date_joined').values_list('date_joined', flat=True).first()
        earliest_event = AnalyticsEvent.objects.order_by('occurred_at').values_list('occurred_at', flat=True).first()
        candidates = [value for value in [earliest_order, earliest_payment, earliest_subscription, earliest_user, earliest_event] if value is not None]
        if not candidates:
            return 0
        first_dt = min(candidates)
        if isinstance(first_dt, datetime):
            start_date = timezone.localtime(first_dt).date() if timezone.is_aware(first_dt) else first_dt.date()
        else:
            start_date = first_dt
        return self.rebuild(start_date=start_date, end_date=timezone.localdate(), trigger=trigger)

    def _safe_divide(self, numerator: int | Decimal, denominator: int | Decimal, quant: str = '0.0001') -> Decimal:
        if not denominator:
            return Decimal(quant)
        return (Decimal(numerator) / Decimal(denominator)).quantize(Decimal(quant))

    def _normalize_dt_to_date(self, value) -> date:
        if isinstance(value, datetime):
            return timezone.localtime(value).date() if timezone.is_aware(value) else value.date()
        return value

    def _trainer_id_from_order_row(self, order) -> str | None:
        return getattr(order, 'trainer_id', None) or getattr(order, 'seller_id', None) or getattr(order, 'owner_id', None)

    def _rebuild_platform_day(self, target_date: date) -> None:
        orders = self.Order.objects.filter(created_at__date=target_date)
        payments = self.Payment.objects.filter(paid_at__date=target_date, status__in=PAID_PAYMENT_STATUSES)
        users = self.User.objects.filter(date_joined__date=target_date)
        trainers = self.TrainerProfile.objects.filter(created_at__date=target_date)
        active_subscriptions = self.Subscription.objects.filter(status__in=ACTIVE_SUBSCRIPTION_STATUSES, started_at__date__lte=target_date).count()
        new_subscriptions = self.Subscription.objects.filter(started_at__date=target_date, status__in=NEW_SUBSCRIPTION_STATUSES).count()

        total_orders = orders.count()
        paid_orders = payments.values('order_id').distinct().count()
        gross_revenue = orders.aggregate(total=Sum('total_amount')).get('total') or Decimal('0.00')
        paid_revenue = payments.aggregate(total=Sum('amount')).get('total') or Decimal('0.00')
        new_customers = users.count()
        new_trainers = trainers.count()
        arppu = Decimal('0.00') if paid_orders == 0 else (Decimal(paid_revenue) / Decimal(paid_orders)).quantize(Decimal('0.01'))
        conversion_rate = self._safe_divide(paid_orders, total_orders)

        DailyPlatformKPI.objects.update_or_create(
            date=target_date,
            defaults={
                'total_orders': total_orders,
                'paid_orders': paid_orders,
                'gross_revenue': gross_revenue,
                'paid_revenue': paid_revenue,
                'total_new_customers': new_customers,
                'total_new_trainers': new_trainers,
                'active_subscriptions': active_subscriptions,
                'new_subscriptions': new_subscriptions,
                'arppu': arppu,
                'conversion_rate': conversion_rate,
            },
        )

    def _rebuild_trainer_day(self, target_date: date) -> None:
        orders = list(self.Order.objects.filter(created_at__date=target_date))
        payments = list(self.Payment.objects.filter(paid_at__date=target_date, status__in=PAID_PAYMENT_STATUSES))
        new_subscriptions = list(self.Subscription.objects.filter(started_at__date=target_date, status__in=NEW_SUBSCRIPTION_STATUSES))
        active_subscriptions = list(self.Subscription.objects.filter(status__in=ACTIVE_SUBSCRIPTION_STATUSES, started_at__date__lte=target_date))

        order_by_id = {str(order.id): order for order in orders}
        bucket: dict[str, dict] = defaultdict(lambda: {
            'total_orders': 0,
            'paid_orders': 0,
            'gross_revenue': Decimal('0.00'),
            'paid_revenue': Decimal('0.00'),
            'new_customers': 0,
            'active_subscribers': 0,
            'new_subscriptions': 0,
        })

        for order in orders:
            trainer_id = self._trainer_id_from_order_row(order)
            if not trainer_id:
                continue
            item = bucket[str(trainer_id)]
            item['total_orders'] += 1
            item['gross_revenue'] += getattr(order, 'total_amount', Decimal('0.00')) or Decimal('0.00')
            if getattr(order, 'customer_id', None):
                item['new_customers'] += 1

        for payment in payments:
            order = order_by_id.get(str(getattr(payment, 'order_id', '')))
            if not order:
                continue
            trainer_id = self._trainer_id_from_order_row(order)
            if not trainer_id:
                continue
            item = bucket[str(trainer_id)]
            item['paid_orders'] += 1
            item['paid_revenue'] += getattr(payment, 'amount', Decimal('0.00')) or Decimal('0.00')

        for subscription in new_subscriptions:
            trainer_id = getattr(subscription, 'trainer_id', None)
            if trainer_id:
                bucket[str(trainer_id)]['new_subscriptions'] += 1

        for subscription in active_subscriptions:
            trainer_id = getattr(subscription, 'trainer_id', None)
            if trainer_id:
                bucket[str(trainer_id)]['active_subscribers'] += 1

        DailyTrainerKPI.objects.filter(date=target_date).delete()
        rows = []
        for trainer_id, metrics in bucket.items():
            arppu = Decimal('0.00') if metrics['paid_orders'] == 0 else (metrics['paid_revenue'] / Decimal(metrics['paid_orders'])).quantize(Decimal('0.01'))
            rows.append(DailyTrainerKPI(
                date=target_date,
                trainer_id=trainer_id,
                total_orders=metrics['total_orders'],
                paid_orders=metrics['paid_orders'],
                gross_revenue=metrics['gross_revenue'],
                paid_revenue=metrics['paid_revenue'],
                new_customers=metrics['new_customers'],
                active_subscribers=metrics['active_subscribers'],
                new_subscriptions=metrics['new_subscriptions'],
                arppu=arppu,
            ))
        if rows:
            DailyTrainerKPI.objects.bulk_create(rows)

    def _rebuild_funnel_day(self, target_date: date) -> None:
        signups = self.User.objects.filter(date_joined__date=target_date).count()
        ordering_customers = self.Order.objects.filter(created_at__date=target_date).values('customer_id').distinct().count()
        paid_customers = self.Payment.objects.filter(paid_at__date=target_date, status__in=PAID_PAYMENT_STATUSES).values('user_id').distinct().count()
        new_subscribers = self.Subscription.objects.filter(started_at__date=target_date, status__in=NEW_SUBSCRIPTION_STATUSES).values('user_id').distinct().count()

        DailyPlatformFunnel.objects.update_or_create(
            date=target_date,
            defaults={
                'signups': signups,
                'ordering_customers': ordering_customers,
                'paid_customers': paid_customers,
                'new_subscribers': new_subscribers,
                'signup_to_order_rate': self._safe_divide(ordering_customers, signups),
                'order_to_paid_rate': self._safe_divide(paid_customers, ordering_customers),
                'paid_to_subscription_rate': self._safe_divide(new_subscribers, paid_customers),
            },
        )

    def _rebuild_retention_cohorts(self, start_date: date, end_date: date) -> None:
        for cohort_date in DateRange(start_date=start_date, end_date=end_date).iter_days():
            cohort_users = list(self.User.objects.filter(date_joined__date=cohort_date).values_list('id', flat=True))
            cohort_size = len(cohort_users)
            if not cohort_users:
                DailyUserCohortRetention.objects.update_or_create(
                    cohort_date=cohort_date,
                    defaults={
                        'cohort_size': 0,
                        'retained_day_0': 0,
                        'retained_day_1': 0,
                        'retained_day_7': 0,
                        'retained_day_30': 0,
                        'retention_day_1_rate': Decimal('0.0000'),
                        'retention_day_7_rate': Decimal('0.0000'),
                        'retention_day_30_rate': Decimal('0.0000'),
                    },
                )
                continue

            activity_model = AnalyticsEvent
            retained_day_0 = activity_model.objects.filter(user_id__in=cohort_users, event_date=cohort_date).values('user_id').distinct().count()
            retained_day_1 = activity_model.objects.filter(user_id__in=cohort_users, event_date=cohort_date + timedelta(days=1)).values('user_id').distinct().count()
            retained_day_7 = activity_model.objects.filter(user_id__in=cohort_users, event_date=cohort_date + timedelta(days=7)).values('user_id').distinct().count()
            retained_day_30 = activity_model.objects.filter(user_id__in=cohort_users, event_date=cohort_date + timedelta(days=30)).values('user_id').distinct().count()

            DailyUserCohortRetention.objects.update_or_create(
                cohort_date=cohort_date,
                defaults={
                    'cohort_size': cohort_size,
                    'retained_day_0': retained_day_0,
                    'retained_day_1': retained_day_1,
                    'retained_day_7': retained_day_7,
                    'retained_day_30': retained_day_30,
                    'retention_day_1_rate': self._safe_divide(retained_day_1, cohort_size),
                    'retention_day_7_rate': self._safe_divide(retained_day_7, cohort_size),
                    'retention_day_30_rate': self._safe_divide(retained_day_30, cohort_size),
                },
            )

    def _rebuild_traffic_slice_day(self, target_date: date) -> None:
        events = AnalyticsEvent.objects.filter(event_date=target_date)
        slice_map: dict[tuple, dict] = defaultdict(lambda: {
            'sessions': set(),
            'unique_users': set(),
            'page_views': 0,
            'video_views': 0,
            'checkout_starts': 0,
            'purchases': 0,
        })

        for event in events.iterator():
            key = (
                event.path or '',
                event.utm_source or '',
                event.utm_medium or '',
                event.utm_campaign or '',
                str(event.trainer_id) if event.trainer_id else None,
            )
            bucket = slice_map[key]
            if event.session_id:
                bucket['sessions'].add(event.session_id)
            user_key = str(event.user_id) if event.user_id else event.anonymous_id
            if user_key:
                bucket['unique_users'].add(user_key)
            if event.event_name == AnalyticsEvent.EVENT_PAGE_VIEW:
                bucket['page_views'] += 1
            elif event.event_name == AnalyticsEvent.EVENT_VIDEO_VIEW:
                bucket['video_views'] += 1
            elif event.event_name == AnalyticsEvent.EVENT_CHECKOUT_STARTED:
                bucket['checkout_starts'] += 1
            elif event.event_name == AnalyticsEvent.EVENT_PURCHASE_COMPLETED:
                bucket['purchases'] += 1

        DailyTrafficSlice.objects.filter(date=target_date).delete()
        rows = []
        for (path, utm_source, utm_medium, utm_campaign, trainer_id), metrics in slice_map.items():
            rows.append(DailyTrafficSlice(
                date=target_date,
                path=path,
                utm_source=utm_source,
                utm_medium=utm_medium,
                utm_campaign=utm_campaign,
                trainer_id=trainer_id,
                sessions=len(metrics['sessions']),
                unique_users=len(metrics['unique_users']),
                page_views=metrics['page_views'],
                video_views=metrics['video_views'],
                checkout_starts=metrics['checkout_starts'],
                purchases=metrics['purchases'],
            ))
        if rows:
            DailyTrafficSlice.objects.bulk_create(rows, batch_size=1000)
