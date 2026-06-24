from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from apps.audit.services import AuditService
from apps.entitlements.models import Entitlement, EntitlementSourceType, EntitlementStatus, EntitlementTargetType
from apps.entitlements.services import EntitlementService
from apps.events.services import DomainEventService
from apps.orders.models import OrderType
from apps.payments.models import Payment, PaymentStatus
from apps.subscriptions.models import Subscription, SubscriptionStatus
from apps.subscriptions.services import SubscriptionService


ACTIVE_ACCESS_STATUSES = {SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE}
TERMINAL_STATUSES = {SubscriptionStatus.CANCELLED, SubscriptionStatus.EXPIRED}
PAYMENT_PROBLEM_STATUSES = {PaymentStatus.FAILED, PaymentStatus.CANCELLED}


@dataclass(frozen=True)
class SubscriptionEntitlementSyncResult:
    subscription_id: str
    status: str
    should_have_access: bool
    active_before: int
    active_after: int
    action: str

    def as_dict(self) -> dict[str, Any]:
        return {
            'subscription_id': self.subscription_id,
            'status': self.status,
            'should_have_access': self.should_have_access,
            'active_before': self.active_before,
            'active_after': self.active_after,
            'action': self.action,
        }


class SubscriptionLifecycleService:
    """Production-safe lifecycle helpers built on the existing subscription schema.

    v8.46 deliberately does not introduce new persisted statuses. The current model
    already stores pending/active/past_due/cancelled/expired, so the hardening layer
    adds policy, renewal projection and entitlement reconciliation around those
    values without requiring a migration.
    """

    @staticmethod
    def _now():
        return timezone.now()

    @classmethod
    def status_policy(cls) -> dict[str, Any]:
        return {
            'supported_statuses': [choice[0] for choice in SubscriptionStatus.choices],
            'access_granting_statuses': sorted(ACTIVE_ACCESS_STATUSES),
            'terminal_statuses': sorted(TERMINAL_STATUSES),
            'actions': {
                'cancel': {
                    'allowed_from': [SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE, SubscriptionStatus.PENDING],
                    'result_status': SubscriptionStatus.CANCELLED,
                    'revokes_entitlements': True,
                    'requires_reason': False,
                },
                'resume': {
                    'allowed_from': [SubscriptionStatus.CANCELLED, SubscriptionStatus.PAST_DUE],
                    'result_status': SubscriptionStatus.ACTIVE,
                    'grants_entitlements': True,
                    'requires_unexpired_period': True,
                },
                'mark_past_due': {
                    'allowed_from': [SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE, SubscriptionStatus.PENDING],
                    'result_status': SubscriptionStatus.PAST_DUE,
                    'admin_only': True,
                },
                'expire_due': {
                    'allowed_from': [SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE],
                    'result_status': SubscriptionStatus.EXPIRED,
                    'admin_only': True,
                    'revokes_due_entitlements': True,
                },
                'renew_from_webhook': {
                    'allowed_from': [SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE],
                    'result_status': SubscriptionStatus.ACTIVE,
                    'requires_success_payment': True,
                    'idempotent_by_payment': True,
                    'extends_period': True,
                },
                'sync_entitlements': {
                    'admin_only': True,
                    'idempotent': True,
                    'reconciles_library_entitlement': True,
                },
            },
            'virtual_statuses': {
                'paused': {
                    'persisted': False,
                    'reason': 'Current DB schema has no paused status. Keep access policy explicit until a dedicated migration is introduced.',
                },
            },
        }

    @classmethod
    def project_renewal(cls, subscription: Subscription, *, now=None) -> dict[str, Any]:
        now = now or cls._now()
        plan = subscription.plan
        period_days = plan.period_days or 30
        current_end = subscription.ends_at
        is_period_current = current_end is None or current_end > now
        can_renew = (
            subscription.status in {SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE}
            and subscription.auto_renew
            and is_period_current
        )
        next_period_start = current_end if current_end and current_end > now else now
        next_period_end = next_period_start + timedelta(days=period_days)
        reason = 'ready'
        if subscription.status in TERMINAL_STATUSES:
            reason = 'terminal_status'
        elif not subscription.auto_renew:
            reason = 'auto_renew_disabled'
        elif not is_period_current:
            reason = 'period_expired'
        elif subscription.status == SubscriptionStatus.TRIAL:
            reason = 'trial_active'
        elif subscription.status == SubscriptionStatus.PAST_DUE:
            reason = 'payment_recovery_required'
        return {
            'subscription_id': str(subscription.id),
            'status': subscription.status,
            'auto_renew': subscription.auto_renew,
            'period_days': period_days,
            'current_period_start': subscription.starts_at.isoformat() if subscription.starts_at else None,
            'current_period_end': subscription.ends_at.isoformat() if subscription.ends_at else None,
            'can_renew': can_renew,
            'reason': reason,
            'next_period_start': next_period_start.isoformat() if next_period_start else None,
            'next_period_end': next_period_end.isoformat() if next_period_end else None,
            'amount': str(plan.price),
            'currency': plan.currency,
        }

    @classmethod
    def _has_current_period_access(cls, subscription: Subscription, *, now=None) -> bool:
        now = now or cls._now()
        if subscription.status not in ACTIVE_ACCESS_STATUSES:
            return False
        if subscription.starts_at and subscription.starts_at > now:
            return False
        if subscription.ends_at and subscription.ends_at <= now:
            return False
        return True

    @classmethod
    @transaction.atomic
    def apply_renewal_webhook(
        cls,
        *,
        subscription: Subscription,
        payment=None,
        payload: dict | None = None,
        actor=None,
        request=None,
    ) -> dict[str, Any]:
        payload = dict(payload or {})
        subscription = (
            Subscription.objects.select_for_update()
            .select_related('plan', 'user')
            .get(pk=subscription.pk)
        )
        if subscription.status in TERMINAL_STATUSES:
            raise ValueError('Terminal subscription cannot be renewed.')

        payment_payload = dict(getattr(payment, 'provider_payload', None) or {})
        renewal_key = (
            str(payload.get('renewal_id') or payload.get('external_event_id') or '')
            or (f'payment:{payment.id}' if payment else '')
            or f'subscription:{subscription.id}:{subscription.updated_at.isoformat()}'
        )
        applied_keys = list(payment_payload.get('subscription_renewal_keys') or [])
        if payment is not None and renewal_key in applied_keys:
            return {
                'subscription_id': str(subscription.id),
                'payment_id': str(payment.id),
                'status': subscription.status,
                'changed': False,
                'reason': 'already_applied',
                'renewal_key': renewal_key,
                'starts_at': subscription.starts_at.isoformat() if subscription.starts_at else None,
                'ends_at': subscription.ends_at.isoformat() if subscription.ends_at else None,
            }

        now = cls._now()
        previous_status = subscription.status
        previous_ends_at = subscription.ends_at
        period_days = subscription.plan.period_days or 30
        next_start = previous_ends_at if previous_ends_at and previous_ends_at > now else now
        next_end = next_start + timedelta(days=period_days)

        if not subscription.starts_at:
            subscription.starts_at = now
        subscription.ends_at = next_end
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.cancelled_at = None
        subscription.auto_renew = True
        subscription.save(update_fields=['status', 'starts_at', 'ends_at', 'cancelled_at', 'auto_renew', 'updated_at'])

        sync_result = cls.sync_subscription_entitlements(
            subscription=subscription,
            actor=actor or getattr(subscription, 'user', None),
            request=request,
            reason='subscription_renewal_webhook',
        )

        if payment is not None:
            payment_payload['subscription_renewal_applied'] = True
            payment_payload['subscription_renewal_keys'] = [*applied_keys, renewal_key]
            payment_payload['subscription_id'] = str(subscription.id)
            payment.provider_payload = payment_payload
            payment.save(update_fields=['provider_payload', 'updated_at'])

        AuditService.log(
            actor=actor or subscription.user,
            event_type='subscription.renewed',
            entity_type='subscription',
            entity_id=str(subscription.id),
            context={
                'payment_id': str(payment.id) if payment else '',
                'renewal_key': renewal_key,
                'previous_status': previous_status,
                'previous_ends_at': previous_ends_at.isoformat() if previous_ends_at else None,
                'new_ends_at': subscription.ends_at.isoformat() if subscription.ends_at else None,
                'payload': payload,
                'entitlement_sync': sync_result.as_dict(),
            },
            request=request,
        )
        DomainEventService().emit(
            event_type='subscription.renewed',
            aggregate_type='subscription',
            aggregate_id=str(subscription.id),
            idempotency_key=f'subscription:{subscription.id}:renewed:{renewal_key}',
            payload={
                'subscription_id': str(subscription.id),
                'payment_id': str(payment.id) if payment else None,
                'renewal_key': renewal_key,
                'previous_status': previous_status,
                'previous_ends_at': previous_ends_at.isoformat() if previous_ends_at else None,
                'starts_at': subscription.starts_at.isoformat() if subscription.starts_at else None,
                'ends_at': subscription.ends_at.isoformat() if subscription.ends_at else None,
            },
        )
        return {
            'subscription_id': str(subscription.id),
            'payment_id': str(payment.id) if payment else '',
            'status': subscription.status,
            'changed': True,
            'reason': 'renewed',
            'renewal_key': renewal_key,
            'previous_status': previous_status,
            'previous_ends_at': previous_ends_at.isoformat() if previous_ends_at else None,
            'starts_at': subscription.starts_at.isoformat() if subscription.starts_at else None,
            'ends_at': subscription.ends_at.isoformat() if subscription.ends_at else None,
            'entitlement_sync': sync_result.as_dict(),
        }

    @classmethod
    @transaction.atomic
    def sync_subscription_entitlements(
        cls,
        *,
        subscription: Subscription,
        actor=None,
        request=None,
        reason: str = 'subscription_lifecycle_sync',
    ) -> SubscriptionEntitlementSyncResult:
        subscription = (
            Subscription.objects.select_for_update()
            .select_related('plan', 'user')
            .get(pk=subscription.pk)
        )
        active_before = Entitlement.objects.filter(
            source_type=EntitlementSourceType.SUBSCRIPTION,
            source_subscription=subscription,
            status=EntitlementStatus.ACTIVE,
        ).count()
        should_have_access = cls._has_current_period_access(subscription)
        action = 'noop'
        if should_have_access:
            EntitlementService.grant(
                user=subscription.user,
                source_type=EntitlementSourceType.SUBSCRIPTION,
                source_subscription=subscription,
                target_type=EntitlementTargetType.LIBRARY,
                target_id=None,
                starts_at=subscription.starts_at,
                ends_at=subscription.ends_at,
                metadata={
                    'plan_id': str(subscription.plan_id),
                    'plan_code': subscription.plan.code,
                    'title': subscription.plan.title,
                    'trainer_id': getattr(subscription.plan, 'trainer_id', ''),
                    'lifecycle_sync_reason': reason,
                    'subscription_status': subscription.status,
                },
            )
            action = 'granted_or_refreshed'
        else:
            revoked = EntitlementService.revoke_by_source(
                source_type=EntitlementSourceType.SUBSCRIPTION,
                source_subscription=subscription,
            )
            action = 'revoked' if revoked else 'noop'
        active_after = Entitlement.objects.filter(
            source_type=EntitlementSourceType.SUBSCRIPTION,
            source_subscription=subscription,
            status=EntitlementStatus.ACTIVE,
        ).count()
        AuditService.log(
            actor=actor,
            event_type='subscription.entitlements_synced',
            entity_type='subscription',
            entity_id=str(subscription.id),
            context={
                'status': subscription.status,
                'reason': reason,
                'should_have_access': should_have_access,
                'active_before': active_before,
                'active_after': active_after,
                'action': action,
            },
            request=request,
        )
        DomainEventService().emit(
            event_type='subscription.entitlements_synced',
            aggregate_type='subscription',
            aggregate_id=str(subscription.id),
            idempotency_key=f'subscription:{subscription.id}:entitlements_synced:{subscription.updated_at.isoformat()}',
            payload={
                'subscription_id': str(subscription.id),
                'status': subscription.status,
                'should_have_access': should_have_access,
                'active_before': active_before,
                'active_after': active_after,
                'action': action,
            },
        )
        return SubscriptionEntitlementSyncResult(
            subscription_id=str(subscription.id),
            status=subscription.status,
            should_have_access=should_have_access,
            active_before=active_before,
            active_after=active_after,
            action=action,
        )

    @classmethod
    @transaction.atomic
    def resume_subscription(cls, *, subscription: Subscription, actor=None, request=None, reason: str = '') -> Subscription:
        subscription = SubscriptionService.reactivate_subscription(
            subscription=subscription,
            actor=actor,
            request=request,
        )
        cls.sync_subscription_entitlements(
            subscription=subscription,
            actor=actor,
            request=request,
            reason=reason or 'subscription_resumed',
        )
        return subscription

    @classmethod
    @transaction.atomic
    def cancel_subscription(cls, *, subscription: Subscription, actor=None, request=None, reason: str = '') -> Subscription:
        subscription = SubscriptionService.cancel_subscription(
            subscription=subscription,
            actor=actor,
            reason=reason,
            request=request,
        )
        cls.sync_subscription_entitlements(
            subscription=subscription,
            actor=actor,
            request=request,
            reason=reason or 'subscription_cancelled',
        )
        return subscription

    @classmethod
    def reconcile_subscriptions(cls, *, limit: int = 100, actor=None, request=None, subscription_id=None) -> dict[str, Any]:
        qs = Subscription.objects.select_related('plan', 'user').order_by('-updated_at')
        if subscription_id:
            qs = qs.filter(id=subscription_id)
        else:
            qs = qs[:limit]
        results = []
        for subscription in qs:
            results.append(
                cls.sync_subscription_entitlements(
                    subscription=subscription,
                    actor=actor,
                    request=request,
                    reason='subscription_lifecycle_reconciliation',
                ).as_dict()
            )
        return {
            'checked_count': len(results),
            'granted_or_refreshed_count': sum(1 for item in results if item['action'] == 'granted_or_refreshed'),
            'revoked_count': sum(1 for item in results if item['action'] == 'revoked'),
            'noop_count': sum(1 for item in results if item['action'] == 'noop'),
            'items': results,
        }

    @classmethod
    def notify_expiring_subscriptions(cls, *, days_before: int = 7, limit: int = 250, actor=None, request=None) -> dict[str, Any]:
        from apps.notifications.domain.triggers import DomainNotificationTriggers

        now = cls._now()
        days_before = max(1, min(int(days_before), 90))
        limit = max(1, min(int(limit), 1000))
        window_end = now + timedelta(days=days_before)
        subscriptions = list(
            Subscription.objects
            .select_related('user', 'plan')
            .filter(
                status__in=ACTIVE_ACCESS_STATUSES,
                ends_at__gt=now,
                ends_at__lte=window_end,
            )
            .order_by('ends_at')[:limit]
        )
        trigger = DomainNotificationTriggers()
        notified_ids = []
        for subscription in subscriptions:
            days_left = max(0, (subscription.ends_at - now).days) if subscription.ends_at else None
            trigger.on_subscription_expiring(
                user=subscription.user,
                subscription=subscription,
                days_left=days_left,
            )
            notified_ids.append(str(subscription.id))

        AuditService.log(
            actor=actor,
            event_type='subscription.expiring_notifications_queued',
            entity_type='subscription',
            entity_id='batch',
            context={
                'days_before': days_before,
                'limit': limit,
                'window_end': window_end.isoformat(),
                'notified_count': len(notified_ids),
                'subscription_ids': notified_ids,
            },
            request=request,
        )
        return {
            'days_before': days_before,
            'limit': limit,
            'window_end': window_end.isoformat(),
            'notified_count': len(notified_ids),
            'subscription_ids': notified_ids,
        }

    @classmethod
    def get_lifecycle_summary(cls, *, user=None, days: int = 30) -> dict[str, Any]:
        now = cls._now()
        since = now - timedelta(days=days)
        subscriptions = Subscription.objects.select_related('plan', 'user')
        if user is not None:
            subscriptions = subscriptions.filter(user=user)
        status_breakdown = dict(subscriptions.values_list('status').annotate(count=Count('id')))
        due_soon = subscriptions.filter(
            status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE],
            ends_at__gt=now,
            ends_at__lte=now + timedelta(days=7),
        ).count()
        expired_due = subscriptions.filter(
            status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE],
            ends_at__lte=now,
        ).count()
        failed_payments = Payment.objects.filter(
            order__order_type=OrderType.SUBSCRIPTION,
            status__in=list(PAYMENT_PROBLEM_STATUSES),
            created_at__gte=since,
        )
        if user is not None:
            failed_payments = failed_payments.filter(order__user=user)
        active_access = Entitlement.objects.filter(
            source_type=EntitlementSourceType.SUBSCRIPTION,
            status=EntitlementStatus.ACTIVE,
        )
        if user is not None:
            active_access = active_access.filter(user=user)
        return {
            'summary': {
                'total_count': subscriptions.count(),
                'trial_count': status_breakdown.get(SubscriptionStatus.TRIAL, 0),
                'active_count': status_breakdown.get(SubscriptionStatus.ACTIVE, 0),
                'past_due_count': status_breakdown.get(SubscriptionStatus.PAST_DUE, 0),
                'cancelled_count': status_breakdown.get(SubscriptionStatus.CANCELLED, 0),
                'expired_count': status_breakdown.get(SubscriptionStatus.EXPIRED, 0),
                'pending_count': status_breakdown.get(SubscriptionStatus.PENDING, 0),
                'auto_renew_count': subscriptions.filter(auto_renew=True).count(),
                'due_soon_count': due_soon,
                'expired_due_count': expired_due,
                'failed_payments_count': failed_payments.count(),
                'active_entitlement_count': active_access.count(),
            },
            'status_breakdown': status_breakdown,
            'policy': cls.status_policy(),
        }
