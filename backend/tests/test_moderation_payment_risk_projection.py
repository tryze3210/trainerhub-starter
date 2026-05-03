import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.events.models import InboxMessage
from apps.events.services import DomainEventService
from apps.moderation.models import ModerationCase, ModerationStatus, TrainerRiskFlag
from apps.moderation.projections import MODERATION_RISK_PROJECTION_CONSUMER, PAYMENT_RISK_QUEUE


@pytest.mark.django_db
def test_payment_dispute_event_creates_moderation_case_and_risk_flag():
    trainer = get_user_model().objects.create_user(email='risk-trainer@example.com', password='pass12345')
    service = DomainEventService()
    emitted = service.emit(
        event_type='payment.dispute_opened',
        aggregate_type='payment',
        aggregate_id='pay-risk-001',
        payload={
            'payment_id': 'pay-risk-001',
            'order_id': 'order-risk-001',
            'trainer_id': str(trainer.id),
            'amount': '1000.00',
            'currency': 'RUB',
            'provider': 'mock',
        },
        idempotency_key='payment:pay-risk-001:dispute_opened',
    )

    result = service.dispatch_pending_batch(batch_size=10)

    assert result['processed'] == 1
    case = ModerationCase.objects.get(queue=PAYMENT_RISK_QUEUE, target_id='pay-risk-001')
    assert case.status == ModerationStatus.ESCALATED
    assert case.trainer_id == trainer.id
    assert case.priority == 10
    assert case.events.filter(event_type='payment_dispute_opened').exists()

    flag = TrainerRiskFlag.objects.get(trainer=trainer, code='payment_dispute_opened')
    assert flag.is_active is True
    assert flag.source == 'payment_risk_projection'
    assert flag.details['payment_id'] == 'pay-risk-001'

    assert InboxMessage.objects.filter(
        consumer=MODERATION_RISK_PROJECTION_CONSUMER,
        message_key=emitted['event_id'],
        payload__projection_status='projected',
    ).exists()

    second_result = service.dispatch_pending_batch(batch_size=10)
    assert second_result['claimed'] == 0
    assert ModerationCase.objects.filter(queue=PAYMENT_RISK_QUEUE, target_id='pay-risk-001').count() == 1
    assert TrainerRiskFlag.objects.filter(trainer=trainer, code='payment_dispute_opened').count() == 1


@pytest.mark.django_db
def test_payment_chargeback_won_resolves_payment_risk_case_and_flag():
    trainer = get_user_model().objects.create_user(email='risk-won-trainer@example.com', password='pass12345')
    service = DomainEventService()
    service.emit(
        event_type='payment.dispute_opened',
        aggregate_type='payment',
        aggregate_id='pay-risk-won-001',
        payload={'payment_id': 'pay-risk-won-001', 'trainer_id': str(trainer.id)},
        idempotency_key='payment:pay-risk-won-001:dispute_opened',
    )
    service.dispatch_pending_batch(batch_size=10)

    service.emit(
        event_type='payment.chargeback_won',
        aggregate_type='payment',
        aggregate_id='pay-risk-won-001',
        payload={'payment_id': 'pay-risk-won-001', 'trainer_id': str(trainer.id)},
        idempotency_key='payment:pay-risk-won-001:chargeback_won',
    )
    service.dispatch_pending_batch(batch_size=10)

    case = ModerationCase.objects.get(queue=PAYMENT_RISK_QUEUE, target_id='pay-risk-won-001')
    assert case.status == ModerationStatus.RESOLVED
    assert case.resolved_at is not None
    assert case.events.filter(event_type='payment_chargeback_won').exists()
    assert not TrainerRiskFlag.objects.filter(trainer=trainer, code='payment_dispute_opened', is_active=True).exists()


@pytest.mark.django_db
def test_admin_can_read_payment_risk_dashboard_and_cases():
    admin = get_user_model().objects.create_superuser(email='risk-admin@example.com', password='pass12345')
    client = APIClient()
    client.force_authenticate(user=admin)

    dashboard_response = client.get('/api/v1/moderation/admin/risk-dashboard/')
    cases_response = client.get('/api/v1/moderation/admin/payment-risk-cases/')

    assert dashboard_response.status_code == 200
    assert dashboard_response.json()['consumer'] == MODERATION_RISK_PROJECTION_CONSUMER
    assert cases_response.status_code == 200
