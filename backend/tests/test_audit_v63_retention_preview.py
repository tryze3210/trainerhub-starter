from __future__ import annotations

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent


@pytest.mark.django_db
def test_admin_can_preview_audit_retention_cleanup_without_deleting_events():
    User = get_user_model()
    admin = User.objects.create_user(email='audit-admin@example.com', password='strong-pass-123', is_staff=True)

    oldest = AuditEvent.objects.create(
        actor=admin,
        event_type='admin.referrals.csv_export',
        entity_type='referral_export',
        entity_id='rewards',
        context={'row_count': 10},
    )
    older = AuditEvent.objects.create(
        actor=admin,
        event_type='admin.audit.csv_export',
        entity_type='audit_export',
        entity_id='events',
        context={'row_count': 2},
    )
    fresh = AuditEvent.objects.create(
        actor=admin,
        event_type='auth.login',
        entity_type='user',
        entity_id=str(admin.id),
        context={},
    )

    AuditEvent.objects.filter(id=oldest.id).update(created_at=timezone.now() - timedelta(days=240))
    AuditEvent.objects.filter(id=older.id).update(created_at=timezone.now() - timedelta(days=220))
    AuditEvent.objects.filter(id=fresh.id).update(created_at=timezone.now() - timedelta(days=2))

    client = APIClient()
    client.force_authenticate(admin)

    response = client.get('/api/v1/audit/admin/retention/preview/?older_than_days=180&batch_size=1')

    assert response.status_code == 200
    payload = response.json()
    assert payload['mode'] == 'preview'
    assert payload['deletion_performed'] is False
    assert payload['older_than_days'] == 180
    assert payload['batch_size'] == 1
    assert payload['total_matching_events'] == 3
    assert payload['candidates_total'] == 2
    assert payload['preview_count'] == 1
    assert payload['has_more'] is True
    assert payload['events'][0]['id'] == str(oldest.id)
    assert payload['events'][0]['event_type'] == 'admin.referrals.csv_export'
    assert payload['events'][0]['actor_email'] == 'audit-admin@example.com'
    assert payload['note'].startswith('Read-only cleanup preview')
    assert AuditEvent.objects.count() == 3


@pytest.mark.django_db
def test_audit_retention_preview_supports_filters_and_clamps_batch_size():
    User = get_user_model()
    admin = User.objects.create_user(email='audit-admin@example.com', password='strong-pass-123', is_staff=True)

    referral_export = AuditEvent.objects.create(
        actor=admin,
        event_type='admin.referrals.csv_export',
        entity_type='referral_export',
        entity_id='ledger',
        context={},
    )
    payout_event = AuditEvent.objects.create(
        actor=admin,
        event_type='admin.payouts.approve',
        entity_type='payout_request',
        entity_id='payout-1',
        context={},
    )
    AuditEvent.objects.filter(id__in=[referral_export.id, payout_event.id]).update(
        created_at=timezone.now() - timedelta(days=60)
    )

    client = APIClient()
    client.force_authenticate(admin)

    response = client.get(
        '/api/v1/audit/admin/retention/preview/?older_than_days=30&batch_size=999999&search=referrals'
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['batch_size'] == 1000
    assert payload['filters'] == {'search': 'referrals'}
    assert payload['candidates_total'] == 1
    assert payload['preview_count'] == 1
    assert payload['events'][0]['id'] == str(referral_export.id)


@pytest.mark.django_db
def test_audit_retention_preview_is_admin_only():
    User = get_user_model()
    regular = User.objects.create_user(email='regular@example.com', password='strong-pass-123')

    client = APIClient()
    client.force_authenticate(regular)

    response = client.get('/api/v1/audit/admin/retention/preview/')

    assert response.status_code == 403
