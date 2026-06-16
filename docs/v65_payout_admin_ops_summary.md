# TrainerHub v65 — payout admin ops summary

Adds a read-only payout operations summary endpoint for platform owners and staff.

## Endpoint

```text
GET /api/v1/payouts/admin-ops/summary/
```

## Filters

```text
status
trainer_id
currency
created_from
created_to
limit
```

## Returned sections

- `summary` — payout counts, active payout exposure, ledger totals.
- `wallets` — current wallet exposure across matching trainers/currency.
- `payout_statuses` — amount/count buckets by normalized payout status.
- `ledger` — ledger buckets by entry type/status/direction.
- `reconciliation` — current payout reconciliation status and issue count.
- `recent_payouts` — newest payout requests in the filtered set.

The endpoint is read-only and does not move funds, repair balances, delete data, or transition payout requests.
