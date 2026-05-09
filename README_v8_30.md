# TrainerHub v8.30 — reconciliation repair snapshot auto-capture

Патч собран под текущий публичный репозиторий `tryze3210/trainerhub-starter` на ветке `master`.

## Что уже есть в репозитории

В текущем коде `backend/apps/ops` уже есть:

- `ReconciliationSnapshot`;
- `ReconciliationSnapshot.Source.REPAIR`;
- ручной snapshot capture endpoint;
- repair endpoint `admin/reconciliation-repair/`;
- reconciliation report service.

Но repair action сейчас возвращает только результат repair + audit, без автоматического persisted snapshot после действия.

## Что делает v8.30

1. После успешного `run_reconciliation_repair()` автоматически создаётся `ReconciliationSnapshot(source='repair')`.
2. Snapshot получает `correlation_id='repair:<audit_event_id>'`.
3. Ответ repair endpoint сразу содержит:
   - `repair_snapshot`;
   - `reconciliation_snapshot_id`;
   - `reconciliation_snapshot_href`;
   - `previous_problem_count`;
   - `current_problem_count`;
   - `problem_delta`;
   - `improved`.
4. Добавляется endpoint latest snapshot:
   - `GET /api/v1/ops/admin/reconciliation-snapshots/latest/`
   - `GET /api/v1/ops/admin/reconciliation-snapshots/latest/?source=repair`
5. Snapshot capture не откатывает уже выполненный repair: если snapshot упал, repair response вернётся с `repair_snapshot.status='failed'`.

## Установка

Скопируй архив в корень проекта и выполни:

```bash
unzip trainerhub_v8_30_repo_specific_reconciliation_repair_snapshot_autocapture.zip
python scripts/apply_v8_30_reconciliation_repair_snapshot_autocapture.py
```

## Проверка

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
pytest -q tests/test_ops_reconciliation_repair_snapshot_autocapture.py
pytest -q
```

## Проверка API вручную

```bash
curl -X POST http://127.0.0.1:8000/api/v1/ops/admin/reconciliation-repair/ \
  -H "Authorization: Bearer <ADMIN_ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "retry_outbox",
    "entity_type": "outbox_message",
    "entity_id": "<OUTBOX_MESSAGE_ID>",
    "reason": "v8.30 smoke test"
  }'
```

В ответе должны появиться поля `repair_snapshot`, `problem_delta`, `improved` и `reconciliation_snapshot_href`.
