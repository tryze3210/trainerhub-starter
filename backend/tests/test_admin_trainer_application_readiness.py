from __future__ import annotations

import json
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APIClient

from apps.trainers.application_readiness import build_trainer_application_readiness
from apps.trainers.models import TrainerApplication

pytestmark = pytest.mark.django_db


def _create_user(email: str, *, is_admin: bool = False):
    User = get_user_model()
    if is_admin:
        return User.objects.create_superuser(email=email, password="pass12345")
    return User.objects.create_user(email=email, password="pass12345")


def _application_payload(**overrides):
    payload = {
        "brand_name": "Readiness Coach",
        "legal_name": "Readiness Coach LLC",
        "contact_phone": "+79990001122",
        "country": "RU",
        "city": "Moscow",
        "bio": "Strength coaching and mobility training.",
        "specialties": ["strength", "mobility"],
        "links": ["https://example.com/readiness-coach"],
        "experience_years": 5,
    }
    payload.update(overrides)
    return payload


def test_trainer_application_readiness_detects_approved_access_gap():
    candidate = _create_user("approved-gap@example.com")
    TrainerApplication.objects.create(
        user=candidate,
        status=TrainerApplication.Status.APPROVED,
        **_application_payload(),
    )

    payload = build_trainer_application_readiness(include_samples=False)

    assert payload["status"] == "degraded"
    codes = {issue["code"] for issue in payload["issues"]}
    assert "approved_without_trainer_role" in codes
    assert "approved_without_trainer_profile" in codes
    assert payload["summary"]["approved_count"] == 1
    assert payload["summary"]["dashboard_ready_count"] == 0


def test_admin_can_read_trainer_application_readiness_endpoint():
    candidate = _create_user("readiness-candidate@example.com")
    admin = _create_user("readiness-admin@example.com", is_admin=True)
    TrainerApplication.objects.create(
        user=candidate,
        status=TrainerApplication.Status.UNDER_REVIEW,
        **_application_payload(),
    )

    client = APIClient()
    client.force_authenticate(user=admin)
    response = client.get(reverse("trainer-admin-application-readiness"), {"limit": 10})

    assert response.status_code == 200
    payload = response.json()
    assert "summary" in payload
    assert payload["summary"]["review_queue_count"] >= 1
    assert payload["api_surface"]["admin"]


def test_trainer_application_readiness_endpoint_is_admin_only():
    user = _create_user("readiness-not-admin@example.com")
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(reverse("trainer-admin-application-readiness"))

    assert response.status_code == 403


def test_check_trainer_application_readiness_management_command_outputs_json():
    out = StringIO()

    call_command("check_trainer_application_readiness", "--json", stdout=out)

    payload = json.loads(out.getvalue())
    assert "status" in payload
    assert "summary" in payload
    assert "checks" in payload
