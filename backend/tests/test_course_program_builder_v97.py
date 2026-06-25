import uuid

import pytest
from rest_framework.test import APIClient

from apps.trainer_cms.models import ContentVersion, CourseLessonDraft, TrainerCourseDraft
from apps.users.models import User


pytestmark = pytest.mark.django_db


def make_trainer(email="course-trainer@example.com"):
    return User.objects.create_user(email=email, password="pass", role=User.Roles.TRAINER)


def test_trainer_can_build_course_with_lessons_and_materials():
    trainer = make_trainer()
    client = APIClient()
    client.force_authenticate(user=trainer)

    create_response = client.post(
        "/api/v1/trainer-cms/courses/",
        {
            "title": "Strength foundations",
            "slug": "strength-foundations",
            "description": "A beginner course",
            "price_amount": "1900.00",
            "currency": "RUB",
            "metadata": {"level": "beginner"},
        },
        format="json",
    )

    assert create_response.status_code == 201, create_response.data
    course_id = create_response.data["id"]

    lesson_response = client.post(
        f"/api/v1/trainer-cms/courses/{course_id}/lessons/",
        {
            "title": "Warm up",
            "description": "Prepare joints and breathing",
            "position": 1,
            "video_asset_id": str(uuid.uuid4()),
            "materials": [
                {"title": "Checklist", "url": "https://example.test/checklist.pdf", "kind": "pdf"},
                {"title": "Tempo notes", "kind": "file"},
            ],
            "is_preview": True,
        },
        format="json",
    )

    assert lesson_response.status_code == 201, lesson_response.data
    assert lesson_response.data["materials"][0]["title"] == "Checklist"

    detail_response = client.get(f"/api/v1/trainer-cms/courses/{course_id}/")

    assert detail_response.status_code == 200, detail_response.data
    assert detail_response.data["lessons"][0]["title"] == "Warm up"
    assert detail_response.data["lessons"][0]["materials"][1]["title"] == "Tempo notes"


def test_course_publish_creates_version_snapshot_with_material_counts():
    trainer = make_trainer("publisher@example.com")
    client = APIClient()
    client.force_authenticate(user=trainer)

    course_response = client.post(
        "/api/v1/trainer-cms/courses/",
        {
            "title": "Mobility course",
            "slug": "mobility-course",
            "description": "",
            "price_amount": "990.00",
            "currency": "RUB",
        },
        format="json",
    )
    assert course_response.status_code == 201, course_response.data
    course_id = course_response.data["id"]

    lesson_response = client.post(
        f"/api/v1/trainer-cms/courses/{course_id}/lessons/",
        {
            "title": "Shoulders",
            "position": 1,
            "video_asset_id": str(uuid.uuid4()),
            "materials": [{"title": "Shoulder map", "url": "https://example.test/map"}],
        },
        format="json",
    )
    assert lesson_response.status_code == 201, lesson_response.data

    publish_response = client.post(f"/api/v1/trainer-cms/courses/{course_id}/publish/", {}, format="json")

    assert publish_response.status_code == 200, publish_response.data
    assert publish_response.data["status"] == "published"
    version = ContentVersion.objects.get(entity_type=ContentVersion.EntityType.COURSE, entity_id=course_id)
    assert version.snapshot["lesson_count"] == 1
    assert version.snapshot["materials_count"] == 1


def test_trainer_cannot_mutate_another_trainer_course_lessons():
    owner = make_trainer("owner@example.com")
    intruder = make_trainer("intruder@example.com")
    owner_client = APIClient()
    owner_client.force_authenticate(user=owner)
    intruder_client = APIClient()
    intruder_client.force_authenticate(user=intruder)

    course_response = owner_client.post(
        "/api/v1/trainer-cms/courses/",
        {
            "title": "Private course",
            "slug": "private-course",
            "description": "",
            "price_amount": "0.00",
            "currency": "RUB",
        },
        format="json",
    )
    assert course_response.status_code == 201, course_response.data
    course_id = course_response.data["id"]

    response = intruder_client.post(
        f"/api/v1/trainer-cms/courses/{course_id}/lessons/",
        {"title": "Bad lesson", "position": 1},
        format="json",
    )

    assert response.status_code == 404
    assert TrainerCourseDraft.objects.count() == 1
    assert CourseLessonDraft.objects.count() == 0
