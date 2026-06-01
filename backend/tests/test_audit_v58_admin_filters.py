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
def test_admin_audit_feed_supports_date_range_and_search_filters():
    User = get_user_model()
    admin = User.objects.create_superuser(email='audit-admin-v58@example.com', password='strong-pass-123')
    actor = User.objects.create_user(email='csv-operator-v58@example.com', password='strong-pass-123')

    now = timezone.now()
    old_event = AuditEvent.objects.create(
        actor=actor,
        event_type='admin.referrals.csv_export',
        entity_type='referral_export',
        entity_id='rewards',
        context={'context': {'export_kind': 'rewards'}},
        ip_address='10.0.0.10',
        user_agent='pytest-old',
    )
    current_event = AuditEvent.objects.create(
        actor=actor,
        event_type='admin.referrals.csv_export',
        entity_type='referral_export',
        entity_id='ledger',
        context={'context': {'export_kind': 'ledger'}},
        ip_address='10.0.0.11',
        user_agent='pytest-current',
    )
    payout_event = AuditEvent.objects.create(
        actor=admin,
        event_type='admin.payout_risk_hold.release',
        entity_type='payout',
        entity_id='payout-v58',
        context={'context': {'reason': 'manual release'}},
        ip_address='10.0.0.12',
        user_agent='pytest-payout',
    )

    _set_created_at(old_event, now - timezone.timedelta(days=14))
    _set_created_at(current_event, now - timezone.timedelta(hours=1))
    _set_created_at(payout_event, now - timezone.timedelta(minutes=10))

    client = APIClient()
    client.force_authenticate(admin)

    response = client.get(
        '/api/v1/audit/admin/events/',
        {
            'event_type': 'admin.referrals.csv_export',
            'entity_type': 'referral_export',
            'created_from': (now - timezone.timedelta(days=1)).date().isoformat(),
            'search': 'ledger',
            'limit': 10,
        },
    )

    assert response.status_code == 200
    rows = response.json().get('results', response.json())
    assert [row['entity_id'] for row in rows] == ['ledger']
    assert rows[0]['actor_email'] == 'csv-operator-v58@example.com'


@pytest.mark.django_db
def test_admin_audit_feed_rejects_non_admin_users():
    User = get_user_model()
    user = User.objects.create_user(email='not-admin-audit-v58@example.com', password='strong-pass-123')
    AuditEvent.objects.create(event_type='admin.referrals.csv_export', entity_type='referral_export', entity_id='invites')

    client = APIClient()
    client.force_authenticate(user)

    response = client.get('/api/v1/audit/admin/events/', {'search': 'referral'})

    assert response.status_code == 403
