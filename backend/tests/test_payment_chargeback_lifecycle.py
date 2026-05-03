from decimal import Decimal
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model

from apps.entitlements.models import Entitlement
from apps.orders.models import OrderStatus
from apps.orders.services import OrderService
from apps.payments.models import PaymentStatus, PaymentWebhookEvent
from apps.payments.services import PaymentService, PaymentWebhookService
from apps.payouts.models import BalanceEntry, TrainerBalance
from apps.subscriptions.models import Subscription, SubscriptionPlan, SubscriptionStatus


@pytest.mark.django_db
def test_chargeback_lost_reverses_access_subscription_and_payout_once():
    trainer_id = uuid4()
    user = get_user_model().objects.create_user(email='chargeback-buyer@example.com', password='pass12345')
    plan = SubscriptionPlan.objects.create(
        trainer_id=str(trainer_id),
        title='Chargeback Monthly',
        price=Decimal('1000.00'),
        billing_period=SubscriptionPlan.BillingPeriod.MONTH,
    )
    order = OrderService.create_subscription_order(user=user, plan=plan)
    payment = PaymentService.create_checkout_payment(order=order)

    PaymentService.mark_succeeded(payment=payment, provider_payload={'external_payment_id': payment.external_payment_id})
    balance = TrainerBalance.objects.get(trainer_id=trainer_id)
    assert balance.available_amount == Decimal('900.00')
    assert Entitlement.objects.filter(user=user, is_active=True).exists()

    PaymentService.mark_disputed(payment=payment, provider_payload={'dispute_id': 'dp_001'})
    payment.refresh_from_db()
    order.refresh_from_db()
    assert payment.status == PaymentStatus.DISPUTED
    assert order.status == OrderStatus.DISPUTED

    PaymentService.mark_chargeback_lost(payment=payment, provider_payload={'chargeback_id': 'cb_001'})
    PaymentService.mark_chargeback_lost(payment=payment, provider_payload={'chargeback_id': 'cb_001_duplicate'})

    payment.refresh_from_db()
    order.refresh_from_db()
    balance.refresh_from_db()

    assert payment.status == PaymentStatus.CHARGED_BACK
    assert order.status == OrderStatus.CHARGED_BACK
    assert balance.available_amount == Decimal('0.00')
    assert not Entitlement.objects.filter(user=user, is_active=True).exists()
    assert Subscription.objects.filter(source_order=order, status=SubscriptionStatus.CANCELLED).exists()
    assert BalanceEntry.objects.filter(
        wallet=balance,
        source_type='payment_chargeback',
        source_id=payment.id,
        entry_type='reversal',
    ).count() == 1


@pytest.mark.django_db
def test_chargeback_webhook_is_idempotent():
    trainer_id = uuid4()
    user = get_user_model().objects.create_user(email='chargeback-webhook@example.com', password='pass12345')
    plan = SubscriptionPlan.objects.create(
        trainer_id=str(trainer_id),
        title='Webhook Chargeback Monthly',
        price=Decimal('500.00'),
        billing_period=SubscriptionPlan.BillingPeriod.MONTH,
    )
    order = OrderService.create_subscription_order(user=user, plan=plan)
    payment = PaymentService.create_checkout_payment(order=order)
    PaymentService.mark_succeeded(payment=payment, provider_payload={'external_payment_id': payment.external_payment_id})

    event = PaymentWebhookService.handle(
        provider='mock',
        event_type='payment.dispute.opened',
        external_event_id='evt-dispute-001',
        payload={'external_payment_id': payment.external_payment_id, 'dispute_id': 'dp-webhook-001'},
    )
    assert event.status == PaymentWebhookEvent.Status.PROCESSED
    payment.refresh_from_db()
    assert payment.status == PaymentStatus.DISPUTED

    chargeback = PaymentWebhookService.handle(
        provider='mock',
        event_type='payment.chargeback.lost',
        external_event_id='evt-chargeback-001',
        payload={'external_payment_id': payment.external_payment_id, 'chargeback_id': 'cb-webhook-001'},
    )
    duplicate = PaymentWebhookService.handle(
        provider='mock',
        event_type='payment.chargeback.lost',
        external_event_id='evt-chargeback-001',
        payload={'external_payment_id': payment.external_payment_id, 'chargeback_id': 'cb-webhook-001'},
    )

    payment.refresh_from_db()
    balance = TrainerBalance.objects.get(trainer_id=trainer_id)

    assert chargeback.id == duplicate.id
    assert chargeback.status == PaymentWebhookEvent.Status.PROCESSED
    assert payment.status == PaymentStatus.CHARGED_BACK
    assert balance.available_amount == Decimal('0.00')
    assert BalanceEntry.objects.filter(
        wallet=balance,
        source_type='payment_chargeback',
        source_id=payment.id,
        entry_type='reversal',
    ).count() == 1
