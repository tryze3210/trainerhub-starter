import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.ops.runbooks import REQUIRED_RUNBOOKS, get_ops_runbook, get_ops_runbook_index


@pytest.mark.django_db
def test_v115_required_ops_runbooks_exist_and_have_sections():
    payload = get_ops_runbook_index(include_content=True)

    assert payload["status"] == "ready"
    assert payload["total"] == len(REQUIRED_RUNBOOKS)
    assert payload["missing"] == []
    keys = {item["key"] for item in payload["runbooks"]}
    assert keys == {item.key for item in REQUIRED_RUNBOOKS}
    for item in payload["runbooks"]:
        assert item["exists"] is True
        assert "## Triage" in item["content"]
        assert "## Verification" in item["content"]


@pytest.mark.django_db
def test_v115_ops_runbook_detail_returns_failed_webhook_playbook():
    payload = get_ops_runbook(key="failed_payment_webhook")

    assert payload["title"] == "Failed payment webhook"
    assert payload["incident_type"] == "payments"
    assert "PaymentWebhookEvent.status" in payload["content"]
    assert "Escalation" in payload["sections"]


@pytest.mark.django_db
def test_v115_ops_runbook_api_contracts():
    admin = get_user_model().objects.create_superuser(email="v115-admin@example.com", password="pass12345")
    client = APIClient()
    client.force_authenticate(user=admin)

    index_response = client.get("/api/v1/ops/admin/runbooks/")
    detail_response = client.get("/api/v1/ops/admin/runbooks/database_restore/")

    assert index_response.status_code == 200
    assert index_response.json()["status"] == "ready"
    assert detail_response.status_code == 200
    assert detail_response.json()["key"] == "database_restore"
    assert "Database restore" in detail_response.json()["content"]


@pytest.mark.django_db
def test_v115_ops_runbook_api_requires_auth():
    client = APIClient()

    response = client.get("/api/v1/ops/admin/runbooks/")

    assert response.status_code in {401, 403}
