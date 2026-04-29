from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from apps.audit.services import AuditService
from apps.commerce.services import CommerceFinalizationService
from apps.events.services import emit_event
from apps.notifications.domain.triggers import DomainNotificationTriggers
from apps.orders.models import OrderStatus
from apps.payments.gateway import PaymentGatewayAdapter
from apps.payments.models import Payment, PaymentProvider, PaymentStatus, PaymentWebhookEvent
from apps.payouts.services import PayoutService


class PaymentService:
    PLATFORM_FEE_RATE = Decimal('0.10')

    @staticmethod
    def _safe_notify(callback):
        try:
            callback()
        except Exception:
            return None

    @staticmethod
    def _split_amounts(amount: Decimal) -> tuple[Decimal, Decimal]:
        platform_fee = (amount * PaymentService.PLATFORM_FEE_RATE).quantize(Decimal('0.01'))
        trainer_net = (amount - platform_fee).quantize(Decimal('0.01'))
        return platform_fee, trainer_net

    @staticmethod
    def create_checkout_payment(*, order, provider: str = PaymentProvider.MOCK) -> Payment:
        existing = (
            Payment.objects.filter(order=order, provider=provider, status__in=[PaymentStatus.CREATED, PaymentStatus.PENDING])
            .order_by('-created_at')
            .first()
        )
        if existing:
            return existing

        payment = Payment.objects.create(
            order=order,
            provider=provider,
            status=PaymentStatus.PENDING,
            amount=order.total_amount,
            currency=order.currency,
        )
        gateway_payload = PaymentGatewayAdapter().create_checkout(order=order, payment=payment)
        payment.external_payment_id = gateway_payload['external_payment_id']
        payment.external_checkout_url = gateway_payload['checkout_url']
        payment.provider_payload = gateway_payload['payload']
        payment.save(update_fields=['external_payment_id', 'external_checkout_url', 'provider_payload', 'updated_at'])
        return payment

    @staticmethod
    def _extract_trainer_id(payment: Payment):
        order = payment.order
        first_item = order.items.order_by('created_at').first()
        if not first_item:
            return None

        metadata = first_item.metadata or {}
        candidate = metadata.get('trainer_id')
        if candidate:
            try:
                return UUID(str(candidate))
            except (TypeError, ValueError):
                return None

        from apps.content.models import PublishedBundle, PublishedProgram, PublishedVideo
        from apps.orders.models import PurchasedItemType
        from apps.subscriptions.models import SubscriptionPlan

        if first_item.item_type == PurchasedItemType.SUBSCRIPTION_PLAN:
            plan = SubscriptionPlan.objects.filter(id=first_item.item_id).first()
            candidate = getattr(plan, 'trainer_id', None)
            if candidate:
                try:
                    return UUID(str(candidate))
                except (TypeError, ValueError):
                    return None
            return None

        model_map = {
            PurchasedItemType.VIDEO: PublishedVideo,
            PurchasedItemType.PROGRAM: PublishedProgram,
            PurchasedItemType.BUNDLE: PublishedBundle,
            'video': PublishedVideo,
            'program': PublishedProgram,
            'bundle': PublishedBundle,
        }
        model = model_map.get(first_item.item_type)
        if not model:
            return None

        query = model.objects.select_related('trainer_profile')
        content = query.filter(source_draft_id=first_item.item_id).first()
        if not content:
            published_id = metadata.get('published_id')
            slug = metadata.get('slug')
            if published_id and str(published_id).isdigit():
                content = query.filter(id=int(str(published_id))).first()
            if not content and slug:
                content = query.filter(slug=str(slug)).first()

        if not content:
            return None

        try:
            return UUID(str(content.trainer_profile.user_id))
        except (TypeError, ValueError, AttributeError):
            return None

    @classmethod
    def mark_succeeded(cls, *, payment: Payment, provider_payload: dict | None = None, request=None) -> Payment:
        with transaction.atomic():
            payment = Payment.objects.select_for_update().select_related('order', 'order__user').get(pk=payment.pk)
            if payment.status == PaymentStatus.SUCCEEDED:
                return payment
            if payment.status in {PaymentStatus.CANCELLED, PaymentStatus.REFUNDED}:
                raise ValueError('Cannot mark cancelled/refunded payment as succeeded.')

            payment.status = PaymentStatus.SUCCEEDED
            payment.provider_payload = provider_payload or payment.provider_payload
            payment.confirmed_at = timezone.now()
            payment.save(update_fields=['status', 'provider_payload', 'confirmed_at', 'updated_at'])

            order = payment.order
            if order.status != OrderStatus.COMPLETED:
                order.status = OrderStatus.PAID
                order.paid_at = payment.confirmed_at
                order.save(update_fields=['status', 'paid_at', 'updated_at'])
                CommerceFinalizationService.finalize_paid_order(order=order, payment=payment)

            trainer_id = cls._extract_trainer_id(payment)
            if trainer_id:
                platform_fee, trainer_net = cls._split_amounts(payment.amount)
                if not (payment.provider_payload or {}).get('payout_accrued'):
                    PayoutService.accrue_from_payment(trainer_id=trainer_id, payment=payment, amount=trainer_net)
                    payment.provider_payload = {
                        **(payment.provider_payload or {}),
                        'platform_fee': str(platform_fee),
                        'trainer_net': str(trainer_net),
                        'trainer_id': str(trainer_id),
                        'payout_accrued': True,
                    }
                    payment.save(update_fields=['provider_payload', 'updated_at'])

            AuditService.log(
                actor=order.user,
                event_type='payment.succeeded',
                entity_type='payment',
                entity_id=str(payment.id),
                context={'order_id': str(order.id), 'provider': payment.provider},
                request=request,
            )
            cls._safe_notify(lambda: DomainNotificationTriggers().on_order_paid(user=order.user, order=order))
            emit_event(
                event_name='payment.paid',
                aggregate_type='payment',
                aggregate_id=str(payment.id),
                payload={'order_id': str(order.id), 'user_id': str(order.user_id)},
            )
            return payment

    @classmethod
    def mark_cancelled(cls, *, payment: Payment, provider_payload: dict | None = None, request=None) -> Payment:
        with transaction.atomic():
            payment = Payment.objects.select_for_update().select_related('order', 'order__user').get(pk=payment.pk)
            if payment.status == PaymentStatus.CANCELLED:
                return payment
            if payment.status == PaymentStatus.SUCCEEDED:
                raise ValueError('Cannot cancel succeeded payment.')
            payment.status = PaymentStatus.CANCELLED
            payment.provider_payload = provider_payload or payment.provider_payload
            payment.save(update_fields=['status', 'provider_payload', 'updated_at'])
            order = payment.order
            if order.status not in {OrderStatus.PAID, OrderStatus.COMPLETED}:
                order.status = OrderStatus.CANCELLED
                order.save(update_fields=['status', 'updated_at'])
            AuditService.log(
                actor=order.user,
                event_type='payment.cancelled',
                entity_type='payment',
                entity_id=str(payment.id),
                context={'order_id': str(order.id), 'provider': payment.provider},
                request=request,
            )
            return payment

    @classmethod
    def mark_failed(cls, *, payment: Payment, provider_payload: dict | None = None, request=None) -> Payment:
        with transaction.atomic():
            payment = Payment.objects.select_for_update().select_related('order', 'order__user').get(pk=payment.pk)
            if payment.status == PaymentStatus.FAILED:
                return payment
            if payment.status == PaymentStatus.SUCCEEDED:
                raise ValueError('Cannot mark succeeded payment as failed.')
            payment.status = PaymentStatus.FAILED
            payment.provider_payload = provider_payload or payment.provider_payload
            payment.save(update_fields=['status', 'provider_payload', 'updated_at'])
            order = payment.order
            if order.status not in {OrderStatus.PAID, OrderStatus.COMPLETED}:
                order.status = OrderStatus.FAILED
                order.save(update_fields=['status', 'updated_at'])
            AuditService.log(
                actor=order.user,
                event_type='payment.failed',
                entity_type='payment',
                entity_id=str(payment.id),
                context={'order_id': str(order.id), 'provider': payment.provider},
                request=request,
            )
            cls._safe_notify(lambda: DomainNotificationTriggers().on_payment_failed(user=order.user, payment=payment))
            return payment


