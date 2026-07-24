from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEvent
from apps.entitlements.models import Entitlement
from apps.events.models import DomainEvent
from apps.orders.models import OrderStatus
from apps.orders.services import OrderService
from apps.payments.models import PaymentStatus, PaymentWebhookEvent
from apps.payments.services import PaymentService, PaymentWebhookService
from apps.payouts.models import BalanceEntry, TrainerBalance
from apps.subscriptions.models import Subscription, SubscriptionPlan, SubscriptionStatus
from apps.trainers.models import TrainerProfile


def _trainer_profile(email: str) -> TrainerProfile:
    trainer_user = get_user_model().objects.create_user(email=email, password='pass12345', role='trainer')
    return TrainerProfile.objects.create(
        user=trainer_user,
        slug=email.split('@', 1)[0],
        display_name='Payment Trainer',
        status='active',
    )


@pytest.mark.django_db
def test_refund_reverses_subscription_entitlement_and_payout_once():
    trainer_id = _trainer_profile('refund-trainer@example.com').id
    user = get_user_model().objects.create_user(email='refund-buyer@example.com', password='pass12345')
    plan = SubscriptionPlan.objects.create(
        trainer_id=str(trainer_id),
        title='Refundable Monthly',
        price=Decimal('1000.00'),
        billing_period=SubscriptionPlan.BillingPeriod.MONTH,
    )
    order = OrderService.create_subscription_order(user=user, plan=plan)
    payment = PaymentService.create_checkout_payment(order=order)

    PaymentService.mark_succeeded(payment=payment, provider_payload={'external_payment_id': payment.external_payment_id})

    balance = TrainerBalance.objects.get(trainer_id=trainer_id)
    assert balance.available_amount == Decimal('800.00')
    assert Entitlement.objects.filter(user=user, is_active=True).exists()
    assert Subscription.objects.filter(source_order=order, status=SubscriptionStatus.ACTIVE).exists()

    PaymentService.mark_refunded(payment=payment, provider_payload={'refund_id': 'rfnd_001'})
    PaymentService.mark_refunded(payment=payment, provider_payload={'refund_id': 'rfnd_001_duplicate'})

    payment.refresh_from_db()
    order.refresh_from_db()
    balance.refresh_from_db()

    assert payment.status == PaymentStatus.REFUNDED
    assert order.status == OrderStatus.REFUNDED
    assert balance.available_amount == Decimal('0.00')
    assert not Entitlement.objects.filter(user=user, is_active=True).exists()
    assert Subscription.objects.filter(source_order=order, status=SubscriptionStatus.CANCELLED).exists()
    assert AuditEvent.objects.filter(event_type='entitlement.revoked', context__reason='payment_refunded').count() == 1
    assert DomainEvent.objects.filter(event_type='entitlement.revoked').count() == 1

    assert BalanceEntry.objects.filter(
        wallet=balance,
        source_type='payment',
        source_id=payment.id,
        entry_type=BalanceEntry.EntryType.ACCRUAL,
    ).count() == 1
    assert BalanceEntry.objects.filter(
        wallet=balance,
        source_type='payment_refund',
        source_id=payment.id,
        entry_type='reversal',
    ).count() == 1


@pytest.mark.django_db
def test_refund_webhook_is_idempotent():
    trainer_id = _trainer_profile('refund-webhook-trainer@example.com').id
    user = get_user_model().objects.create_user(email='refund-webhook@example.com', password='pass12345')
    plan = SubscriptionPlan.objects.create(
        trainer_id=str(trainer_id),
        title='Webhook Refund Monthly',
        price=Decimal('500.00'),
        billing_period=SubscriptionPlan.BillingPeriod.MONTH,
    )
    order = OrderService.create_subscription_order(user=user, plan=plan)
    payment = PaymentService.create_checkout_payment(order=order)
    PaymentService.mark_succeeded(payment=payment, provider_payload={'external_payment_id': payment.external_payment_id})

    event = PaymentWebhookService.handle(
        provider='mock',
        event_type='payment.refunded',
        external_event_id='evt-refund-001',
        payload={'external_payment_id': payment.external_payment_id, 'refund_id': 'rfnd-webhook-001'},
    )
    duplicate = PaymentWebhookService.handle(
        provider='mock',
        event_type='payment.refunded',
        external_event_id='evt-refund-001',
        payload={'external_payment_id': payment.external_payment_id, 'refund_id': 'rfnd-webhook-001'},
    )

    payment.refresh_from_db()
    balance = TrainerBalance.objects.get(trainer_id=trainer_id)

    assert event.id == duplicate.id
    assert event.status == PaymentWebhookEvent.Status.PROCESSED
    assert payment.status == PaymentStatus.REFUNDED
    assert balance.available_amount == Decimal('0.00')
    assert BalanceEntry.objects.filter(
        wallet=balance,
        source_type='payment_refund',
        source_id=payment.id,
        entry_type='reversal',
    ).count() == 1


