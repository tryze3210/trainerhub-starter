from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        email="login-audit@example.com",
        password="strong-pass-123",
    )


@pytest.mark.django_db
def test_successful_login_writes_audit_event(user):
    client = APIClient()

    response = client.post(
        "/api/v1/auth/login/",
        {"email": "login-audit@example.com", "password": "strong-pass-123"},
        HTTP_USER_AGENT="pytest-browser",
        REMOTE_ADDR="203.0.113.10",
        format="json",
    )

    assert response.status_code == 200
    audit_event = AuditEvent.objects.get(event_type="auth.login", entity_id=str(user.id))
    assert audit_event.entity_type == "user"
    assert audit_event.context["status"] == "success"
    assert audit_event.context["email"] == "login-audit@example.com"
    assert audit_event.context["ip"] == "203.0.113.10"
    assert audit_event.context["user_agent"] == "pytest-browser"
    assert "password" not in audit_event.context


@pytest.mark.django_db
def test_successful_registration_writes_audit_event_without_password():
    client = APIClient()

    response = client.post(
        "/api/v1/auth/register/",
        {
            "email": "register-audit@example.com",
            "password": "strong-pass-123",
            "full_name": "Register Audit",
        },
        HTTP_USER_AGENT="pytest-browser",
        REMOTE_ADDR="203.0.113.12",
        format="json",
    )

    assert response.status_code == 201
    user = get_user_model().objects.get(email="register-audit@example.com")
    audit_event = AuditEvent.objects.get(event_type="auth.register", entity_id=str(user.id))
    assert audit_event.entity_type == "user"
    assert audit_event.context["status"] == "success"
    assert audit_event.context["email"] == "register-audit@example.com"
    assert audit_event.context["ip"] == "203.0.113.12"
    assert audit_event.context["user_agent"] == "pytest-browser"
    assert audit_event.context["referral_code_present"] is False
    assert "password" not in audit_event.context


@pytest.mark.django_db
def test_logout_writes_audit_event_without_token():
    client = APIClient()
    register_response = client.post(
        "/api/v1/auth/register/",
        {
            "email": "logout-audit@example.com",
            "password": "strong-pass-123",
            "full_name": "Logout Audit",
        },
        format="json",
    )
    assert register_response.status_code == 201
    refresh_token = register_response.json()["refresh_token"]
    user = get_user_model().objects.get(email="logout-audit@example.com")

    response = client.post(
        "/api/v1/auth/logout/",
        {"refresh_token": refresh_token},
        HTTP_USER_AGENT="pytest-browser",
        REMOTE_ADDR="203.0.113.13",
        format="json",
    )

    assert response.status_code == 200
    audit_event = AuditEvent.objects.get(event_type="auth.logout", entity_id=str(user.id))
    assert audit_event.context["status"] == "success"
    assert audit_event.context["ip"] == "203.0.113.13"
    assert audit_event.context["user_agent"] == "pytest-browser"
    assert "refresh_token" not in audit_event.context


@pytest.mark.django_db
def test_failed_logout_writes_audit_event_without_token():
    client = APIClient()

    response = client.post(
        "/api/v1/auth/logout/",
        {"refresh_token": "not-a-token"},
        HTTP_USER_AGENT="pytest-browser",
        REMOTE_ADDR="203.0.113.14",
        format="json",
    )

    assert response.status_code == 401
    audit_event = AuditEvent.objects.get(event_type="auth.logout_failed", entity_id="unknown")
    assert audit_event.context["status"] == "failed"
    assert audit_event.context["reason"] == "invalid_refresh_token"
    assert audit_event.context["ip"] == "203.0.113.14"
    assert "refresh_token" not in audit_event.context


@pytest.mark.django_db
def test_failed_login_writes_audit_event_without_password(user):
    client = APIClient()

    response = client.post(
        "/api/v1/auth/login/",
        {"email": "login-audit@example.com", "password": "wrong-pass"},
        HTTP_USER_AGENT="pytest-browser",
        REMOTE_ADDR="203.0.113.11",
        format="json",
    )

    assert response.status_code == 401
    audit_event = AuditEvent.objects.get(event_type="auth.login_failed", entity_id=str(user.id))
    assert audit_event.entity_type == "user"
    assert audit_event.context["reason"] == "invalid_password"
    assert audit_event.context["email"] == "login-audit@example.com"
    assert audit_event.context["ip"] == "203.0.113.11"
    assert "password" not in audit_event.context


@pytest.mark.django_db
def test_login_endpoint_has_dedicated_throttle(user):
    cache.clear()
    client = APIClient()
    payload = {"email": "login-audit@example.com", "password": "wrong-pass"}

    for _ in range(10):
        assert client.post("/api/v1/auth/login/", payload, REMOTE_ADDR="203.0.113.20", format="json").status_code == 401
    throttled = client.post("/api/v1/auth/login/", payload, REMOTE_ADDR="203.0.113.20", format="json")

    assert throttled.status_code == 429


@pytest.mark.django_db
def test_register_endpoint_has_dedicated_throttle():
    cache.clear()
    client = APIClient()
    payload = {"email": "not-an-email", "password": "strong-pass-123"}

    for _ in range(20):
        assert client.post("/api/v1/auth/register/", payload, REMOTE_ADDR="203.0.113.30", format="json").status_code == 400
    throttled = client.post("/api/v1/auth/register/", payload, REMOTE_ADDR="203.0.113.30", format="json")

    assert throttled.status_code == 429


@pytest.mark.django_db
def test_refresh_endpoint_has_dedicated_throttle():
    cache.clear()
    client = APIClient()

    for _ in range(60):
        assert client.post("/api/v1/auth/refresh/", {}, REMOTE_ADDR="203.0.113.40", format="json").status_code == 401
    throttled = client.post("/api/v1/auth/refresh/", {}, REMOTE_ADDR="203.0.113.40", format="json")

    assert throttled.status_code == 429
