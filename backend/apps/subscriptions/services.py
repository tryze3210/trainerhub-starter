from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from apps.entitlements.services import EntitlementService
from apps.entitlements.models import Entitlement
from apps.subscriptions.models import Subscription, SubscriptionPlan

class SubscriptionService:
    @staticmethod
    def _period_delta(plan: SubscriptionPlan) -> timedelta:
        if plan.billing_period == SubscriptionPlan.BillingPeriod.YEAR:
            return timedelta(days=365)
        return timedelta(days=30)

    @classmethod
    @transaction.atomic
    def activate_subscription(cls, *, user, plan: SubscriptionPlan, external_payment_id: str = '', metadata=None) -> Subscription:
        now = timezone.now()
        ends_at = now + cls._period_delta(plan)
        subscription = Subscription.objects.create(
            user=user,
            plan=plan,
            status=Subscription.Status.ACTIVE,
            starts_at=now,
            current_period_starts_at=now,
            current_period_ends_at=ends_at,
            external_payment_id=external_payment_id,
            metadata=metadata or {},
        )
        EntitlementService.grant(
            user=user,
            kind=Entitlement.Kind.SUBSCRIPTION,
            object_id=str(plan.id),
            source=Entitlement.Source.SUBSCRIPTION,
            source_reference=str(subscription.id),
            starts_at=now,
            ends_at=ends_at,
            metadata={'trainer_id': str(plan.trainer_id)},
        )
        return subscription

    @staticmethod
    @transaction.atomic
    def cancel_subscription(*, subscription: Subscription):
        subscription.status = Subscription.Status.CANCELED
        subscription.canceled_at = timezone.now()
        subscription.save(update_fields=['status', 'canceled_at', 'updated_at'])
        EntitlementService.revoke_by_source(source=Entitlement.Source.SUBSCRIPTION, source_reference=str(subscription.id))
        return subscription
