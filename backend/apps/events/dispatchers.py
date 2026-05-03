from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from django.utils import timezone

from apps.events.models import InboxMessage

EventHandler = Callable[[str, dict[str, Any]], None]


@dataclass(frozen=True)
class RegisteredEventHandler:
    """Runtime registration for one outbox topic handler.

    The registry intentionally stores only Python callables. Handler state and
    idempotency are persisted through InboxMessage rows, so Celery retries and
    manual operator retries do not duplicate internal projections.
    """

    key: str
    consumer: str
    matcher: str
    pattern: str
    handler: EventHandler

    def matches(self, topic: str) -> bool:
        if self.matcher == 'exact':
            return topic == self.pattern
        if self.matcher == 'prefix':
            return topic.startswith(self.pattern)
        if self.matcher == 'wildcard':
            return True
        return False

    def as_dict(self) -> dict[str, Any]:
        return {
            'key': self.key,
            'consumer': self.consumer,
            'matcher': self.matcher,
            'pattern': self.pattern,
            'handler': getattr(self.handler, '__name__', self.handler.__class__.__name__),
        }


class EventDispatcherRegistry:
    """Small in-process dispatcher registry for the transactional outbox.

    This is deliberately boring: no dynamic imports, no runtime plugin magic and
    no external broker assumption. Domain services write durable outbox messages;
    workers call this registry to route each topic to one or more idempotent
    consumers. External adapters can be added as registered handlers later.
    """

    def __init__(self) -> None:
        self._handlers: list[RegisteredEventHandler] = []

    def register(
        self,
        *,
        consumer: str,
        topic: str | None = None,
        prefix: str | None = None,
        key: str | None = None,
    ):
        if bool(topic) == bool(prefix):
            raise ValueError('Register handler with exactly one of topic or prefix.')

        matcher = 'exact' if topic else 'prefix'
        pattern = topic or prefix or ''
        registration_key = key or f'{consumer}:{matcher}:{pattern}'

        def decorator(handler: EventHandler) -> EventHandler:
            self._handlers.append(
                RegisteredEventHandler(
                    key=registration_key,
                    consumer=consumer,
                    matcher=matcher,
                    pattern=pattern,
                    handler=handler,
                )
            )
            return handler

        return decorator

    def register_wildcard(self, *, consumer: str, key: str | None = None):
        registration_key = key or f'{consumer}:wildcard:*'

        def decorator(handler: EventHandler) -> EventHandler:
            self._handlers.append(
                RegisteredEventHandler(
                    key=registration_key,
                    consumer=consumer,
                    matcher='wildcard',
                    pattern='*',
                    handler=handler,
                )
            )
            return handler

        return decorator

    def list_handlers(self) -> list[dict[str, Any]]:
        return [handler.as_dict() for handler in self._handlers]

    def matching_handlers(self, topic: str) -> list[RegisteredEventHandler]:
        return [handler for handler in self._handlers if handler.matches(topic)]

    def dispatch(self, topic: str, payload: dict[str, Any]) -> dict[str, Any]:
        handlers = self.matching_handlers(topic)
        if not handlers:
            raise LookupError(f'No outbox handler registered for topic {topic!r}.')

        dispatched: list[str] = []
        for registration in handlers:
            registration.handler(topic, payload)
            dispatched.append(registration.consumer)
        return {'topic': topic, 'handlers': dispatched, 'handler_count': len(dispatched)}


registry = EventDispatcherRegistry()


def _message_key(payload: dict[str, Any], topic: str) -> str:
    event_id = payload.get('event_id')
    if event_id:
        return str(event_id)[:160]

    idempotency_key = payload.get('idempotency_key')
    if idempotency_key:
        return str(idempotency_key)[:160]

    aggregate_type = payload.get('aggregate_type') or 'unknown'
    aggregate_id = payload.get('aggregate_id') or 'unknown'
    return f'{topic}:{aggregate_type}:{aggregate_id}'[:160]


def _record_inbox_projection(*, consumer: str, topic: str, payload: dict[str, Any]) -> None:
    InboxMessage.objects.update_or_create(
        consumer=consumer,
        message_key=_message_key(payload, topic),
        defaults={
            'status': InboxMessage.Status.PROCESSED,
            'payload': {
                'topic': topic,
                'event': payload,
            },
            'processed_at': timezone.now(),
            'last_error': '',
        },
    )


def _projection_handler(consumer: str) -> EventHandler:
    def handler(topic: str, payload: dict[str, Any]) -> None:
        _record_inbox_projection(consumer=consumer, topic=topic, payload=payload)

    handler.__name__ = f'{consumer.replace(".", "_")}_handler'
    return handler




