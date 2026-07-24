from django.db.models import Count
from django.utils import timezone

from .constants import EventStatus
from .models import DeadLetterEvent, DomainOutboxEvent, InboundMessage


class OutboxSelector:
    @staticmethod
    def due_events(limit=100):
        return DomainOutboxEvent.objects.filter(
            status__in=[EventStatus.PENDING, EventStatus.FAILED],
            available_at__lte=timezone.now(),
        ).order_by("available_at", "id")[:limit]

    @staticmethod
    def backlog_summary():
        return DomainOutboxEvent.objects.values("status").annotate(total=Count("id")).order_by("status")


class DeadLetterSelector:
    @staticmethod
    def unresolved():
        return DeadLetterEvent.objects.filter(resolved_at__isnull=True).select_related("outbox_event")


class InboundMessageSelector:
    @staticmethod
    def recent_failures(limit=100):
        return InboundMessage.objects.exclude(processing_error="").order_by("-received_at")[:limit]
