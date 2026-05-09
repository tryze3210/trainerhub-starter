# v8.40 — Ops production readiness checkpoint

## Purpose

v8.40 closes the v8.30-v8.39 ops/reconciliation series with a non-mutating production readiness layer. It verifies that the admin operations surface is importable, routable and documented before the project moves to the next domain area.

This patch does not introduce migrations and does not execute repair, outbox dispatch, snapshot capture or snapshot pruning from the readiness endpoint.

## New backend endpoint

```http
GET /api/v1/ops/admin/operations-readiness/
GET /api/v1/ops/admin/operations-readiness/?include_commands=false&include_recommendations=false
```

The endpoint is admin-only and returns:

- readiness status;
- URL/API surface contracts;
- required Python symbols from v8.30-v8.40;
- management command availability;
- recommended smoke command suite;
- frontend/admin surface links;
- environment flags for scheduled snapshot capture, alerting and retention.

## New management command

```bash
python manage.py check_ops_readiness --json
python manage.py check_ops_readiness --json --fail-on-degraded
python manage.py check_ops_readiness --no-commands --no-recommendations
```

Use `--fail-on-degraded` in CI if the ops surface must block release when a required URL, service or command is missing.

## Production smoke suite

Run from `backend/`:

```bash
python -m py_compile \
  apps/ops/operations_readiness.py \
  apps/ops/operations_hub.py \
  apps/ops/reconciliation_snapshots.py \
  apps/ops/repair.py \
  apps/ops/tasks.py \
  apps/ops/api/views.py \
  apps/ops/api/urls.py

python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py check_ops_readiness --json --fail-on-degraded

pytest -q \
  tests/test_ops_admin_operations_readiness.py \
  tests/test_ops_admin_operations_hub.py \
  tests/test_ops_reconciliation_issue_registry.py \
  tests/test_ops_reconciliation_snapshot_alerting.py \
  tests/test_ops_reconciliation_repair_snapshot_autocapture.py
```

Run from `frontend/`:

```bash
npm run typecheck
npm run build
npm run test:contracts
```

## Expected release gate

A clean v8.40 release means:

- `operations-readiness` endpoint returns `status=ok`;
- `check_ops_readiness --fail-on-degraded` exits with code 0;
- backend ops/reconciliation targeted tests pass;
- frontend typecheck/build/contracts pass;
- no migration drift exists.

If status is `degraded` or `critical`, inspect `checks[]` in the payload. The service reports exactly which URL name, import symbol or management command is missing or mismatched.
