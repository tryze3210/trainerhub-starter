from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any
from uuid import UUID

from django.db import transaction
from django.db.models import Count, DecimalField, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.events.models import InboxMessage
from apps.payouts.models import BalanceEntry, TrainerWallet
from apps.payouts.services import PayoutService


PAYOUT_REVENUE_PROJECTION_CONSUMER = 'payouts.revenue_projection'
DEFAULT_TRAINER_REVENUE_RATE = Decimal('0.90')


@dataclass(frozen=True, slots=True)
class PayoutProjectionResult:
    status: str
    topic: str
    message_key: str
    reason: str = ''
    trainer_id: str = ''
    payment_id: str = ''
    amount: str = ''
    currency: str = ''
    created: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            'status': self.status,
            'topic': self.topic,
            'message_key': self.message_key,
            'reason': self.reason,
            'trainer_id': self.trainer_id,
            'payment_id': self.payment_id,
            'amount': self.amount,
            'currency': self.currency,
            'created': self.created,
        }


class PayoutRevenueProjectionService:
    """Project commercial payment events into trainer payout ledger rows.

    The direct payment service already accrues trainer revenue for the happy path.
    This projection is the durable safety net: it can backfill missed accruals
    from outbox events and it is idempotent on ``payment_id`` + ledger entry.
    """

    PAYOUTABLE_TOPICS = {
        'payment.succeeded',
        'payment.paid',
        'payment.captured',
    }

    def project_outbox_payload(self, *, topic: str, payload: dict[str, Any] | None) -> dict[str, Any]:
        envelope = payload or {}
        message_key = self._message_key(envelope=envelope, topic=topic)

        if topic not in self.PAYOUTABLE_TOPICS:
            self._record_inbox(
                message_key=message_key,
                topic=topic,
                envelope=envelope,
                status=InboxMessage.Status.PROCESSED,
                projection_status='skipped',
                reason='Topic is not mapped to payout revenue accrual.',
            )
            return PayoutProjectionResult(
                status='skipped',
                topic=topic,
                message_key=message_key,
                reason='Topic is not mapped to payout revenue accrual.',
            ).as_dict()

        extracted = self._extract_revenue_payload(envelope=envelope)
        if extracted['error']:
            self._record_inbox(
                message_key=message_key,
                topic=topic,
                envelope=envelope,
                status=InboxMessage.Status.PROCESSED,
                projection_status='skipped',
                reason=extracted['error'],
            )
            return PayoutProjectionResult(
                status='skipped',
                topic=topic,
                message_key=message_key,
                reason=extracted['error'],
            ).as_dict()

        trainer_id = extracted['trainer_id']
        payment_id = extracted['payment_id']
        amount = extracted['amount']
        currency = extracted['currency']

        with transaction.atomic():
            existing = BalanceEntry.objects.filter(
                source_type='payment',
                source_id=payment_id,
                entry_type=BalanceEntry.EntryType.ACCRUAL,
            ).select_related('wallet', 'wallet__trainer').first()
            if existing:
                self._record_inbox(
                    message_key=message_key,
                    topic=topic,
                    envelope=envelope,
                    status=InboxMessage.Status.PROCESSED,
                    projection_status='already_projected',
                    reason='Payment accrual ledger entry already exists.',
                    trainer_id=str(existing.wallet.trainer.user_id),
                    payment_id=str(payment_id),
                    amount=str(existing.amount),
                    currency=existing.currency,
                )
                return PayoutProjectionResult(
                    status='already_projected',
                    topic=topic,
                    message_key=message_key,
                    reason='Payment accrual ledger entry already exists.',
                    trainer_id=str(existing.wallet.trainer.user_id),
                    payment_id=str(payment_id),
                    amount=str(existing.amount),
                    currency=existing.currency,
                    created=False,
                ).as_dict()

            trainer = PayoutService._resolve_trainer_profile(trainer_id)
            wallet, _ = TrainerWallet.objects.select_for_update().get_or_create(
                trainer=trainer,
                defaults={'currency': currency},
            )
            wallet.available_amount += amount
            wallet.save(update_fields=['available_amount', 'updated_at'])

            BalanceEntry.objects.create(
                wallet=wallet,
                entry_type=BalanceEntry.EntryType.ACCRUAL,
                direction='credit',
                amount=amount,
                currency=currency,
                status='available',
                source_type='payment',
                source_id=payment_id,
            )

            self._record_inbox(
                message_key=message_key,
                topic=topic,
                envelope=envelope,
                status=InboxMessage.Status.PROCESSED,
                projection_status='projected',
                reason='',
                trainer_id=str(trainer.user_id),
                payment_id=str(payment_id),
                amount=str(amount),
                currency=currency,
            )

        return PayoutProjectionResult(
            status='projected',
            topic=topic,
            message_key=message_key,
            trainer_id=str(trainer.user_id),
            payment_id=str(payment_id),
            amount=str(amount),
            currency=currency,
            created=True,
        ).as_dict()

    def projection_health(self) -> dict[str, Any]:
        inbox_qs = InboxMessage.objects.filter(consumer=PAYOUT_REVENUE_PROJECTION_CONSUMER)
        latest = inbox_qs.order_by('-processed_at', '-created_at').first()
        projected = inbox_qs.filter(payload__projection_status__in=['projected', 'already_projected']).count()
        skipped = inbox_qs.filter(payload__projection_status='skipped').count()
        failed = inbox_qs.filter(status=InboxMessage.Status.FAILED).count()
        ledger_total = BalanceEntry.objects.filter(
            source_type='payment',
            entry_type=BalanceEntry.EntryType.ACCRUAL,
        ).aggregate(
            amount=Coalesce(
                Sum('amount'),
                Value(Decimal('0.00')),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )['amount']
        ledger_counts = list(
            BalanceEntry.objects.filter(source_type='payment')
            .values('entry_type', 'currency')
            .annotate(count=Count('id'), amount=Coalesce(Sum('amount'), Value(Decimal('0.00')), output_field=DecimalField(max_digits=14, decimal_places=2)))
            .order_by('entry_type', 'currency')
        )
        return {
            'consumer': PAYOUT_REVENUE_PROJECTION_CONSUMER,
            'status': 'degraded' if failed else 'ok',
            'projected_messages': projected,
            'skipped_messages': skipped,
            'failed_messages': failed,
            'latest_processed_at': latest.processed_at if latest else None,
            'latest_message_key': latest.message_key if latest else '',
            'latest_payload': latest.payload if latest else {},
            'ledger_accrual_amount': ledger_total,
            'ledger_counts': ledger_counts,
        }

    def _record_inbox(
        self,
        *,
        message_key: str,
        topic: str,
        envelope: dict[str, Any],
        status: str,
        projection_status: str,
        reason: str,
        trainer_id: str = '',
        payment_id: str = '',
        amount: str = '',
        currency: str = '',
    ) -> None:
        InboxMessage.objects.update_or_create(
            consumer=PAYOUT_REVENUE_PROJECTION_CONSUMER,
            message_key=message_key[:160],
            defaults={
                'status': status,
                'payload': {
                    'topic': topic,
                    'projection_status': projection_status,
                    'reason': reason,
                    'trainer_id': trainer_id,
                    'payment_id': payment_id,
                    'amount': amount,
                    'currency': currency,
                    'event': envelope,
                },
                'processed_at': timezone.now(),
                'last_error': '',
            },
        )

    def _extract_revenue_payload(self, *, envelope: dict[str, Any]) -> dict[str, Any]:
        domain_payload = envelope.get('payload') or {}
        domain_metadata = envelope.get('metadata') or {}
        provider_payload = domain_payload.get('provider_payload') or {}

        sources = (domain_payload, provider_payload, domain_metadata)
        payment_id_raw = self._first_value(
            sources,
            'payment_id',
        ) or (envelope.get('aggregate_id') if envelope.get('aggregate_type') == 'payment' else '')
        payment_id = self._uuid_or_none(payment_id_raw)
        if payment_id is None:
            return {'error': 'Payment id is missing or is not a UUID.'}

        trainer_id_raw = self._first_value(
            sources,
            'trainer_id',
            'seller_id',
            'owner_id',
        )
        trainer_id = self._uuid_or_none(trainer_id_raw)
        if trainer_id is None:
            return {'error': 'Trainer id is missing or is not a UUID.'}

        currency = str(self._first_value(sources, 'currency') or 'RUB')[:8]
        amount = self._decimal_or_none(
            self._first_value(
                sources,
                'trainer_net',
                'payout_amount',
                'trainer_amount',
                'net_amount',
            )
        )
        if amount is None:
            gross = self._decimal_or_none(self._first_value(sources, 'amount', 'total_amount'))
            if gross is not None:
                amount = (gross * DEFAULT_TRAINER_REVENUE_RATE).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        if amount is None or amount <= Decimal('0.00'):
            return {'error': 'Positive trainer payout amount is missing.'}

        return {
            'error': '',
            'trainer_id': trainer_id,
            'payment_id': payment_id,
            'amount': amount,
            'currency': currency,
        }

    def _message_key(self, *, envelope: dict[str, Any], topic: str) -> str:
        return str(
            envelope.get('event_id')
            or envelope.get('idempotency_key')
            or f"{topic}:{envelope.get('aggregate_type', 'unknown')}:{envelope.get('aggregate_id', 'unknown')}"
        )[:160]

    def _first_value(self, sources: tuple[dict[str, Any], ...], *keys: str):
        for key in keys:
            for source in sources:
                if not isinstance(source, dict):
                    continue
                value = source.get(key)
                if value not in (None, ''):
                    return value
        return ''

    def _uuid_or_none(self, value: Any) -> UUID | None:
        if not value:
            return None
        try:
            return UUID(str(value))
        except (TypeError, ValueError):
            return None

    def _decimal_or_none(self, value: Any) -> Decimal | None:
        if value in (None, ''):
            return None
        try:
            return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except (InvalidOperation, TypeError, ValueError):
            return None


payout_revenue_projection_service = PayoutRevenueProjectionService()
