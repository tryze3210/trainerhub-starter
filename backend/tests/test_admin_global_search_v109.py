from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.models import AccountRoleAssignment
from apps.ops.admin_global_search import get_admin_global_search
from apps.orders.models import Order, OrderItem, OrderStatus, OrderType, PurchasedItemType
from apps.payments.models import Payment, PaymentProvider, PaymentStatus
from apps.payouts.models import PayoutRequest, TrainerWallet
from apps.subscriptions.models import Subscription, SubscriptionPlan, SubscriptionStatus
from apps.tenancy.models import Tenant, TenantMembership
from apps.trainer_cms.models import TrainerCourseDraft
from apps.trainers.models import TrainerProfile


def _user(email, role="customer"):
    return get_user_model().objects.create_user(email=email, password="pass12345", role=role)


def _trainer(email, slug):
    user = _user(email, role="trainer")
    profile = TrainerProfile.objects.create(user=user, slug=slug, display_name=slug.title())
    return user, profile


def _tenant_for_trainer(trainer):
    tenant = Tenant.objects.create(
        code=f"v109-tenant-{trainer.id}",
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


def _commerce_bundle(*, trainer, trainer_profile, student, marker):
    plan = SubscriptionPlan.objects.create(
        trainer_id=str(trainer.id),
        title=f"{marker} subscription",
        price=Decimal("100.00"),
        currency="RUB",
    )
    order = Order.objects.create(
        user=student,
        order_type=OrderType.SUBSCRIPTION,
        status=OrderStatus.PAID,
        currency="RUB",
        total_amount=Decimal("100.00"),
        external_checkout_id=f"checkout-{marker}",
    )
    OrderItem.objects.create(
        order=order,
        item_type=PurchasedItemType.SUBSCRIPTION_PLAN,
        item_id=str(plan.id),
        title_snapshot=plan.title,
        quantity=1,
        unit_price=Decimal("100.00"),
        total_price=Decimal("100.00"),
    )
    payment = Payment.objects.create(
        order=order,
        provider=PaymentProvider.MOCK,
        status=PaymentStatus.SUCCEEDED,
        amount=Decimal("100.00"),
        currency="RUB",
        external_payment_id=f"payment-{marker}",
    )
    wallet = TrainerWallet.objects.create(trainer=trainer_profile, available_amount=Decimal("25.00"))
    payout = PayoutRequest.objects.create(
        trainer=trainer_profile,
        wallet=wallet,
        amount=Decimal("10.00"),
        currency="RUB",
        destination_json={"external_reference": f"payout-{marker}"},
    )
    course = TrainerCourseDraft.objects.create(
        trainer_id=trainer.id,
        title=f"{marker} course",
        slug=f"{marker}-course",
        description=f"{marker} content",
        price_amount=Decimal("100.00"),
        currency="RUB",
    )
    subscription = Subscription.objects.create(
        user=student,
        plan=plan,
        source_order=order,
        status=SubscriptionStatus.ACTIVE,
    )
    return {
        "order": order,
        "payment": payment,
        "payout": payout,
        "course": course,
        "subscription": subscription,
    }


@pytest.mark.django_db
def test_v109_admin_global_search_returns_core_entity_categories():
    admin = get_user_model().objects.create_superuser(email="v109-admin@example.com", password="pass12345")
    trainer, trainer_profile = _trainer("v109-search-trainer@example.com", "v109-search-trainer")
    student = _user("v109-search-student@example.com")
    _commerce_bundle(trainer=trainer, trainer_profile=trainer_profile, student=student, marker="v109-search")

    payload = get_admin_global_search(user=admin, query="v109-search", limit=10)

    categories = {item["category"] for item in payload["results"]}
    assert {"users", "trainers", "orders", "payments", "payouts", "content", "subscriptions"}.issubset(categories)
    assert payload["results_by_category"]["orders"]
    assert payload["results_by_category"]["payments"]
    assert payload["results_by_category"]["content"]


@pytest.mark.django_db
def test_v109_global_search_is_tenant_scoped_for_finance_operator():
    trainer_a, profile_a = _trainer("v109-scope-trainer-a@example.com", "v109-scope-a")
    trainer_b, profile_b = _trainer("v109-scope-trainer-b@example.com", "v109-scope-b")
    tenant_a = _tenant_for_trainer(trainer_a)
    _tenant_for_trainer(trainer_b)
    student_a = _user("v109-scope-student-a@example.com")
    student_b = _user("v109-scope-student-b@example.com")
    rows_a = _commerce_bundle(trainer=trainer_a, trainer_profile=profile_a, student=student_a, marker="v109-scope")
    rows_b = _commerce_bundle(trainer=trainer_b, trainer_profile=profile_b, student=student_b, marker="v109-scope")
    finance = _user("v109-finance@example.com")
    AccountRoleAssignment.objects.create(user=finance, role=AccountRoleAssignment.ROLE_FINANCE, is_active=True)
    TenantMembership.objects.create(
        tenant_id=str(tenant_a.id),
        account_id=str(finance.id),
        role="finance",
        status="active",
        permissions=["payments.view", "payouts.view"],
    )

    payload = get_admin_global_search(
        user=finance,
        query="v109-scope",
        categories=("orders", "payments", "payouts", "content", "subscriptions"),
        limit=10,
    )
    entity_ids = {item["entity_id"] for item in payload["results"]}

    assert str(rows_a["order"].id) in entity_ids
    assert str(rows_a["payment"].id) in entity_ids
    assert str(rows_a["payout"].id) in entity_ids
    assert str(rows_a["course"].id) in entity_ids
    assert str(rows_a["subscription"].id) in entity_ids
    assert str(rows_b["order"].id) not in entity_ids
    assert str(rows_b["payment"].id) not in entity_ids
    assert str(rows_b["payout"].id) not in entity_ids
    assert str(rows_b["course"].id) not in entity_ids
    assert str(rows_b["subscription"].id) not in entity_ids


@pytest.mark.django_db
def test_v109_admin_global_search_endpoint_contract():
    admin = get_user_model().objects.create_superuser(email="v109-endpoint-admin@example.com", password="pass12345")
    trainer, trainer_profile = _trainer("v109-endpoint-trainer@example.com", "v109-endpoint-trainer")
    student = _user("v109-endpoint-student@example.com")
    _commerce_bundle(trainer=trainer, trainer_profile=trainer_profile, student=student, marker="v109-endpoint")
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get("/api/v1/ops/admin/global-search/?q=v109-endpoint&limit=5")

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "v109-endpoint"
    assert payload["total_count"] > 0
    assert "results_by_category" in payload