def _analytics_projection_handler(topic: str, payload: dict[str, Any]) -> None:
    from apps.analytics.projections import analytics_projection_service

    analytics_projection_service.project_outbox_payload(topic=topic, payload=payload or {})


def _notification_projection_handler(topic: str, payload: dict[str, Any]) -> None:
    from apps.notifications.projections import notification_projection_service

    notification_projection_service.project_outbox_payload(topic=topic, payload=payload or {})


def _payout_revenue_projection_handler(topic: str, payload: dict[str, Any]) -> None:
    from apps.payouts.projections import payout_revenue_projection_service

    payout_revenue_projection_service.project_outbox_payload(topic=topic, payload=payload or {})


def _moderation_risk_projection_handler(topic: str, payload: dict[str, Any]) -> None:
    from apps.moderation.projections import moderation_risk_projection_service

    moderation_risk_projection_service.project_outbox_payload(topic=topic, payload=payload or {})


registry.register(prefix='payment.', consumer='analytics.commerce_projection')(
    _analytics_projection_handler
)
registry.register(prefix='order.', consumer='analytics.commerce_projection')(
    _analytics_projection_handler
)
registry.register(prefix='checkout.', consumer='analytics.commerce_projection')(
    _analytics_projection_handler
)
registry.register(prefix='media.', consumer='analytics.commerce_projection')(
    _analytics_projection_handler
)
registry.register(prefix='content.', consumer='analytics.commerce_projection')(
    _analytics_projection_handler
)
registry.register(prefix='video.', consumer='analytics.commerce_projection')(
    _analytics_projection_handler
)
registry.register(prefix='page.', consumer='analytics.commerce_projection')(
    _analytics_projection_handler
)
registry.register(prefix='session.', consumer='analytics.commerce_projection')(
    _analytics_projection_handler
)
registry.register(prefix='subscription.', consumer='analytics.commerce_projection')(
    _analytics_projection_handler
)
registry.register(prefix='entitlement.', consumer='analytics.commerce_projection')(
    _analytics_projection_handler
)
registry.register(prefix='payout.', consumer='analytics.commerce_projection')(
    _analytics_projection_handler
)

registry.register(prefix='payment.', consumer='notifications.event_projection')(
    _notification_projection_handler
)
registry.register(prefix='payment.', consumer='payouts.revenue_projection')(
    _payout_revenue_projection_handler
)
registry.register(prefix='order.', consumer='notifications.event_projection')(
    _notification_projection_handler
)
registry.register(prefix='entitlement.', consumer='notifications.event_projection')(
    _notification_projection_handler
)
registry.register(prefix='subscription.', consumer='notifications.event_projection')(
    _notification_projection_handler
)
registry.register(prefix='payout.', consumer='notifications.event_projection')(
    _notification_projection_handler
)
registry.register(prefix='moderation.', consumer='notifications.event_projection')(
    _notification_projection_handler
)

registry.register(topic='payment.dispute_opened', consumer='moderation.risk_projection')(
    _moderation_risk_projection_handler
)
registry.register(topic='payment.chargeback_lost', consumer='moderation.risk_projection')(
    _moderation_risk_projection_handler
)
registry.register(topic='payment.chargeback_won', consumer='moderation.risk_projection')(
    _moderation_risk_projection_handler
)

registry.register(prefix='payment.', consumer='events.payment_projection')(
    _projection_handler('events.payment_projection')
)
registry.register(prefix='order.', consumer='events.order_projection')(
    _projection_handler('events.order_projection')
)
registry.register(prefix='checkout.', consumer='events.checkout_projection')(
    _projection_handler('events.checkout_projection')
)
registry.register(prefix='entitlement.', consumer='events.entitlement_projection')(
    _projection_handler('events.entitlement_projection')
)
registry.register(prefix='subscription.', consumer='events.subscription_projection')(
    _projection_handler('events.subscription_projection')
)
registry.register(prefix='payout.', consumer='events.payout_projection')(
    _projection_handler('events.payout_projection')
)
registry.register(prefix='media.', consumer='events.media_projection')(
    _projection_handler('events.media_projection')
)
registry.register(prefix='moderation.', consumer='events.moderation_projection')(
    _projection_handler('events.moderation_projection')
)
registry.register(prefix='notification.', consumer='events.notification_projection')(
    _projection_handler('events.notification_projection')
)
registry.register_wildcard(consumer='events.audit_projection')(
    _projection_handler('events.audit_projection')
)


def dispatch_outbox_message(topic: str, payload: dict[str, Any]) -> dict[str, Any]:
    return registry.dispatch(topic, payload or {})


def list_dispatch_handlers() -> list[dict[str, Any]]:
    return registry.list_handlers()
