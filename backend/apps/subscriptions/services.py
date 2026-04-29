from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.audit.services import AuditService
from apps.entitlements.models import EntitlementSourceType, EntitlementStatus, EntitlementTargetType
from apps.entitlements.services import EntitlementService
from apps.subscriptions.models import Subscription, SubscriptionPlan, SubscriptionStatus


class SubscriptionService:
    """Subscription lifecycle service aligned with the current DB schema."""

    @staticmethod
    def _period_delta(plan: SubscriptionPlan) -> timedelta:
        return timedelta(days=plan.period_days or 30)

    @classmethod
    @transaction.atomic
    def activate_subscription(
        cls,
        *,
        user,
        plan: SubscriptionPlan,
        source_order=None,
        auto_renew: bool = False,
        starts_at=None,
        metadata: dict | None = None,
    ) -> Subscription:
        now = starts_at or timezone.now()
        ends_at = now + cls._period_delta(plan)
        lookup = {'user': user, 'source_order': source_order} if source_order is not None else {'user': user, 'plan': plan}
        subscription, _ = Subscription.objects.update_or_create(
            **lookup,
            defaults={
                'plan': plan,
                'status': SubscriptionStatus.ACTIVE,
                'starts_at': now,
                'ends_at': ends_at,
                'cancelled_at': None,
                'auto_renew': auto_renew,
            },
        )
        EntitlementService.grant(
            user=user,
            source_type=EntitlementSourceType.SUBSCRIPTION,
            source_subscription=subscription,
            target_type=EntitlementTargetType.LIBRARY,
            target_id=None,
            starts_at=subscription.starts_at,
            ends_at=subscription.ends_at,
            metadata={
                'plan_id': str(plan.id),
                'plan_code': plan.code,
                'title': plan.title,
                'trainer_id': getattr(plan, 'trainer_id', ''),
                **(metadata or {}),
            },
        )
        return subscription

    @classmethod
    @transaction.atomic
    def cancel_subscription(cls, *, subscription: Subscription, actor=None, reason: str = '', request=None) -> Subscription:
        subscription = Subscription.objects.select_for_update().select_related('plan', 'user').get(pk=subscription.pk)
        if subscription.status in {SubscriptionStatus.CANCELLED, SubscriptionStatus.EXPIRED}:
            return subscription

        now = timezone.now()
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.cancelled_at = now
        subscription.auto_renew = False
        subscription.save(update_fields=['status', 'cancelled_at', 'auto_renew', 'updated_at'])

        EntitlementService.revoke_by_source(
            source_type=EntitlementSourceType.SUBSCRIPTION,
            source_subscription=subscription,
        )
        AuditService.log(
            actor=actor or subscription.user,
            event_type='subscription.cancelled',
            entity_type='subscription',
            entity_id=str(subscription.id),
            context={'user_id': str(subscription.user_id), 'plan_id': str(subscription.plan_id), 'reason': reason},
            request=request,
        )
        return subscription

    @classmethod
    @transaction.atomic
    def reactivate_subscription(cls, *, subscription: Subscription, actor=None, request=None) -> Subscription:
        subscription = Subscription.objects.select_for_update().select_related('plan', 'user').get(pk=subscription.pk)
        now = timezone.now()
        if subscription.ends_at and subscription.ends_at <= now:
            raise ValueError('Expired subscription cannot be reactivated without a new checkout')

        subscription.status = SubscriptionStatus.ACTIVE
        subscription.cancelled_at = None
        subscription.auto_renew = True
        if not subscription.starts_at:
            subscription.starts_at = now
        if not subscription.ends_at:
            subscription.ends_at = now + cls._period_delta(subscription.plan)
        subscription.save(update_fields=['status', 'cancelled_at', 'auto_renew', 'starts_at', 'ends_at', 'updated_at'])

        EntitlementService.grant(
            user=subscription.user,
            source_type=EntitlementSourceType.SUBSCRIPTION,
            source_subscription=subscription,
            target_type=EntitlementTargetType.LIBRARY,
            target_id=None,
            starts_at=subscription.starts_at,
            ends_at=subscription.ends_at,
            metadata={'plan_id': str(subscription.plan_id), 'plan_code': subscription.plan.code, 'title': subscription.plan.title},
        )
        AuditService.log(
            actor=actor or subscription.user,
            event_type='subscription.reactivated',
            entity_type='subscription',
            entity_id=str(subscription.id),
            context={'user_id': str(subscription.user_id), 'plan_id': str(subscription.plan_id)},
            request=request,
        )
        return subscription

    @classmethod
    @transaction.atomic
    def expire_due_subscriptions(cls, *, now=None, actor=None, request=None) -> int:
        now = now or timezone.now()
        due_ids = list(
            Subscription.objects.filter(
                status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE],
                ends_at__lt=now,
            ).values_list('id', flat=True)
        )
        if not due_ids:
            return 0

        updated = Subscription.objects.filter(id__in=due_ids).update(
            status=SubscriptionStatus.EXPIRED,
            auto_renew=False,
            updated_at=now,
        )
        EntitlementService.expire_due_entitlements(now=now)
        for subscription_id in due_ids[:50]:
            AuditService.log(
                actor=actor,
                event_type='subscription.expired',
                entity_type='subscription',
                entity_id=str(subscription_id),
                context={'expired_by_maintenance': True},
                request=request,
            )
        return updated

    @classmethod
    @transaction.atomic
    def mark_past_due(cls, *, subscription: Subscription, actor=None, reason: str = '', request=None) -> Subscription:
        subscription = Subscription.objects.select_for_update().select_related('user').get(pk=subscription.pk)
        if subscription.status in {SubscriptionStatus.CANCELLED, SubscriptionStatus.EXPIRED}:
            return subscription
        subscription.status = SubscriptionStatus.PAST_DUE
        subscription.save(update_fields=['status', 'updated_at'])
        AuditService.log(
            actor=actor,
            event_type='subscription.past_due',
            entity_type='subscription',
            entity_id=str(subscription.id),
            context={'user_id': str(subscription.user_id), 'reason': reason},
            request=request,
        )
        return subscription
