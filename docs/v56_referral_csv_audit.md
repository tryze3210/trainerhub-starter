# TrainerHub v56 — referral CSV export audit

## Цель

Закрыть audit trail для admin CSV exports в referral ops. После v54 CSV выгрузки уже доступны, но скачивание финансовых данных должно оставлять операторский след в `audit_event`.

## Изменения

- `AdminReferralRewardExportView` пишет audit event после успешной подготовки CSV.
- `AdminReferralLedgerExportView` пишет отдельный audit event.
- `AdminReferralInviteExportView` пишет отдельный audit event.
- В audit context сохраняются:
  - `export_kind`;
  - `filename`;
  - `row_count`;
  - `total_count`;
  - `limit`;
  - `truncated`;
  - применённые filters;
  - request metadata через `AuditService.log_admin_action`.

## Event contract

```text
AuditEvent.event_type = admin.referrals.csv_export
AuditEvent.entity_type = referral_export
AuditEvent.entity_id   = rewards | ledger | invites
```

## Проверка

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
pytest tests/test_referrals_v54_admin_csv_exports.py \
       tests/test_referrals_v56_admin_csv_audit.py -q
```

Миграции не добавляются.
