# TrainerHub v58 — admin audit filter hardening

## Scope

v58 strengthens the shared admin audit feed used by referral CSV export monitoring.

## Backend

`GET /api/v1/audit/admin/events/` now supports:

- `created_from=YYYY-MM-DD` or ISO datetime
- `created_to=YYYY-MM-DD` or ISO datetime
- `search=...`
- existing filters: `event_type`, `entity_type`, `entity_id`, `actor_id`, `limit`

The endpoint remains admin-only and keeps the maximum limit capped at `500` rows.

## Frontend API client

`frontend/src/modules/admin-audit/api.ts` now exposes the same filter fields in `AuditEventFilters`.

The admin audit page is not replaced in this patch. v58 only expands the API contract and the small TypeScript client used by both `/admin/audit` and `/admin/referrals`.

## Verification

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
pytest tests/test_audit_v58_admin_filters.py -q

cd ../frontend
npm run typecheck
npm run build
```
