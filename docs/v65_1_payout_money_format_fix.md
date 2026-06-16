# v65.1 — payout money format fix

Fixes payout admin ops summary monetary serialization.

## Problem

`Decimal("250.00")` aggregated by Django/PostgreSQL could be serialized as `"250"` when converted with `str(value)`. The v65 contract expects stable money strings with two decimal places, e.g. `"250.00"`.

## Change

`backend/apps/payouts/ops_selectors.py` now formats all payout ops money values through `Decimal.quantize(Decimal("0.01"))`.

Affected fields include:

- `summary.total_payout_amount`
- `summary.active_payout_amount`
- `summary.ledger_entry_amount`
- `wallets.available_amount`
- `wallets.pending_amount`
- `wallets.locked_amount`
- payout status bucket amounts
- ledger bucket amounts
- recent payout amounts

No migrations.
