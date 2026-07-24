from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.entitlements.models import Entitlement
from apps.entitlements.selectors import EntitlementAccessCenterSelector, has_active_entitlement
from apps.events.models import DomainEvent
from apps.orders.models import OrderStatus
from apps.orders.services import OrderService
from apps.payments.models import PaymentStatus
from apps.payments.commission_policy import CommissionPolicyService
from apps.payments.services import PaymentService, PaymentWebhookService
from apps.payouts.models import PayoutLedgerEntry, TrainerBalance
from apps.subscriptions.models import Subscription, SubscriptionPlan
from apps.trainers.models import TrainerProfile


class PaymentServiceTest(TestCase):
    def _create_trainer_profile(self, *, email: str = 'payment-trainer@example.com'):
        trainer_user = get_user_model().objects.create_user(email=email, password='pass12345', role='trainer')
        return TrainerProfile.objects.create(
            user=trainer_user,
            slug=email.split('@', 1)[0],
            display_name='Payment Trainer',
            status='active',
        )

    def test_split_amounts(self):
        platform_fee, trainer_net = PaymentService._split_amounts(Decimal('1000.00'))
        self.assertEqual(platform_fee, Decimal('200.00'))
        self.assertEqual(trainer_net, Decimal('800.00'))

    def test_commission_policy_uses_global_percent_setting(self):
        split = CommissionPolicyService.split(gross_amount=Decimal('1000.00'), currency='RUB')

        self.assertEqual(split.rate, Decimal('0.2000'))
        self.assertEqual(split.rate_percent, Decimal('20.00'))
        self.assertEqual(split.platform_commission, Decimal('200.00'))
        self.assertEqual(split.trainer_net, Decimal('800.00'))

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
        self.assertTrue(has_active_entitlement(user=user, target_type='video', target_id=str(item_id)))
        access = EntitlementAccessCenterSelector().check(user=user, target_type='video', target_id=str(item_id))
        self.assertTrue(access['allowed'])
        self.assertEqual(access['source'], 'direct')
        self.assertTrue(
            AuditEvent.objects.filter(
                event_type='entitlement.activated',
                context__source_order_id=str(order.id),
                context__target_type='video',
            ).exists()
        )

    def test_notification_side_effect_failure_is_audited_without_rolling_back_payment(self):
        user = get_user_model().objects.create_user(email='side-effect-failure@example.com', password='pass12345')
        order = OrderService.create_one_time_order(
            user=user,
            item_type='video',
            item_id=uuid4(),
            title='Side Effect Audit',
            amount=Decimal('499.00'),
        )
        payment = PaymentService.create_checkout_payment(order=order)

        with patch(
            'apps.notifications.domain.triggers.DomainNotificationTriggers.on_payment_succeeded',
            side_effect=RuntimeError('notification provider unavailable'),
        ):
            PaymentService.mark_succeeded(
                payment=payment,
                provider_payload={'external_payment_id': payment.external_payment_id},
            )

        payment.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(payment.status, PaymentStatus.SUCCEEDED)
        self.assertEqual(order.status, OrderStatus.COMPLETED)
        audit_event = AuditEvent.objects.get(
            event_type='side_effect.failed',
            entity_type='payment',
            entity_id=str(payment.id),
        )
        self.assertEqual(audit_event.actor, user)
        self.assertEqual(audit_event.context['side_effect'], 'notification.payment_succeeded')
        self.assertEqual(audit_event.context['error_class'], 'RuntimeError')

    def test_webhook_success_for_subscription_is_idempotent_and_accrues_balance_once(self):
        trainer = self._create_trainer_profile(email='subscription-trainer@example.com')
        trainer_id = trainer.id
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
        self.assertTrue(has_active_entitlement(user=user, target_type='library', target_id=''))
        self.assertTrue(has_active_entitlement(user=user, target_type='video', target_id=str(uuid4())))
        access = EntitlementAccessCenterSelector().check(user=user, target_type='video', target_id=str(uuid4()))
        self.assertTrue(access['allowed'])
        self.assertEqual(access['source'], 'library')
        self.assertEqual(balance.available_amount, Decimal('800.00'))
        self.assertEqual(
            PayoutLedgerEntry.objects.filter(
                trainer_id=trainer_id,
                payment_id=str(payment.id),
                entry_type=PayoutLedgerEntry.EntryType.ACCRUAL,
            ).count(),
            1,
        )
        self.assertEqual(
            AuditEvent.objects.filter(
                event_type='entitlement.activated',
                context__source_type='subscription',
            ).count(),
            1,
        )

    def test_subscription_payout_uses_plan_owner_not_order_metadata_trainer_id(self):
        real_trainer = self._create_trainer_profile(email='real-plan-owner@example.com')
        injected_trainer = self._create_trainer_profile(email='metadata-injected-owner@example.com')
        user = get_user_model().objects.create_user(email='metadata-buyer@example.com', password='pass12345')
        plan = SubscriptionPlan.objects.create(
            trainer_id=str(real_trainer.id),
            title='Metadata Injection Guard',
            price=Decimal('1000.00'),
            billing_period=SubscriptionPlan.BillingPeriod.MONTH,
        )
        order = OrderService.create_subscription_order(user=user, plan=plan)
        order.items.update(metadata={'trainer_id': str(injected_trainer.id)})
        payment = PaymentService.create_checkout_payment(order=order)

        PaymentService.mark_succeeded(payment=payment, provider_payload={'external_payment_id': payment.external_payment_id})

        real_balance = TrainerBalance.objects.get(trainer_id=real_trainer.id)
        self.assertEqual(real_balance.available_amount, Decimal('800.00'))
        self.assertFalse(TrainerBalance.objects.filter(trainer_id=injected_trainer.id).exists())

    def test_already_succeeded_payment_reconciles_missing_effects_once(self):
        trainer = self._create_trainer_profile(email='reconcile-trainer@example.com')
        trainer_id = trainer.id
        user = get_user_model().objects.create_user(email='succeeded-reconcile@example.com', password='pass12345')
        plan = SubscriptionPlan.objects.create(
            trainer_id=str(trainer_id),
            title='Recoverable Monthly',
            price=Decimal('1000.00'),
            billing_period=SubscriptionPlan.BillingPeriod.MONTH,
        )
        order = OrderService.create_subscription_order(user=user, plan=plan)
        payment = PaymentService.create_checkout_payment(order=order)
        confirmed_at = timezone.now()
        payment.status = PaymentStatus.SUCCEEDED
        payment.confirmed_at = confirmed_at
        payment.provider_payload = {'external_payment_id': payment.external_payment_id}
        payment.save(update_fields=['status', 'confirmed_at', 'provider_payload', 'updated_at'])

        PaymentService.mark_succeeded(payment=payment, provider_payload={'external_payment_id': payment.external_payment_id})
        PaymentService.mark_succeeded(payment=payment, provider_payload={'external_payment_id': payment.external_payment_id})

        payment.refresh_from_db()
        order.refresh_from_db()
        balance = TrainerBalance.objects.get(trainer_id=trainer_id)

        self.assertEqual(payment.status, PaymentStatus.SUCCEEDED)
        self.assertEqual(payment.confirmed_at, confirmed_at)
        self.assertEqual(order.status, OrderStatus.COMPLETED)
        self.assertEqual(Subscription.objects.filter(source_order=order).count(), 1)
        self.assertEqual(
            Entitlement.objects.filter(
                user=user,
                source=Entitlement.Source.SUBSCRIPTION,
                is_active=True,
            ).count(),
            1,
        )
        self.assertEqual(balance.available_amount, Decimal('800.00'))
        self.assertEqual(
            PayoutLedgerEntry.objects.filter(
                trainer_id=trainer_id,
                payment_id=str(payment.id),
                entry_type=PayoutLedgerEntry.EntryType.ACCRUAL,
            ).count(),
            1,
        )
        self.assertEqual(
            DomainEvent.objects.filter(
                event_type='payment.succeeded_reconciled',
                aggregate_id=str(payment.id),
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
