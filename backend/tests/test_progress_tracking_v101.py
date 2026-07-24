from decimal import Decimal
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.test import APIClient

from apps.content.models import PublishedLesson, PublishedProgram
from apps.entitlements.models import Entitlement, EntitlementSourceType, EntitlementStatus, EntitlementTargetType
from apps.orders.models import Order, OrderStatus, OrderType
from apps.progress.api.views import MyLessonProgressViewSet, MyVideoProgressViewSet
from apps.progress.models import LessonProgress, ProgramProgress
from apps.trainer_profiles.models import TrainerPublicProfile


pytestmark = pytest.mark.django_db


def make_user(email, *, role="customer"):
    return get_user_model().objects.create_user(email=email, password="pass12345", role=role)


def make_program():
    suffix = uuid4().hex[:8]
    trainer_user = make_user(f"progress-trainer-{suffix}@example.com", role="trainer")
    profile = TrainerPublicProfile.objects.create(
        user=trainer_user,
        trainer_uuid=uuid4(),
        slug=f"progress-trainer-{suffix}",
        display_name="Progress Trainer",
    )
    program = PublishedProgram.objects.create(
        trainer_profile=profile,
        source_draft_id=uuid4(),
        slug="progress-program",
        title="Progress Program",
        description="",
        price_amount=Decimal("900.00"),
        currency="RUB",
        is_active=True,
    )
    first = PublishedLesson.objects.create(
        program=program,
        source_draft_id=uuid4(),
        slug="progress-first",
        title="First",
        position=1,
    )
    second = PublishedLesson.objects.create(
        program=program,
        source_draft_id=uuid4(),
        slug="progress-second",
        title="Second",
        position=2,
    )
    return trainer_user, program, first, second


def grant_program_access(*, user, program):
    order = Order.objects.create(
        user=user,
        order_type=OrderType.ONE_TIME,
        status=OrderStatus.COMPLETED,
        currency="RUB",
        total_amount=Decimal("900.00"),
    )
    Entitlement.objects.create(
        user=user,
        source_type=EntitlementSourceType.ORDER,
        source_order=order,
        target_type=EntitlementTargetType.PROGRAM,
        target_id=str(program.source_draft_id),
        status=EntitlementStatus.ACTIVE,
    )


def test_student_marks_lesson_completed_and_learning_area_updates_progress():
    student = make_user("progress-student@example.com")
    _, program, first, second = make_program()
    grant_program_access(user=student, program=program)
    client = APIClient()
    client.force_authenticate(user=student)

    response = client.post(
        "/api/v1/progress/lessons/complete/",
        {"lesson_id": str(first.source_draft_id), "content_type": "program"},
        format="json",
    )

    assert response.status_code == 200, response.data
    assert response.data["is_completed"] is True
    assert response.data["program_id"] == str(program.source_draft_id)
    assert response.data["content_type"] == "program"

    progress = ProgramProgress.objects.get(user=student, program_id=str(program.source_draft_id))
    assert progress.completed_lessons == 1
    assert progress.total_lessons == 2
    assert str(progress.completion_percent) == "50.00"
    assert progress.last_activity_at is not None

    learning_response = client.get("/api/v1/content/student/learning-area/")
    assert learning_response.status_code == 200, learning_response.data
    item = learning_response.data["items"][0]
    assert item["progress_percent"] == "50.00"
    completed = [lesson for lesson in item["lessons"] if lesson["is_completed"]]
    assert completed[0]["lesson_id"] == str(first.source_draft_id)
    assert learning_response.data["next_lesson"]["lesson_id"] == str(second.source_draft_id)


def test_lesson_completion_ignores_spoofed_program_id():
    student = make_user("progress-spoof-student@example.com")
    _, program, first, _second = make_program()
    grant_program_access(user=student, program=program)
    spoofed_program_id = str(uuid4())
    client = APIClient()
    client.force_authenticate(user=student)

    response = client.post(
        "/api/v1/progress/lessons/complete/",
        {
            "lesson_id": str(first.source_draft_id),
            "content_type": "program",
            "program_id": spoofed_program_id,
        },
        format="json",
    )

    assert response.status_code == 200, response.data
    assert response.data["program_id"] == str(program.source_draft_id)
    assert not ProgramProgress.objects.filter(user=student, program_id=spoofed_program_id).exists()


def test_progress_write_actions_use_scoped_throttles():
    rates = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]

    assert rates["progress_video_save"] == "600/hour"
    assert MyVideoProgressViewSet.throttle_scope == "progress_video_save"
    assert "ScopedRateThrottle" in MyVideoProgressViewSet.get_throttles.__code__.co_names

    video_view = MyVideoProgressViewSet()
    video_view.action = "save"
    assert isinstance(video_view.get_throttles()[0], ScopedRateThrottle)

    assert rates["progress_lesson_complete"] == "120/hour"
    assert MyLessonProgressViewSet.throttle_scope == "progress_lesson_complete"
    assert "ScopedRateThrottle" in MyLessonProgressViewSet.get_throttles.__code__.co_names

    lesson_view = MyLessonProgressViewSet()
    lesson_view.action = "complete"
    assert isinstance(lesson_view.get_throttles()[0], ScopedRateThrottle)


def test_trainer_can_see_student_progress_for_owned_program():
    student = make_user("progress-visible-student@example.com")
    trainer_user, program, first, _ = make_program()
    grant_program_access(user=student, program=program)

    LessonProgress.objects.create(
        user=student,
        lesson_id=str(first.source_draft_id),
        program_id=str(program.source_draft_id),
        content_type=LessonProgress.ContentType.PROGRAM,
        is_completed=True,
    )
    ProgramProgress.objects.create(
        user=student,
        program_id=str(program.source_draft_id),
        content_type=ProgramProgress.ContentType.PROGRAM,
        total_lessons=2,
        completed_lessons=1,
        completion_percent=Decimal("50.00"),
    )

    client = APIClient()
    client.force_authenticate(user=trainer_user)
    response = client.get("/api/v1/progress/trainer/students/")

    assert response.status_code == 200, response.data
    assert response.data["summary"]["students_count"] == 1
    assert response.data["items"][0]["student_email"] == "p***@example.com"
    assert response.data["items"][0]["student_email_masked"] is True
    assert response.data["items"][0]["completion_percent"] == "50.00"
