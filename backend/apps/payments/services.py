from __future__ import annotations

from decimal import Decimal
from uuid import NAMESPACE_URL, UUID, uuid5

from django.db import transaction
from django.utils import timezone

from apps.audit.services import AuditService
from apps.commerce.services import CommerceFinalizationService
from apps.events.services import DomainEventService, emit_event
from apps.notifications.domain.triggers import DomainNotificationTriggers
from apps.orders.models import OrderStatus
from apps.payments.commission_policy import CommissionPolicyService
from apps.payments.gateway import PaymentGatewayAdapter, mock_payments_allowed
from apps.payments.models import Payment, PaymentProvider, PaymentStatus, PaymentWebhookEvent
from apps.payments.webhook_security import NormalizedWebhookPayload, PaymentWebhookSecurity
from apps.payouts.models import BalanceEntry
from apps.payouts.services import PayoutService


class PaymentService:
    @staticmethod
    def _safe_notify(
        callback,
        *,
        event_type: str,
        entity_type: str,
        entity_id: str,
        actor=None,
        context: dict | None = None,
    ) -> None:
        try:
            callback()
        except Exception as exc:
            AuditService.log(
                actor=actor,
                event_type='side_effect.failed',
                entity_type=entity_type,
                entity_id=str(entity_id),
                context={
                    'side_effect': event_type,
                    'error_class': exc.__class__.__name__,
                    'error_message': str(exc)[:500],
                    **(context or {}),
                },
            )

    @staticmethod
    def _split_amounts(amount: Decimal) -> tuple[Decimal, Decimal]:
        split = CommissionPolicyService.split(gross_amount=amount)
        return split.platform_commission, split.trainer_net

    @staticmethod
    def _money(value) -> Decimal:
        return Decimal(str(value or '0.00')).quantize(Decimal('0.01'))

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
        if provider == PaymentProvider.MOCK and not mock_payments_allowed():
            raise ValueError('Mock payment provider is disabled for this environment.')

        existing = (
            Payment.objects.filter(order=order, provider=provider, status__in=[PaymentStatus.CREATED, PaymentStatus.PENDING])
            .order_by('-created_at')
            .first()
        )
        if existing:
            PaymentService._emit_payment_event(event_type='payment.checkout_reused', payment=existing)
            return existing

        with transaction.atomic():
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

        from apps.content.models import PublishedBundle, PublishedProgram, PublishedVideo
        from apps.orders.models import PurchasedItemType
        from apps.subscriptions.models import SubscriptionPlan

        metadata = first_item.metadata or {}

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
    def _ensure_paid_order_finalized(cls, *, payment: Payment) -> tuple[Payment, bool]:
        order = payment.order
        had_active_access = CommerceFinalizationService._has_active_access_for_order(order)
        was_completed = order.status == OrderStatus.COMPLETED and bool(order.completed_at)
        changed = False
        if order.status != OrderStatus.COMPLETED:
            order.status = OrderStatus.PAID
            order.paid_at = order.paid_at or payment.confirmed_at or timezone.now()
            order.save(update_fields=['status', 'paid_at', 'updated_at'])
            cls._emit_order_payment_event(event_type='order.paid', payment=payment)
            changed = True

        CommerceFinalizationService.finalize_paid_order(order=order, payment=payment)
        order.refresh_from_db(fields=['status', 'paid_at', 'completed_at', 'updated_at'])
        has_active_access = CommerceFinalizationService._has_active_access_for_order(order)
        if (not was_completed and order.status == OrderStatus.COMPLETED) or (not had_active_access and has_active_access):
            changed = True
        return payment, changed

    @classmethod
    def _ensure_payout_accrued_once(cls, *, payment: Payment) -> tuple[Payment, bool]:
        trainer_id = cls._extract_trainer_id(payment)
        if not trainer_id:
            return payment, False

        existing_accrual = BalanceEntry.objects.filter(
            source_type='payment',
            source_id=payment.id,
            entry_type=BalanceEntry.EntryType.ACCRUAL,
        ).exists()
        provider_payload = dict(payment.provider_payload or {})
        if provider_payload.get('payout_accrued') and existing_accrual:
            return payment, False

        platform_fee, trainer_net = cls._split_amounts(payment.amount)
        changed = False
        if not existing_accrual:
            PayoutService.accrue_from_payment(trainer_id=trainer_id, payment=payment, amount=trainer_net)
            changed = True

        payment.provider_payload = {
            **provider_payload,
            'platform_fee': str(platform_fee),
            'trainer_net': str(trainer_net),
            'trainer_id': str(trainer_id),
            'payout_accrued': True,
        }
        payment.save(update_fields=['provider_payload', 'updated_at'])
        return payment, changed

    @classmethod
    def mark_succeeded(cls, *, payment: Payment, provider_payload: dict | None = None, request=None) -> Payment:
        with transaction.atomic():
            payment = Payment.objects.select_for_update().select_related('order', 'order__user').get(pk=payment.pk)
            already_succeeded = payment.status == PaymentStatus.SUCCEEDED
            if payment.status in {PaymentStatus.CANCELLED, PaymentStatus.REFUNDED, PaymentStatus.CHARGED_BACK}:
                raise ValueError('Cannot mark cancelled/refunded/charged-back payment as succeeded.')

            order = payment.order
            if not already_succeeded:
                payment.status = PaymentStatus.SUCCEEDED
                payment.provider_payload = {
                    **(payment.provider_payload or {}),
                    **(provider_payload or {}),
                }
                payment.confirmed_at = timezone.now()
                payment.save(update_fields=['status', 'provider_payload', 'confirmed_at', 'updated_at'])
            elif provider_payload:
                payment.provider_payload = {
                    **(payment.provider_payload or {}),
                    **provider_payload,
                }
                payment.save(update_fields=['provider_payload', 'updated_at'])

            payment, order_changed = cls._ensure_paid_order_finalized(payment=payment)
            payment, payout_changed = cls._ensure_payout_accrued_once(payment=payment)
            repaired = already_succeeded and (order_changed or payout_changed)

            if not already_succeeded:
                AuditService.log(
                    actor=order.user,
                    event_type='payment.succeeded',
                    entity_type='payment',
                    entity_id=str(payment.id),
                    context={'order_id': str(order.id), 'provider': payment.provider},
                    request=request,
                )
                cls._safe_notify(
                    lambda: DomainNotificationTriggers().on_order_paid(user=order.user, order=order),
                    event_type='notification.order_paid',
                    entity_type='payment',
                    entity_id=str(payment.id),
                    actor=order.user,
                    context={'order_id': str(order.id), 'provider': payment.provider},
                )
                cls._safe_notify(
                    lambda: DomainNotificationTriggers().on_payment_succeeded(user=order.user, payment=payment),
                    event_type='notification.payment_succeeded',
                    entity_type='payment',
                    entity_id=str(payment.id),
                    actor=order.user,
                    context={'order_id': str(order.id), 'provider': payment.provider},
                )
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
            elif repaired:
                AuditService.log(
                    actor=order.user,
                    event_type='payment.succeeded_reconciled',
                    entity_type='payment',
                    entity_id=str(payment.id),
                    context={
                        'order_id': str(order.id),
                        'provider': payment.provider,
                        'order_repaired': order_changed,
                        'payout_repaired': payout_changed,
                    },
                    request=request,
                )
                cls._emit_payment_event(
                    event_type='payment.succeeded_reconciled',
                    payment=payment,
                    extra_payload={
                        'order_status': order.status,
                        'order_repaired': order_changed,
                        'payout_repaired': payout_changed,
                        'provider_payload': payment.provider_payload or {},
                    },
                )
            return payment


    @staticmethod
    def _refund_operation_id(*, payment: Payment, refund_id: str) -> UUID:
        return uuid5(NAMESPACE_URL, f'trainerhub:payment-refund:{payment.id}:{refund_id}')

    @classmethod
    def _refund_summary(cls, payment: Payment) -> tuple[list[dict], Decimal]:
        operations = list((payment.provider_payload or {}).get('refund_operations') or [])
        refunded_amount = sum((cls._money(item.get('amount')) for item in operations), Decimal('0.00')).quantize(Decimal('0.01'))
        return operations, refunded_amount

    @classmethod
    def _refund_trainer_net(cls, *, payment: Payment, refund_amount: Decimal) -> Decimal:
        if payment.amount <= Decimal('0.00'):
            return Decimal('0.00')
        _platform_fee, total_trainer_net = cls._split_amounts(payment.amount)
        ratio = refund_amount / payment.amount
        return (total_trainer_net * ratio).quantize(Decimal('0.01'))

    @classmethod
    def mark_refunded(
        cls,
        *,
        payment: Payment,
        provider_payload: dict | None = None,
        amount: Decimal | str | None = None,
        refund_id: str = '',
        reason: str = '',
        request=None,
    ) -> Payment:
        """
        Refund a succeeded payment and reverse all downstream commercial effects.

        The method is intentionally idempotent:
        - duplicate refund_id operations return without touching money again;
        - partial refunds keep access active and only reverse the refunded share;
        - full refunds revoke access/subscriptions and mark order/payment refunded;
        - entitlement revocation is based on order source;
        - payout reversal is guarded by operation source_type/source_id;
        - domain events use deterministic idempotency keys.
        """
        from apps.entitlements.models import EntitlementSourceType
        from apps.entitlements.services import EntitlementService
        from apps.subscriptions.models import Subscription
        from apps.subscriptions.services import SubscriptionService

        with transaction.atomic():
            payment = Payment.objects.select_for_update().select_related('order', 'order__user').get(pk=payment.pk)
            provider_payload = dict(provider_payload or {})
            refund_id = str(refund_id or provider_payload.get('refund_id') or provider_payload.get('id') or provider_payload.get('RefundId') or '')
            if not refund_id:
                refund_id = f'full-{payment.id}' if amount is None else f'amount-{payment.id}-{cls._money(amount)}'

            operations, already_refunded_amount = cls._refund_summary(payment)
            if any(str(item.get('refund_id')) == refund_id for item in operations):
                return payment

            if payment.status == PaymentStatus.REFUNDED:
                return payment
            if payment.status != PaymentStatus.SUCCEEDED:
                raise ValueError('Only succeeded payments can be refunded.')

            order = payment.order
            previous_order_status = order.status
            remaining_amount = (payment.amount - already_refunded_amount).quantize(Decimal('0.01'))
            refund_amount = remaining_amount if amount is None else min(cls._money(amount), remaining_amount)
            if refund_amount <= Decimal('0.00'):
                raise ValueError('Refund amount must be positive.')
            total_refunded_amount = (already_refunded_amount + refund_amount).quantize(Decimal('0.01'))
            is_full_refund = total_refunded_amount >= payment.amount
            refund_kind = 'full' if is_full_refund else 'partial'
            refund_operation_id = cls._refund_operation_id(payment=payment, refund_id=refund_id)
            payout_reversal_amount = cls._refund_trainer_net(payment=payment, refund_amount=refund_amount)
            payout_reversal = PayoutService.reverse_payment_accrual(
                payment=payment,
                source_type='payment_refund' if is_full_refund else 'payment_refund_partial',
                source_id=payment.id if is_full_refund else refund_operation_id,
                amount=payout_reversal_amount,
            )

            revoked_entitlements_count = 0
            cancelled_subscriptions_count = 0
            if is_full_refund:
                revoked_entitlements_count = EntitlementService.revoke_by_source(
                    source_type=EntitlementSourceType.ORDER,
                    source_order=order,
                    reason='payment_refunded',
                    revoked_by='payment_refund',
                    request=request,
                )
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

            operation = {
                'refund_id': refund_id,
                'refund_operation_id': str(refund_operation_id),
                'amount': str(refund_amount),
                'currency': payment.currency,
                'kind': refund_kind,
                'reason': reason or provider_payload.get('reason', ''),
                'created_at': timezone.now().isoformat(),
                'payout_reversal': payout_reversal,
                'revoked_entitlements_count': revoked_entitlements_count,
                'cancelled_subscriptions_count': cancelled_subscriptions_count,
            }
            merged_payload = {
                **(payment.provider_payload or {}),
                **(provider_payload or {}),
                'refund_operations': [*operations, operation],
                'refunded_amount': str(total_refunded_amount),
                'refund_status': 'refunded' if is_full_refund else 'partially_refunded',
                'last_refund_id': refund_id,
                'last_refund_kind': refund_kind,
                'last_refunded_at': operation['created_at'],
            }
            if is_full_refund:
                merged_payload['refunded_at'] = operation['created_at']

            payment.status = PaymentStatus.REFUNDED if is_full_refund else PaymentStatus.SUCCEEDED
            payment.provider_payload = {
                **merged_payload,
                'revoked_entitlements_count': revoked_entitlements_count,
                'cancelled_subscriptions_count': cancelled_subscriptions_count,
                'payout_reversal': payout_reversal,
            }
            payment.save(update_fields=['status', 'provider_payload', 'updated_at'])

            if is_full_refund:
                order.status = OrderStatus.REFUNDED
                order.save(update_fields=['status', 'updated_at'])
                cls._emit_order_payment_event(
                    event_type='order.refunded',
                    payment=payment,
                    extra_payload={
                        'previous_order_status': previous_order_status,
                        'refund_id': refund_id,
                        'refund_amount': str(refund_amount),
                        'total_refunded_amount': str(total_refunded_amount),
                        'revoked_entitlements_count': revoked_entitlements_count,
                        'payout_reversal': payout_reversal,
                        'cancelled_subscriptions_count': cancelled_subscriptions_count,
                    },
                )

            AuditService.log(
                actor=order.user,
                event_type='payment.refunded' if is_full_refund else 'payment.refund_partial',
                entity_type='payment',
                entity_id=str(payment.id),
                context={
                    'order_id': str(order.id),
                    'provider': payment.provider,
                    'refund_id': refund_id,
                    'refund_amount': str(refund_amount),
                    'total_refunded_amount': str(total_refunded_amount),
                    'refund_kind': refund_kind,
                    'revoked_entitlements_count': revoked_entitlements_count,
                    'payout_reversal': payout_reversal,
                    'cancelled_subscriptions_count': cancelled_subscriptions_count,
                },
                request=request,
            )
            cls._emit_payment_event(
                event_type='payment.refunded' if is_full_refund else 'payment.refund_partial',
                payment=payment,
                extra_payload={
                    'order_status': order.status,
                    'refund_id': refund_id,
                    'refund_amount': str(refund_amount),
                    'total_refunded_amount': str(total_refunded_amount),
                    'refund_kind': refund_kind,
                    'revoked_entitlements_count': revoked_entitlements_count,
                    'payout_reversal': payout_reversal,
                    'cancelled_subscriptions_count': cancelled_subscriptions_count,
                    'provider_payload': payment.provider_payload or {},
                },
            )
            cls._safe_notify(
                lambda: DomainNotificationTriggers().on_payment_refunded(
                    user=order.user,
                    payment=payment,
                    refund_id=refund_id,
                    refund_kind=refund_kind,
                    amount=refund_amount,
                ),
                event_type='notification.payment_refunded',
                entity_type='payment',
                entity_id=str(payment.id),
                actor=order.user,
                context={
                    'order_id': str(order.id),
                    'provider': payment.provider,
                    'refund_id': refund_id,
                    'refund_kind': refund_kind,
                    'refund_amount': str(refund_amount),
                },
            )
            if is_full_refund:
                emit_event(
                    event_name='payment.refunded',
                    aggregate_type='payment',
                    aggregate_id=str(payment.id),
                    payload={
                        'order_id': str(order.id),
                        'user_id': str(order.user_id),
                        'refund_id': refund_id,
                        'refund_amount': str(refund_amount),
                        'total_refunded_amount': str(total_refunded_amount),
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

            original_order_status = (payment.provider_payload or {}).get('previous_order_status')
            if original_order_status in {OrderStatus.PAID, OrderStatus.COMPLETED}:
                order.status = original_order_status
            else:
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
                reason='payment_chargeback_lost',
                revoked_by='payment_chargeback',
                request=request,
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
            cls._safe_notify(
                lambda: DomainNotificationTriggers().on_payment_failed(user=order.user, payment=payment),
                event_type='notification.payment_failed',
                entity_type='payment',
                entity_id=str(payment.id),
                actor=order.user,
                context={'order_id': str(order.id), 'provider': payment.provider},
            )
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
    def _audit_webhook_event(*, event: PaymentWebhookEvent, event_type: str, payment: Payment | None = None, context: dict | None = None) -> None:
        AuditService.log(
            event_type=event_type,
            entity_type='payment_webhook',
            entity_id=str(event.id),
            context={
                'provider': event.provider,
                'webhook_event_type': event.event_type,
                'external_event_id': event.external_event_id,
                'external_payment_id': (event.payload or {}).get('external_payment_id'),
                'payment_id': str(payment.id) if payment else str(event.payment_id) if event.payment_id else '',
                'status': event.status,
                'raw_payload_hash': event.raw_payload_hash,
                'attempts': event.attempts,
                **(context or {}),
            },
        )

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
    def _find_raw_hash_duplicate(cls, *, event: PaymentWebhookEvent, normalized: NormalizedWebhookPayload) -> PaymentWebhookEvent | None:
        if not normalized.raw_payload_hash:
            return None
        return (
            PaymentWebhookEvent.objects.select_for_update()
            .filter(
                provider=normalized.provider,
                raw_payload_hash=normalized.raw_payload_hash,
                status__in=[
                    PaymentWebhookEvent.Status.PROCESSED,
                    PaymentWebhookEvent.Status.IGNORED,
                    PaymentWebhookEvent.Status.DUPLICATE,
                    PaymentWebhookEvent.Status.PROCESSING,
                ],
            )
            .exclude(pk=event.pk)
            .order_by('-processed_at', '-received_at')
            .first()
        )

    @staticmethod
    def _provider_event_id(normalized: NormalizedWebhookPayload) -> str:
        return f'{normalized.provider}:{normalized.external_event_id}'

    @classmethod
    def _upsert_received_event(cls, normalized: NormalizedWebhookPayload) -> PaymentWebhookEvent:
        provider_event_id = cls._provider_event_id(normalized)
        event, _created = PaymentWebhookEvent.objects.get_or_create(
            provider_event_id=provider_event_id,
            defaults={
                'provider': normalized.provider,
                'event_type': normalized.event_type,
                'payload': normalized.payload,
                'headers': normalized.headers,
                'signature': normalized.signature,
                'raw_payload_hash': normalized.raw_payload_hash,
                'external_event_id': normalized.external_event_id,
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
            event = PaymentWebhookEvent.objects.select_for_update().get(
                provider_event_id=cls._provider_event_id(normalized),
            )

            if event.processed_at or event.status == PaymentWebhookEvent.Status.PROCESSED:
                cls._emit_webhook_event(event=event, emitted_type='payment.webhook_duplicate', payment=event.payment)
                cls._audit_webhook_event(
                    event=event,
                    event_type='payment.webhook_duplicate',
                    payment=event.payment,
                    context={'duplicate_reason': 'external_event_id_already_processed'},
                )
                return event

            raw_duplicate = cls._find_raw_hash_duplicate(event=event, normalized=normalized)
            if raw_duplicate:
                event.provider = normalized.provider
                event.event_type = normalized.event_type
                event.payload = normalized.payload
                event.headers = normalized.headers
                event.signature = normalized.signature
                event.raw_payload_hash = normalized.raw_payload_hash
                event.external_event_id = normalized.external_event_id
                event.provider_event_id = cls._provider_event_id(normalized)
                event.payment = raw_duplicate.payment
                event.status = PaymentWebhookEvent.Status.DUPLICATE
                event.error_message = f'Duplicate webhook raw payload hash for event {raw_duplicate.external_event_id}.'
                event.processed_at = timezone.now()
                event.save(update_fields=[
                    'provider',
                    'event_type',
                    'payload',
                    'headers',
                    'signature',
                    'raw_payload_hash',
                    'external_event_id',
                    'provider_event_id',
                    'payment',
                    'status',
                    'error_message',
                    'processed_at',
                    'updated_at',
                ])
                cls._emit_webhook_event(event=event, emitted_type='payment.webhook_duplicate', payment=event.payment)
                cls._audit_webhook_event(
                    event=event,
                    event_type='payment.webhook_duplicate',
                    payment=event.payment,
                    context={
                        'duplicate_reason': 'raw_payload_hash_already_seen',
                        'duplicate_of_webhook_event_id': str(raw_duplicate.id),
                        'duplicate_of_external_event_id': raw_duplicate.external_event_id,
                    },
                )
                return event

            event.provider = normalized.provider
            event.event_type = normalized.event_type
            event.payload = normalized.payload
            event.headers = normalized.headers
            event.signature = normalized.signature
            event.raw_payload_hash = normalized.raw_payload_hash
            event.external_event_id = normalized.external_event_id
            event.provider_event_id = cls._provider_event_id(normalized)
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
                'external_event_id',
                'provider_event_id',
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
                    payment = PaymentService.mark_succeeded(payment=payment, provider_payload=normalized.payload)
                    metadata = normalized.payload.get('metadata') if isinstance(normalized.payload.get('metadata'), dict) else {}
                    subscription_id = (
                        normalized.payload.get('subscription_id')
                        or normalized.payload.get('SubscriptionId')
                        or metadata.get('subscription_id')
                    )
                    if subscription_id:
                        from apps.subscriptions.lifecycle import SubscriptionLifecycleService
                        from apps.subscriptions.models import Subscription

                        subscription = Subscription.objects.select_for_update().get(pk=subscription_id)
                        renewal_result = SubscriptionLifecycleService.apply_renewal_webhook(
                            subscription=subscription,
                            payment=payment,
                            payload={**normalized.payload, 'external_event_id': normalized.external_event_id},
                            actor=payment.order.user,
                        )
                        event.payload = {**(event.payload or {}), 'subscription_renewal': renewal_result}
                    event.status = PaymentWebhookEvent.Status.PROCESSED
                elif normalized.event_type in cls.FAILED_EVENTS:
                    PaymentService.mark_failed(payment=payment, provider_payload=normalized.payload)
                    event.status = PaymentWebhookEvent.Status.PROCESSED
                elif normalized.event_type in cls.CANCELLED_EVENTS:
                    PaymentService.mark_cancelled(payment=payment, provider_payload=normalized.payload)
                    event.status = PaymentWebhookEvent.Status.PROCESSED
                elif normalized.event_type in cls.REFUNDED_EVENTS:
                    PaymentService.mark_refunded(
                        payment=payment,
                        provider_payload=normalized.payload,
                        amount=normalized.payload.get('refund_amount') or normalized.payload.get('amount'),
                        refund_id=normalized.payload.get('refund_id') or normalized.payload.get('id') or '',
                        reason=normalized.payload.get('reason') or '',
                    )
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
                event.save(update_fields=['payment', 'payload', 'status', 'error_message', 'processed_at', 'updated_at'])

                cls._emit_webhook_event(
                    event=event,
                    emitted_type='payment.webhook_processed' if event.status == PaymentWebhookEvent.Status.PROCESSED else 'payment.webhook_ignored',
                    payment=payment,
                )
                cls._audit_webhook_event(
                    event=event,
                    event_type='payment.webhook_processed' if event.status == PaymentWebhookEvent.Status.PROCESSED else 'payment.webhook_ignored',
                    payment=payment,
                )
                return event
            except Exception as exc:
                event.status = PaymentWebhookEvent.Status.FAILED
                event.error_message = str(exc)[:4000]
                event.save(update_fields=['status', 'error_message', 'updated_at'])
                cls._emit_webhook_event(event=event, emitted_type='payment.webhook_failed')
                cls._audit_webhook_event(
                    event=event,
                    event_type='payment.webhook_failed',
                    context={'error_message': event.error_message},
                )
                raise
