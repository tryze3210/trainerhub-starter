from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID, NAMESPACE_URL, uuid5

from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.analytics.models import AnalyticsEvent
from apps.events.models import InboxMessage


ANALYTICS_PROJECTION_CONSUMER = 'analytics.commerce_projection'
ANALYTICS_PROJECTION_SOURCE = 'domain_event_outbox'


@dataclass(frozen=True, slots=True)
class AnalyticsProjectionResult:
    status: str
    topic: str
    message_key: str
    event_name: str | None = None
    event_uuid: str | None = None
    created: bool = False
    reason: str = ''

    def as_dict(self) -> dict[str, Any]:
        return {
            'status': self.status,
            'topic': self.topic,
            'message_key': self.message_key,
            'event_name': self.event_name,
            'event_uuid': self.event_uuid,
            'created': self.created,
            'reason': self.reason,
        }


class AnalyticsEventProjectionService:
    """Project domain outbox events into the analytics event stream.

    This service is intentionally idempotent. The domain event id becomes the
    analytics event UUID, so re-dispatching the same outbox message updates the
    inbox marker but never creates duplicate analytics rows.
    """

    PURCHASE_TOPICS = {
        'payment.paid',
        'payment.succeeded',
        'payment.captured',
        'order.paid',
        'order.completed',
    }
    CHECKOUT_TOPICS = {
        'checkout.started',
        'checkout.created',
        'checkout.payment_created',
        'checkout.session_created',
        'payment.checkout_created',
    }
    VIDEO_TOPICS = {
        'video.viewed',
        'media.video_viewed',
        'content.video_viewed',
    }
    SESSION_TOPICS = {'session.started', 'session_start'}
    PAGE_TOPICS = {'page.viewed', 'page_viewed', 'page_view'}

    def project_outbox_payload(self, *, topic: str, payload: dict[str, Any] | None) -> dict[str, Any]:
        envelope = payload or {}
        message_key = self._message_key(envelope=envelope, topic=topic)
        event_name = self._analytics_event_name(topic=topic)

        if not event_name:
            self._record_inbox(
                message_key=message_key,
                topic=topic,
                envelope=envelope,
                status=InboxMessage.Status.PROCESSED,
                projection_status='skipped',
                reason='Topic is not mapped to analytics_event.',
            )
            return AnalyticsProjectionResult(
                status='skipped',
                topic=topic,
                message_key=message_key,
                reason='Topic is not mapped to analytics_event.',
            ).as_dict()

        event_uuid = self._event_uuid(envelope=envelope, message_key=message_key)
        occurred_at = self._occurred_at(envelope=envelope)
        dimensions = self._dimensions(envelope=envelope, topic=topic)
        metadata = self._metadata(envelope=envelope, topic=topic)

        with transaction.atomic():
            analytics_event, created = AnalyticsEvent.objects.get_or_create(
                event_uuid=event_uuid,
                defaults={
                    'event_name': event_name,
                    'occurred_at': occurred_at,
                    'event_date': timezone.localtime(occurred_at).date() if timezone.is_aware(occurred_at) else occurred_at.date(),
                    'session_id': dimensions['session_id'],
                    'anonymous_id': dimensions['anonymous_id'],
                    'user_id': dimensions['user_id'],
                    'trainer_id': dimensions['trainer_id'],
                    'order_id': dimensions['order_id'],
                    'path': dimensions['path'],
                    'referrer': dimensions['referrer'],
                    'utm_source': dimensions['utm_source'],
                    'utm_medium': dimensions['utm_medium'],
                    'utm_campaign': dimensions['utm_campaign'],
                    'country_code': dimensions['country_code'],
                    'device_type': dimensions['device_type'],
                    'metadata': metadata,
                },
            )
            self._record_inbox(
                message_key=message_key,
                topic=topic,
                envelope=envelope,
                status=InboxMessage.Status.PROCESSED,
                projection_status='projected',
                reason='',
                analytics_event_uuid=str(analytics_event.event_uuid),
            )

        return AnalyticsProjectionResult(
            status='projected',
            topic=topic,
            message_key=message_key,
            event_name=event_name,
            event_uuid=str(analytics_event.event_uuid),
            created=created,
        ).as_dict()

    def projection_health(self) -> dict[str, Any]:
        inbox_qs = InboxMessage.objects.filter(consumer=ANALYTICS_PROJECTION_CONSUMER)
        latest = inbox_qs.order_by('-processed_at', '-created_at').first()
        event_counts = (
            AnalyticsEvent.objects.values('event_name')
            .annotate(count=Count('id'))
            .order_by('event_name')
        )
        projected = inbox_qs.filter(payload__projection_status='projected').count()
        skipped = inbox_qs.filter(payload__projection_status='skipped').count()
        failed = inbox_qs.filter(status=InboxMessage.Status.FAILED).count()
        return {
            'consumer': ANALYTICS_PROJECTION_CONSUMER,
            'status': 'degraded' if failed else 'ok',
            'projected_messages': projected,
            'skipped_messages': skipped,
            'failed_messages': failed,
            'latest_processed_at': latest.processed_at if latest else None,
            'latest_message_key': latest.message_key if latest else '',
            'latest_payload': latest.payload if latest else {},
            'analytics_event_counts': list(event_counts),
        }

    def _record_inbox(
        self,
        *,
        message_key: str,
        topic: str,
        envelope: dict[str, Any],
        status: str,
        projection_status: str,
        reason: str,
        analytics_event_uuid: str = '',
    ) -> None:
        InboxMessage.objects.update_or_create(
            consumer=ANALYTICS_PROJECTION_CONSUMER,
            message_key=message_key[:160],
            defaults={
                'status': status,
                'payload': {
                    'topic': topic,
                    'projection_status': projection_status,
                    'analytics_event_uuid': analytics_event_uuid,
                    'reason': reason,
                    'event': envelope,
                },
                'processed_at': timezone.now(),
                'last_error': '',
            },
        )

    def _analytics_event_name(self, *, topic: str) -> str | None:
        if topic in self.PURCHASE_TOPICS:
            return AnalyticsEvent.EVENT_PURCHASE_COMPLETED
        if topic in self.CHECKOUT_TOPICS:
            return AnalyticsEvent.EVENT_CHECKOUT_STARTED
        if topic in self.VIDEO_TOPICS:
            return AnalyticsEvent.EVENT_VIDEO_VIEW
        if topic in self.SESSION_TOPICS:
            return AnalyticsEvent.EVENT_SESSION_START
        if topic in self.PAGE_TOPICS:
            return AnalyticsEvent.EVENT_PAGE_VIEW
        return None

    def _message_key(self, *, envelope: dict[str, Any], topic: str) -> str:
        return str(
            envelope.get('event_id')
            or envelope.get('idempotency_key')
            or f"{topic}:{envelope.get('aggregate_type', 'unknown')}:{envelope.get('aggregate_id', 'unknown')}"
        )[:160]

    def _event_uuid(self, *, envelope: dict[str, Any], message_key: str) -> UUID:
        raw_event_id = envelope.get('event_id')
        if raw_event_id:
            try:
                return UUID(str(raw_event_id))
            except (TypeError, ValueError):
                pass
        return uuid5(NAMESPACE_URL, f'trainerhub:analytics:{message_key}')

    def _occurred_at(self, *, envelope: dict[str, Any]):
        raw_value = envelope.get('occurred_at')
        parsed = parse_datetime(str(raw_value)) if raw_value else None
        if parsed is None:
            return timezone.now()
        if timezone.is_naive(parsed):
            return timezone.make_aware(parsed, timezone.get_current_timezone())
        return parsed

    def _dimensions(self, *, envelope: dict[str, Any], topic: str) -> dict[str, Any]:
        domain_payload = envelope.get('payload') or {}
        domain_metadata = envelope.get('metadata') or {}
        session_id = self._string(domain_payload, domain_metadata, 'session_id') or f'domain:{self._message_key(envelope=envelope, topic=topic)}'
        return {
            'session_id': session_id[:128],
            'anonymous_id': self._string(domain_payload, domain_metadata, 'anonymous_id')[:128],
            'user_id': self._uuid_or_none(self._string(domain_payload, domain_metadata, 'user_id', 'customer_id', 'buyer_id')),
            'trainer_id': self._uuid_or_none(self._string(domain_payload, domain_metadata, 'trainer_id', 'seller_id', 'owner_id')),
            'order_id': self._uuid_or_none(self._string(domain_payload, domain_metadata, 'order_id') or (envelope.get('aggregate_id') if envelope.get('aggregate_type') == 'order' else '')),
            'path': self._string(domain_payload, domain_metadata, 'path')[:512],
            'referrer': self._string(domain_payload, domain_metadata, 'referrer')[:1024],
            'utm_source': self._string(domain_payload, domain_metadata, 'utm_source')[:128],
            'utm_medium': self._string(domain_payload, domain_metadata, 'utm_medium')[:128],
            'utm_campaign': self._string(domain_payload, domain_metadata, 'utm_campaign')[:128],
            'country_code': self._string(domain_payload, domain_metadata, 'country_code')[:8],
            'device_type': self._string(domain_payload, domain_metadata, 'device_type')[:32],
        }

    def _metadata(self, *, envelope: dict[str, Any], topic: str) -> dict[str, Any]:
        domain_payload = envelope.get('payload') or {}
        return {
            'source': ANALYTICS_PROJECTION_SOURCE,
            'topic': topic,
            'domain_event_id': envelope.get('event_id'),
            'domain_event_type': envelope.get('event_type') or topic,
            'aggregate_type': envelope.get('aggregate_type'),
            'aggregate_id': envelope.get('aggregate_id'),
            'idempotency_key': envelope.get('idempotency_key'),
            'amount': str(domain_payload.get('amount') or domain_payload.get('total_amount') or ''),
            'currency': domain_payload.get('currency') or '',
            'domain_payload': domain_payload,
            'domain_metadata': envelope.get('metadata') or {},
        }

    def _string(self, domain_payload: dict[str, Any], domain_metadata: dict[str, Any], *keys: str) -> str:
        for key in keys:
            value = domain_payload.get(key)
            if value not in (None, ''):
                return str(value)
            value = domain_metadata.get(key)
            if value not in (None, ''):
                return str(value)
        return ''

    def _uuid_or_none(self, value: str | None) -> UUID | None:
        if not value:
            return None
        try:
            return UUID(str(value))
        except (TypeError, ValueError):
            return None


analytics_projection_service = AnalyticsEventProjectionService()
