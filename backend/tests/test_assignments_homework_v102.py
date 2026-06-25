from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.assignments.models import Assignment, AssignmentStatus, SubmissionStatus
from apps.entitlements.models import Entitlement, EntitlementSourceType, EntitlementStatus, EntitlementTargetType
from apps.trainer_cms.models import CourseLessonDraft, PublishStatus, TrainerCourseDraft


pytestmark = pytest.mark.django_db


def make_user(email, *, role="customer"):
    return get_user_model().objects.create_user(email=email, password="pass12345", role=role)


def make_course():
    course = TrainerCourseDraft.objects.create(
        trainer_id=uuid4(),
        title="Homework Course",
        slug="homework-course",
        description="Course with homework",
        status=PublishStatus.PUBLISHED,
    )
    lesson = CourseLessonDraft.objects.create(
        course_draft=course,
        title="Homework lesson",
        position=1,
    )
    return course, lesson


def grant_course(*, user, course):
    return Entitlement.objects.create(
        user=user,
        source_type=EntitlementSourceType.ADMIN_GRANT,
        target_type=EntitlementTargetType.COURSE,
        target_id=str(course.id),
        status=EntitlementStatus.ACTIVE,
    )


def test_trainer_creates_student_submits_and_trainer_reviews_assignment():
    trainer = make_user("homework-trainer@example.com", role="trainer")
    student = make_user("homework-student@example.com")
    course, lesson = make_course()
    grant_course(user=student, course=course)

    trainer_client = APIClient()
    trainer_client.force_authenticate(user=trainer)
    create_response = trainer_client.post(
        "/api/v1/assignments/trainer/",
        {
            "title": "Record squat technique",
            "description": "Attach notes and self-review.",
            "content_type": EntitlementTargetType.COURSE,
            "content_id": str(course.id),
            "lesson_id": str(lesson.id),
            "status": AssignmentStatus.PUBLISHED,
        },
        format="json",
    )

    assert create_response.status_code == 201, create_response.data
    assignment_id = create_response.data["id"]

    student_client = APIClient()
    student_client.force_authenticate(user=student)
    list_response = student_client.get("/api/v1/assignments/student/")

    assert list_response.status_code == 200, list_response.data
    assert list_response.data["summary"]["total"] == 1
    assert list_response.data["items"][0]["id"] == assignment_id
    assert list_response.data["items"][0]["submission"] is None

    submit_response = student_client.post(
        f"/api/v1/assignments/student/{assignment_id}/submit/",
        {"answer_text": "Video link and training notes", "attachments": [{"url": "https://example.test/video"}]},
        format="json",
    )

    assert submit_response.status_code == 200, submit_response.data
    assert submit_response.data["submission"]["status"] == SubmissionStatus.SUBMITTED
    assert submit_response.data["submission"]["answer_text"] == "Video link and training notes"

    submissions_response = trainer_client.get("/api/v1/assignments/trainer/submissions/")
    assert submissions_response.status_code == 200, submissions_response.data
    submission_id = submissions_response.data["items"][0]["id"]

    review_response = trainer_client.post(
        f"/api/v1/assignments/trainer/submissions/{submission_id}/review/",
        {"status": SubmissionStatus.APPROVED, "review_comment": "Good control.", "score": "95.00"},
        format="json",
    )

    assert review_response.status_code == 200, review_response.data
    assert review_response.data["submission"]["status"] == SubmissionStatus.APPROVED
    assert review_response.data["submission"]["review_comment"] == "Good control."
    assert review_response.data["submission"]["score"] == "95.00"


def test_student_without_entitlement_cannot_see_or_submit_assignment():
    trainer = make_user("homework-deny-trainer@example.com", role="trainer")
    student = make_user("homework-deny-student@example.com")
    course, _lesson = make_course()
    assignment = Assignment.objects.create(
        trainer=trainer,
        title="Protected homework",
        content_type=EntitlementTargetType.COURSE,
        content_id=str(course.id),
        status=AssignmentStatus.PUBLISHED,
    )
    client = APIClient()
    client.force_authenticate(user=student)

    list_response = client.get("/api/v1/assignments/student/")
    submit_response = client.post(
        f"/api/v1/assignments/student/{assignment.id}/submit/",
        {"answer_text": "I should not pass"},
        format="json",
    )

    assert list_response.status_code == 200, list_response.data
    assert list_response.data["summary"]["total"] == 0
    assert submit_response.status_code == 403, submit_response.data
