from decimal import Decimal
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.models import AccountRoleAssignment
from apps.entitlements.models import Entitlement, EntitlementSourceType, EntitlementStatus, EntitlementTargetType
from apps.orders.models import Order, OrderStatus, OrderType
from apps.trainers.models import TrainerProfile
from apps.videos.models import MediaAsset, Video, VideoAccessLog


pytestmark = pytest.mark.django_db


def make_user(email, *, role="customer", is_staff=False):
    return get_user_model().objects.create_user(
        email=email,
        password="pass12345",
        role=role,
        is_staff=is_staff,
    )


def make_video(*, is_free=False):
    trainer_user = make_user("delivery-trainer@example.com", role="trainer")
    trainer = TrainerProfile.objects.create(
        user=trainer_user,
        slug="delivery-trainer",
        display_name="Delivery Trainer",
        status="approved",
        is_public=True,
    )
    asset = MediaAsset.objects.create(
        owner_user=trainer_user,
        bucket_name="private-media",
        object_key=f"videos/{uuid4()}.mp4",
        asset_type="video",
        visibility=MediaAsset.Visibility.PRIVATE,
        status=MediaAsset.Status.VERIFIED,
        content_type="video/mp4",
        file_size_bytes=123,
    )
    video = Video.objects.create(
        trainer=trainer,
        media_asset=asset,
        slug=f"delivery-{uuid4()}",
        title="Delivery video",
        description="",
        is_free=is_free,
        status="ready",
    )
    return video


def make_upload_trainer(email="upload-trainer@example.com", slug="upload-trainer"):
    user = make_user(email, role="trainer")
    AccountRoleAssignment.objects.create(user=user, role=AccountRoleAssignment.ROLE_TRAINER, is_active=True)
    TrainerProfile.objects.create(
        user=user,
        slug=slug,
        display_name="Upload Trainer",
        status="approved",
        is_public=True,
    )
    return user


def grant_video_access(*, user, video, order_status=OrderStatus.COMPLETED):
    order = Order.objects.create(
        user=user,
        order_type=OrderType.ONE_TIME,
        status=order_status,
        currency="RUB",
        total_amount=Decimal("499.00"),
    )
    return Entitlement.objects.create(
        user=user,
        source_type=EntitlementSourceType.ORDER,
        source_order=order,
        target_type=EntitlementTargetType.VIDEO,
        target_id=str(video.id),
        status=EntitlementStatus.ACTIVE,
    )


def test_upload_intent_denies_customer_without_media_upload_capability():
    user = make_user("upload-customer@example.com")
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        "/api/v1/videos/upload-intents/",
        {
            "filename": "lesson.mp4",
            "content_type": "video/mp4",
            "file_size_bytes": 1024,
            "visibility": "private",
        },
        format="json",
    )

    assert response.status_code == 403
    assert not MediaAsset.objects.filter(owner_user=user).exists()


def test_upload_intent_allows_trainer_with_media_upload_capability():
    user = make_upload_trainer()
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        "/api/v1/videos/upload-intents/",
        {
            "filename": "lesson.mp4",
            "content_type": "video/mp4",
            "file_size_bytes": 1024,
            "visibility": "private",
        },
        format="json",
    )

    assert response.status_code == 201, response.data
    asset = MediaAsset.objects.get(owner_user=user)
    assert response.data["media_asset_id"] == str(asset.id)
    assert response.data["upload_url"].startswith("https://mock-storage.local/")
    assert asset.visibility == MediaAsset.Visibility.PRIVATE


def test_upload_complete_denies_customer_without_media_upload_capability():
    user = make_user("upload-complete-customer@example.com")
    asset = MediaAsset.objects.create(
        owner_user=user,
        bucket_name="private-media",
        object_key=f"videos/{uuid4()}.mp4",
        asset_type="video",
        visibility=MediaAsset.Visibility.PRIVATE,
        status=MediaAsset.Status.DRAFT,
        content_type="video/mp4",
        file_size_bytes=1024,
    )
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        f"/api/v1/videos/upload-intents/{asset.id}/complete/",
        {"checksum_sha256": "a" * 64},
        format="json",
    )

    asset.refresh_from_db()
    assert response.status_code == 403
    assert asset.status == MediaAsset.Status.DRAFT


