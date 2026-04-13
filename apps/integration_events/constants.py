class EventStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    PUBLISHED = "published"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"

    CHOICES = [
        (PENDING, "Pending"),
        (PROCESSING, "Processing"),
        (PUBLISHED, "Published"),
        (FAILED, "Failed"),
        (DEAD_LETTER, "Dead letter"),
    ]


class DeliveryTargetType:
    WEBHOOK = "webhook"
    MESSAGE_BUS = "message_bus"
    ACCOUNTING = "accounting"

    CHOICES = [
        (WEBHOOK, "Webhook"),
        (MESSAGE_BUS, "Message bus"),
        (ACCOUNTING, "Accounting"),
    ]


class AuditActorType:
    USER = "user"
    SYSTEM = "system"
    TASK = "task"
    WEBHOOK = "webhook"

    CHOICES = [
        (USER, "User"),
        (SYSTEM, "System"),
        (TASK, "Task"),
        (WEBHOOK, "Webhook"),
    ]
