class NotificationChannel:
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"
    IN_APP = "in_app"

    CHOICES = (
        (EMAIL, "Email"),
        (PUSH, "Push"),
        (SMS, "SMS"),
        (IN_APP, "In-app"),
    )


class NotificationCategory:
    SYSTEM = "system"
    TRANSACTIONAL = "transactional"
    MARKETING = "marketing"
    BILLING = "billing"
    PAYOUT = "payout"
    SECURITY = "security"

    CHOICES = (
        (SYSTEM, "System"),
        (TRANSACTIONAL, "Transactional"),
        (MARKETING, "Marketing"),
        (BILLING, "Billing"),
        (PAYOUT, "Payout"),
        (SECURITY, "Security"),
    )


class TemplateStatus:
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"

    CHOICES = (
        (DRAFT, "Draft"),
        (ACTIVE, "Active"),
        (ARCHIVED, "Archived"),
    )


class DeliveryStatus:
    PENDING = "pending"
    DISPATCHING = "dispatching"
    SENT = "sent"
    FAILED = "failed"
    SUPPRESSED = "suppressed"
    CANCELED = "canceled"

    CHOICES = (
        (PENDING, "Pending"),
        (DISPATCHING, "Dispatching"),
        (SENT, "Sent"),
        (FAILED, "Failed"),
        (SUPPRESSED, "Suppressed"),
        (CANCELED, "Canceled"),
    )


class EventKey:
    ORDER_PAID = "order.paid"
    PAYMENT_REFUNDED = "payment.refunded"
    SUBSCRIPTION_RENEWED = "subscription.renewed"
    SUBSCRIPTION_CANCELED = "subscription.canceled"
    PAYOUT_CREATED = "payout.created"
    PAYOUT_PAID = "payout.paid"
    SECURITY_LOGIN = "security.login"
