from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.entitlements.models import Entitlement, EntitlementSourceType, EntitlementStatus, EntitlementTargetType
from apps.orders.models import Order, OrderStatus, OrderType
from apps.subscriptions.models import Subscription, SubscriptionPlan, SubscriptionStatus


@pytest.mark.django_db
def test_access_check_allows_active_order_entitlement():
    user = get_user_model().objects.create_user(email="access-order@example.com", password="pass12345")
    target_id = str(uuid4())
    order = Order.objects.create(
        user=user,
        order_type=OrderType.ONE_TIME,
        status=OrderStatus.COMPLETED,
        currency="RUB",
        total_amount=Decimal("499.00"),
    )
    entitlement = Entitlement.objects.create(
        user=user,
        source_type=EntitlementSourceType.ORDER,
        source_order=order,
        target_type=EntitlementTargetType.VIDEO,
        target_id=target_id,
        status=EntitlementStatus.ACTIVE,
        starts_at=timezone.now() - timedelta(minutes=1),
    )

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get(
        "/api/v1/entitlements/me/access-check/",
        {"content_type": "video", "object_id": target_id},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["allowed"] is True
    assert payload["code"] == "access_granted"
    assert payload["entitlement_id"] == str(entitlement.id)
    assert payload["source"] == "direct"
    assert any(rule["code"] == "source_order_valid" for rule in payload["rules"])


@pytest.mark.django_db
def test_access_check_denies_refunded_order_even_if_entitlement_is_still_active():
    user = get_user_model().objects.create_user(email="access-refunded@example.com", password="pass12345")
    target_id = "video-refunded-001"
    order = Order.objects.create(
        user=user,
        order_type=OrderType.ONE_TIME,
        status=OrderStatus.REFUNDED,
        currency="RUB",
        total_amount=Decimal("499.00"),
    )
    Entitlement.objects.create(
        user=user,
        source_type=EntitlementSourceType.ORDER,
        source_order=order,
        target_type=EntitlementTargetType.VIDEO,
        target_id=target_id,
        status=EntitlementStatus.ACTIVE,
    )

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get(
        "/api/v1/entitlements/me/access-check/",
        {"target_type": "video", "target_id": target_id},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["allowed"] is False
    assert payload["code"] == "source_order_invalid"
    assert payload["audit"]["selected_entitlement"]["source_order_status"] == OrderStatus.REFUNDED


@pytest.mark.django_db
def test_access_check_allows_active_library_subscription_entitlement():
    user = get_user_model().objects.create_user(email="access-sub@example.com", password="pass12345")
    plan = SubscriptionPlan.objects.create(title="Library", price=Decimal("1000.00"), currency="RUB")
    subscription = Subscription.objects.create(
        user=user,
        plan=plan,
        status=SubscriptionStatus.ACTIVE,
        starts_at=timezone.now() - timedelta(days=1),
        ends_at=timezone.now() + timedelta(days=29),
    )
    library = Entitlement.objects.create(
        user=user,
        source_type=EntitlementSourceType.SUBSCRIPTION,
        source_subscription=subscription,
        target_type=EntitlementTargetType.LIBRARY,
        target_id="library",
        status=EntitlementStatus.ACTIVE,
        starts_at=timezone.now() - timedelta(days=1),
        ends_at=timezone.now() + timedelta(days=29),
    )

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get(
        "/api/v1/entitlements/me/access-check/",
        {"target_type": "video", "target_id": "any-video-id"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["allowed"] is True
    assert payload["source"] == "library"
    assert payload["entitlement_id"] == str(library.id)
    assert any(rule["code"] == "source_subscription_valid" for rule in payload["rules"])


@pytest.mark.django_db
def test_access_check_denies_cancelled_subscription_entitlement():
    user = get_user_model().objects.create_user(email="access-cancelled@example.com", password="pass12345")
    plan = SubscriptionPlan.objects.create(title="Cancelled Library", price=Decimal("1000.00"), currency="RUB")
    subscription = Subscription.objects.create(
        user=user,
        plan=plan,
        status=SubscriptionStatus.CANCELLED,
        starts_at=timezone.now() - timedelta(days=10),
        ends_at=timezone.now() + timedelta(days=20),
    )
    Entitlement.objects.create(
        user=user,
        source_type=EntitlementSourceType.SUBSCRIPTION,
        source_subscription=subscription,
        target_type=EntitlementTargetType.LIBRARY,
        target_id="library",
        status=EntitlementStatus.ACTIVE,
    )

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get(
        "/api/v1/entitlements/me/access-check/",
        {"target_type": "video", "target_id": "cancelled-video"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["allowed"] is False
    assert payload["code"] == "source_subscription_invalid"
    assert payload["audit"]["selected_entitlement"]["source_subscription_status"] == SubscriptionStatus.CANCELLED


@pytest.mark.django_db
def test_access_check_admin_override_is_explicit_and_read_only():
    admin = get_user_model().objects.create_superuser(email="access-admin@example.com", password="pass12345")
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get(
        "/api/v1/entitlements/me/access-check/",
        {"target_type": "video", "target_id": "missing-video"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["allowed"] is True
    assert payload["code"] == "admin_override"
    assert payload["source"] == "admin_override"
    assert payload["entitlement_id"] is None
    assert Entitlement.objects.filter(user=admin).count() == 0


@pytest.mark.django_db
def test_access_check_requires_authentication():
    client = APIClient()
    response = client.get(
        "/api/v1/entitlements/me/access-check/",
        {"target_type": "video", "target_id": "missing-video"},
    )
    assert response.status_code in {401, 403}
