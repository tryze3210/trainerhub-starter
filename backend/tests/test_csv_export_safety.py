import csv
import io

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent
from common.csv_safe import csv_safe_value, spreadsheet_safe_value


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("=HYPERLINK(\"https://evil.test\")", "'=HYPERLINK(\"https://evil.test\")"),
        ("+SUM(1,2)", "'+SUM(1,2)"),
        ("-10+20", "'-10+20"),
        ("@cmd", "'@cmd"),
        ("ordinary", "ordinary"),
        ("", ""),
        (None, ""),
    ],
)
def test_csv_safe_value_escapes_formula_prefixes(raw, expected):
    assert csv_safe_value(raw) == expected


@pytest.mark.parametrize("raw", ["=HYPERLINK(\"https://evil.test\")", "+SUM(1,2)", "-10+20", "@cmd"])
def test_spreadsheet_safe_value_escapes_formula_strings(raw):
    assert spreadsheet_safe_value(raw) == f"'{raw}"


def test_spreadsheet_safe_value_preserves_non_string_values():
    assert spreadsheet_safe_value(123) == 123
    assert spreadsheet_safe_value(None) is None


@pytest.mark.django_db
def test_admin_audit_csv_export_escapes_formula_values():
    admin = get_user_model().objects.create_superuser(email='csv-safe-admin@example.com', password='pass12345')
    AuditEvent.objects.create(
        event_type='=audit.export',
        entity_type='audit_export',
        entity_id='=cmd|calc',
        user_agent='@evil-agent',
        context={'note': '+SUM(1,2)'},
    )
    client = APIClient()
    client.force_authenticate(admin)

    response = client.get('/api/v1/audit/admin/events/export.csv')

    assert response.status_code == 200
    rows = list(csv.DictReader(io.StringIO(response.content.decode('utf-8-sig'))))
    assert rows[0]['event_type'] == "'=audit.export"
    assert rows[0]['entity_id'] == "'=cmd|calc"
    assert rows[0]['user_agent'] == "'@evil-agent"
