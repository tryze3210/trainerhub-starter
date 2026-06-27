from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent
from apps.events.models import DomainEvent, OutboxMessage
from apps.observability.runtime import get_observability_runtime_snapshot
from apps.orders.models import Order, OrderStatus, OrderType
from apps.payments.models import Payment, PaymentProvider, PaymentStatus, PaymentWebhookEvent


def _user(email, role="customer"):
    return get_user_model().objects.create_user(email=email, password="pass12345", role=role)


def _payment(*, student, status=PaymentStatus.SUCCEEDED, marker="v114"):
    order = Order.objects.create(
        user=student,
        order_type=OrderType.ONE_TIME,
        status=OrderStatus.COMPLETED,
        currency="RUB",
        total_amount=Decimal("100.00"),
    )
    return Payment.objects.create(
        order=order,
        provider=PaymentProvider.MOCK,
        status=status,
        amount=Decimal("100.00"),
        currency="RUB",
        external_payment_id=f"pay-{marker}",
    )


def _dead_outbox(marker="v114"):
    event = DomainEvent.objects.create(
        event_type="observability.test",
        aggregate_type="test",
        aggregate_id=marker,
        idempotency_key=f"observability:{marker}",
        payload={"marker": marker},
    )
    return OutboxMessage.objects.create(
        event=event,
        topic="observability",
        status=OutboxMessage.Status.DEAD,
        attempts=10,
        last_error="boom",
    )


@pytest.mark.django_db
def test_v114_observability_runtime_reports_rates_and_alerts():
    student = _user("v114-student@example.com")
    payment_ok = _payment(student=student, marker="ok")
    payment_failed = _payment(student=student, status=PaymentStatus.FAILED, marker="failed")
    PaymentWebhookEvent.objects.create(
        provider=PaymentProvider.MOCK,
        event_type="payment.succeeded",
        external_event_id="v114-webhook-ok",
        payment=payment_ok,
        status=PaymentWebhookEvent.Status.PROCESSED,
        payload={},
    )
    PaymentWebhookEvent.objects.create(
        provider=PaymentProvider.MOCK,
        event_type="payment.failed",
        external_event_id="v114-webhook-failed",
        payment=payment_failed,
        status=PaymentWebhookEvent.Status.FAILED,
        payload={},
        error_message="provider error",
    )
    AuditEvent.objects.create(
        event_type="admin.payouts.repair_execution",
        entity_type="payout_repair_execution",
        entity_id="repair-v114",
        context={"repaired_count": 2, "manual_review_count": 1},
    )
    _dead_outbox()

    payload = get_observability_runtime_snapshot(window_hours=24)

    assert payload["overall_status"] in {"degraded", "critical"}
    assert payload["webhooks"]["failed"] == 1
    assert payload["webhooks"]["failure_rate"] == 50.0
    assert payload["payments"]["failed"] == 1
    assert payload["payout_repairs"]["repaired_count"] == 2
    assert payload["payout_repairs"]["manual_review_count"] == 1
    assert payload["background_jobs"]["outbox_failed_or_dead"] >= 1
    assert payload["admin_ops_alerts"]["total"] >= 1
    assert {item["key"] for item in payload["health_indicators"]} == {
        "webhooks",
        "payments",
        "payout_repairs",
        "background_jobs",
    }


@pytest.mark.django_db
def test_v114_observability_runtime_api_contracts():
    admin = get_user_model().objects.create_superuser(email="v114-admin@example.com", password="pass12345")
    client = APIClient()
    client.force_authenticate(user=admin)

    direct_response = client.get("/api/v1/observability/runtime/?window_hours=24")
    ops_response = client.get("/api/v1/ops/admin/observability-runtime/?window_hours=24")

    assert direct_response.status_code == 200
    assert ops_response.status_code == 200
    assert "webhooks" in direct_response.json()
    assert "admin_ops_alerts" in ops_response.json()


@pytest.mark.django_db
def test_v114_observability_runtime_api_requires_auth():
    client = APIClient()

    response = client.get("/api/v1/observability/runtime/")

    assert response.status_code in {401, 403}
