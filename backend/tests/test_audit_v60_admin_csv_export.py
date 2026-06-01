import csv
import io

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent


def _set_created_at(event: AuditEvent, value):
    AuditEvent.objects.filter(pk=event.pk).update(created_at=value)
    event.refresh_from_db()
    return event


@pytest.mark.django_db
def test_admin_audit_csv_export_uses_filters_and_records_export_audit_event():
    User = get_user_model()
    admin = User.objects.create_superuser(email='audit-admin-v60@example.com', password='strong-pass-123')
    actor = User.objects.create_user(email='referral-operator-v60@example.com', password='strong-pass-123')

    now = timezone.now()
    old_event = AuditEvent.objects.create(
        actor=actor,
        event_type='admin.referrals.csv_export',
        entity_type='referral_export',
        entity_id='rewards',
        context={'context': {'export_kind': 'rewards'}},
        ip_address='10.60.0.1',
        user_agent='pytest-old-v60',
    )
    current_event = AuditEvent.objects.create(
        actor=actor,
        event_type='admin.referrals.csv_export',
        entity_type='referral_export',
        entity_id='ledger',
        context={'context': {'export_kind': 'ledger'}},
        ip_address='10.60.0.2',
        user_agent='pytest-current-v60',
    )
    AuditEvent.objects.create(
        actor=admin,
        event_type='admin.payout_risk_hold.release',
        entity_type='payout',
        entity_id='payout-v60',
        context={'context': {'reason': 'manual release'}},
        ip_address='10.60.0.3',
        user_agent='pytest-payout-v60',
    )

    _set_created_at(old_event, now - timezone.timedelta(days=10))
    _set_created_at(current_event, now - timezone.timedelta(minutes=10))

    client = APIClient()
    client.force_authenticate(admin)

    response = client.get(
        '/api/v1/audit/admin/events/export.csv',
        {
            'event_type': 'admin.referrals.csv_export',
            'entity_type': 'referral_export',
            'created_from': (now - timezone.timedelta(days=1)).date().isoformat(),
            'search': 'ledger',
        },
        HTTP_USER_AGENT='pytest-export-v60',
        HTTP_X_REQUEST_ID='corr-v60',
    )

    assert response.status_code == 200
    assert response['Content-Type'].startswith('text/csv')
    assert 'trainerhub-admin-audit-events.csv' in response['Content-Disposition']

    content = response.content.decode('utf-8-sig')
    rows = list(csv.DictReader(io.StringIO(content)))

    assert len(rows) == 1
    assert rows[0]['entity_id'] == 'ledger'
    assert rows[0]['actor_email'] == 'referral-operator-v60@example.com'
    assert 'export_kind' in rows[0]['context_json']

    export_event = AuditEvent.objects.get(event_type='admin.audit.csv_export')
    assert export_event.actor == admin
    assert export_event.entity_type == 'audit_export'
    assert export_event.entity_id == 'events'
    assert export_event.context['context']['row_count'] == 1
    assert export_event.context['context']['total_count'] == 1
    assert export_event.context['context']['truncated'] is False
    assert export_event.context['context']['filters']['search'] == 'ledger'
    assert export_event.context['request']['correlation_id'] == 'corr-v60'


@pytest.mark.django_db
def test_admin_audit_csv_export_rejects_non_admin_users():
    User = get_user_model()
    user = User.objects.create_user(email='not-admin-audit-export-v60@example.com', password='strong-pass-123')
    AuditEvent.objects.create(event_type='admin.referrals.csv_export', entity_type='referral_export', entity_id='invites')

    client = APIClient()
    client.force_authenticate(user)

    response = client.get('/api/v1/audit/admin/events/export.csv')

    assert response.status_code == 403
    assert not AuditEvent.objects.filter(event_type='admin.audit.csv_export').exists()
