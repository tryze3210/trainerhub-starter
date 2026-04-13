from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from apps.audit.services import AuditService
from apps.payouts.models import TrainerBalance, PayoutLedgerEntry, PayoutRequest


class PayoutService:
    @staticmethod
    def get_or_create_balance(*, trainer_id, currency='RUB'):
        balance, _ = TrainerBalance.objects.get_or_create(
            trainer_id=trainer_id,
            defaults={'currency': currency},
        )
        return balance

    @classmethod
    @transaction.atomic
    def accrue_from_payment(cls, *, trainer_id, payment, amount: Decimal):
        balance = cls.get_or_create_balance(trainer_id=trainer_id, currency=payment.currency)
        balance.available_amount += amount
        balance.lifetime_earned_amount += amount
        balance.save(update_fields=['available_amount', 'lifetime_earned_amount', 'updated_at'])
        PayoutLedgerEntry.objects.create(
            trainer_id=trainer_id,
            payment_id=str(payment.id),
            entry_type=PayoutLedgerEntry.EntryType.ACCRUAL,
            amount=amount,
            currency=payment.currency,
            metadata={'payment_id': str(payment.id)},
        )
        return balance

    @classmethod
    @transaction.atomic
    def request_payout(cls, *, trainer_id, amount: Decimal, destination_masked: str, request=None):
        balance = cls.get_or_create_balance(trainer_id=trainer_id)
        if amount > balance.available_amount:
            raise ValueError('Insufficient available balance for payout request.')
        balance.available_amount -= amount
        balance.reserved_amount += amount
        balance.save(update_fields=['available_amount', 'reserved_amount', 'updated_at'])
        payout = PayoutRequest.objects.create(
            trainer_id=trainer_id,
            amount=amount,
            currency=balance.currency,
            destination_masked=destination_masked,
        )
        PayoutLedgerEntry.objects.create(
            trainer_id=trainer_id,
            payout_request=payout,
            entry_type=PayoutLedgerEntry.EntryType.RESERVE,
            amount=amount,
            currency=balance.currency,
        )
        AuditService.log(event_type='payout.requested', entity_type='payout_request', entity_id=str(payout.id), context={'trainer_id': str(trainer_id), 'amount': str(amount)}, request=request)
        return payout

    @classmethod
    @transaction.atomic
    def approve_payout(cls, *, payout: PayoutRequest, actor=None, request=None):
        payout.status = PayoutRequest.Status.APPROVED
        payout.approved_at = timezone.now()
        payout.save(update_fields=['status', 'approved_at', 'updated_at'])
        AuditService.log(actor=actor, event_type='payout.approved', entity_type='payout_request', entity_id=str(payout.id), request=request)
        return payout

    @classmethod
    @transaction.atomic
    def mark_processing(cls, *, payout: PayoutRequest, actor=None, request=None):
        payout.status = PayoutRequest.Status.PROCESSING
        payout.save(update_fields=['status', 'updated_at'])
        AuditService.log(actor=actor, event_type='payout.processing', entity_type='payout_request', entity_id=str(payout.id), request=request)
        return payout

    @classmethod
    @transaction.atomic
    def mark_paid(cls, *, payout: PayoutRequest, actor=None, request=None):
        balance = cls.get_or_create_balance(trainer_id=payout.trainer_id, currency=payout.currency)
        balance.reserved_amount -= payout.amount
        balance.save(update_fields=['reserved_amount', 'updated_at'])
        payout.status = PayoutRequest.Status.PAID
        payout.processed_at = timezone.now()
        payout.save(update_fields=['status', 'processed_at', 'updated_at'])
        PayoutLedgerEntry.objects.create(
            trainer_id=payout.trainer_id,
            payout_request=payout,
            entry_type=PayoutLedgerEntry.EntryType.PAYOUT,
            amount=payout.amount,
            currency=payout.currency,
        )
        AuditService.log(actor=actor, event_type='payout.paid', entity_type='payout_request', entity_id=str(payout.id), request=request)
        return payout
