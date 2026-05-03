from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from apps.audit.services import AuditService
from apps.commerce.services import CommerceFinalizationService
from apps.events.services import DomainEventService, emit_event
from apps.notifications.domain.triggers import DomainNotificationTriggers
from apps.orders.models import OrderStatus
from apps.payments.gateway import PaymentGatewayAdapter
from apps.payments.models import Payment, PaymentProvider, PaymentStatus, PaymentWebhookEvent
from apps.payments.webhook_security import NormalizedWebhookPayload, PaymentWebhookSecurity
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
    def _emit_payment_event(*, event_type: str, payment: Payment, extra_payload: dict | None = None) -> None:
        order = payment.order
        DomainEventService().emit(
            event_type=event_type,
            aggregate_type='payment',
            aggregate_id=str(payment.id),
            idempotency_key=f'payment:{payment.id}:{event_type}',
            payload={
                'payment_id': str(payment.id),
                'order_id': str(order.id),
                'user_id': str(order.user_id),
                'provider': payment.provider,
                'status': payment.status,
                'amount': str(payment.amount),
                'currency': payment.currency,
                'external_payment_id': payment.external_payment_id,
                **(extra_payload or {}),
            },
        )

    @staticmethod
    def _emit_order_payment_event(*, event_type: str, payment: Payment, extra_payload: dict | None = None) -> None:
        order = payment.order
        DomainEventService().emit(
            event_type=event_type,
            aggregate_type='order',
            aggregate_id=str(order.id),
            idempotency_key=f'order:{order.id}:{event_type}:payment:{payment.id}',
            payload={
                'order_id': str(order.id),
                'payment_id': str(payment.id),
                'user_id': str(order.user_id),
                'order_type': order.order_type,
                'status': order.status,
                'amount': str(payment.amount),
                'currency': payment.currency,
                **(extra_payload or {}),
            },
        )

    @staticmethod
    def create_checkout_payment(*, order, provider: str = PaymentProvider.MOCK) -> Payment:
        existing = (
            Payment.objects.filter(order=order, provider=provider, status__in=[PaymentStatus.CREATED, PaymentStatus.PENDING])
            .order_by('-created_at')
            .first()
        )
        if existing:
            PaymentService._emit_payment_event(event_type='payment.checkout_reused', payment=existing)
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
        PaymentService._emit_payment_event(
            event_type='payment.checkout_created',
            payment=payment,
            extra_payload={'checkout_url': payment.external_checkout_url},
        )
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
            if payment.status in {PaymentStatus.CANCELLED, PaymentStatus.REFUNDED, PaymentStatus.CHARGED_BACK}:
                raise ValueError('Cannot mark cancelled/refunded/charged-back payment as succeeded.')

            payment.status = PaymentStatus.SUCCEEDED
            payment.provider_payload = provider_payload or payment.provider_payload
            payment.confirmed_at = timezone.now()
            payment.save(update_fields=['status', 'provider_payload', 'confirmed_at', 'updated_at'])

            order = payment.order
            if order.status != OrderStatus.COMPLETED:
                order.status = OrderStatus.PAID
                order.paid_at = payment.confirmed_at
                order.save(update_fields=['status', 'paid_at', 'updated_at'])
                cls._emit_order_payment_event(event_type='order.paid', payment=payment)
                CommerceFinalizationService.finalize_paid_order(order=order, payment=payment)
                order.refresh_from_db(fields=["status", "completed_at", "updated_at"])

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
            cls._emit_payment_event(
                event_type='payment.succeeded',
                payment=payment,
                extra_payload={
                    'order_status': order.status,
                    'confirmed_at': payment.confirmed_at.isoformat() if payment.confirmed_at else None,
                    'provider_payload': payment.provider_payload or {},
                },
            )
            emit_event(
                event_name='payment.paid',
                aggregate_type='payment',
                aggregate_id=str(payment.id),
                payload={'order_id': str(order.id), 'user_id': str(order.user_id)},
                idempotency_key=f'payment:{payment.id}:payment.paid',
            )
            return payment


    @classmethod
    def mark_refunded(cls, *, payment: Payment, provider_payload: dict | None = None, request=None) -> Payment:
        """
        Refund a succeeded payment and reverse all downstream commercial effects.

        The method is intentionally idempotent:
        - a second call for an already-refunded payment returns the same payment;
        - entitlement revocation is based on order source;
        - payout reversal is guarded by ledger source_type/source_id;
        - domain events use deterministic idempotency keys.
        """
        from apps.entitlements.models import EntitlementSourceType
        from apps.entitlements.services import EntitlementService
        from apps.subscriptions.models import Subscription
        from apps.subscriptions.services import SubscriptionService

        with transaction.atomic():
            payment = Payment.objects.select_for_update().select_related('order', 'order__user').get(pk=payment.pk)
            if payment.status == PaymentStatus.REFUNDED:
                return payment
            if payment.status != PaymentStatus.SUCCEEDED:
                raise ValueError('Only succeeded payments can be refunded.')

            order = payment.order
            previous_order_status = order.status
            merged_payload = {
                **(payment.provider_payload or {}),
                **(provider_payload or {}),
                'refunded_at': timezone.now().isoformat(),
            }

            revoked_entitlements_count = EntitlementService.revoke_by_source(
                source_type=EntitlementSourceType.ORDER,
                source_order=order,
            )
            cancelled_subscriptions_count = 0
            for subscription in Subscription.objects.select_for_update().filter(source_order=order):
                before_status = subscription.status
                updated_subscription = SubscriptionService.cancel_subscription(
                    subscription=subscription,
                    actor=order.user,
                    reason='payment_refunded',
                    request=request,
                )
                if before_status != updated_subscription.status:
                    cancelled_subscriptions_count += 1
            payout_reversal = PayoutService.reverse_payment_accrual(payment=payment)

            payment.status = PaymentStatus.REFUNDED
            payment.provider_payload = {
                **merged_payload,
                'revoked_entitlements_count': revoked_entitlements_count,
                'cancelled_subscriptions_count': cancelled_subscriptions_count,
                'payout_reversal': payout_reversal,
            }
            payment.save(update_fields=['status', 'provider_payload', 'updated_at'])

            order.status = OrderStatus.REFUNDED
            order.save(update_fields=['status', 'updated_at'])
            cls._emit_order_payment_event(
                event_type='order.refunded',
                payment=payment,
                extra_payload={
                    'previous_order_status': previous_order_status,
                    'revoked_entitlements_count': revoked_entitlements_count,
                    'payout_reversal': payout_reversal,
                    'cancelled_subscriptions_count': cancelled_subscriptions_count,
                },
            )

            AuditService.log(
                actor=order.user,
                event_type='payment.refunded',
                entity_type='payment',
                entity_id=str(payment.id),
                context={
                    'order_id': str(order.id),
                    'provider': payment.provider,
                    'revoked_entitlements_count': revoked_entitlements_count,
                    'payout_reversal': payout_reversal,
                    'cancelled_subscriptions_count': cancelled_subscriptions_count,
                },
                request=request,
            )
            cls._emit_payment_event(
                event_type='payment.refunded',
                payment=payment,
                extra_payload={
                    'order_status': order.status,
                    'revoked_entitlements_count': revoked_entitlements_count,
                    'payout_reversal': payout_reversal,
                    'cancelled_subscriptions_count': cancelled_subscriptions_count,
                    'provider_payload': payment.provider_payload or {},
                },
            )
            emit_event(
                event_name='payment.refunded',
                aggregate_type='payment',
                aggregate_id=str(payment.id),
                payload={
                    'order_id': str(order.id),
                    'user_id': str(order.user_id),
                    'revoked_entitlements_count': revoked_entitlements_count,
                    'payout_reversal': payout_reversal,
                    'cancelled_subscriptions_count': cancelled_subscriptions_count,
                },
                idempotency_key=f'payment:{payment.id}:payment.refunded:legacy',
            )
            return payment


    @classmethod
    def mark_disputed(cls, *, payment: Payment, provider_payload: dict | None = None, request=None) -> Payment:
        """
        Mark a succeeded payment as disputed/chargeback-opened.

        This does not revoke access yet: the dispute may still be won. It does
        place the order/payment into an explicit risk state and emits durable
        events for admin/risk workflows.
        """
        with transaction.atomic():
            payment = Payment.objects.select_for_update().select_related('order', 'order__user').get(pk=payment.pk)
            if payment.status == PaymentStatus.DISPUTED:
                return payment
            if payment.status in {PaymentStatus.REFUNDED, PaymentStatus.CHARGED_BACK}:
                return payment
            if payment.status != PaymentStatus.SUCCEEDED:
                raise ValueError('Only succeeded payments can be moved to disputed status.')

            order = payment.order
            previous_order_status = order.status
            payout_hold = PayoutService.hold_payment_accrual(
                payment=payment,
                reason='payment_dispute_opened',
            )
            payment.status = PaymentStatus.DISPUTED
            payment.provider_payload = {
                **(payment.provider_payload or {}),
                **(provider_payload or {}),
                'dispute_opened_at': timezone.now().isoformat(),
                'previous_order_status': previous_order_status,
                'payout_hold': payout_hold,
            }
            payment.save(update_fields=['status', 'provider_payload', 'updated_at'])

            order.status = OrderStatus.DISPUTED
            order.save(update_fields=['status', 'updated_at'])

            cls._emit_order_payment_event(
                event_type='order.disputed',
                payment=payment,
                extra_payload={
                    'previous_order_status': previous_order_status,
                    'payout_hold': payout_hold,
                    'provider_payload': payment.provider_payload or {},
                },
            )
            AuditService.log(
                actor=order.user,
                event_type='payment.dispute_opened',
                entity_type='payment',
                entity_id=str(payment.id),
                context={'order_id': str(order.id), 'provider': payment.provider},
                request=request,
            )
            cls._emit_payment_event(
                event_type='payment.dispute_opened',
                payment=payment,
                extra_payload={
                    'order_status': order.status,
                    'previous_order_status': previous_order_status,
                    'payout_hold': payout_hold,
                    'provider_payload': payment.provider_payload or {},
                },
            )
            return payment

    @classmethod
    def mark_chargeback_won(cls, *, payment: Payment, provider_payload: dict | None = None, request=None) -> Payment:
        """Close an opened dispute in favor of the platform/trainer."""
        with transaction.atomic():
            payment = Payment.objects.select_for_update().select_related('order', 'order__user').get(pk=payment.pk)
            if payment.status == PaymentStatus.SUCCEEDED:
                return payment
            if payment.status != PaymentStatus.DISPUTED:
                raise ValueError('Only disputed payments can be marked as chargeback won.')

            order = payment.order
            previous_order_status = order.status
            payout_hold_release = PayoutService.release_payment_hold(
                payment=payment,
                reason='payment_chargeback_won',
            )
            payment.status = PaymentStatus.SUCCEEDED
            payment.provider_payload = {
                **(payment.provider_payload or {}),
                **(provider_payload or {}),
                'dispute_resolved_at': timezone.now().isoformat(),
                'dispute_resolution': 'won',
                'payout_hold_release': payout_hold_release,
            }
            payment.save(update_fields=['status', 'provider_payload', 'updated_at'])

            order.status = OrderStatus.COMPLETED if order.completed_at else OrderStatus.PAID
            order.save(update_fields=['status', 'updated_at'])

            cls._emit_order_payment_event(
                event_type='order.dispute_won',
                payment=payment,
                extra_payload={
                    'previous_order_status': previous_order_status,
                    'payout_hold_release': payout_hold_release,
                    'provider_payload': payment.provider_payload or {},
                },
            )
            AuditService.log(
                actor=order.user,
                event_type='payment.chargeback_won',
                entity_type='payment',
                entity_id=str(payment.id),
                context={'order_id': str(order.id), 'provider': payment.provider},
                request=request,
            )
            cls._emit_payment_event(
                event_type='payment.chargeback_won',
                payment=payment,
                extra_payload={
                    'order_status': order.status,
                    'previous_order_status': previous_order_status,
                    'payout_hold_release': payout_hold_release,
                    'provider_payload': payment.provider_payload or {},
                },
            )
            return payment

    @classmethod
    def mark_chargeback_lost(cls, *, payment: Payment, provider_payload: dict | None = None, request=None) -> Payment:
        """
        Apply a lost chargeback and reverse all downstream commercial effects.

        This is separate from refund because chargebacks are forced by the
        payment network/provider and should be visible in risk, support and
        payout operations as a distinct lifecycle.
        """
        from apps.entitlements.models import EntitlementSourceType
        from apps.entitlements.services import EntitlementService
        from apps.subscriptions.models import Subscription
        from apps.subscriptions.services import SubscriptionService

        with transaction.atomic():
            payment = Payment.objects.select_for_update().select_related('order', 'order__user').get(pk=payment.pk)
            if payment.status == PaymentStatus.CHARGED_BACK:
                return payment
            if payment.status == PaymentStatus.REFUNDED:
                return payment
            if payment.status not in {PaymentStatus.SUCCEEDED, PaymentStatus.DISPUTED}:
                raise ValueError('Only succeeded/disputed payments can be charged back.')

            order = payment.order
            previous_order_status = order.status
            merged_payload = {
                **(payment.provider_payload or {}),
                **(provider_payload or {}),
                'chargeback_lost_at': timezone.now().isoformat(),
                'previous_order_status': previous_order_status,
            }

            revoked_entitlements_count = EntitlementService.revoke_by_source(
                source_type=EntitlementSourceType.ORDER,
                source_order=order,
            )
            cancelled_subscriptions_count = 0
            for subscription in Subscription.objects.select_for_update().filter(source_order=order):
                before_status = subscription.status
                updated_subscription = SubscriptionService.cancel_subscription(
                    subscription=subscription,
                    actor=order.user,
                    reason='payment_chargeback_lost',
                    request=request,
                )
                if before_status != updated_subscription.status:
                    cancelled_subscriptions_count += 1

            payout_reversal = PayoutService.reverse_payment_accrual(
                payment=payment,
                source_type='payment_chargeback',
                reversal_status='chargeback_reversed',
            )

            payment.status = PaymentStatus.CHARGED_BACK
            payment.provider_payload = {
                **merged_payload,
                'revoked_entitlements_count': revoked_entitlements_count,
                'cancelled_subscriptions_count': cancelled_subscriptions_count,
                'payout_reversal': payout_reversal,
            }
            payment.save(update_fields=['status', 'provider_payload', 'updated_at'])

            order.status = OrderStatus.CHARGED_BACK
            order.save(update_fields=['status', 'updated_at'])

            cls._emit_order_payment_event(
                event_type='order.chargeback_lost',
                payment=payment,
                extra_payload={
                    'previous_order_status': previous_order_status,
                    'revoked_entitlements_count': revoked_entitlements_count,
                    'payout_reversal': payout_reversal,
                    'cancelled_subscriptions_count': cancelled_subscriptions_count,
                },
            )
            AuditService.log(
                actor=order.user,
                event_type='payment.chargeback_lost',
                entity_type='payment',
                entity_id=str(payment.id),
                context={
                    'order_id': str(order.id),
                    'provider': payment.provider,
                    'revoked_entitlements_count': revoked_entitlements_count,
                    'payout_reversal': payout_reversal,
                    'cancelled_subscriptions_count': cancelled_subscriptions_count,
                },
                request=request,
            )
            cls._emit_payment_event(
                event_type='payment.chargeback_lost',
                payment=payment,
                extra_payload={
                    'order_status': order.status,
                    'previous_order_status': previous_order_status,
                    'revoked_entitlements_count': revoked_entitlements_count,
                    'payout_reversal': payout_reversal,
                    'cancelled_subscriptions_count': cancelled_subscriptions_count,
                    'provider_payload': payment.provider_payload or {},
                },
            )
            emit_event(
                event_name='payment.charged_back',
                aggregate_type='payment',
                aggregate_id=str(payment.id),
                payload={
                    'order_id': str(order.id),
                    'user_id': str(order.user_id),
                    'revoked_entitlements_count': revoked_entitlements_count,
                    'payout_reversal': payout_reversal,
                    'cancelled_subscriptions_count': cancelled_subscriptions_count,
                },
                idempotency_key=f'payment:{payment.id}:payment.charged_back:legacy',
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
                cls._emit_order_payment_event(event_type='order.cancelled', payment=payment)
            AuditService.log(
                actor=order.user,
                event_type='payment.cancelled',
                entity_type='payment',
                entity_id=str(payment.id),
                context={'order_id': str(order.id), 'provider': payment.provider},
                request=request,
            )
            cls._emit_payment_event(event_type='payment.cancelled', payment=payment, extra_payload={'provider_payload': payment.provider_payload or {}})
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
                cls._emit_order_payment_event(event_type='order.failed', payment=payment)
            AuditService.log(
                actor=order.user,
                event_type='payment.failed',
                entity_type='payment',
                entity_id=str(payment.id),
                context={'order_id': str(order.id), 'provider': payment.provider},
                request=request,
            )
            cls._safe_notify(lambda: DomainNotificationTriggers().on_payment_failed(user=order.user, payment=payment))
            cls._emit_payment_event(event_type='payment.failed', payment=payment, extra_payload={'provider_payload': payment.provider_payload or {}})
            return payment


class PaymentWebhookService:
    SUCCESS_EVENTS = {'payment.succeeded', 'payment.paid', 'payment.captured', 'checkout.paid'}
    FAILED_EVENTS = {'payment.failed', 'checkout.failed'}
    CANCELLED_EVENTS = {'payment.cancelled', 'checkout.cancelled'}
    REFUNDED_EVENTS = {'payment.refunded', 'payment.refund.succeeded', 'refund.succeeded', 'checkout.refunded'}
    DISPUTE_OPENED_EVENTS = {'payment.dispute.opened', 'payment.disputed', 'payment.chargeback.opened', 'chargeback.opened', 'dispute.opened'}
    CHARGEBACK_LOST_EVENTS = {'payment.chargeback.lost', 'payment.dispute.lost', 'payment.charged_back', 'chargeback.lost', 'chargeback.succeeded', 'dispute.lost'}
    CHARGEBACK_WON_EVENTS = {'payment.chargeback.won', 'payment.dispute.won', 'chargeback.won', 'dispute.won'}

    @staticmethod
    def _emit_webhook_event(*, event: PaymentWebhookEvent, emitted_type: str, payment: Payment | None = None) -> None:
        DomainEventService().emit(
            event_type=emitted_type,
            aggregate_type='payment_webhook',
            aggregate_id=str(event.id),
            idempotency_key=f'payment_webhook:{event.provider}:{event.external_event_id}:{emitted_type}',
            payload={
                'webhook_event_id': str(event.id),
                'provider': event.provider,
                'event_type': event.event_type,
                'external_event_id': event.external_event_id,
                'external_payment_id': (event.payload or {}).get('external_payment_id'),
                'payment_id': str(payment.id) if payment else str(event.payment_id) if event.payment_id else None,
                'status': event.status,
            },
        )

    @classmethod
    def _upsert_received_event(cls, normalized: NormalizedWebhookPayload) -> PaymentWebhookEvent:
        event, _created = PaymentWebhookEvent.objects.get_or_create(
            external_event_id=normalized.external_event_id,
            defaults={
                'provider': normalized.provider,
                'event_type': normalized.event_type,
                'payload': normalized.payload,
                'headers': normalized.headers,
                'signature': normalized.signature,
                'raw_payload_hash': normalized.raw_payload_hash,
                'status': PaymentWebhookEvent.Status.RECEIVED,
            },
        )
        return event

    @classmethod
    def handle(
        cls,
        *,
        provider: str,
        event_type: str,
        external_event_id: str,
        payload: dict,
        headers: dict | None = None,
        signature: str = '',
        raw_payload_hash: str = '',
        verify_signature: bool = False,
    ) -> PaymentWebhookEvent:
        normalized = PaymentWebhookSecurity.normalize(
            provider=provider,
            payload={
                **(payload or {}),
                'provider': provider,
                'event_type': event_type,
                'external_event_id': external_event_id,
            },
            headers=headers or {},
            signature=signature,
            raw_body=None,
            verify_signature=verify_signature,
        )
        if raw_payload_hash:
            normalized = NormalizedWebhookPayload(
                provider=normalized.provider,
                event_type=normalized.event_type,
                external_event_id=normalized.external_event_id,
                external_payment_id=normalized.external_payment_id,
                payload=normalized.payload,
                headers=normalized.headers,
                signature=normalized.signature,
                raw_payload_hash=raw_payload_hash,
            )
        return cls.process_normalized(normalized=normalized)

    @classmethod
    def handle_raw(
        cls,
        *,
        provider: str | None,
        payload: dict,
        raw_body: bytes,
        headers: dict | None = None,
        signature: str | None = None,
        verify_signature: bool = True,
    ) -> PaymentWebhookEvent:
        normalized = PaymentWebhookSecurity.normalize(
            provider=provider,
            payload=payload,
            headers=headers or {},
            raw_body=raw_body,
            signature=signature,
            verify_signature=verify_signature,
        )
        return cls.process_normalized(normalized=normalized)

    @classmethod
    def process_normalized(cls, *, normalized: NormalizedWebhookPayload) -> PaymentWebhookEvent:
        with transaction.atomic():
            cls._upsert_received_event(normalized)
            event = PaymentWebhookEvent.objects.select_for_update().get(external_event_id=normalized.external_event_id)

            if event.processed_at or event.status == PaymentWebhookEvent.Status.PROCESSED:
                cls._emit_webhook_event(event=event, emitted_type='payment.webhook_duplicate', payment=event.payment)
                return event

            event.provider = normalized.provider
            event.event_type = normalized.event_type
            event.payload = normalized.payload
            event.headers = normalized.headers
            event.signature = normalized.signature
            event.raw_payload_hash = normalized.raw_payload_hash
            event.status = PaymentWebhookEvent.Status.PROCESSING
            event.error_message = ''
            event.attempts = event.attempts + 1
            event.save(update_fields=[
                'provider',
                'event_type',
                'payload',
                'headers',
                'signature',
                'raw_payload_hash',
                'status',
                'error_message',
                'attempts',
                'updated_at',
            ])

            try:
                payment = Payment.objects.select_for_update().select_related('order', 'order__user').get(
                    external_payment_id=normalized.external_payment_id,
                )
                event.payment = payment

                if normalized.event_type in cls.SUCCESS_EVENTS:
                    PaymentService.mark_succeeded(payment=payment, provider_payload=normalized.payload)
                    event.status = PaymentWebhookEvent.Status.PROCESSED
                elif normalized.event_type in cls.FAILED_EVENTS:
                    PaymentService.mark_failed(payment=payment, provider_payload=normalized.payload)
                    event.status = PaymentWebhookEvent.Status.PROCESSED
                elif normalized.event_type in cls.CANCELLED_EVENTS:
                    PaymentService.mark_cancelled(payment=payment, provider_payload=normalized.payload)
                    event.status = PaymentWebhookEvent.Status.PROCESSED
                elif normalized.event_type in cls.REFUNDED_EVENTS:
                    PaymentService.mark_refunded(payment=payment, provider_payload=normalized.payload)
                    event.status = PaymentWebhookEvent.Status.PROCESSED
                elif normalized.event_type in cls.DISPUTE_OPENED_EVENTS:
                    PaymentService.mark_disputed(payment=payment, provider_payload=normalized.payload)
                    event.status = PaymentWebhookEvent.Status.PROCESSED
                elif normalized.event_type in cls.CHARGEBACK_LOST_EVENTS:
                    PaymentService.mark_chargeback_lost(payment=payment, provider_payload=normalized.payload)
                    event.status = PaymentWebhookEvent.Status.PROCESSED
                elif normalized.event_type in cls.CHARGEBACK_WON_EVENTS:
                    PaymentService.mark_chargeback_won(payment=payment, provider_payload=normalized.payload)
                    event.status = PaymentWebhookEvent.Status.PROCESSED
                else:
                    event.status = PaymentWebhookEvent.Status.IGNORED
                    event.error_message = f'Unsupported webhook event_type: {normalized.event_type}'

                event.processed_at = timezone.now()
                event.save(update_fields=['payment', 'status', 'error_message', 'processed_at', 'updated_at'])

                cls._emit_webhook_event(
                    event=event,
                    emitted_type='payment.webhook_processed' if event.status == PaymentWebhookEvent.Status.PROCESSED else 'payment.webhook_ignored',
                    payment=payment,
                )
                return event
            except Exception as exc:
                event.status = PaymentWebhookEvent.Status.FAILED
                event.error_message = str(exc)[:4000]
                event.save(update_fields=['status', 'error_message', 'updated_at'])
                cls._emit_webhook_event(event=event, emitted_type='payment.webhook_failed')
                raise
