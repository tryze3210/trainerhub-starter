class IntegrationEventError(Exception):
    """Base integration event error."""


class DuplicateInboundMessageError(IntegrationEventError):
    """Raised when inbound message is duplicated."""


class DeliveryTargetNotConfiguredError(IntegrationEventError):
    """Raised when target is missing adapter configuration."""
