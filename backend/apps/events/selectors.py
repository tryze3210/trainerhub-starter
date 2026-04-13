from __future__ import annotations

from apps.events.models import InboxMessage, OutboxMessage


OUTBOX_MESSAGES: list[OutboxMessage] = [
    OutboxMessage(
        id='out_1',
        event_id='evt_1',
        topic='payments.payment_paid',
        status='pending',
        attempts=0,
        payload={'payment_id': 'pay_1', 'order_id': 'ord_1', 'tenant_id': 'tenant_studio_1'},
        next_retry_at=None,
    ),
    OutboxMessage(
        id='out_2',
        event_id='evt_2',
        topic='moderation.content_approved',
        status='processing',
        attempts=1,
        payload={'content_type': 'video', 'content_id': 'vid_101', 'tenant_id': 'tenant_studio_1'},
        next_retry_at=None,
    ),
]

INBOX_MESSAGES: list[InboxMessage] = [
    InboxMessage(
        id='in_1',
        consumer='public_catalog.projector',
        message_key='evt_2',
        status='processed',
        processed_at='2026-04-09T11:00:00Z',
    ),
]


def list_outbox_messages() -> list[OutboxMessage]:
    return OUTBOX_MESSAGES


def list_inbox_messages() -> list[InboxMessage]:
    return INBOX_MESSAGES
