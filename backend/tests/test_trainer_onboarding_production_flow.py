from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import AccountRoleAssignment
from apps.trainers.models import TrainerApplication, TrainerProfile

pytestmark = pytest.mark.django_db


def _create_user(email: str, *, is_admin: bool = False):
    User = get_user_model()
    if is_admin:
        return User.objects.create_superuser(email=email, password="pass12345")
    return User.objects.create_user(email=email, password="pass12345")


def _application_payload(**overrides):
    payload = {
        "brand_name": "Coach Flow",
        "legal_name": "Coach Flow LLC",
        "contact_phone": "+79990000000",
        "country": "RU",
        "city": "Moscow",
        "bio": "Strength and mobility trainer for remote clients.",
        "specialties": ["strength", "mobility"],
        "links": ["https://example.com/coach-flow"],
        "experience_years": 7,
    }
    payload.update(overrides)
    return payload


def test_customer_can_start_and_submit_trainer_application_before_trainer_role():
    user = _create_user("candidate@example.com")
    client = APIClient()
    client.force_authenticate(user=user)

    status_response = client.get(reverse("trainer-me-onboarding-status"))
    assert status_response.status_code == 200
    assert status_response.json()["dashboard_unlocked"] is False
    assert status_response.json()["application"]["status"] == TrainerApplication.Status.DRAFT

    patch_response = client.patch(reverse("trainer-me-application"), _application_payload(), format="json")
    assert patch_response.status_code == 200
    assert patch_response.json()["brand_name"] == "Coach Flow"

    submit_response = client.post(reverse("trainer-me-application-submit"), _application_payload(), format="json")
    assert submit_response.status_code == 202
    assert submit_response.json()["status"] == TrainerApplication.Status.UNDER_REVIEW

    state_response = client.get(reverse("trainer-me-application-status"))
    assert state_response.status_code == 200
    payload = state_response.json()
    assert payload["dashboard_unlocked"] is False
    assert payload["application"]["is_complete"] is True
    assert payload["summary"]["next_step"] in {"admin_review", "dashboard_unlock"}


def test_admin_can_approve_application_and_unlock_trainer_dashboard():
    candidate = _create_user("candidate-approve@example.com")
    admin = _create_user("admin-approve@example.com", is_admin=True)
    application = TrainerApplication.objects.create(
        user=candidate,
        status=TrainerApplication.Status.UNDER_REVIEW,
        **_application_payload(),
    )

    client = APIClient()
    client.force_authenticate(user=admin)

    list_response = client.get(reverse("trainer-admin-application-list"), {"status": TrainerApplication.Status.UNDER_REVIEW})
    assert list_response.status_code == 200
    assert list_response.json()["count"] >= 1

    review_response = client.post(
        reverse("trainer-admin-application-review", kwargs={"application_id": application.id}),
        {"decision": "approve", "reviewer_note": "Profile is valid."},
        format="json",
    )
    assert review_response.status_code == 200
    payload = review_response.json()
    assert payload["application"]["status"] == TrainerApplication.Status.APPROVED
    assert payload["onboarding_state"]["dashboard_unlocked"] is True

    candidate.refresh_from_db()
    assert candidate.role == get_user_model().Roles.TRAINER
    profile = TrainerProfile.objects.get(user=candidate)
    assert profile.status == "active"
    assert profile.is_public is True


def test_onboarding_unlock_uses_active_trainer_assignment_not_legacy_role():
    candidate = _create_user("candidate-assignment-unlock@example.com")
    application = TrainerApplication.objects.create(
        user=candidate,
        status=TrainerApplication.Status.APPROVED,
        **_application_payload(brand_name="Assigned Coach"),
    )
    TrainerProfile.objects.create(
        user=candidate,
        slug="assigned-coach",
        display_name="Assigned Coach",
        status="active",
        is_public=True,
    )
    AccountRoleAssignment.objects.create(
        user=candidate,
        role=AccountRoleAssignment.ROLE_TRAINER,
        is_active=True,
    )

    client = APIClient()
    client.force_authenticate(user=candidate)
    response = client.get(reverse("trainer-me-onboarding-status"))

    assert application.user.role == get_user_model().Roles.CUSTOMER
    assert response.status_code == 200
    assert response.json()["dashboard_unlocked"] is True
    assert response.json()["can_access_content_studio"] is True


def test_admin_reject_requires_reviewer_note():
    candidate = _create_user("candidate-reject@example.com")
    admin = _create_user("admin-reject@example.com", is_admin=True)
    application = TrainerApplication.objects.create(
        user=candidate,
        status=TrainerApplication.Status.UNDER_REVIEW,
        **_application_payload(brand_name="Reject Candidate"),
    )

    client = APIClient()
    client.force_authenticate(user=admin)
    response = client.post(
        reverse("trainer-admin-application-review", kwargs={"application_id": application.id}),
        {"decision": "reject"},
        format="json",
    )

    assert response.status_code == 400
    assert "reviewer_note" in response.json()


def test_non_admin_cannot_read_admin_trainer_applications():
    user = _create_user("not-admin@example.com")
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(reverse("trainer-admin-application-list"))

    assert response.status_code == 403
