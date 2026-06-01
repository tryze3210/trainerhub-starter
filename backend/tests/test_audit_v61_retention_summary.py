from __future__ import annotations

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent


@pytest.mark.django_db
def test_admin_can_view_audit_retention_summary_without_deleting_events():
    User = get_user_model()
    admin = User.objects.create_user(email='audit-admin@example.com', password='strong-pass-123', is_staff=True)
    regular = User.objects.create_user(email='audit-user@example.com', password='strong-pass-123')

    old_action = AuditEvent.objects.create(
        actor=admin,
        event_type='admin.referrals.csv_export',
        entity_type='referral_export',
        entity_id='rewards',
        context={'row_count': 10},
    )
    old_login = AuditEvent.objects.create(
        actor=regular,
        event_type='auth.login',
        entity_type='user',
        entity_id=str(regular.id),
        context={},
    )
    fresh_action = AuditEvent.objects.create(
        actor=admin,
        event_type='admin.audit.csv_export',
        entity_type='audit_export',
        entity_id='events',
        context={'row_count': 2},
    )

    AuditEvent.objects.filter(id=old_action.id).update(created_at=timezone.now() - timedelta(days=220))
    AuditEvent.objects.filter(id=old_login.id).update(created_at=timezone.now() - timedelta(days=210))
    AuditEvent.objects.filter(id=fresh_action.id).update(created_at=timezone.now() - timedelta(days=2))

    client = APIClient()
    client.force_authenticate(admin)

    response = client.get('/api/v1/audit/admin/retention/summary/?older_than_days=180')

    assert response.status_code == 200
    payload = response.json()
    assert payload['older_than_days'] == 180
    assert payload['total_matching_events'] == 3
    assert payload['stale_events'] == 2
    assert payload['oldest_created_at'] is not None
    assert payload['newest_created_at'] is not None
    assert payload['note'].startswith('Read-only summary')
    assert AuditEvent.objects.count() == 3

    counts_by_event_type = {row['event_type']: row['count'] for row in payload['by_event_type']}
    assert counts_by_event_type['admin.referrals.csv_export'] == 1
    assert counts_by_event_type['auth.login'] == 1


@pytest.mark.django_db
def test_audit_retention_summary_supports_filters_and_clamps_days():
    User = get_user_model()
    admin = User.objects.create_user(email='audit-admin@example.com', password='strong-pass-123', is_staff=True)

    export_event = AuditEvent.objects.create(
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
    AuditEvent.objects.filter(id__in=[export_event.id, payout_event.id]).update(
        created_at=timezone.now() - timedelta(days=40)
    )

    client = APIClient()
    client.force_authenticate(admin)

    response = client.get(
        '/api/v1/audit/admin/retention/summary/?older_than_days=0&event_type=admin.referrals.csv_export'
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['older_than_days'] == 1
    assert payload['total_matching_events'] == 1
    assert payload['stale_events'] == 1
    assert payload['filters'] == {'event_type': 'admin.referrals.csv_export'}
    assert payload['by_event_type'] == [{'event_type': 'admin.referrals.csv_export', 'count': 1}]


@pytest.mark.django_db
def test_audit_retention_summary_is_admin_only():
    User = get_user_model()
    regular = User.objects.create_user(email='regular@example.com', password='strong-pass-123')

    client = APIClient()
    client.force_authenticate(regular)

    response = client.get('/api/v1/audit/admin/retention/summary/')

    assert response.status_code == 403
