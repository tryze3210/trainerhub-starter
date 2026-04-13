from finance_closing.constants import AccountingDocumentType


PREFIX_BY_TYPE = {
    AccountingDocumentType.TRAINER_STATEMENT: 'STM',
    AccountingDocumentType.PLATFORM_INVOICE: 'INV',
    AccountingDocumentType.CREDIT_NOTE: 'CRN',
}


def build_document_number(*, document_type: str, period_code: str, sequence: int) -> str:
    prefix = PREFIX_BY_TYPE[document_type]
    return f'{prefix}-{period_code}-{sequence:05d}'
