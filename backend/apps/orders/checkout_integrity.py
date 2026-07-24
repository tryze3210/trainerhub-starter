from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from typing import Any

from django.db import transaction

from apps.events.services import DomainEventService
from apps.orders.models import Order, OrderItem, OrderStatus, OrderType, PurchasedItemType
from apps.orders.services import CheckoutCatalogResolver, CheckoutItemSnapshot
from apps.payments.commission_policy import CommissionPolicyService
from apps.payments.models import PaymentProvider
from apps.payments.services import PaymentService
from apps.subscriptions.models import SubscriptionPlan


PENDING_ORDER_STATUSES = {OrderStatus.PENDING, OrderStatus.AWAITING_PAYMENT}
CHECKOUT_INTEGRITY_SCHEMA_VERSION = 'v8.45'


@dataclass(frozen=True)
class CheckoutIntegrityResult:
    order: Order
    payment: Any
    reused_order: bool
    reused_payment: bool
    integrity: dict[str, Any]


def _decimal(value: Any, *, default: Decimal = Decimal('0.00')) -> Decimal:
    if value is None or value == '':
        return default.quantize(Decimal('0.01'))
    try:
        return Decimal(str(value)).quantize(Decimal('0.01'))
    except (InvalidOperation, TypeError, ValueError):
        return default.quantize(Decimal('0.01'))


def _money(value: Any) -> str:
    return str(_decimal(value))


def _normalize_text(value: Any) -> str:
    return str(value or '').strip()


def _normalize_provider(provider: str | None) -> str:
    value = _normalize_text(provider).lower()
    return value or PaymentProvider.MOCK


def _commission_snapshot(*, gross_amount: Decimal, currency: str) -> dict[str, str]:
    return CommissionPolicyService.split(
        gross_amount=gross_amount,
        currency=currency,
    ).as_snapshot(source='checkout_integrity_v8_45')


def _fingerprint(payload: dict[str, Any]) -> str:
    normalized = '|'.join(f'{key}={payload[key]}' for key in sorted(payload))
    return sha256(normalized.encode('utf-8')).hexdigest()


def _emit_order_event(*, event_type: str, order: Order, extra_payload: dict[str, Any] | None = None) -> None:
    DomainEventService().emit(
        event_type=event_type,
        aggregate_type='order',
        aggregate_id=str(order.id),
        idempotency_key=f'order:{order.id}:{event_type}',
        payload={
            'order_id': str(order.id),
            'user_id': str(order.user_id),
            'order_type': order.order_type,
            'status': order.status,
            'currency': order.currency,
            'total_amount': str(order.total_amount),
            **(extra_payload or {}),
        },
    )


def _metadata_value(metadata: dict[str, Any], path: list[str]) -> Any:
    node: Any = metadata or {}
    for part in path:
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node


