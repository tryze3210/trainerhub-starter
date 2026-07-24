from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.accounts.models import AccountRoleAssignment
from apps.entitlements.models import Entitlement, EntitlementSourceType, EntitlementStatus, EntitlementTargetType
from apps.notifications.models import NotificationChannel, NotificationDelivery, NotificationStatus, NotificationType
from apps.orders.models import Order, OrderItem, OrderStatus, OrderType, PurchasedItemType
from apps.payments.models import Payment, PaymentProvider, PaymentStatus
from apps.payouts.models import PayoutRequest, TrainerWallet
from apps.subscriptions.models import SubscriptionPlan
from apps.tenancy.models import Tenant, TenantMembership
from apps.tenancy.scoping import (
    scope_entitlements_for_user,
    scope_notification_deliveries_for_user,
    scope_orders_for_user,
    scope_payments_for_user,
    scope_payouts_for_user,
    trainer_scope_user_ids,
)
from apps.trainers.models import TrainerProfile


def _user(email, role="customer"):
    return get_user_model().objects.create_user(email=email, password="pass12345", role=role)


def _trainer(email, slug):
    user = _user(email, role="trainer")
    profile = TrainerProfile.objects.create(user=user, slug=slug, display_name=slug.title())
    return user, profile


def _assign_role(user, role):
    return AccountRoleAssignment.objects.create(user=user, role=role, is_active=True)


def _tenant_for_trainer(trainer):
    tenant = Tenant.objects.create(
        code=f"tenant-{trainer.id}",
        kind="trainer_space",
        name=f"Tenant {trainer.email}",
        owner_account_id=str(trainer.id),
        status="active",
    )
    TenantMembership.objects.create(
        tenant_id=str(tenant.id),
        account_id=str(trainer.id),
        role="owner",
        status="active",
        permissions=["tenant.manage"],
    )
    return tenant


def _commerce_row(*, student, trainer, amount="100.00"):
    plan = SubscriptionPlan.objects.create(
        trainer_id=str(trainer.id),
        title=f"Plan {trainer.email}",
        price=Decimal(amount),
    )
    order = Order.objects.create(
        user=student,
        order_type=OrderType.SUBSCRIPTION,
        status=OrderStatus.PAID,
        currency="RUB",
        total_amount=Decimal(amount),
    )
    OrderItem.objects.create(
        order=order,
        item_type=PurchasedItemType.SUBSCRIPTION_PLAN,
        item_id=str(plan.id),
        title_snapshot=plan.title,
        quantity=1,
        unit_price=Decimal(amount),
        total_price=Decimal(amount),
    )
    payment = Payment.objects.create(
        order=order,
        provider=PaymentProvider.MOCK,
        status=PaymentStatus.SUCCEEDED,
        amount=Decimal(amount),
        currency="RUB",
    )
    entitlement = Entitlement.objects.create(
        user=student,
        source_type=EntitlementSourceType.ORDER,
        source_order=order,
        target_type=EntitlementTargetType.PROGRAM,
        target_id=f"program-{trainer.id}",
        status=EntitlementStatus.ACTIVE,
        metadata={"trainer_id": str(trainer.id)},
    )
    return order, payment, entitlement


@pytest.mark.django_db
def test_v108_finance_operator_is_scoped_to_accessible_tenant():
    trainer_a, profile_a = _trainer("v108-trainer-a@example.com", "trainer-a")
    trainer_b, profile_b = _trainer("v108-trainer-b@example.com", "trainer-b")
    tenant_a = _tenant_for_trainer(trainer_a)
    _tenant_for_trainer(trainer_b)
    finance = _user("v108-finance@example.com")
    _assign_role(finance, AccountRoleAssignment.ROLE_FINANCE)
    TenantMembership.objects.create(
        tenant_id=str(tenant_a.id),
        account_id=str(finance.id),
        role="finance",
        status="active",
        permissions=["payments.view", "payouts.view"],
    )
    student = _user("v108-student@example.com")

    order_a, payment_a, entitlement_a = _commerce_row(student=student, trainer=trainer_a)
    order_b, payment_b, entitlement_b = _commerce_row(student=student, trainer=trainer_b)
    order_b.items.update(metadata={"trainer_id": str(trainer_a.id)})
    payment_b.provider_payload = {"trainer_id": str(trainer_a.id)}
    payment_b.save(update_fields=["provider_payload", "updated_at"])
    entitlement_b.metadata = {"trainer_id": str(trainer_a.id)}
    entitlement_b.save(update_fields=["metadata", "updated_at"])
    wallet_a = TrainerWallet.objects.create(trainer=profile_a, available_amount=Decimal("50.00"))
    wallet_b = TrainerWallet.objects.create(trainer=profile_b, available_amount=Decimal("50.00"))
    payout_a = PayoutRequest.objects.create(trainer=profile_a, wallet=wallet_a, amount=Decimal("10.00"), currency="RUB")
    payout_b = PayoutRequest.objects.create(trainer=profile_b, wallet=wallet_b, amount=Decimal("10.00"), currency="RUB")

    assert trainer_scope_user_ids(finance) == [str(trainer_a.id)]
    assert set(scope_orders_for_user(Order.objects.all(), finance)) == {order_a}
    assert set(scope_payments_for_user(Payment.objects.all(), finance)) == {payment_a}
    assert set(scope_entitlements_for_user(Entitlement.objects.all(), finance)) == {entitlement_a}
    assert set(scope_payouts_for_user(PayoutRequest.objects.all(), finance)) == {payout_a}

    assert order_b not in scope_orders_for_user(Order.objects.all(), finance)
    assert payment_b not in scope_payments_for_user(Payment.objects.all(), finance)
    assert entitlement_b not in scope_entitlements_for_user(Entitlement.objects.all(), finance)
    assert payout_b not in scope_payouts_for_user(PayoutRequest.objects.all(), finance)


