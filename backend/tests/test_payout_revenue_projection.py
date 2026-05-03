from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.events.models import InboxMessage, OutboxMessage
from apps.events.services import DomainEventService
from apps.payouts.models import BalanceEntry, TrainerWallet
from apps.payouts.projections import PAYOUT_REVENUE_PROJECTION_CONSUMER
from apps.trainers.models import TrainerProfile


@pytest.mark.django_db
def test_payment_success_event_projects_to_payout_ledger_once():
    trainer_user = get_user_model().objects.create_user(
        email='payout-projection-trainer@example.com',
        password='pass12345',
        role='trainer',
    )
    TrainerProfile.objects.create(
        user=trainer_user,
        slug='payout-projection-trainer',
        display_name='Payout Projection Trainer',
        status='active',
    )
    payment_id = uuid4()

    emitted = DomainEventService().emit(
        event_type='payment.succeeded',
        aggregate_type='payment',
        aggregate_id=str(payment_id),
        payload={
            'payment_id': str(payment_id),
            'trainer_id': str(trainer_user.id),
            'amount': '100.00',
            'trainer_net': '90.00',
            'currency': 'RUB',
        },
        idempotency_key=f'payment:{payment_id}:succeeded',
    )

    result = DomainEventService().dispatch_pending_batch(batch_size=10)

    assert result['claimed'] == 1
    assert result['processed'] == 1
    wallet = TrainerWallet.objects.get(trainer__user=trainer_user)
    assert wallet.available_amount == Decimal('90.00')
    assert BalanceEntry.objects.filter(
        wallet=wallet,
        source_type='payment',
        source_id=payment_id,
        entry_type=BalanceEntry.EntryType.ACCRUAL,
    ).count() == 1

    inbox = InboxMessage.objects.get(
        consumer=PAYOUT_REVENUE_PROJECTION_CONSUMER,
        message_key=emitted['event_id'],
    )
    assert inbox.status == InboxMessage.Status.PROCESSED
    assert inbox.payload['projection_status'] == 'projected'

    OutboxMessage.objects.filter(pk=emitted['outbox_message_id']).update(status=OutboxMessage.Status.PENDING)
    replay = DomainEventService().dispatch_pending_batch(batch_size=10)

    assert replay['claimed'] == 1
    assert replay['processed'] == 1
    wallet.refresh_from_db()
    assert wallet.available_amount == Decimal('90.00')
    assert BalanceEntry.objects.filter(
        wallet=wallet,
        source_type='payment',
        source_id=payment_id,
        entry_type=BalanceEntry.EntryType.ACCRUAL,
    ).count() == 1
    inbox.refresh_from_db()
    assert inbox.payload['projection_status'] == 'already_projected'


@pytest.mark.django_db
def test_payout_projection_records_skip_when_trainer_missing():
    payment_id = uuid4()
    emitted = DomainEventService().emit(
        event_type='payment.succeeded',
        aggregate_type='payment',
        aggregate_id=str(payment_id),
        payload={
            'payment_id': str(payment_id),
            'amount': '100.00',
            'currency': 'RUB',
        },
        idempotency_key=f'payment:{payment_id}:missing-trainer',
    )

    result = DomainEventService().dispatch_pending_batch(batch_size=10)

    assert result['processed'] == 1
    inbox = InboxMessage.objects.get(
        consumer=PAYOUT_REVENUE_PROJECTION_CONSUMER,
        message_key=emitted['event_id'],
    )
    assert inbox.payload['projection_status'] == 'skipped'
    assert 'trainer id' in inbox.payload['reason'].lower()
    assert TrainerWallet.objects.count() == 0
    assert BalanceEntry.objects.count() == 0


@pytest.mark.django_db
def test_admin_can_read_payout_projection_health():
    admin = get_user_model().objects.create_superuser(
        email='payout-projection-admin@example.com',
        password='pass12345',
    )
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get('/api/v1/payouts/admin/projection-health/')

    assert response.status_code == 200
    payload = response.json()
    assert payload['consumer'] == PAYOUT_REVENUE_PROJECTION_CONSUMER
    assert 'ledger_accrual_amount' in payload
