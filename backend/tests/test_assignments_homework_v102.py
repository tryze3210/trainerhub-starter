from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.assignments.api.serializers import AssignmentSubmitSerializer
from apps.assignments.api.views import StudentAssignmentViewSet, TrainerAssignmentViewSet, TrainerSubmissionViewSet
from apps.assignments.models import Assignment, AssignmentStatus, SubmissionStatus
from apps.entitlements.models import Entitlement, EntitlementSourceType, EntitlementStatus, EntitlementTargetType
from apps.trainer_cms.models import CourseLessonDraft, PublishStatus, TrainerCourseDraft, TrainerProgramDraft


pytestmark = pytest.mark.django_db


def make_user(email, *, role="customer"):
    return get_user_model().objects.create_user(email=email, password="pass12345", role=role)


def test_assignment_write_actions_use_scoped_throttles(settings):
    assert settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["assignment_submit"] == "120/hour"
    assert settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["assignment_create"] == "60/hour"
    assert settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["assignment_review"] == "120/hour"
    assert StudentAssignmentViewSet.throttle_scope == "assignment_submit"
    assert TrainerAssignmentViewSet.throttle_scope == "assignment_create"
    assert TrainerSubmissionViewSet.throttle_scope == "assignment_review"
    assert "ScopedRateThrottle" in StudentAssignmentViewSet.get_throttles.__code__.co_names
    assert "ScopedRateThrottle" in TrainerAssignmentViewSet.get_throttles.__code__.co_names
    assert "ScopedRateThrottle" in TrainerSubmissionViewSet.get_throttles.__code__.co_names


def test_assignment_submission_attachment_validation_rejects_private_or_unexpected_payloads():
    local_url = AssignmentSubmitSerializer(
        data={
            "answer_text": "Local link",
            "attachments": [{"url": "http://127.0.0.1:8000/admin"}],
        }
    )
    unexpected_field = AssignmentSubmitSerializer(
        data={
            "answer_text": "Unexpected field",
            "attachments": [{"url": "https://example.test/file", "internal_path": "/etc/passwd"}],
        }
    )

    assert not local_url.is_valid()
    assert "attachments" in local_url.errors
    assert not unexpected_field.is_valid()
    assert "attachments" in unexpected_field.errors


def test_assignment_submission_attachment_validation_normalizes_allowed_payload():
    serializer = AssignmentSubmitSerializer(
        data={
            "answer_text": "Safe link",
            "attachments": [
                {
                    "url": "https://example.test/video",
                    "title": " Technique notes ",
                    "content_type": "video/mp4",
                    "size_bytes": "1024",
                }
            ],
        }
    )

    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["attachments"] == [
        {
            "url": "https://example.test/video",
            "title": "Technique notes",
            "content_type": "video/mp4",
            "size_bytes": 1024,
        }
    ]


def make_course(*, trainer_id=None):
    course = TrainerCourseDraft.objects.create(
        trainer_id=trainer_id or uuid4(),
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
    course, lesson = make_course(trainer_id=trainer.id)
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


def test_trainer_cannot_create_assignment_for_another_trainers_course():
    owner = make_user("homework-owner@example.com", role="trainer")
    trainer = make_user("homework-intruder@example.com", role="trainer")
    course, lesson = make_course(trainer_id=owner.id)
    client = APIClient()
    client.force_authenticate(user=trainer)

    response = client.post(
        "/api/v1/assignments/trainer/",
        {
            "title": "Wrong owner homework",
            "content_type": EntitlementTargetType.COURSE,
            "content_id": str(course.id),
            "lesson_id": str(lesson.id),
            "status": AssignmentStatus.PUBLISHED,
        },
        format="json",
    )

    assert response.status_code == 403, response.data
    assert Assignment.objects.count() == 0


def test_trainer_cannot_create_assignment_for_another_trainers_program():
    owner = make_user("homework-program-owner@example.com", role="trainer")
    trainer = make_user("homework-program-intruder@example.com", role="trainer")
    program = TrainerProgramDraft.objects.create(
        trainer_id=owner.id,
        title="Owner Program",
        slug="owner-program",
        status=PublishStatus.PUBLISHED,
    )
    client = APIClient()
    client.force_authenticate(user=trainer)

    response = client.post(
        "/api/v1/assignments/trainer/",
        {
            "title": "Wrong owner program homework",
            "content_type": EntitlementTargetType.PROGRAM,
            "content_id": str(program.id),
            "status": AssignmentStatus.PUBLISHED,
        },
        format="json",
    )

    assert response.status_code == 403, response.data
    assert Assignment.objects.count() == 0