@pytest.mark.django_db
def test_v108_notification_deliveries_are_scoped_to_visible_tenant_users():
    trainer_a, _profile_a = _trainer("v108-delivery-trainer-a@example.com", "delivery-trainer-a")
    trainer_b, _profile_b = _trainer("v108-delivery-trainer-b@example.com", "delivery-trainer-b")
    tenant_a = _tenant_for_trainer(trainer_a)
    _tenant_for_trainer(trainer_b)
    support = _user("v108-delivery-support@example.com")
    _assign_role(support, AccountRoleAssignment.ROLE_SUPPORT)
    TenantMembership.objects.create(
        tenant_id=str(tenant_a.id),
        account_id=str(support.id),
        role="support",
        status="active",
        permissions=["support.view"],
    )
    student_a = _user("v108-delivery-student-a@example.com")
    student_b = _user("v108-delivery-student-b@example.com")
    _commerce_row(student=student_a, trainer=trainer_a)
    _commerce_row(student=student_b, trainer=trainer_b)
    delivery_a = NotificationDelivery.objects.create(
        user=student_a,
        channel=NotificationChannel.IN_APP,
        type=NotificationType.ACCESS_GRANTED,
        status=NotificationStatus.FAILED,
    )
    delivery_b = NotificationDelivery.objects.create(
        user=student_b,
        channel=NotificationChannel.IN_APP,
        type=NotificationType.ACCESS_GRANTED,
        status=NotificationStatus.FAILED,
    )

    scoped = scope_notification_deliveries_for_user(NotificationDelivery.objects.all(), support)

    assert set(scoped) == {delivery_a}
    assert delivery_b not in scoped


@pytest.mark.django_db
def test_v108_student_self_service_never_sees_another_students_purchases():
    trainer, _profile = _trainer("v108-trainer-self-service@example.com", "trainer-self-service")
    student_a = _user("v108-student-a@example.com")
    student_b = _user("v108-student-b@example.com")
    order_a, payment_a, entitlement_a = _commerce_row(student=student_a, trainer=trainer)
    order_b, payment_b, entitlement_b = _commerce_row(student=student_b, trainer=trainer)

    assert set(scope_orders_for_user(Order.objects.all(), student_a)) == {order_a}
    assert set(scope_payments_for_user(Payment.objects.all(), student_a)) == {payment_a}
    assert set(scope_entitlements_for_user(Entitlement.objects.all(), student_a)) == {entitlement_a}

    assert order_b not in scope_orders_for_user(Order.objects.all(), student_a)
    assert payment_b not in scope_payments_for_user(Payment.objects.all(), student_a)
    assert entitlement_b not in scope_entitlements_for_user(Entitlement.objects.all(), student_a)


@pytest.mark.django_db
def test_v108_global_admin_can_see_all_tenant_rows():
    trainer_a, profile_a = _trainer("v108-admin-trainer-a@example.com", "admin-trainer-a")
    trainer_b, profile_b = _trainer("v108-admin-trainer-b@example.com", "admin-trainer-b")
    student = _user("v108-admin-student@example.com")
    admin = get_user_model().objects.create_superuser(email="v108-admin@example.com", password="pass12345")
    _commerce_row(student=student, trainer=trainer_a)
    _commerce_row(student=student, trainer=trainer_b)
    wallet_a = TrainerWallet.objects.create(trainer=profile_a, available_amount=Decimal("50.00"))
    wallet_b = TrainerWallet.objects.create(trainer=profile_b, available_amount=Decimal("50.00"))
    PayoutRequest.objects.create(trainer=profile_a, wallet=wallet_a, amount=Decimal("10.00"), currency="RUB")
    PayoutRequest.objects.create(trainer=profile_b, wallet=wallet_b, amount=Decimal("10.00"), currency="RUB")

    assert scope_orders_for_user(Order.objects.all(), admin).count() == 2
    assert scope_payments_for_user(Payment.objects.all(), admin).count() == 2
    assert scope_entitlements_for_user(Entitlement.objects.all(), admin).count() == 2
    assert scope_payouts_for_user(PayoutRequest.objects.all(), admin).count() == 2
