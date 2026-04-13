from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from finance_closing.constants import SnapshotStatus
from finance_closing.models import ClosingPeriod, FinanceSnapshot
from payouts.models import LedgerEntry


class SnapshotService:
    @classmethod
    @transaction.atomic
    def generate_month_end_snapshot(cls, *, period: ClosingPeriod, actor=None) -> FinanceSnapshot:
        latest = FinanceSnapshot.objects.filter(period=period).order_by('-version').first()
        next_version = 1 if latest is None else latest.version + 1

        if latest and latest.status == SnapshotStatus.READY:
            latest.status = SnapshotStatus.SUPERSEDED
            latest.save(update_fields=['status', 'updated_at'])

        cutoff = period.ends_at
        ledger_qs = LedgerEntry.objects.filter(created_at__lte=cutoff, currency=period.currency)

        payload = {
            'ledger': {
                'platform_commission_accrued': str(
                    ledger_qs.filter(account_code='platform_commission_receivable').aggregate(total=Sum('credit_amount'))['total'] or Decimal('0.00')
                ),
                'trainer_payable_balance': str(
                    (ledger_qs.filter(account_code='trainer_payable').aggregate(total=Sum('credit_amount'))['total'] or Decimal('0.00'))
                    -
                    (ledger_qs.filter(account_code='trainer_payable').aggregate(total=Sum('debit_amount'))['total'] or Decimal('0.00'))
                ),
            },
            'generated_from_period': period.code,
        }

        snapshot = FinanceSnapshot.objects.create(
            period=period,
            version=next_version,
            ledger_cutoff_at=cutoff,
            generated_by=actor,
            generated_at=timezone.now(),
            status=SnapshotStatus.READY,
            payload=payload,
        )
        return snapshot
