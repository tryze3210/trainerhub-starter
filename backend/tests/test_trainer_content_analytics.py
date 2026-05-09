from decimal import Decimal
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.orders.models import Order, OrderItem, OrderStatus, OrderType, PurchasedItemType
from apps.payouts.models import BalanceEntry, TrainerWallet
from apps.products.models import Product, ProductItem
from apps.trainers.models import TrainerProfile
from apps.videos.models import MediaAsset, Video

pytestmark = pytest.mark.django_db


def _create_user(email: str, *, role: str = "customer"):
    User = get_user_model()
    user = User.objects.create_user(email=email, password="password123", role=role)
    return user


def _create_trainer_fixture():
    trainer_user = _create_user("trainer-content-analytics@example.com", role="trainer")
    buyer = _create_user("buyer-content-analytics@example.com", role="customer")
    profile = TrainerProfile.objects.create(
        user=trainer_user,
        slug="trainer-content-analytics",
        display_name="Trainer Content Analytics",
        status="active",
        is_public=True,
    )
    asset = MediaAsset.objects.create(
        owner_user=trainer_user,
        bucket_name="trainerhub-test",
        object_key="videos/content-analytics.mp4",
        asset_type="video",
        visibility=MediaAsset.Visibility.PUBLIC,
        status=MediaAsset.Status.VERIFIED,
        content_type="video/mp4",
        metadata_json={"views_count": 100},
    )
    video = Video.objects.create(
        trainer=profile,
        media_asset=asset,
        slug="content-analytics-video",
        title="Content Analytics Video",
        description="Performance test video",
        is_free=False,
        status="published",
    )
    product = Product.objects.create(
        trainer=profile,
        slug="content-analytics-product",
        title="Content Analytics Product",
        description="Performance test product",
        product_type="video",
        access_type="lifetime",
        status="published",
        currency="RUB",
        price_amount=Decimal("1200.00"),
    )
    ProductItem.objects.create(product=product, video=video, position=1)

    wallet = TrainerWallet.objects.create(
        trainer=profile,
        currency="RUB",
        available_amount=Decimal("900.00"),
    )
    BalanceEntry.objects.create(
        wallet=wallet,
        entry_type="sale_credit",
        direction="credit",
        amount=Decimal("800.00"),
        currency="RUB",
        status="posted",
        source_type="video",
        source_id=video.id,
    )
    BalanceEntry.objects.create(
        wallet=wallet,
        entry_type="refund_debit",
        direction="debit",
        amount=Decimal("100.00"),
        currency="RUB",
        status="posted",
        source_type="video",
        source_id=video.id,
    )

    order = Order.objects.create(
        user=buyer,
        order_type=OrderType.ONE_TIME,
        status=OrderStatus.COMPLETED,
        currency="RUB",
        total_amount=Decimal("1200.00"),
    )
    OrderItem.objects.create(
        order=order,
        item_type=PurchasedItemType.VIDEO,
        item_id=str(video.id),
        title_snapshot=video.title,
        quantity=1,
        unit_price=Decimal("1200.00"),
        total_price=Decimal("1200.00"),
        metadata={"trainer_id": str(profile.id)},
    )
    return trainer_user, video, product


def test_trainer_can_read_content_analytics_overview():
    trainer_user, video, _ = _create_trainer_fixture()
    client = APIClient()
    client.force_authenticate(user=trainer_user)

    response = client.get(reverse("trainer-me-analytics-overview"), {"days": 90})

    assert response.status_code == 200
    payload = response.json()
    assert payload["trainer"]["slug"] == "trainer-content-analytics"
    assert payload["counts"]["videos"] == 1
    assert payload["counts"]["products"] == 1
    assert payload["performance"]["net_revenue"] == "700.00"
    assert payload["performance"]["total_purchases"] >= 1
    assert payload["top_content"][0]["id"] == str(video.id)


def test_trainer_can_read_content_and_sales_analytics_lists():
    trainer_user, video, _ = _create_trainer_fixture()
    client = APIClient()
    client.force_authenticate(user=trainer_user)

    content_response = client.get(reverse("trainer-me-analytics-content"), {"type": "video", "limit": 10})
    sales_response = client.get(reverse("trainer-me-analytics-sales"), {"limit": 10})

    assert content_response.status_code == 200
    content_payload = content_response.json()
    assert content_payload["count"] == 1
    assert content_payload["results"][0]["id"] == str(video.id)
    assert content_payload["results"][0]["views_count"] == 100
    assert content_payload["results"][0]["purchase_count"] == 1
    assert content_payload["results"][0]["net_revenue"] == "700.00"

    assert sales_response.status_code == 200
    sales_payload = sales_response.json()
    assert sales_payload["count"] == 1
    assert sales_payload["results"][0]["matched_content_id"] == str(video.id)
    assert sales_payload["results"][0]["total_price"] == "1200.00"
