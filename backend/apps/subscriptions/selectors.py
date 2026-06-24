from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.entitlements.models import Entitlement, EntitlementStatus
from apps.orders.models import Order, OrderStatus, OrderType
from apps.payments.models import Payment, PaymentStatus
from apps.subscriptions.models import Subscription, SubscriptionPlan, SubscriptionStatus


def list_active_plans():
    return SubscriptionPlan.objects.filter(is_active=True).order_by('price', 'title')


def get_active_subscription_for_user(user):
    now = timezone.now()
    return (
        Subscription.objects.filter(
            user=user,
            status__in=[SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE],
            starts_at__lte=now,
        )
        .filter(Q(ends_at__isnull=True) | Q(ends_at__gt=now))
        .select_related('plan')
        .first()
    )


def list_user_subscriptions(user):
    return (
        Subscription.objects.filter(user=user)
        .select_related('plan', 'source_order')
        .prefetch_related('granted_entitlements', 'source_order__payments')
        .order_by('-created_at')
    )


def serialize_subscription(subscription: Subscription, *, now=None) -> dict:
    now = now or timezone.now()
    plan = subscription.plan
    latest_payment = None
    if subscription.source_order_id:
        latest_payment = subscription.source_order.payments.order_by('-created_at').first()

    entitlement_count = subscription.granted_entitlements.filter(status=EntitlementStatus.ACTIVE).count()
    ends_at = subscription.ends_at
    is_active = subscription.status in {SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE} and (ends_at is None or ends_at > now)
    remaining_days = None
    if ends_at:
        remaining_days = max(0, (ends_at - now).days)

    return {
        'id': str(subscription.id),
        'status': subscription.status,
        'starts_at': subscription.starts_at.isoformat() if subscription.starts_at else None,
        'ends_at': subscription.ends_at.isoformat() if subscription.ends_at else None,
        'cancelled_at': subscription.cancelled_at.isoformat() if subscription.cancelled_at else None,
        'auto_renew': subscription.auto_renew,
        'is_active': is_active,
        'remaining_days': remaining_days,
        'entitlement_count': entitlement_count,
        'plan': {
            'id': str(plan.id),
            'code': plan.code,
            'title': plan.title,
            'period_days': plan.period_days,
            'price': str(plan.price),
            'currency': plan.currency,
            'is_active': plan.is_active,
        },
        'plan_name': plan.title,
        'title': plan.title,
        'currency': plan.currency,
        'amount': str(plan.price),
        'price_amount': str(plan.price),
        'started_at': subscription.starts_at.isoformat() if subscription.starts_at else None,
        'created_at': subscription.created_at.isoformat() if subscription.created_at else None,
        'updated_at': subscription.updated_at.isoformat() if subscription.updated_at else None,
        'current_period_start': subscription.starts_at.isoformat() if subscription.starts_at else None,
        'current_period_end': subscription.ends_at.isoformat() if subscription.ends_at else None,
        'cancel_at': subscription.cancelled_at.isoformat() if subscription.cancelled_at else None,
        'canceled_at': subscription.cancelled_at.isoformat() if subscription.cancelled_at else None,
        'source_order_id': str(subscription.source_order_id),
        'latest_payment': {
            'id': str(latest_payment.id),
            'status': latest_payment.status,
            'amount': str(latest_payment.amount),
            'currency': latest_payment.currency,
            'confirmed_at': latest_payment.confirmed_at.isoformat() if latest_payment.confirmed_at else None,
        } if latest_payment else None,
    }


