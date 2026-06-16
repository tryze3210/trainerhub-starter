# v68 — payout admin frontend dashboard

This increment connects the existing `/admin/payouts` frontend surface to the payout admin-ops APIs introduced in v65-v67.

## New UI capabilities

- Read-only payout admin-ops summary.
- Wallet totals block.
- Payout status buckets.
- Payout ledger buckets.
- Recent admin-ops payout requests.
- Reconciliation snapshot block.
- CSV export buttons:
  - payout requests CSV;
  - payout ledger CSV.

## Backend dependencies

Requires the following endpoints from v65-v67:

- `GET /api/v1/payouts/admin-ops/summary/`
- `GET /api/v1/payouts/admin-ops/requests/export.csv`
- `GET /api/v1/payouts/admin-ops/ledger/export.csv`
- `GET /api/v1/payouts/admin-ops/reconciliation/snapshot/`

## Safety

No backend models, migrations, payout transition logic, ledger logic, wallet logic, or repair action logic are changed in this increment.
