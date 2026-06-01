# v55 — referral admin CSV frontend

## Goal

Connect the v54 referral admin CSV export endpoints to the owner/admin UI.

## Scope

Frontend only.

Changed files:

- `frontend/src/modules/referrals/api.ts`
- `frontend/src/app/admin/referrals/page.tsx`
- `frontend/tests/contracts/api-contract.test.js`

## Behavior

The `/admin/referrals` page now contains a `CSV exports` card with three actions:

- `Rewards CSV`
- `Ledger CSV`
- `Invites CSV`

Each action sends the currently selected filters to the matching backend endpoint:

- `/api/v1/referrals/admin/rewards/export.csv`
- `/api/v1/referrals/admin/ledger/export.csv`
- `/api/v1/referrals/admin/invites/export.csv`

The downloader uses bearer auth from local storage and respects the backend `Content-Disposition` filename when present. If the response has no filename header, the frontend falls back to `trainerhub-referrals-{kind}-{YYYY-MM-DD}.csv`.

## Verification

```bash
cd frontend
npm run typecheck
npm run build
npm run test:contracts
```

A lightweight local check was also run against the copied contract file:

```bash
node frontend/tests/contracts/api-contract.test.js
```

Result:

```text
frontend contract routes ok
```

## Backend prerequisite

v54 must be applied before these buttons are useful in browser, because v54 introduced the CSV endpoints.
