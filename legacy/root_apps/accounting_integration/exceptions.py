class AccountingIntegrationError(Exception):
    """Base domain exception."""


class AccountMappingError(AccountingIntegrationError):
    """Raised when no valid chart mapping exists."""


class JournalBatchStateError(AccountingIntegrationError):
    """Raised on invalid journal batch transition."""


class ExportRunStateError(AccountingIntegrationError):
    """Raised on invalid export run transition."""
