from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent
from apps.events.models import OutboxMessage
from apps.events.services import DomainEventService


@pytest.mark.django_db
def test_admin_can_retry_outbox_from_reconciliation_repair():
    admin = get_user_model().objects.create_superuser(email='repair-admin@example.com', password='pass12345')
    emitted = DomainEventService().emit(
        event_type='payment.succeeded',
        aggregate_type='payment',
        aggregate_id='repair-pay-001',
        payload={'amount': '100.00'},
        idempotency_key='repair:payment:repair-pay-001:succeeded',
    )
    outbox = OutboxMessage.objects.get(id=emitted['outbox_message_id'])
    DomainEventService().mark_outbox_dead(message_id=outbox.id, reason='test dead')

    client = APIClient()
    client.force_authenticate(user=admin)
    response = client.post(
        '/api/v1/ops/admin/reconciliation-repair/',
        {
            'action': 'retry_outbox',
            'entity_type': 'outbox_message',
            'entity_id': str(outbox.id),
            'reason': 'retry from reconciliation report',
        },
        format='json',
    )

    assert response.status_code == 202
    outbox.refresh_from_db()
    assert outbox.status == OutboxMessage.Status.PENDING
    assert response.json()['action'] == 'retry_outbox'
    assert AuditEvent.objects.filter(
        event_type='admin.reconciliation.retry_outbox',
        entity_type='outbox_message',
        entity_id=str(outbox.id),
    ).exists()


@pytest.mark.django_db
def test_reconciliation_repair_requires_admin():
    client = APIClient()
    response = client.post(
        '/api/v1/ops/admin/reconciliation-repair/',
        {
            'action': 'retry_outbox',
            'entity_type': 'outbox_message',
            'entity_id': '00000000-0000-0000-0000-000000000000',
            'reason': 'not allowed',
        },
        format='json',
    )
    assert response.status_code in {401, 403}
