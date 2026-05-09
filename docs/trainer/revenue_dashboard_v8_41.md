# v8.41 — Trainer revenue dashboard

## Goal

Give approved trainers a production-grade read-only revenue dashboard before payout request automation is expanded in v8.42.

## Backend

New endpoints:

```http
GET /api/v1/trainers/me/revenue/summary/?days=30
GET /api/v1/trainers/me/revenue/transactions/?limit=100
GET /api/v1/trainers/me/revenue/payouts/?limit=100
```

The implementation is read-only and uses existing payout domain models:

- `TrainerWallet`
- `BalanceEntry`
- `PayoutRequest`
- `TrainerProfile`

No migrations are required.

## Revenue semantics

The payout ledger stores trainer-side net entries. Where provider gross price snapshots are not present on ledger rows, `gross_sales` and `platform_commission` are estimated from net revenue using:

- `TRAINERHUB_DEFAULT_PLATFORM_COMMISSION_RATE`, or
- `GLOBAL_COMMISSION_RATE`, or
- default `20%`.

This keeps the trainer dashboard useful now without corrupting accounting history. Later checkout/order hardening should persist explicit gross/commission snapshots per sale.

## Frontend

New page:

```text
/trainer/dashboard/revenue
```

It displays:

- net revenue;
- estimated gross sales;
- platform commission;
- available payout;
- pending payout;
- refunds;
- chargebacks;
- wallet balances;
- top revenue sources;
- recent ledger transactions;
- payout requests.

No new npm packages are required.

## Verification

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
pytest -q tests/test_trainer_revenue_dashboard.py
pytest -q

cd ../frontend
npm run typecheck
npm run build
npm run test:contracts
```
