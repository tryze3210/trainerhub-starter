from __future__ import annotations

import json
from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.events.models import OutboxMessage
from apps.events.services import DomainEventService


@pytest.mark.django_db
def test_dispatch_outbox_management_command_processes_pending_message(capsys):
    emitted = DomainEventService().emit(
        event_type='notification.test',
        aggregate_type='notification',
        aggregate_id='notif_cmd_001',
        payload={'message': 'command smoke'},
        idempotency_key='notification:notif_cmd_001:test',
    )

    call_command('dispatch_outbox', '--batch-size', '10', '--json')

    output = capsys.readouterr().out.strip()
    summary = json.loads(output)
    assert summary['claimed'] == 1
    assert summary['processed'] == 1
    assert summary['failed'] == 0

    message = OutboxMessage.objects.get(pk=emitted['outbox_message_id'])
    assert message.status == OutboxMessage.Status.PROCESSED
    assert message.processed_at is not None


@pytest.mark.django_db
def test_requeue_stuck_outbox_management_command_requeues_processing_message(capsys):
    emitted = DomainEventService().emit(
        event_type='notification.test',
        aggregate_type='notification',
        aggregate_id='notif_cmd_stuck_001',
        payload={'message': 'stuck command smoke'},
        idempotency_key='notification:notif_cmd_stuck_001:test',
    )
    message = OutboxMessage.objects.get(pk=emitted['outbox_message_id'])
    message.status = OutboxMessage.Status.PROCESSING
    message.locked_at = timezone.now() - timedelta(minutes=30)
    message.save(update_fields=['status', 'locked_at', 'updated_at'])

    call_command('requeue_stuck_outbox', '--older-than-minutes', '15', '--limit', '10', '--json')

    output = capsys.readouterr().out.strip()
    summary = json.loads(output)
    assert summary['requeued'] == 1

    message.refresh_from_db()
    assert message.status == OutboxMessage.Status.PENDING
    assert message.locked_at is None
