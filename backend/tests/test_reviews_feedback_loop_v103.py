from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.entitlements.models import Entitlement, EntitlementSourceType, EntitlementStatus, EntitlementTargetType
from apps.reviews.models import Review
from apps.trainer_cms.models import PublishStatus, TrainerCourseDraft


pytestmark = pytest.mark.django_db


def make_user(email, *, role="customer", is_staff=False):
    return get_user_model().objects.create_user(email=email, password="pass12345", role=role, is_staff=is_staff)


def test_course_review_moderation_aggregation_and_trainer_reply():
    trainer = make_user("review-trainer@example.com", role="trainer")
    student = make_user("review-student@example.com")
    admin = make_user("review-admin@example.com", role="admin", is_staff=True)
    course = TrainerCourseDraft.objects.create(
        trainer_id=trainer.id,
        title="Review Course",
        slug="review-course",
        description="Course eligible for reviews",
        status=PublishStatus.PUBLISHED,
    )
    Entitlement.objects.create(
        user=student,
        source_type=EntitlementSourceType.ADMIN_GRANT,
        target_type=EntitlementTargetType.COURSE,
        target_id=str(course.id),
        status=EntitlementStatus.ACTIVE,
    )

    student_client = APIClient()
    student_client.force_authenticate(user=student)
    create_response = student_client.post(
        f"/api/v1/reviews/course/{course.id}/",
        {
            "rating": 5,
            "title": "Strong course",
            "body": "Detailed lessons, useful homework and clear progression.",
        },
        format="json",
    )

    assert create_response.status_code == 201, create_response.data
    review_id = create_response.data["id"]
    assert create_response.data["status"] == Review.STATUS_PENDING
    assert create_response.data["verified_purchase"] is True
    assert create_response.data["target_title"] == "Review Course"

    admin_client = APIClient()
    admin_client.force_authenticate(user=admin)
    publish_response = admin_client.post(
        f"/api/v1/reviews/admin/{review_id}/moderate/",
        {"decision": "publish", "note": "Looks good"},
        format="json",
    )

    assert publish_response.status_code == 200, publish_response.data
    assert publish_response.data["status"] == Review.STATUS_PUBLISHED

    trainer_client = APIClient()
    trainer_client.force_authenticate(user=trainer)
    reply_response = trainer_client.post(
        f"/api/v1/reviews/trainer/{review_id}/reply/",
        {"reply": "Спасибо за отзыв, добавлю ещё один блок по технике."},
        format="json",
    )

    assert reply_response.status_code == 200, reply_response.data
    assert reply_response.data["trainer_reply"].startswith("Спасибо")
    assert reply_response.data["trainer_reply_by_id"] == str(trainer.id)

    public_response = student_client.get(f"/api/v1/reviews/course/{course.id}/")

    assert public_response.status_code == 200, public_response.data
    assert public_response.data["summary"]["reviews_count"] == 1
    assert public_response.data["summary"]["average_rating"] == 5.0
    assert public_response.data["summary"]["rating_distribution"]["5"] == 1
    assert public_response.data["items"][0]["trainer_reply"].startswith("Спасибо")


def test_student_without_course_access_cannot_review_paid_course():
    student = make_user("review-no-access@example.com")
    course = TrainerCourseDraft.objects.create(
        trainer_id=uuid4(),
        title="Locked Review Course",
        slug="locked-review-course",
        status=PublishStatus.PUBLISHED,
    )
    client = APIClient()
    client.force_authenticate(user=student)

    response = client.post(
        f"/api/v1/reviews/course/{course.id}/",
        {"rating": 4, "title": "No access", "body": "Trying without entitlement."},
        format="json",
    )

    assert response.status_code == 400, response.data
    assert Review.objects.count() == 0
