# TrainerHub v57 — referral export audit frontend

## Purpose

v56 writes audit events for referral CSV exports. v57 surfaces those audit events directly on `/admin/referrals`, so platform owner/admin can validate who exported rewards, ledger and invites without leaving the referral operations workflow.

## Scope

- Adds a `Recent CSV export audit` block to `/admin/referrals`.
- Loads latest audit events through existing `adminAuditApi.listEvents()`.
- Filters audit events by:
  - `event_type=admin.referrals.csv_export`
  - `entity_type=referral_export`
  - `limit=25`
- Refreshes the audit block immediately after a successful CSV download.
- Keeps the general `/admin/audit` page untouched.

## Files

- `frontend/src/app/admin/referrals/page.tsx`

## Requirements

Requires previous packs:

- v52 backend referral admin ops API
- v54 backend referral CSV exports
- v55 frontend CSV buttons
- v56 backend CSV audit logging

## Verification

```bash
cd frontend
npm run typecheck
npm run build
npm run test:contracts
```

No backend migrations are required.