@pytest.mark.django_db
def test_partial_refund_keeps_access_and_full_refund_revokes_remaining_once():
    trainer_id = _trainer_profile('partial-refund-trainer@example.com').id
    user = get_user_model().objects.create_user(email='partial-refund@example.com', password='pass12345')
    plan = SubscriptionPlan.objects.create(
        trainer_id=str(trainer_id),
        title='Partial Refund Monthly',
        price=Decimal('1000.00'),
        billing_period=SubscriptionPlan.BillingPeriod.MONTH,
    )
    order = OrderService.create_subscription_order(user=user, plan=plan)
    payment = PaymentService.create_checkout_payment(order=order)
    PaymentService.mark_succeeded(payment=payment, provider_payload={'external_payment_id': payment.external_payment_id})

    PaymentService.mark_refunded(
        payment=payment,
        amount=Decimal('250.00'),
        refund_id='rfnd_partial_001',
        reason='goodwill_credit',
        provider_payload={'refund_id': 'rfnd_partial_001'},
    )
    PaymentService.mark_refunded(
        payment=payment,
        amount=Decimal('250.00'),
        refund_id='rfnd_partial_001',
        reason='duplicate_retry',
        provider_payload={'refund_id': 'rfnd_partial_001'},
    )

    payment.refresh_from_db()
    order.refresh_from_db()
    balance = TrainerBalance.objects.get(trainer_id=trainer_id)

    assert payment.status == PaymentStatus.SUCCEEDED
    assert order.status == OrderStatus.COMPLETED
    assert payment.provider_payload['refund_status'] == 'partially_refunded'
    assert payment.provider_payload['refunded_amount'] == '250.00'
    assert balance.available_amount == Decimal('600.00')
    assert Entitlement.objects.filter(user=user, is_active=True).exists()
    assert Subscription.objects.filter(source_order=order, status=SubscriptionStatus.ACTIVE).exists()
    assert BalanceEntry.objects.filter(
        wallet=balance,
        source_type='payment_refund_partial',
        entry_type='reversal',
    ).count() == 1
    assert AuditEvent.objects.filter(
        event_type='payment.refund_partial',
        entity_id=str(payment.id),
        context__refund_id='rfnd_partial_001',
    ).count() == 1

    PaymentService.mark_refunded(
        payment=payment,
        refund_id='rfnd_full_remaining_001',
        provider_payload={'refund_id': 'rfnd_full_remaining_001'},
    )
    PaymentService.mark_refunded(
        payment=payment,
        refund_id='rfnd_full_remaining_001',
        provider_payload={'refund_id': 'rfnd_full_remaining_001'},
    )

    payment.refresh_from_db()
    order.refresh_from_db()
    balance.refresh_from_db()

    assert payment.status == PaymentStatus.REFUNDED
    assert order.status == OrderStatus.REFUNDED
    assert payment.provider_payload['refund_status'] == 'refunded'
    assert payment.provider_payload['refunded_amount'] == '1000.00'
    assert len(payment.provider_payload['refund_operations']) == 2
    assert balance.available_amount == Decimal('0.00')
    assert not Entitlement.objects.filter(user=user, is_active=True).exists()
    assert Subscription.objects.filter(source_order=order, status=SubscriptionStatus.CANCELLED).exists()
    assert AuditEvent.objects.filter(event_type='entitlement.revoked', context__reason='payment_refunded').count() == 1
    assert DomainEvent.objects.filter(event_type='entitlement.revoked').count() == 1
    assert BalanceEntry.objects.filter(
        wallet=balance,
        source_type='payment_refund',
        source_id=payment.id,
        entry_type='reversal',
    ).count() == 1
    assert AuditEvent.objects.filter(
        event_type='payment.refunded',
        entity_id=str(payment.id),
        context__refund_id='rfnd_full_remaining_001',
    ).count() == 1
