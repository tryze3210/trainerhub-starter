from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent
from apps.audit.services import AuditService
from apps.events.models import OutboxMessage
from apps.events.services import DomainEventService


@pytest.mark.django_db
def test_audit_service_records_json_safe_admin_action(rf):
    admin = get_user_model().objects.create_superuser(email='audit-admin@example.com', password='pass12345')
    request = rf.post('/api/v1/events/outbox/dispatch/', HTTP_X_CORRELATION_ID='corr-audit-001')
    request.user = admin

    event = AuditService.log_admin_action(
        request=request,
        action='outbox.dispatch',
        target_type='outbox_batch',
        target_id='dispatch',
        context={'batch_size': 25},
    )

    assert event.actor == admin
    assert event.event_type == 'admin.outbox.dispatch'
    assert event.entity_type == 'outbox_batch'
    assert event.entity_id == 'dispatch'
    assert event.context['request']['correlation_id'] == 'corr-audit-001'
    assert event.context['context']['batch_size'] == 25


@pytest.mark.django_db
def test_operator_outbox_retry_writes_audit_log():
    admin = get_user_model().objects.create_superuser(email='outbox-audit@example.com', password='pass12345')
    emitted = DomainEventService().emit(
        event_type='payment.succeeded',
        aggregate_type='payment',
        aggregate_id='pay-audit-001',
        payload={'amount': '100.00'},
        idempotency_key='payment:pay-audit-001:audit',
    )
    message = OutboxMessage.objects.get(id=emitted['outbox_message_id'])
    message.status = OutboxMessage.Status.FAILED
    message.attempts = 1
    message.last_error = 'temporary projection failure'
    message.save(update_fields=['status', 'attempts', 'last_error', 'updated_at'])

    client = APIClient()
    client.force_authenticate(user=admin)
    response = client.post(
        f'/api/v1/events/outbox/{message.id}/retry/',
        {'reset_attempts': True},
        format='json',
        HTTP_X_CORRELATION_ID='corr-outbox-retry-001',
    )

    assert response.status_code == 202
    audit = AuditEvent.objects.get(event_type='admin.outbox.retry', entity_id=str(message.id))
    assert audit.actor == admin
    assert audit.entity_type == 'outbox_message'
    assert audit.context['action'] == 'outbox.retry'
    assert audit.context['request']['correlation_id'] == 'corr-outbox-retry-001'
    assert audit.context['context']['input']['reset_attempts'] is True
    assert audit.context['context']['result']['status'] == OutboxMessage.Status.PENDING


@pytest.mark.django_db
def test_operator_outbox_dead_writes_audit_log():
    admin = get_user_model().objects.create_superuser(email='outbox-dead-audit@example.com', password='pass12345')
    emitted = DomainEventService().emit(
        event_type='notification.failed',
        aggregate_type='notification',
        aggregate_id='notify-audit-001',
        payload={'channel': 'email'},
        idempotency_key='notification:notify-audit-001:audit',
    )
    message = OutboxMessage.objects.get(id=emitted['outbox_message_id'])

    client = APIClient()
    client.force_authenticate(user=admin)
    response = client.post(
        f'/api/v1/events/outbox/{message.id}/dead/',
        {'reason': 'payload cannot be projected'},
        format='json',
    )

    assert response.status_code == 202
    audit = AuditEvent.objects.get(event_type='admin.outbox.mark_dead', entity_id=str(message.id))
    assert audit.actor == admin
    assert audit.context['reason'] == 'payload cannot be projected'
    assert audit.context['context']['result']['status'] == OutboxMessage.Status.DEAD
