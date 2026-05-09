# v8.42 — Trainer payout request flow

This patch exposes the existing payout domain service through production-facing API endpoints and adds a trainer dashboard page for payout requests.

## Backend endpoints

Trainer scope:

- `GET /api/v1/payouts/my/balance/`
- `GET /api/v1/payouts/my/`
- `GET /api/v1/payouts/my/<payout_id>/`
- `POST /api/v1/payouts/my/request/`

Admin scope:

- `GET /api/v1/payouts/admin/overview/`
- `GET /api/v1/payouts/admin/`
- `GET /api/v1/payouts/admin/<payout_id>/`
- `POST /api/v1/payouts/admin/<payout_id>/approve/`
- `POST /api/v1/payouts/admin/<payout_id>/processing/`
- `POST /api/v1/payouts/admin/<payout_id>/mark-paid/`
- `POST /api/v1/payouts/admin/<payout_id>/reject/`
- `POST /api/v1/payouts/admin/<payout_id>/transition/`

## Flow

1. Trainer requests payout.
2. Amount is moved from `TrainerWallet.available_amount` to `TrainerWallet.locked_amount`.
3. A `BalanceEntry(entry_type=reserve, direction=debit)` is created.
4. Admin approves, moves to processing, then marks paid.
5. On paid, locked balance is consumed and a payout ledger entry is created.
6. On reject, locked balance is released back to available balance.

## Settings

Optional setting:

```python
TRAINERHUB_MIN_PAYOUT_AMOUNT = "100.00"
```

No migrations are required. The patch uses existing `TrainerWallet`, `BalanceEntry`, `PayoutRequest`, and `PayoutService`.
