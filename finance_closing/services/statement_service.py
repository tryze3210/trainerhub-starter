from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from finance_closing.constants import AccountingDocumentStatus, AccountingDocumentType
from finance_closing.models import (
    AccountingDocument,
    AccountingDocumentLine,
    TaxProfile,
    TrainerMonthStatement,
)
from finance_closing.services.numbering import build_document_number
from payouts.models import LedgerEntry

TWOPLACES = Decimal('0.01')


class TrainerStatementService:
    @classmethod
    def _q(cls, value: Decimal) -> Decimal:
        return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)

    @classmethod
    def _build_statement_lines(cls, *, trainer, period, currency):
        entries = LedgerEntry.objects.filter(trainer=trainer, currency=currency, created_at__range=(period.starts_at, period.ends_at))
        gross_sales = sum((e.credit_amount for e in entries.filter(account_code='cash_clearing')), Decimal('0.00'))
        refunds = sum((e.debit_amount for e in entries.filter(account_code='cash_clearing_refund')), Decimal('0.00'))
        commissions = sum((e.credit_amount for e in entries.filter(account_code='platform_commission_receivable')), Decimal('0.00'))
        payout_fees = sum((e.debit_amount for e in entries.filter(account_code='payout_fee_expense')), Decimal('0.00'))
        reserve = sum((e.credit_amount for e in entries.filter(account_code='trainer_reserve_hold')), Decimal('0.00'))
        net_payable = sum((e.credit_amount - e.debit_amount for e in entries.filter(account_code='trainer_payable')), Decimal('0.00'))

        line_items = [
            {'code': 'gross_sales', 'label': 'Gross sales settled', 'amount': str(cls._q(gross_sales))},
            {'code': 'refunds', 'label': 'Refunds and reversals', 'amount': str(cls._q(refunds))},
            {'code': 'commission', 'label': 'Platform commission', 'amount': str(cls._q(commissions))},
            {'code': 'payout_fees', 'label': 'Payout fees', 'amount': str(cls._q(payout_fees))},
            {'code': 'reserve', 'label': 'Reserve holdback', 'amount': str(cls._q(reserve))},
            {'code': 'net_payable', 'label': 'Net payable', 'amount': str(cls._q(net_payable))},
        ]
        return {
            'gross_sales_amount': cls._q(gross_sales),
            'refunds_amount': cls._q(refunds),
            'commission_amount': cls._q(commissions),
            'payout_fees_amount': cls._q(payout_fees),
            'reserve_amount': cls._q(reserve),
            'net_payable_amount': cls._q(net_payable),
            'line_items': line_items,
        }

    @classmethod
    @transaction.atomic
    def build_or_replace_statement(cls, *, trainer, period, snapshot):
        data = cls._build_statement_lines(trainer=trainer, period=period, currency=period.currency)
        statement, _ = TrainerMonthStatement.objects.update_or_create(
            trainer=trainer,
            period=period,
            currency=period.currency,
            defaults={
                'snapshot': snapshot,
                **data,
            },
        )
        return statement

    @classmethod
    @transaction.atomic
    def issue_statement_document(cls, *, statement: TrainerMonthStatement):
        existing = statement.accounting_document
        if existing and existing.status == AccountingDocumentStatus.ISSUED:
            return existing

        sequence = AccountingDocument.objects.filter(period=statement.period, document_type=AccountingDocumentType.TRAINER_STATEMENT).count() + 1
        number = build_document_number(
            document_type=AccountingDocumentType.TRAINER_STATEMENT,
            period_code=statement.period.code,
            sequence=sequence,
        )
        tax_profile = getattr(statement.trainer, 'tax_profile', None)
        withholding_rate = tax_profile.withholding_rate if tax_profile else Decimal('0.00')
        withholding_amount = cls._q(statement.net_payable_amount * withholding_rate / Decimal('100.00'))
        total_after_withholding = cls._q(statement.net_payable_amount - withholding_amount)

        document = AccountingDocument.objects.create(
            document_type=AccountingDocumentType.TRAINER_STATEMENT,
            status=AccountingDocumentStatus.ISSUED,
            number=number,
            period=statement.period,
            trainer=statement.trainer,
            currency=statement.currency,
            subtotal_amount=statement.net_payable_amount,
            tax_amount=withholding_amount,
            total_amount=total_after_withholding,
            issued_at=timezone.now(),
            payload={
                'statement_snapshot_id': str(statement.snapshot_id),
                'line_items': statement.line_items,
                'withholding_rate': str(withholding_rate),
            },
        )

        lines = []
        for index, item in enumerate(statement.line_items):
            sign = Decimal('-1.00') if item['code'] in {'refunds', 'commission', 'payout_fees', 'reserve'} else Decimal('1.00')
            line_amount = cls._q(Decimal(item['amount']) * sign)
            lines.append(AccountingDocumentLine(
                document=document,
                sort_order=index,
                code=item['code'],
                description=item['label'],
                quantity=Decimal('1.00'),
                unit_amount=line_amount,
                line_amount=line_amount,
                metadata=item,
            ))
        if withholding_amount > Decimal('0.00'):
            lines.append(AccountingDocumentLine(
                document=document,
                sort_order=len(lines) + 1,
                code='withholding_tax',
                description='Withholding tax',
                quantity=Decimal('1.00'),
                unit_amount=withholding_amount * Decimal('-1.00'),
                line_amount=withholding_amount * Decimal('-1.00'),
                metadata={'rate': str(withholding_rate)},
            ))
        AccountingDocumentLine.objects.bulk_create(lines)

        statement.accounting_document = document
        statement.issued_at = document.issued_at
        statement.save(update_fields=['accounting_document', 'issued_at', 'updated_at'])
        return document
