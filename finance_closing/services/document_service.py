from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from finance_closing.constants import AccountingDocumentStatus, AccountingDocumentType
from finance_closing.models import AccountingDocument, AccountingDocumentLine
from finance_closing.services.numbering import build_document_number


class CreditNoteService:
    @classmethod
    @transaction.atomic
    def issue_credit_note(cls, *, replaced_document: AccountingDocument, reason: str, line_items: list[dict]):
        sequence = AccountingDocument.objects.filter(
            period=replaced_document.period,
            document_type=AccountingDocumentType.CREDIT_NOTE,
        ).count() + 1
        number = build_document_number(
            document_type=AccountingDocumentType.CREDIT_NOTE,
            period_code=replaced_document.period.code,
            sequence=sequence,
        )
        total_amount = sum((Decimal(item['amount']) for item in line_items), Decimal('0.00'))
        document = AccountingDocument.objects.create(
            document_type=AccountingDocumentType.CREDIT_NOTE,
            status=AccountingDocumentStatus.ISSUED,
            number=number,
            period=replaced_document.period,
            trainer=replaced_document.trainer,
            currency=replaced_document.currency,
            subtotal_amount=total_amount,
            tax_amount=Decimal('0.00'),
            total_amount=total_amount,
            issued_at=timezone.now(),
            replaces_document=replaced_document,
            payload={'reason': reason, 'source_document_number': replaced_document.number},
        )
        AccountingDocumentLine.objects.bulk_create([
            AccountingDocumentLine(
                document=document,
                sort_order=index,
                code=item['code'],
                description=item['description'],
                quantity=Decimal('1.00'),
                unit_amount=Decimal(item['amount']),
                line_amount=Decimal(item['amount']),
                metadata=item.get('metadata', {}),
            )
            for index, item in enumerate(line_items)
        ])
        return document
