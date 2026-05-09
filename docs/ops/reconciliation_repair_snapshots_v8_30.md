# v8.30 — reconciliation snapshot auto-capture after repair actions

## Цель

После любого успешного `admin/reconciliation-repair/` backend автоматически делает persisted snapshot `source=repair` и возвращает в ответе repair action краткую динамику проблем.

## Что меняется

- `ReconciliationRepairService.execute()` после audit log вызывает `capture_repair_reconciliation_snapshot()`.
- Snapshot создаётся с `source='repair'` и `correlation_id='repair:<audit_event_id>'`.
- Ответ repair endpoint теперь содержит:
  - `repair_snapshot`;
  - `reconciliation_snapshot_id`;
  - `reconciliation_snapshot_href`;
  - `previous_problem_count`;
  - `current_problem_count`;
  - `problem_delta`;
  - `improved`.
- Добавлен read endpoint latest snapshot:
  - `GET /api/v1/ops/admin/reconciliation-snapshots/latest/`
  - `GET /api/v1/ops/admin/reconciliation-snapshots/latest/?source=repair`

## Проверка

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
pytest -q tests/test_ops_reconciliation_repair_snapshot_autocapture.py
pytest -q
```
