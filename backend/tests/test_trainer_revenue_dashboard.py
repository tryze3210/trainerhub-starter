from decimal import Decimal
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.payouts.models import BalanceEntry, PayoutRequest, TrainerWallet
from apps.trainers.models import TrainerProfile

pytestmark = pytest.mark.django_db


def _create_trainer_user():
    User = get_user_model()
    kwargs = {"email": "trainer-revenue@example.com", "password": "password123"}
    if any(field.name == "username" for field in User._meta.fields):
        kwargs["username"] = "trainer-revenue"
    user = User.objects.create_user(**kwargs)
    if hasattr(User, "Roles"):
        user.role = User.Roles.TRAINER
    else:
        user.role = "trainer"
    user.save(update_fields=["role", "updated_at"] if hasattr(user, "updated_at") else ["role"])
    return user


def _create_revenue_fixture():
    user = _create_trainer_user()
    profile = TrainerProfile.objects.create(
        user=user,
        slug="trainer-revenue",
        display_name="Trainer Revenue",
        status="active",
        is_public=True,
    )
    wallet = TrainerWallet.objects.create(
        trainer=profile,
        currency="RUB",
        available_amount=Decimal("700.00"),
        pending_amount=Decimal("80.00"),
        locked_amount=Decimal("20.00"),
    )
    BalanceEntry.objects.create(
        wallet=wallet,
        entry_type="sale_credit",
        direction="credit",
        amount=Decimal("1000.00"),
        currency="RUB",
        status="posted",
        source_type="video",
        source_id=uuid4(),
    )
    BalanceEntry.objects.create(
        wallet=wallet,
        entry_type="refund_debit",
        direction="debit",
        amount=Decimal("150.00"),
        currency="RUB",
        status="posted",
        source_type="payment",
        source_id=uuid4(),
    )
    PayoutRequest.objects.create(
        trainer=profile,
        wallet=wallet,
        amount=Decimal("300.00"),
        currency="RUB",
        status="requested",
        destination_json={"method": "manual", "destination_masked": "manual"},
    )
    return user


def test_trainer_can_read_revenue_summary():
    user = _create_revenue_fixture()
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(reverse("trainer-me-revenue-summary"), {"days": 90})

    assert response.status_code == 200
    payload = response.json()
    assert payload["trainer"]["slug"] == "trainer-revenue"
    assert payload["currency"] == "RUB"
    assert payload["wallet"]["available_amount"] == "700.00"
    assert payload["revenue"]["net_revenue"] == "1000.00"
    assert payload["revenue"]["refunds"] == "150.00"
    assert payload["revenue"]["pending_payout"] == "300.00"
    assert payload["top_sources"]


def test_trainer_can_read_revenue_transactions_and_payouts():
    user = _create_revenue_fixture()
    client = APIClient()
    client.force_authenticate(user=user)

    transactions_response = client.get(reverse("trainer-me-revenue-transactions"), {"limit": 10})
    payouts_response = client.get(reverse("trainer-me-revenue-payouts"), {"limit": 10})

    assert transactions_response.status_code == 200
    assert transactions_response.json()["count"] == 2
    assert transactions_response.json()["results"][0]["amount"] in {"1000.00", "150.00"}

    assert payouts_response.status_code == 200
    assert payouts_response.json()["count"] == 1
    assert payouts_response.json()["results"][0]["amount"] == "300.00"
