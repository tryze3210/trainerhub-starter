from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from apps.audit.services import AuditService
from apps.billing.models import CheckoutSession
from apps.orders.services import OrderService
from apps.payments.gateway import PaymentGateway
from apps.subscriptions.models import SubscriptionPlan


class CheckoutService:
    @staticmethod
    def _price_for_subscription_target(target_id: str):
        plan = SubscriptionPlan.objects.get(pk=target_id, is_active=True)
        return plan, plan.price, plan.currency

    @classmethod
    @transaction.atomic
    def create_subscription_checkout(cls, *, user, plan_id: str, success_url: str = '', cancel_url: str = '', request=None):
        plan, amount, currency = cls._price_for_subscription_target(plan_id)
        checkout = CheckoutSession.objects.create(
            user=user,
            checkout_type=CheckoutSession.CheckoutType.SUBSCRIPTION,
            target_id=str(plan.id),
            currency=currency,
            gross_amount=Decimal(amount),
            status=CheckoutSession.Status.CREATED,
            success_url=success_url,
            cancel_url=cancel_url,
            expires_at=timezone.now() + timezone.timedelta(minutes=30),
            metadata={'trainer_id': str(plan.trainer_id), 'plan_id': str(plan.id)},
        )
        provider_data = PaymentGateway().create_checkout(checkout_session=checkout)
        checkout.provider_session_id = provider_data['provider_session_id']
        checkout.status = CheckoutSession.Status.PENDING_PROVIDER
        checkout.save(update_fields=['provider_session_id', 'status', 'updated_at'])
        AuditService.log(actor=user, event_type='checkout.created', entity_type='checkout_session', entity_id=str(checkout.id), context={'checkout_type': checkout.checkout_type}, request=request)
        return checkout, provider_data['checkout_url']

    @classmethod
    @transaction.atomic
    def create_one_time_checkout(cls, *, user, order, success_url: str = '', cancel_url: str = '', request=None):
        checkout = CheckoutSession.objects.create(
            user=user,
            checkout_type=CheckoutSession.CheckoutType.PURCHASE,
            target_id=f'{order.item_type}:{order.item_id}',
            order_id=str(order.id),
            currency=order.currency,
            gross_amount=order.gross_amount,
            status=CheckoutSession.Status.CREATED,
            success_url=success_url,
            cancel_url=cancel_url,
            expires_at=timezone.now() + timezone.timedelta(minutes=30),
            metadata={'trainer_id': order.trainer_id, 'order_id': str(order.id), 'item_type': order.item_type, 'item_id': order.item_id},
        )
        provider_data = PaymentGateway().create_checkout(checkout_session=checkout)
        checkout.provider_session_id = provider_data['provider_session_id']
        checkout.status = CheckoutSession.Status.PENDING_PROVIDER
        checkout.save(update_fields=['provider_session_id', 'status', 'updated_at'])
        OrderService.attach_checkout_session(order=order, checkout_session_id=str(checkout.id))
        AuditService.log(actor=user, event_type='checkout.created', entity_type='checkout_session', entity_id=str(checkout.id), context={'checkout_type': checkout.checkout_type, 'order_id': str(order.id)}, request=request)
        return checkout, provider_data['checkout_url']
