from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.content.models import PublishedLesson, PublishedProgram
from apps.entitlements.models import Entitlement, EntitlementSourceType, EntitlementStatus, EntitlementTargetType
from apps.orders.models import Order, OrderStatus, OrderType
from apps.trainer_cms.models import CourseLessonDraft, PublishStatus, TrainerCourseDraft
from apps.trainer_profiles.models import TrainerPublicProfile


pytestmark = pytest.mark.django_db


def make_user(email="student@example.com", *, role="customer"):
    return get_user_model().objects.create_user(email=email, password="pass12345", role=role)


def make_program_with_lesson(*, is_preview=False):
    trainer = make_user("runtime-trainer@example.com", role="trainer")
    profile = TrainerPublicProfile.objects.create(
        user=trainer,
        trainer_uuid=uuid4(),
        slug="runtime-trainer",
        display_name="Runtime Trainer",
    )
    program = PublishedProgram.objects.create(
        trainer_profile=profile,
        source_draft_id=uuid4(),
        slug="runtime-program",
        title="Runtime Program",
        description="",
        price_amount=Decimal("1200.00"),
        currency="RUB",
        is_active=True,
    )
    lesson = PublishedLesson.objects.create(
        program=program,
        source_draft_id=uuid4(),
        slug="lesson-one",
        title="Lesson one",
        description="Protected lesson",
        position=1,
        video_asset_id=uuid4(),
        materials=[{"title": "Workbook", "url": "https://example.test/workbook.pdf", "kind": "pdf"}],
        is_preview=is_preview,
    )
    return program, lesson


def grant_program_entitlement(*, user, program, order_status=OrderStatus.COMPLETED, ends_at=None):
    order = Order.objects.create(
        user=user,
        order_type=OrderType.ONE_TIME,
        status=order_status,
        currency="RUB",
        total_amount=Decimal("1200.00"),
    )
    return Entitlement.objects.create(
        user=user,
        source_type=EntitlementSourceType.ORDER,
        source_order=order,
        target_type=EntitlementTargetType.PROGRAM,
        target_id=str(program.source_draft_id),
        status=EntitlementStatus.ACTIVE,
        starts_at=timezone.now() - timedelta(minutes=1),
        ends_at=ends_at,
    )


def test_student_opens_program_lesson_with_active_entitlement():
    user = make_user("runtime-active@example.com")
    program, lesson = make_program_with_lesson()
    entitlement = grant_program_entitlement(user=user, program=program)
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(f"/api/v1/content/runtime/programs/{program.slug}/lessons/{lesson.slug}/")

    assert response.status_code == 200, response.data
    assert response.data["allowed"] is True
    assert response.data["lesson"]["video_asset_id"] == str(lesson.video_asset_id)
    assert response.data["lesson"]["materials"][0]["title"] == "Workbook"
    assert response.data["access"]["entitlement_id"] == str(entitlement.id)


def test_refunded_order_blocks_program_lesson_runtime_fields():
    user = make_user("runtime-refunded@example.com")
    program, lesson = make_program_with_lesson()
    grant_program_entitlement(user=user, program=program, order_status=OrderStatus.REFUNDED)
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(f"/api/v1/content/runtime/programs/{program.slug}/lessons/{lesson.slug}/")

    assert response.status_code == 403, response.data
    assert response.data["blocked"] is True
    assert response.data["lesson"]["video_asset_id"] is None
    assert response.data["lesson"]["materials"] == []
    assert response.data["access"]["code"] == "source_order_invalid"


def test_expired_program_entitlement_blocks_lesson_runtime_fields():
    user = make_user("runtime-expired@example.com")
    program, lesson = make_program_with_lesson()
    grant_program_entitlement(
        user=user,
        program=program,
        ends_at=timezone.now() - timedelta(minutes=1),
    )
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(f"/api/v1/content/runtime/programs/{program.slug}/lessons/{lesson.slug}/")

    assert response.status_code == 403, response.data
    assert response.data["blocked"] is True
    assert response.data["lesson"]["video_asset_id"] is None
    assert response.data["lesson"]["materials"] == []


def test_preview_program_lesson_opens_without_authentication():
    program, lesson = make_program_with_lesson(is_preview=True)
    client = APIClient()

    response = client.get(f"/api/v1/content/runtime/programs/{program.slug}/lessons/{lesson.slug}/")

    assert response.status_code == 200, response.data
    assert response.data["allowed"] is True
    assert response.data["access"]["code"] == "preview_lesson"
    assert response.data["lesson"]["materials"][0]["title"] == "Workbook"


def test_course_lesson_runtime_uses_course_entitlement():
    user = make_user("runtime-course@example.com")
    course = TrainerCourseDraft.objects.create(
        trainer_id=uuid4(),
        title="Runtime Course",
        slug="runtime-course",
        description="",
        price_amount=Decimal("1500.00"),
        currency="RUB",
        status=PublishStatus.PUBLISHED,
    )
    lesson = CourseLessonDraft.objects.create(
        course_draft=course,
        title="Course lesson",
        description="",
        position=1,
        video_asset_id=uuid4(),
        materials=[{"title": "Course notes", "url": "https://example.test/course"}],
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

    response = client.get(f"/api/v1/content/runtime/courses/{course.id}/lessons/{lesson.id}/")

    assert response.status_code == 200, response.data
    assert response.data["runtime"] == "course_lesson"
    assert response.data["allowed"] is True
    assert response.data["lesson"]["materials"][0]["title"] == "Course notes"
