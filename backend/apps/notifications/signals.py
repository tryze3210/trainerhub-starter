"""
Integration seam.
Connect domain events here instead of embedding delivery logic into transactional models.

Example hooks:
- payment succeeded -> DomainNotificationTriggers.on_order_paid(...)
- payment failed -> DomainNotificationTriggers.on_payment_failed(...)
- subscription activated -> DomainNotificationTriggers.on_subscription_activated(...)
"""
