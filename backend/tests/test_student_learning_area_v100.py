from decimal import Decimal
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.content.models import PublishedLesson, PublishedProgram
from apps.entitlements.models import Entitlement, EntitlementSourceType, EntitlementStatus, EntitlementTargetType
from apps.orders.models import Order, OrderStatus, OrderType
from apps.trainer_cms.models import CourseLessonDraft, PublishStatus, TrainerCourseDraft
from apps.trainer_profiles.models import TrainerPublicProfile


pytestmark = pytest.mark.django_db


def make_user(email="learning-student@example.com", *, role="customer"):
    return get_user_model().objects.create_user(email=email, password="pass12345", role=role)


def make_profile():
    trainer = make_user("learning-trainer@example.com", role="trainer")
    return TrainerPublicProfile.objects.create(
        user=trainer,
        trainer_uuid=uuid4(),
        slug="learning-trainer",
        display_name="Learning Trainer",
    )


def grant(*, user, target_type, target_id, order_status=OrderStatus.COMPLETED):
    order = Order.objects.create(
        user=user,
        order_type=OrderType.ONE_TIME,
        status=order_status,
        currency="RUB",
        total_amount=Decimal("900.00"),
    )
    return Entitlement.objects.create(
        user=user,
        source_type=EntitlementSourceType.ORDER,
        source_order=order,
        target_type=target_type,
        target_id=str(target_id),
        status=EntitlementStatus.ACTIVE,
    )


def test_student_learning_area_lists_active_program_lessons_and_materials():
    user = make_user()
    profile = make_profile()
    program = PublishedProgram.objects.create(
        trainer_profile=profile,
        source_draft_id=uuid4(),
        slug="learning-program",
        title="Learning Program",
        description="Program description",
        price_amount=Decimal("900.00"),
        currency="RUB",
        is_active=True,
    )
    lesson = PublishedLesson.objects.create(
        program=program,
        source_draft_id=uuid4(),
        slug="first-lesson",
        title="First lesson",
        position=1,
        materials=[{"title": "Workbook", "url": "https://example.test/workbook.pdf", "kind": "pdf"}],
    )
    entitlement = grant(user=user, target_type=EntitlementTargetType.PROGRAM, target_id=program.source_draft_id)
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/v1/content/student/learning-area/")

    assert response.status_code == 200, response.data
    assert response.data["summary"]["programs_count"] == 1
    assert response.data["summary"]["lessons_count"] == 1
    assert response.data["summary"]["materials_count"] == 1
    item = response.data["items"][0]
    assert item["entitlement_id"] == str(entitlement.id)
    assert item["lessons"][0]["lesson_id"] == str(lesson.source_draft_id)
    assert item["lessons"][0]["runtime_url"] == f"/content/runtime/programs/{program.slug}/lessons/{lesson.slug}/"
    assert response.data["materials"][0]["title"] == "Workbook"
    assert response.data["next_lesson"]["title"] == "First lesson"


def test_student_learning_area_excludes_refunded_program_access():
    user = make_user("learning-refunded@example.com")
    profile = make_profile()
    program = PublishedProgram.objects.create(
        trainer_profile=profile,
        source_draft_id=uuid4(),
        slug="refunded-program",
        title="Refunded Program",
        description="",
        price_amount=Decimal("900.00"),
        currency="RUB",
        is_active=True,
    )
    grant(
        user=user,
        target_type=EntitlementTargetType.PROGRAM,
        target_id=program.source_draft_id,
        order_status=OrderStatus.REFUNDED,
    )
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/v1/content/student/learning-area/")

    assert response.status_code == 200, response.data
    assert response.data["summary"]["items_count"] == 0
    assert response.data["summary"]["unresolved_count"] == 1
    assert response.data["unresolved"][0]["reason"] == "source_order_invalid"


def test_student_learning_area_lists_published_course_lessons():
    user = make_user("learning-course@example.com")
    course = TrainerCourseDraft.objects.create(
        trainer_id=uuid4(),
        title="Learning Course",
        slug="learning-course",
        description="Course description",
        price_amount=Decimal("1200.00"),
        currency="RUB",
        status=PublishStatus.PUBLISHED,
    )
    lesson = CourseLessonDraft.objects.create(
        course_draft=course,
        title="Course lesson",
        position=1,
        materials=[{"title": "Course notes", "url": "https://example.test/notes"}],
    )
    Entitlement.objects.create(
        user=user,
        source_type=EntitlementSourceType.ADMIN_GRANT,
        target_type=EntitlementTargetType.COURSE,
        target_id=str(course.id),
        status=EntitlementStatus.ACTIVE,
    )
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/v1/content/student/learning-area/")

    assert response.status_code == 200, response.data
    assert response.data["summary"]["courses_count"] == 1
    assert response.data["items"][0]["kind"] == "course"
    assert response.data["items"][0]["lessons"][0]["lesson_id"] == str(lesson.id)
    assert response.data["items"][0]["lessons"][0]["runtime_url"] == f"/content/runtime/courses/{course.id}/lessons/{lesson.id}/"