class CheckoutIntegrityService:
    """Checkout/order hardening without schema changes.

    Integrity data is persisted inside OrderItem.metadata and Payment.provider_payload.
    This keeps the patch safe for existing databases while providing stable snapshots
    for reconciliation, support and payout accounting.
    """

    @classmethod
    def normalize_idempotency_key(cls, value: str | None) -> str:
        key = _normalize_text(value)
        if not key:
            return ''
        if len(key) > 160:
            raise ValueError('idempotency_key must be 160 characters or fewer.')
        return key

    @classmethod
    def build_one_time_integrity(
        cls,
        *,
        user,
        snapshot: CheckoutItemSnapshot,
        requested: dict[str, Any],
        idempotency_key: str = '',
    ) -> dict[str, Any]:
        canonical = {
            'user_id': str(getattr(user, 'id', '')),
            'mode': OrderType.ONE_TIME,
            'item_type': snapshot.item_type,
            'item_id': snapshot.item_id,
            'amount': str(snapshot.amount),
            'currency': snapshot.currency,
        }
        checkout_fingerprint = _fingerprint(canonical)
        price_snapshot = {
            'requested_item_type': _normalize_text(requested.get('item_type')),
            'requested_item_id': _normalize_text(requested.get('item_id')),
            'requested_title': _normalize_text(requested.get('title')),
            'requested_amount': _money(requested.get('amount')) if requested.get('amount') is not None else '',
            'requested_currency': _normalize_text(requested.get('currency') or 'RUB'),
            'resolved_title': snapshot.title,
            'resolved_amount': str(snapshot.amount),
            'resolved_currency': snapshot.currency,
            'resolved_item_id': snapshot.item_id,
            'price_source': (snapshot.metadata or {}).get('price_source', 'unknown'),
        }
        return {
            'schema_version': CHECKOUT_INTEGRITY_SCHEMA_VERSION,
            'mode': OrderType.ONE_TIME,
            'idempotency_key': idempotency_key,
            'fingerprint': checkout_fingerprint,
            'canonical': canonical,
            'price_snapshot': price_snapshot,
            'commission_snapshot': _commission_snapshot(gross_amount=snapshot.amount, currency=snapshot.currency),
        }

    @classmethod
    def build_subscription_integrity(
        cls,
        *,
        user,
        plan: SubscriptionPlan,
        idempotency_key: str = '',
    ) -> dict[str, Any]:
        amount = _decimal(plan.price)
        canonical = {
            'user_id': str(getattr(user, 'id', '')),
            'mode': OrderType.SUBSCRIPTION,
            'item_type': PurchasedItemType.SUBSCRIPTION_PLAN,
            'item_id': str(plan.id),
            'amount': str(amount),
            'currency': plan.currency or 'RUB',
        }
        return {
            'schema_version': CHECKOUT_INTEGRITY_SCHEMA_VERSION,
            'mode': OrderType.SUBSCRIPTION,
            'idempotency_key': idempotency_key,
            'fingerprint': _fingerprint(canonical),
            'canonical': canonical,
            'price_snapshot': {
                'plan_id': str(plan.id),
                'plan_code': getattr(plan, 'code', ''),
                'resolved_title': plan.title,
                'resolved_amount': str(amount),
                'resolved_currency': plan.currency or 'RUB',
                'price_source': 'subscription_plan',
            },
            'commission_snapshot': _commission_snapshot(gross_amount=amount, currency=plan.currency or 'RUB'),
        }

    @classmethod
    def find_reusable_pending_order(
        cls,
        *,
        user,
        fingerprint: str,
        idempotency_key: str = '',
        provider: str = PaymentProvider.MOCK,
    ) -> Order | None:
        queryset = (
            Order.objects.filter(
                user=user,
                status__in=PENDING_ORDER_STATUSES,
            )
            .prefetch_related('items', 'payments')
            .order_by('-created_at')[:50]
        )
        for order in queryset:
            first_item = next(iter(order.items.all()), None)
            metadata = getattr(first_item, 'metadata', {}) or {}
            integrity = metadata.get('checkout_integrity') or {}
            same_fingerprint = integrity.get('fingerprint') == fingerprint
            same_key = bool(idempotency_key) and integrity.get('idempotency_key') == idempotency_key
            if not same_fingerprint and not same_key:
                continue
            active_payment = next(
                (
                    payment
                    for payment in order.payments.all()
                    if payment.provider == provider and payment.status in {'created', 'pending'}
                ),
                None,
            )
            if active_payment or not order.payments.exists():
                return order
        return None

    @classmethod
    @transaction.atomic
    def create_one_time_checkout(
        cls,
        *,
        user,
        item_type: str,
        item_id: Any,
        title: str | None = None,
        amount: Decimal | None = None,
        currency: str = 'RUB',
        provider: str = PaymentProvider.MOCK,
        idempotency_key: str = '',
    ) -> CheckoutIntegrityResult:
        idempotency_key = cls.normalize_idempotency_key(idempotency_key)
        provider = _normalize_provider(provider)
        snapshot = CheckoutCatalogResolver.resolve_one_time_item(
            item_type=item_type,
            item_id=item_id,
            title=title,
            amount=amount,
            currency=currency,
        )
        integrity = cls.build_one_time_integrity(
            user=user,
            snapshot=snapshot,
            requested={
                'item_type': item_type,
                'item_id': item_id,
                'title': title,
                'amount': amount,
                'currency': currency,
            },
            idempotency_key=idempotency_key,
        )
        order = cls.find_reusable_pending_order(
            user=user,
            fingerprint=integrity['fingerprint'],
            idempotency_key=idempotency_key,
            provider=provider,
        )
        reused_order = order is not None
        if not order:
            order = Order.objects.create(
                user=user,
                order_type=OrderType.ONE_TIME,
                status=OrderStatus.AWAITING_PAYMENT,
                total_amount=snapshot.amount,
                currency=snapshot.currency,
            )
            metadata = {
                **(snapshot.metadata or {}),
                'checkout_integrity': integrity,
            }
            OrderItem.objects.create(
                order=order,
                item_type=snapshot.item_type,
                item_id=snapshot.item_id,
                title_snapshot=snapshot.title,
                quantity=1,
                unit_price=snapshot.amount,
                total_price=snapshot.amount,
                metadata=metadata,
            )
            _emit_order_event(
                event_type='order.awaiting_payment',
                order=order,
                extra_payload={
                    'item_type': snapshot.item_type,
                    'item_id': snapshot.item_id,
                    'title': snapshot.title,
                    'checkout_fingerprint': integrity['fingerprint'],
                    'idempotency_key': idempotency_key,
                    'price_source': snapshot.metadata.get('price_source'),
                },
            )
        else:
            _emit_order_event(
                event_type='order.reused_pending',
                order=order,
                extra_payload={
                    'checkout_fingerprint': integrity['fingerprint'],
                    'idempotency_key': idempotency_key,
                },
            )

        payment_before = order.payments.filter(provider=provider, status__in=['created', 'pending']).order_by('-created_at').first()
        payment = PaymentService.create_checkout_payment(order=order, provider=provider)
        reused_payment = payment_before is not None and payment_before.pk == payment.pk
        cls.enrich_payment_payload(payment=payment, integrity=integrity, reused_order=reused_order)
        return CheckoutIntegrityResult(
            order=order,
            payment=payment,
            reused_order=reused_order,
            reused_payment=reused_payment,
            integrity=integrity,
        )

    @classmethod
    @transaction.atomic
    def create_subscription_checkout(
        cls,
        *,
        user,
        plan: SubscriptionPlan,
        provider: str = PaymentProvider.MOCK,
        idempotency_key: str = '',
    ) -> CheckoutIntegrityResult:
        idempotency_key = cls.normalize_idempotency_key(idempotency_key)
        provider = _normalize_provider(provider)
        integrity = cls.build_subscription_integrity(user=user, plan=plan, idempotency_key=idempotency_key)
        order = cls.find_reusable_pending_order(
            user=user,
            fingerprint=integrity['fingerprint'],
            idempotency_key=idempotency_key,
            provider=provider,
        )
        reused_order = order is not None
        if not order:
            order = Order.objects.create(
                user=user,
                order_type=OrderType.SUBSCRIPTION,
                status=OrderStatus.AWAITING_PAYMENT,
                total_amount=plan.price,
                currency=plan.currency,
            )
            OrderItem.objects.create(
                order=order,
                item_type=PurchasedItemType.SUBSCRIPTION_PLAN,
                item_id=str(plan.id),
                title_snapshot=plan.title,
                quantity=1,
                unit_price=plan.price,
                total_price=plan.price,
                metadata={
                    'plan_code': plan.code,
                    'title': plan.title,
                    'trainer_id': getattr(plan, 'trainer_id', ''),
                    'checkout_integrity': integrity,
                },
            )
            _emit_order_event(
                event_type='order.awaiting_payment',
                order=order,
                extra_payload={
                    'item_type': PurchasedItemType.SUBSCRIPTION_PLAN,
                    'item_id': str(plan.id),
                    'plan_code': plan.code,
                    'title': plan.title,
                    'checkout_fingerprint': integrity['fingerprint'],
                    'idempotency_key': idempotency_key,
                },
            )
        else:
            _emit_order_event(
                event_type='order.reused_pending',
                order=order,
                extra_payload={
                    'checkout_fingerprint': integrity['fingerprint'],
                    'idempotency_key': idempotency_key,
                },
            )

        payment_before = order.payments.filter(provider=provider, status__in=['created', 'pending']).order_by('-created_at').first()
        payment = PaymentService.create_checkout_payment(order=order, provider=provider)
        reused_payment = payment_before is not None and payment_before.pk == payment.pk
        cls.enrich_payment_payload(payment=payment, integrity=integrity, reused_order=reused_order)
        return CheckoutIntegrityResult(
            order=order,
            payment=payment,
            reused_order=reused_order,
            reused_payment=reused_payment,
            integrity=integrity,
        )

    @classmethod
    def enrich_payment_payload(cls, *, payment, integrity: dict[str, Any], reused_order: bool) -> None:
        payload = payment.provider_payload or {}
        checkout_integrity = {
            'schema_version': CHECKOUT_INTEGRITY_SCHEMA_VERSION,
            'order_fingerprint': integrity.get('fingerprint'),
            'idempotency_key': integrity.get('idempotency_key', ''),
            'reused_order': reused_order,
            'price_snapshot': integrity.get('price_snapshot', {}),
            'commission_snapshot': integrity.get('commission_snapshot', {}),
        }
        payment.provider_payload = {
            **payload,
            'checkout_integrity': checkout_integrity,
        }
        payment.save(update_fields=['provider_payload', 'updated_at'])

    @classmethod
    def extract_order_integrity(cls, order: Order) -> dict[str, Any]:
        first_item = order.items.order_by('created_at').first()
        metadata = getattr(first_item, 'metadata', {}) or {}
        return metadata.get('checkout_integrity') or {}
