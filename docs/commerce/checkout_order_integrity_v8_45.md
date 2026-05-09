# v8.45 — Checkout / order integrity hardening

This patch hardens checkout without database migrations.

## Main changes

- one-time and subscription checkout now use an integrity-aware service;
- repeated checkout requests reuse the same pending order/payment by `idempotency_key` or canonical fingerprint;
- `OrderItem.metadata.checkout_integrity` stores a stable snapshot;
- `Payment.provider_payload.checkout_integrity` mirrors the payment-facing snapshot;
- checkout responses expose `checkout_integrity` and return `200` when an existing pending order/payment is reused.

## Stored snapshot

The snapshot includes:

- schema version `v8.45`;
- idempotency key;
- canonical checkout fingerprint;
- requested price payload;
- resolved price payload;
- commission snapshot;
- provider reuse flags.

## Why no migration

Existing tables already have safe JSON extension points:

- `OrderItem.metadata`;
- `Payment.provider_payload`.

That is enough for production reconciliation, support and audit while keeping rollout safe.

## Check

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
pytest -q tests/test_checkout_order_integrity.py
pytest -q
```
