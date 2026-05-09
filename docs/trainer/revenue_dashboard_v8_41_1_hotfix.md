# v8.41.1 — Trainer revenue dashboard compatibility hotfix

This hotfix fixes v8.41 integration regressions against the current codebase:

- uses `common.permissions.IsTrainer` instead of the non-existing `apps.common.permissions` module;
- restores the existing trainer API view/serializer/service imports;
- removes `TrainerProfile.Status` usage because `TrainerProfile.status` is currently a plain string field;
- avoids non-existing `BalanceEntry.description`, `PayoutRequest.reviewed_at`, `paid_at`, `reject_reason`, and `notes` fields;
- keeps the v8.41 revenue endpoints unchanged:
  - `GET /api/v1/trainers/me/revenue/summary/`
  - `GET /api/v1/trainers/me/revenue/transactions/`
  - `GET /api/v1/trainers/me/revenue/payouts/`

No migrations are required.
