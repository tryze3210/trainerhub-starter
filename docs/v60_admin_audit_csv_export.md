# TrainerHub v60 — admin audit CSV export

## Scope

Adds a CSV export for the admin audit feed.

New endpoint:

```text
GET /api/v1/audit/admin/events/export.csv
```

The endpoint uses the same filters as `/api/v1/audit/admin/events/`:

- `event_type`
- `entity_type`
- `entity_id`
- `actor_id`
- `created_from`
- `created_to`
- `search`

The CSV export is capped at 10,000 rows per request and writes a meta-audit event after successful export:

```text
event_type = admin.audit.csv_export
entity_type = audit_export
entity_id   = events
```

The frontend `/admin/audit` page now has CSV export actions that download the currently filtered audit feed.

## Files

- `backend/apps/audit/api/views.py`
- `backend/apps/audit/api/urls.py`
- `backend/tests/test_audit_v60_admin_csv_export.py`
- `frontend/src/modules/admin-audit/api.ts`
- `frontend/src/app/admin/audit/page.tsx`
- `frontend/tests/contracts/api-contract.test.js`

## Verification

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
pytest tests/test_audit_v58_admin_filters.py tests/test_audit_v60_admin_csv_export.py -q

cd ../frontend
npm run typecheck
npm run build
npm run test:contracts
```

No migrations are required.
