from __future__ import annotations

import json

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.events.health import get_outbox_health
from apps.events.models import OutboxMessage
from apps.events.services import DomainEventService


@pytest.mark.django_db
def test_outbox_health_reports_pending_message_without_failing(capsys):
    DomainEventService().emit(
        event_type='notification.test',
        aggregate_type='notification',
        aggregate_id='notif_health_001',
        payload={'message': 'health smoke'},
        idempotency_key='notification:notif_health_001:test',
    )

    call_command('outbox_health', '--json', '--max-pending-age-minutes', '60')

    output = capsys.readouterr().out.strip()
    payload = json.loads(output)
    assert payload['ok'] is True
    assert payload['status'] == 'ok'
    assert payload['outbox']['pending_count'] == 1


@pytest.mark.django_db
def test_outbox_health_fails_when_dead_messages_exceed_limit():
    emitted = DomainEventService().emit(
        event_type='payment.failed_projection',
        aggregate_type='payment',
        aggregate_id='pay_health_dead_001',
        payload={'reason': 'smoke'},
        idempotency_key='payment:pay_health_dead_001:failed_projection',
    )
    message = OutboxMessage.objects.get(pk=emitted['outbox_message_id'])
    message.status = OutboxMessage.Status.DEAD
    message.last_error = 'permanent smoke failure'
    message.save(update_fields=['status', 'last_error', 'updated_at'])

    health = get_outbox_health(max_dead_messages=0)
    assert health['ok'] is False
    assert health['status'] == 'critical'
    assert health['outbox']['dead_count'] == 1

    with pytest.raises(CommandError):
        call_command('outbox_health', '--json', '--fail-on-unhealthy')


@pytest.mark.django_db
def test_outbox_health_api_is_admin_only():
    user_model = get_user_model()
    admin = user_model.objects.create_user(
        email='events-admin@example.com',
        password='pass12345',
        is_staff=True,
    )
    customer = user_model.objects.create_user(
        email='events-customer@example.com',
        password='pass12345',
    )

    client = APIClient()
    client.force_authenticate(user=customer)
    forbidden = client.get('/api/v1/events/outbox/health/')
    assert forbidden.status_code == 403

    client.force_authenticate(user=admin)
    allowed = client.get('/api/v1/events/outbox/health/')
    assert allowed.status_code == 200
    assert 'outbox' in allowed.json()
    assert 'status' in allowed.json()
