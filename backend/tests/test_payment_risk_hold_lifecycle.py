from decimal import Decimal
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.orders.services import OrderService
from apps.payments.models import PaymentStatus
from apps.payments.services import PaymentService
from apps.payouts.models import BalanceEntry, TrainerBalance
from apps.subscriptions.models import SubscriptionPlan
from apps.trainers.models import TrainerProfile


def _trainer_profile(email: str):
    trainer_user = get_user_model().objects.create_user(email=email, password='pass12345', role='trainer')
    return TrainerProfile.objects.create(
        user=trainer_user,
        slug=email.split('@', 1)[0],
        display_name='Risk Hold Trainer',
        status='active',
    )


@pytest.mark.django_db
def test_dispute_holds_trainer_revenue_and_chargeback_won_releases_once():
    trainer_id = _trainer_profile('risk-hold-won-trainer@example.com').id
    user = get_user_model().objects.create_user(email='risk-hold-won@example.com', password='pass12345')
    plan = SubscriptionPlan.objects.create(
        trainer_id=str(trainer_id),
        title='Risk Hold Monthly',
        price=Decimal('1000.00'),
        billing_period=SubscriptionPlan.BillingPeriod.MONTH,
    )
    order = OrderService.create_subscription_order(user=user, plan=plan)
    payment = PaymentService.create_checkout_payment(order=order)

    PaymentService.mark_succeeded(payment=payment, provider_payload={'external_payment_id': payment.external_payment_id})
    wallet = TrainerBalance.objects.get(trainer_id=trainer_id)
    assert wallet.available_amount == Decimal('800.00')
    assert wallet.locked_amount == Decimal('0.00')

    PaymentService.mark_disputed(payment=payment, provider_payload={'dispute_id': 'dp-risk-001'})
    PaymentService.mark_disputed(payment=payment, provider_payload={'dispute_id': 'dp-risk-001-duplicate'})

    payment.refresh_from_db()
    wallet.refresh_from_db()
    assert payment.status == PaymentStatus.DISPUTED
    assert wallet.available_amount == Decimal('0.00')
    assert wallet.locked_amount == Decimal('800.00')
    assert BalanceEntry.objects.filter(
        wallet=wallet,
        source_type='payment_dispute_hold',
        source_id=payment.id,
        entry_type=BalanceEntry.EntryType.RISK_HOLD,
    ).count() == 1

    PaymentService.mark_chargeback_won(payment=payment, provider_payload={'resolution': 'won'})
    PaymentService.mark_chargeback_won(payment=payment, provider_payload={'resolution': 'won-duplicate'})

    payment.refresh_from_db()
    wallet.refresh_from_db()
    assert payment.status == PaymentStatus.SUCCEEDED
    assert wallet.available_amount == Decimal('800.00')
    assert wallet.locked_amount == Decimal('0.00')
    assert BalanceEntry.objects.filter(
        wallet=wallet,
        source_type='payment_dispute_release',
        source_id=payment.id,
        entry_type=BalanceEntry.EntryType.RISK_HOLD_RELEASE,
    ).count() == 1


@pytest.mark.django_db
def test_chargeback_lost_consumes_risk_hold_without_double_debiting_available_balance():
    trainer_id = _trainer_profile('risk-hold-lost-trainer@example.com').id
    user = get_user_model().objects.create_user(email='risk-hold-lost@example.com', password='pass12345')
    plan = SubscriptionPlan.objects.create(
        trainer_id=str(trainer_id),
        title='Risk Hold Chargeback',
        price=Decimal('500.00'),
        billing_period=SubscriptionPlan.BillingPeriod.MONTH,
    )
    order = OrderService.create_subscription_order(user=user, plan=plan)
    payment = PaymentService.create_checkout_payment(order=order)

    PaymentService.mark_succeeded(payment=payment, provider_payload={'external_payment_id': payment.external_payment_id})
    PaymentService.mark_disputed(payment=payment, provider_payload={'dispute_id': 'dp-risk-lost-001'})

    wallet = TrainerBalance.objects.get(trainer_id=trainer_id)
    assert wallet.available_amount == Decimal('0.00')
    assert wallet.locked_amount == Decimal('400.00')

    PaymentService.mark_chargeback_lost(payment=payment, provider_payload={'chargeback_id': 'cb-risk-lost-001'})
    PaymentService.mark_chargeback_lost(payment=payment, provider_payload={'chargeback_id': 'cb-risk-lost-001-duplicate'})

    payment.refresh_from_db()
    wallet.refresh_from_db()
    assert payment.status == PaymentStatus.CHARGED_BACK
    assert wallet.available_amount == Decimal('0.00')
    assert wallet.locked_amount == Decimal('0.00')
    assert BalanceEntry.objects.filter(
        wallet=wallet,
        source_type='payment_chargeback',
        source_id=payment.id,
        entry_type=BalanceEntry.EntryType.REVERSAL,
    ).count() == 1
    assert BalanceEntry.objects.filter(
        wallet=wallet,
        source_type='payment_chargeback_hold_consumed',
        source_id=payment.id,
        entry_type=BalanceEntry.EntryType.RISK_HOLD_CONSUMED,
    ).count() == 1


@pytest.mark.django_db
def test_admin_can_read_payout_risk_hold_summary():
    trainer_id = _trainer_profile('risk-hold-admin-trainer@example.com').id
    buyer = get_user_model().objects.create_user(email='risk-hold-admin-buyer@example.com', password='pass12345')
    admin = get_user_model().objects.create_superuser(email='risk-hold-admin@example.com', password='pass12345')
    plan = SubscriptionPlan.objects.create(
        trainer_id=str(trainer_id),
        title='Risk Hold Admin',
        price=Decimal('1000.00'),
        billing_period=SubscriptionPlan.BillingPeriod.MONTH,
    )
    order = OrderService.create_subscription_order(user=buyer, plan=plan)
    payment = PaymentService.create_checkout_payment(order=order)
    PaymentService.mark_succeeded(payment=payment, provider_payload={'external_payment_id': payment.external_payment_id})
    PaymentService.mark_disputed(payment=payment, provider_payload={'dispute_id': 'dp-risk-admin-001'})

    client = APIClient()
    client.force_authenticate(user=admin)
    response = client.get('/api/v1/payouts/admin/risk-holds/summary/')

    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'attention'
    assert payload['active_hold_count'] == 1
    assert payload['active_hold_amount'] == '800.00'
