from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.products.models import Product, ProductItem
from apps.trainers.models import TrainerProfile
from apps.users.models import User
from apps.videos.models import MediaAsset, Video


pytestmark = pytest.mark.django_db


def make_trainer(email="trainer@example.com"):
    user = User.objects.create_user(email=email, password="pass", role=User.Roles.TRAINER)
    profile = TrainerProfile.objects.create(
        user=user,
        slug=email.split("@")[0],
        display_name="Trainer",
        status="approved",
        is_public=True,
    )
    return user, profile


def make_video(profile, title="Ready video", status="ready"):
    asset = MediaAsset.objects.create(
        owner_user=profile.user,
        bucket_name="private-media",
        object_key=f"videos/{title}.mp4",
        asset_type="video",
        visibility=MediaAsset.Visibility.PRIVATE,
        status=MediaAsset.Status.VERIFIED,
        content_type="video/mp4",
        file_size_bytes=100,
    )
    return Video.objects.create(
        trainer=profile,
        media_asset=asset,
        slug=title.lower().replace(" ", "-"),
        title=title,
        description="",
        status=status,
    )


def test_trainer_can_create_and_publish_single_video_product():
    user, profile = make_trainer()
    video = make_video(profile)
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        "/api/v1/products/trainer/",
        {
            "title": "Morning strength",
            "product_type": "video",
            "access_type": "one_time",
            "currency": "RUB",
            "price_amount": "990.00",
            "item_video_ids": [str(video.id)],
        },
        format="json",
    )

    assert response.status_code == 201, response.data
    assert response.data["slug"] == "morning-strength"
    assert response.data["status"] == "draft"
    assert response.data["readiness"]["status"] == "ready"

    product_id = response.data["id"]
    publish_response = client.post(f"/api/v1/products/trainer/{product_id}/publish/", {}, format="json")

    assert publish_response.status_code == 200, publish_response.data
    assert publish_response.data["status"] == "published"
    product = Product.objects.get(id=product_id)
    assert product.status == "published"
    assert product.price_amount == Decimal("990.00")
    assert ProductItem.objects.filter(product=product, video=video).exists()


def test_bundle_publish_requires_at_least_two_ready_videos():
    user, profile = make_trainer("bundle@example.com")
    video = make_video(profile, title="Only video")
    client = APIClient()
    client.force_authenticate(user=user)

    create_response = client.post(
        "/api/v1/products/trainer/",
        {
            "title": "Small bundle",
            "product_type": "bundle",
            "access_type": "one_time",
            "price_amount": "1500.00",
            "item_video_ids": [str(video.id)],
        },
        format="json",
    )
    assert create_response.status_code == 201, create_response.data

    product_id = create_response.data["id"]
    publish_response = client.post(f"/api/v1/products/trainer/{product_id}/publish/", {}, format="json")

    assert publish_response.status_code == 400
    assert publish_response.data["readiness"]["status"] == "blocked"


def test_customer_cannot_use_trainer_product_builder():
    customer = User.objects.create_user(email="customer@example.com", password="pass", role=User.Roles.CUSTOMER)
    client = APIClient()
    client.force_authenticate(user=customer)

    response = client.get("/api/v1/products/trainer/")

    assert response.status_code == 403
