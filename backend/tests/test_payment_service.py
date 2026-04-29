from decimal import Decimal
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.entitlements.models import Entitlement
from apps.orders.models import OrderStatus
from apps.orders.services import OrderService
from apps.payments.models import PaymentStatus
from apps.payments.services import PaymentService, PaymentWebhookService
from apps.payouts.models import PayoutLedgerEntry, TrainerBalance
from apps.subscriptions.models import Subscription, SubscriptionPlan


class PaymentServiceTest(TestCase):
    def test_split_amounts(self):
        platform_fee, trainer_net = PaymentService._split_amounts(Decimal('1000.00'))
        self.assertEqual(platform_fee, Decimal('100.00'))
        self.assertEqual(trainer_net, Decimal('900.00'))

    def test_create_checkout_payment_reuses_existing_pending_payment(self):
        user = get_user_model().objects.create_user(email='reuse@example.com', password='pass12345')
        order = OrderService.create_one_time_order(
            user=user,
            item_type='video',
            item_id=uuid4(),
            title='Mobility Flow',
            amount=Decimal('399.00'),
        )

        first = PaymentService.create_checkout_payment(order=order)
        second = PaymentService.create_checkout_payment(order=order)

        self.assertEqual(first.id, second.id)

    def test_mark_succeeded_completes_one_time_order_and_grants_entitlement(self):
        user = get_user_model().objects.create_user(email='buyer@example.com', password='pass12345')
        item_id = uuid4()
        order = OrderService.create_one_time_order(
            user=user,
            item_type='video',
            item_id=item_id,
            title='Core Blast',
            amount=Decimal('499.00'),
        )
        payment = PaymentService.create_checkout_payment(order=order)

        PaymentService.mark_succeeded(payment=payment, provider_payload={'external_payment_id': payment.external_payment_id})

        payment.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(payment.status, PaymentStatus.SUCCEEDED)
        self.assertEqual(order.status, OrderStatus.COMPLETED)
        self.assertTrue(
            Entitlement.objects.filter(
                user=user,
                kind=Entitlement.Kind.VIDEO,
                object_id=str(item_id),
                source=Entitlement.Source.ORDER,
                source_reference=str(order.id),
                is_active=True,
            ).exists()
        )

    def test_webhook_success_for_subscription_is_idempotent_and_accrues_balance_once(self):
        trainer_id = uuid4()
        user = get_user_model().objects.create_user(email='subscriber@example.com', password='pass12345')
        plan = SubscriptionPlan.objects.create(
            trainer_id=str(trainer_id),
            title='Pro Monthly',
            price=Decimal('1000.00'),
            billing_period=SubscriptionPlan.BillingPeriod.MONTH,
        )
        order = OrderService.create_subscription_order(user=user, plan=plan)
        payment = PaymentService.create_checkout_payment(order=order)

        event = PaymentWebhookService.handle(
            provider='mock',
            event_type='payment.succeeded',
            external_event_id='evt-1',
            payload={'external_payment_id': payment.external_payment_id},
        )
        duplicate_event = PaymentWebhookService.handle(
            provider='mock',
            event_type='payment.succeeded',
            external_event_id='evt-2',
            payload={'external_payment_id': payment.external_payment_id},
        )

        payment.refresh_from_db()
        order.refresh_from_db()
        balance = TrainerBalance.objects.get(trainer_id=trainer_id)

        self.assertIsNotNone(event.processed_at)
        self.assertIsNotNone(duplicate_event.processed_at)
        self.assertEqual(payment.status, PaymentStatus.SUCCEEDED)
        self.assertEqual(order.status, OrderStatus.COMPLETED)
        self.assertEqual(Subscription.objects.filter(source_order=order).count(), 1)
        self.assertTrue(
            Entitlement.objects.filter(
                user=user,
                source=Entitlement.Source.SUBSCRIPTION,
                is_active=True,
            ).exists()
        )
        self.assertEqual(balance.available_amount, Decimal('900.00'))
        self.assertEqual(
            PayoutLedgerEntry.objects.filter(
                trainer_id=trainer_id,
                payment_id=str(payment.id),
                entry_type=PayoutLedgerEntry.EntryType.ACCRUAL,
            ).count(),
            1,
        )

    def test_mark_failed_marks_order_failed(self):
        user = get_user_model().objects.create_user(email='failed@example.com', password='pass12345')
        order = OrderService.create_one_time_order(
            user=user,
            item_type='video',
            item_id=uuid4(),
            title='Stretch',
            amount=Decimal('199.00'),
        )
        payment = PaymentService.create_checkout_payment(order=order)

        PaymentWebhookService.handle(
            provider='mock',
            event_type='payment.failed',
            external_event_id='evt-failed-1',
            payload={'external_payment_id': payment.external_payment_id},
        )

        payment.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(payment.status, PaymentStatus.FAILED)
        self.assertEqual(order.status, OrderStatus.FAILED)