def get_user_subscription_center(user, *, days: int = 30) -> dict:
    now = timezone.now()
    since = now - timedelta(days=days)
    subscriptions = list(list_user_subscriptions(user))
    items = [serialize_subscription(item, now=now) for item in subscriptions]
    active_items = [item for item in items if item['is_active']]
    failed_payments = Payment.objects.filter(
        order__user=user,
        order__order_type=OrderType.SUBSCRIPTION,
        status__in=[PaymentStatus.FAILED, PaymentStatus.CANCELLED],
        created_at__gte=since,
    ).count()
    paid_orders = Order.objects.filter(
        user=user,
        order_type=OrderType.SUBSCRIPTION,
        status__in=[OrderStatus.PAID, OrderStatus.COMPLETED],
        created_at__gte=since,
    )
    period_spend = paid_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    return {
        'summary': {
            'total_count': len(items),
            'trial_count': sum(1 for item in items if item['status'] == SubscriptionStatus.TRIAL),
            'active_count': len(active_items),
            'cancelled_count': sum(1 for item in items if item['status'] == SubscriptionStatus.CANCELLED),
            'expired_count': sum(1 for item in items if item['status'] == SubscriptionStatus.EXPIRED),
            'past_due_count': sum(1 for item in items if item['status'] == SubscriptionStatus.PAST_DUE),
            'auto_renew_count': sum(1 for item in items if item['auto_renew']),
            'failed_payments_count': failed_payments,
            'period_spend': str(period_spend),
            'currency': active_items[0]['currency'] if active_items else 'RUB',
        },
        'items': items,
        'readiness': [
            {'code': 'has_active_subscription', 'label': 'Есть активная подписка', 'done': bool(active_items)},
            {'code': 'no_failed_payments', 'label': 'Нет проблемных оплат за период', 'done': failed_payments == 0},
            {'code': 'has_library_access', 'label': 'Есть активный доступ к библиотеке', 'done': Entitlement.objects.filter(user=user, status=EntitlementStatus.ACTIVE, source_type='subscription').exists()},
        ],
    }


def get_admin_subscription_overview(*, days: int = 30) -> dict:
    now = timezone.now()
    since = now - timedelta(days=days)
    qs = Subscription.objects.all()
    by_status = dict(qs.values_list('status').annotate(count=Count('id')))
    new_count = qs.filter(created_at__gte=since).count()
    due_soon = qs.filter(status__in=[SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE], ends_at__gte=now, ends_at__lte=now + timedelta(days=7)).count()
    expired_due = qs.filter(status__in=[SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE], ends_at__lt=now).count()
    mrr = qs.filter(status=SubscriptionStatus.ACTIVE).select_related('plan').aggregate(total=Sum('plan__price'))['total'] or Decimal('0.00')

    failed_payments = Payment.objects.filter(
        order__order_type=OrderType.SUBSCRIPTION,
        status__in=[PaymentStatus.FAILED, PaymentStatus.CANCELLED],
        created_at__gte=since,
    ).count()
    successful_payments = Payment.objects.filter(
        order__order_type=OrderType.SUBSCRIPTION,
        status=PaymentStatus.SUCCEEDED,
        created_at__gte=since,
    ).aggregate(total=Sum('amount'), count=Count('id'))

    return {
        'summary': {
            'total_count': qs.count(),
            'trial_count': by_status.get(SubscriptionStatus.TRIAL, 0),
            'active_count': by_status.get(SubscriptionStatus.ACTIVE, 0),
            'pending_count': by_status.get(SubscriptionStatus.PENDING, 0),
            'past_due_count': by_status.get(SubscriptionStatus.PAST_DUE, 0),
            'cancelled_count': by_status.get(SubscriptionStatus.CANCELLED, 0),
            'expired_count': by_status.get(SubscriptionStatus.EXPIRED, 0),
            'new_count': new_count,
            'due_soon_count': due_soon,
            'expired_due_count': expired_due,
            'failed_payments_count': failed_payments,
            'successful_payments_count': successful_payments['count'] or 0,
            'subscription_revenue': str(successful_payments['total'] or Decimal('0.00')),
            'estimated_mrr': str(mrr),
            'currency': 'RUB',
        },
        'status_breakdown': by_status,
    }


def list_admin_subscriptions(*, status: str | None = None, search: str | None = None, limit: int = 100):
    qs = Subscription.objects.select_related('user', 'plan', 'source_order').prefetch_related('granted_entitlements').order_by('-created_at')
    if status:
        qs = qs.filter(status=status)
    if search:
        qs = qs.filter(Q(user__email__icontains=search) | Q(plan__title__icontains=search) | Q(plan__code__icontains=search))
    return qs[:limit]