class PaymentWebhookService:
    SUCCESS_EVENTS = {'payment.succeeded', 'checkout.paid'}
    FAILED_EVENTS = {'payment.failed', 'checkout.failed'}
    CANCELLED_EVENTS = {'payment.cancelled', 'checkout.cancelled'}

    @classmethod
    def handle(cls, *, provider: str, event_type: str, external_event_id: str, payload: dict) -> PaymentWebhookEvent:
        with transaction.atomic():
            event, _ = PaymentWebhookEvent.objects.get_or_create(
                external_event_id=external_event_id,
                defaults={'provider': provider, 'event_type': event_type, 'payload': payload},
            )
            event = PaymentWebhookEvent.objects.select_for_update().get(pk=event.pk)
            if event.processed_at:
                return event

            external_payment_id = payload.get('external_payment_id')
            if not external_payment_id:
                raise ValueError('Webhook payload must include external_payment_id.')

            payment = Payment.objects.get(external_payment_id=external_payment_id)
            if event_type in cls.SUCCESS_EVENTS:
                PaymentService.mark_succeeded(payment=payment, provider_payload=payload)
            elif event_type in cls.FAILED_EVENTS:
                PaymentService.mark_failed(payment=payment, provider_payload=payload)
            elif event_type in cls.CANCELLED_EVENTS:
                PaymentService.mark_cancelled(payment=payment, provider_payload=payload)

            event.provider = provider
            event.event_type = event_type
            event.payload = payload
            event.processed_at = timezone.now()
            event.save(update_fields=['provider', 'event_type', 'payload', 'processed_at', 'updated_at'])
            return event