def test_upload_complete_rejects_non_draft_asset_state():
    user = make_upload_trainer("upload-complete-trainer@example.com", "upload-complete-trainer")
    asset = MediaAsset.objects.create(
        owner_user=user,
        bucket_name="private-media",
        object_key=f"videos/{uuid4()}.mp4",
        asset_type="video",
        visibility=MediaAsset.Visibility.PRIVATE,
        status=MediaAsset.Status.VERIFIED,
        content_type="video/mp4",
        file_size_bytes=1024,
    )
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        f"/api/v1/videos/upload-intents/{asset.id}/complete/",
        {"checksum_sha256": "b" * 64},
        format="json",
    )

    asset.refresh_from_db()
    assert response.status_code == 400
    assert asset.status == MediaAsset.Status.VERIFIED


def test_video_access_url_returns_signed_lease_and_access_log(settings):
    settings.ALLOWED_HOSTS = ["testserver"]
    user = make_user("delivery-active@example.com")
    video = make_video()
    entitlement = grant_video_access(user=user, video=video)
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        f"/api/v1/videos/{video.id}/access-url/",
        {},
        HTTP_REFERER="http://testserver/course/lesson",
        HTTP_USER_AGENT="pytest-agent",
        REMOTE_ADDR="127.0.0.1",
        format="json",
    )

    assert response.status_code == 200, response.data
    assert response.data["playback_url"].startswith("https://mock-storage.local/")
    assert response.data["access_token"]
    assert response.data["delivery_policy"]["signed_url"] is True
    assert response.data["delivery_policy"]["anti_leech"]["status"] == "pass"

    log = VideoAccessLog.objects.get(id=response.data["access_log_id"])
    assert log.decision == VideoAccessLog.Decision.GRANTED
    assert log.reason == VideoAccessLog.AccessReason.ENTITLEMENT
    assert log.user == user
    assert log.video == video
    assert log.access_token_hash
    assert log.entitlement_decision["entitlement_id"] == str(entitlement.id)
    assert log.user_agent == "pytest-agent"


def test_denied_video_access_is_logged_without_signed_token():
    user = make_user("delivery-denied@example.com")
    video = make_video()
    grant_video_access(user=user, video=video, order_status=OrderStatus.REFUNDED)
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(f"/api/v1/videos/{video.id}/access-url/", {}, format="json")

    assert response.status_code == 403
    log = VideoAccessLog.objects.get(video=video)
    assert log.decision == VideoAccessLog.Decision.DENIED
    assert log.reason == VideoAccessLog.AccessReason.DENIED
    assert log.access_token_hash == ""
    assert log.entitlement_decision["code"] == "source_order_invalid"


def test_free_video_access_is_logged_with_anti_leech_warning(settings):
    settings.ALLOWED_HOSTS = ["testserver"]
    video = make_video(is_free=True)
    client = APIClient()

    response = client.post(
        f"/api/v1/videos/{video.id}/access-url/",
        {},
        HTTP_REFERER="https://unexpected.example/watch",
        format="json",
    )

    assert response.status_code == 200, response.data
    log = VideoAccessLog.objects.get(video=video)
    assert log.reason == VideoAccessLog.AccessReason.FREE_VIDEO
    assert log.anti_leech["status"] == "warning"
    assert log.anti_leech["reason"] == "referer_origin_unrecognized"


def test_video_access_url_clamps_read_ttl_to_configured_max(settings):
    settings.MEDIA_READ_TTL_SECONDS = 3600
    settings.MEDIA_READ_MAX_TTL_SECONDS = 900
    video = make_video(is_free=True)
    client = APIClient()

    response = client.post(f"/api/v1/videos/{video.id}/access-url/", {}, format="json")

    assert response.status_code == 200, response.data
    assert response.data["expires_in"] == 900
    assert response.data["delivery_policy"]["ttl_seconds"] == 900
    assert "expires_in=900" in response.data["playback_url"]
