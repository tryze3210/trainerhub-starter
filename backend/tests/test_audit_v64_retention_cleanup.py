from __future__ import annotations

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent


def _age_event(event: AuditEvent, *, days: int) -> AuditEvent:
    AuditEvent.objects.filter(id=event.id).update(created_at=timezone.now() - timedelta(days=days))
    event.refresh_from_db()
    return event


@pytest.mark.django_db
def test_audit_retention_cleanup_requires_explicit_confirmation():
    User = get_user_model()
    admin = User.objects.create_user(email='audit-admin-v64@example.com', password='strong-pass-123', is_staff=True)

    old_event = AuditEvent.objects.create(
        actor=admin,
        event_type='admin.referrals.csv_export',
        entity_type='referral_export',
        entity_id='rewards',
        context={},
    )
    _age_event(old_event, days=220)

    client = APIClient()
    client.force_authenticate(admin)

    response = client.post('/api/v1/audit/admin/retention/cleanup/', {'older_than_days': 180}, format='json')

    assert response.status_code == 400
    payload = response.json()
    assert payload['mode'] == 'cleanup'
    assert payload['deletion_performed'] is False
    assert payload['deleted_count'] == 0
    assert 'Confirmation required' in payload['error']
    assert AuditEvent.objects.filter(id=old_event.id).exists()
    assert not AuditEvent.objects.filter(event_type='admin.audit.retention.cleanup').exists()


@pytest.mark.django_db
def test_admin_can_cleanup_old_audit_events_in_bounded_batch_and_records_audit_event():
    User = get_user_model()
    admin = User.objects.create_user(email='audit-admin-v64@example.com', password='strong-pass-123', is_staff=True)

    old_first = AuditEvent.objects.create(
        actor=admin,
        event_type='admin.referrals.csv_export',
        entity_type='referral_export',
        entity_id='rewards',
        context={'row_count': 10},
    )
    old_second = AuditEvent.objects.create(
        actor=admin,
        event_type='admin.audit.csv_export',
        entity_type='audit_export',
        entity_id='events',
        context={'row_count': 2},
    )
    old_third = AuditEvent.objects.create(
        actor=admin,
        event_type='admin.payouts.approve',
        entity_type='payout_request',
        entity_id='payout-v64',
        context={},
    )
    fresh = AuditEvent.objects.create(
        actor=admin,
        event_type='auth.login',
        entity_type='user',
        entity_id=str(admin.id),
        context={},
    )

    _age_event(old_first, days=240)
    _age_event(old_second, days=230)
    _age_event(old_third, days=220)
    _age_event(fresh, days=2)

    client = APIClient()
    client.force_authenticate(admin)

    response = client.post(
        '/api/v1/audit/admin/retention/cleanup/',
        {'confirm': True, 'older_than_days': 180, 'batch_size': 2},
        format='json',
        HTTP_USER_AGENT='pytest-cleanup-v64',
        HTTP_X_REQUEST_ID='corr-cleanup-v64',
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['mode'] == 'cleanup'
    assert payload['deletion_performed'] is True
    assert payload['older_than_days'] == 180
    assert payload['batch_size'] == 2
    assert payload['total_matching_events'] == 4
    assert payload['candidates_total'] == 3
    assert payload['deleted_count'] == 2
    assert payload['has_more'] is True
    assert payload['audit_event_id']

    assert not AuditEvent.objects.filter(id=old_first.id).exists()
    assert not AuditEvent.objects.filter(id=old_second.id).exists()
    assert AuditEvent.objects.filter(id=old_third.id).exists()
    assert AuditEvent.objects.filter(id=fresh.id).exists()

    cleanup_event = AuditEvent.objects.get(event_type='admin.audit.retention.cleanup')
    assert cleanup_event.actor == admin
    assert cleanup_event.entity_type == 'audit_retention'
    assert cleanup_event.entity_id == 'cleanup'
    assert cleanup_event.context['context']['deleted_count'] == 2
    assert cleanup_event.context['context']['candidates_total'] == 3
    assert cleanup_event.context['context']['has_more'] is True
    assert cleanup_event.context['request']['correlation_id'] == 'corr-cleanup-v64'
    assert cleanup_event.user_agent == 'pytest-cleanup-v64'


@pytest.mark.django_db
def test_audit_retention_cleanup_respects_filters_and_never_deletes_fresh_events():
    User = get_user_model()
    admin = User.objects.create_user(email='audit-admin-v64@example.com', password='strong-pass-123', is_staff=True)

    old_referral = AuditEvent.objects.create(
        actor=admin,
        event_type='admin.referrals.csv_export',
        entity_type='referral_export',
        entity_id='ledger',
        context={},
    )
    old_payout = AuditEvent.objects.create(
        actor=admin,
        event_type='admin.payouts.approve',
        entity_type='payout_request',
        entity_id='payout-v64',
        context={},
    )
    fresh_referral = AuditEvent.objects.create(
        actor=admin,
        event_type='admin.referrals.csv_export',
        entity_type='referral_export',
        entity_id='fresh-ledger',
        context={},
    )

    _age_event(old_referral, days=80)
    _age_event(old_payout, days=80)
    _age_event(fresh_referral, days=2)

    client = APIClient()
    client.force_authenticate(admin)

    response = client.post(
        '/api/v1/audit/admin/retention/cleanup/',
        {
            'confirm': 'true',
            'older_than_days': 30,
            'batch_size': 100,
            'event_type': 'admin.referrals.csv_export',
        },
        format='json',
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['deleted_count'] == 1
    assert payload['filters'] == {'event_type': 'admin.referrals.csv_export'}

    assert not AuditEvent.objects.filter(id=old_referral.id).exists()
    assert AuditEvent.objects.filter(id=old_payout.id).exists()
    assert AuditEvent.objects.filter(id=fresh_referral.id).exists()


@pytest.mark.django_db
def test_audit_retention_cleanup_is_admin_only():
    User = get_user_model()
    regular = User.objects.create_user(email='regular-v64@example.com', password='strong-pass-123')

    client = APIClient()
    client.force_authenticate(regular)

    response = client.post('/api/v1/audit/admin/retention/cleanup/', {'confirm': True}, format='json')

    assert response.status_code == 403
