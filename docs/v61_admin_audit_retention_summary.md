# TrainerHub v61 — Admin audit retention summary

Adds a read-only admin endpoint for planning audit log retention safely.

## Endpoint

```text
GET /api/v1/audit/admin/retention/summary/
```

Supported query params:

- `older_than_days` — defaults to `180`, clamped to `1..3650`.
- `event_type`
- `entity_type`
- `entity_id`
- `actor_id`
- `created_from`
- `created_to`
- `search`

The endpoint returns:

- total matching audit events;
- stale events older than the cutoff;
- oldest/newest stale timestamps;
- top event types;
- top entity types;
- active filter snapshot.

This endpoint is intentionally read-only. It does not delete audit data and does not mutate `AuditEvent` rows.

## Verification

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
pytest tests/test_audit_v61_retention_summary.py -q
```
