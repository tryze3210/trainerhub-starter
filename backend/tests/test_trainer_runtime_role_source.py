import pytest
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from apps.accounts.models import AccountRoleAssignment
from apps.assignments.models import AssignmentContentType
from apps.assignments.services import AssignmentService
from apps.products.api.views import ProductListCreateApi
from apps.products.models import Product
from apps.trainer_cms.models import PublishStatus, TrainerCourseDraft
from apps.trainers.models import TrainerProfile
from apps.users.models import User
from apps.videos.models import MediaAsset, Video, VideoAccessLog
from common.permissions import IsTrainer


pytestmark = pytest.mark.django_db


def _user(email: str, *, role: str = User.Roles.CUSTOMER):
    return User.objects.create_user(email=email, password="pass12345", role=role)


def _assign_role(user, role: str):
    return AccountRoleAssignment.objects.create(user=user, role=role, is_active=True)


def _trainer(email: str, slug: str, *, legacy_role: str = User.Roles.CUSTOMER):
    user = _user(email, role=legacy_role)
    _assign_role(user, AccountRoleAssignment.ROLE_TRAINER)
    profile = TrainerProfile.objects.create(
        user=user,
        slug=slug,
        display_name=slug.title(),
        status="approved",
        is_public=True,
    )
    return user, profile


def _video(profile, *, slug: str = "role-source-video", status: str = "draft"):
    asset = MediaAsset.objects.create(
        owner_user=profile.user,
        bucket_name="private-media",
        object_key=f"videos/{slug}.mp4",
        asset_type="video",
        visibility=MediaAsset.Visibility.PRIVATE,
        status=MediaAsset.Status.VERIFIED,
        content_type="video/mp4",
        file_size_bytes=100,
    )
    return Video.objects.create(
        trainer=profile,
        media_asset=asset,
        slug=slug,
        title=slug.replace("-", " ").title(),
        status=status,
    )


def test_active_trainer_assignment_can_manage_video_without_legacy_trainer_role():
    user, profile = _trainer("assigned-video-trainer@example.com", "assigned-video-trainer")
    video = _video(profile, slug="assigned-role-video")
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.patch(
        f"/api/v1/videos/{video.id}/",
        {"title": "Updated by assigned role"},
        format="json",
    )

    assert response.status_code == 200, response.data
    video.refresh_from_db()
    assert video.title == "Updated by assigned role"


def test_active_trainer_assignment_can_see_own_draft_products_without_legacy_trainer_role():
    user, profile = _trainer("assigned-product-trainer@example.com", "assigned-product-trainer")
    product = Product.objects.create(
        trainer=profile,
        slug="assigned-role-product",
        title="Assigned role product",
        product_type="video",
        access_type="one_time",
        currency="RUB",
        price_amount="990.00",
        status="draft",
    )
    factory = APIRequestFactory()
    request = factory.get("/api/v1/products/")
    force_authenticate(request, user=user)

    response = ProductListCreateApi.as_view()(request)

    assert response.status_code == 200, response.data
    rows = response.data["results"] if isinstance(response.data, dict) and "results" in response.data else response.data
    assert any(item["id"] == str(product.id) for item in rows)


def test_video_owner_access_uses_active_trainer_assignment_without_legacy_trainer_role(settings):
    settings.ALLOWED_HOSTS = ["testserver"]
    user, profile = _trainer("assigned-access-trainer@example.com", "assigned-access-trainer")
    video = _video(profile, slug="assigned-role-access-video", status="ready")
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(f"/api/v1/videos/{video.id}/access-url/", {}, format="json")

    assert response.status_code == 200, response.data
    log = VideoAccessLog.objects.get(id=response.data["access_log_id"])
    assert log.reason == VideoAccessLog.AccessReason.TRAINER_OWNER


def test_inactive_assignment_does_not_override_legacy_non_trainer_for_video_update():
    user = _user("inactive-assignment-trainer@example.com", role=User.Roles.CUSTOMER)
    AccountRoleAssignment.objects.create(user=user, role=AccountRoleAssignment.ROLE_TRAINER, is_active=False)
    profile = TrainerProfile.objects.create(
        user=user,
        slug="inactive-assignment-trainer",
        display_name="Inactive Assignment Trainer",
        status="approved",
        is_public=True,
    )
    video = _video(profile, slug="inactive-assignment-video")
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.patch(f"/api/v1/videos/{video.id}/", {"title": "Denied"}, format="json")

    assert response.status_code == 403


def test_common_is_trainer_permission_uses_active_role_assignment():
    user = _user("common-assigned-trainer@example.com", role=User.Roles.CUSTOMER)
    _assign_role(user, AccountRoleAssignment.ROLE_TRAINER)
    factory = APIRequestFactory()
    request = factory.get("/trainer-only")
    request.user = user

    assert IsTrainer().has_permission(request, view=None) is True


def test_assignment_service_create_uses_active_trainer_assignment():
    trainer = _user("assignment-assigned-trainer@example.com", role=User.Roles.CUSTOMER)
    _assign_role(trainer, AccountRoleAssignment.ROLE_TRAINER)
    course = TrainerCourseDraft.objects.create(
        trainer_id=trainer.id,
        title="Assigned role course",
        slug="assigned-role-course",
        status=PublishStatus.PUBLISHED,
    )

    assignment = AssignmentService.create_assignment(
        trainer=trainer,
        data={
            "title": "Assigned role homework",
            "content_type": AssignmentContentType.COURSE,
            "content_id": str(course.id),
            "status": "published",
        },
    )

    assert assignment.trainer == trainer
    assert assignment.title == "Assigned role homework"
