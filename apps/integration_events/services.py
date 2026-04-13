from dataclasses import dataclass
from typing import Any

from django.db import transaction
from django.utils import timezone

from .constants import EventStatus
from .exceptions import DuplicateInboundMessageError
from .models import (
    AuditLogEntry,
    DeadLetterEvent,
    DomainOutboxEvent,
    EventDeliveryAttempt,
    EventSubscription,
    InboundMessage,
)


@dataclass
class PublishResult:
    delivered: int
    failed: int


class AuditLogService:
    @staticmethod
    def record(*, action: str, actor_type: str, object_type: str, object_id: str, payload: dict | None = None, actor_user=None, correlation_id: str = ""):
        return AuditLogEntry.objects.create(
            action=action,
            actor_type=actor_type,
            actor_user=actor_user,
            object_type=object_type,
            object_id=object_id,
            payload=payload or {},
            correlation_id=correlation_id,
        )


class DomainEventService:
    @staticmethod
    @transaction.atomic
    def append(*, event_name: str, aggregate_type: str, aggregate_id: str, idempotency_key: str, payload: dict, headers: dict | None = None, correlation_id: str = "", causation_id: str = "", source_app: str = "", source_model: str = "", source_id: str = ""):
        event, _ = DomainOutboxEvent.objects.get_or_create(
            idempotency_key=idempotency_key,
            defaults={
                "event_name": event_name,
                "aggregate_type": aggregate_type,
                "aggregate_id": aggregate_id,
                "payload": payload,
                "headers": headers or {},
                "correlation_id": correlation_id,
                "causation_id": causation_id,
                "source_app": source_app,
                "source_model": source_model,
                "source_id": source_id,
            },
        )
        return event


class EventPublisherService:
    @staticmethod
    @transaction.atomic
    def publish_event(outbox_event: DomainOutboxEvent) -> PublishResult:
        subscriptions = EventSubscription.objects.filter(is_enabled=True, event_names__contains=[outbox_event.event_name])
        delivered = 0
        failed = 0
        outbox_event.status = EventStatus.PROCESSING
        outbox_event.attempt_count += 1
        outbox_event.save(update_fields=["status", "attempt_count", "updated_at"])

        for subscription in subscriptions:
            attempt = EventDeliveryAttempt.objects.create(
                outbox_event=outbox_event,
                subscription=subscription,
                attempt_no=outbox_event.attempt_count,
            )
            try:
                # transport adapter call belongs here; omitted intentionally in patch skeleton
                attempt.success = True
                attempt.response_code = "simulated-200"
                delivered += 1
            except Exception as exc:  # pragma: no cover - integration placeholder
                attempt.success = False
                attempt.error_message = str(exc)
                failed += 1
            finally:
                attempt.finished_at = timezone.now()
                attempt.save()

        if failed == 0:
            outbox_event.status = EventStatus.PUBLISHED
            outbox_event.published_at = timezone.now()
            outbox_event.last_error = ""
        else:
            outbox_event.status = EventStatus.FAILED
            outbox_event.failed_at = timezone.now()
            outbox_event.last_error = f"{failed} delivery attempt(s) failed"
        outbox_event.save()
        return PublishResult(delivered=delivered, failed=failed)

    @staticmethod
    @transaction.atomic
    def dead_letter(outbox_event: DomainOutboxEvent, reason: str):
        outbox_event.status = EventStatus.DEAD_LETTER
        outbox_event.dead_lettered_at = timezone.now()
        outbox_event.last_error = reason
        outbox_event.save(update_fields=["status", "dead_lettered_at", "last_error", "updated_at"])
        DeadLetterEvent.objects.get_or_create(
            outbox_event=outbox_event,
            defaults={
                "reason": reason,
                "payload_snapshot": outbox_event.payload,
                "headers_snapshot": outbox_event.headers,
            },
        )
        return outbox_event


class InboundMessageService:
    @staticmethod
    @transaction.atomic
    def register(*, provider: str, message_type: str, external_event_key: str, payload: dict, headers: dict | None = None, correlation_id: str = "") -> InboundMessage:
        try:
            return InboundMessage.objects.create(
                provider=provider,
                message_type=message_type,
                external_event_key=external_event_key,
                payload=payload,
                headers=headers or {},
                correlation_id=correlation_id,
            )
        except Exception as exc:
            raise DuplicateInboundMessageError(str(exc)) from exc

    @staticmethod
    @transaction.atomic
    def mark_processed(message: InboundMessage):
        message.processed_at = timezone.now()
        message.processing_error = ""
        message.save(update_fields=["processed_at", "processing_error", "updated_at"])
        return message

    @staticmethod
    @transaction.atomic
    def mark_failed(message: InboundMessage, error: Exception | str):
        message.processing_error = str(error)
        message.save(update_fields=["processing_error", "updated_at"])
        return message
