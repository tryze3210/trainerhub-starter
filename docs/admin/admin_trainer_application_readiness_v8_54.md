# v8.54 — Admin trainer applications backend readiness hardening

This patch adds a production readiness layer for the trainer onboarding/application flow introduced in v8.48.

## Goals

- Detect approved trainer applications that did not unlock the trainer dashboard.
- Detect missing trainer role/profile sync after approval.
- Detect stale or incomplete review queue items.
- Detect weak audit metadata on rejected / changes requested / approved applications.
- Expose an admin-only readiness endpoint and management command.

## New endpoint

```http
GET /api/v1/trainers/admin/applications/readiness/
GET /api/v1/trainers/admin/applications/readiness/?limit=100&stale_after_days=14
GET /api/v1/trainers/admin/applications/readiness/?include_samples=false&include_recommendations=false
```

The endpoint is admin-only via `permissions.IsAdminUser`.

## New management command

```bash
python manage.py check_trainer_application_readiness --json
python manage.py check_trainer_application_readiness --json --fail-on-degraded
python manage.py check_trainer_application_readiness --stale-after-days 14 --limit 100
```

## Detected issue codes

- `approved_without_trainer_role`
- `approved_without_active_trainer_assignment`
- `approved_without_trainer_profile`
- `approved_profile_not_dashboard_ready`
- `review_queue_incomplete_application`
- `stale_trainer_application_review`
- `blocked_application_without_reviewer_note`
- `approved_application_without_reviewed_at`
- `duplicate_trainer_profile_slug`

## Files

```text
backend/apps/trainers/application_readiness.py
backend/apps/trainers/api/readiness_serializers.py
backend/apps/trainers/api/readiness_views.py
backend/apps/trainers/api/urls.py
backend/apps/trainers/management/commands/check_trainer_application_readiness.py
backend/tests/test_admin_trainer_application_readiness.py
docs/admin/admin_trainer_application_readiness_v8_54.md
```

## Smoke check

```bash
cd backend
python -m py_compile \
  apps/trainers/application_readiness.py \
  apps/trainers/api/readiness_serializers.py \
  apps/trainers/api/readiness_views.py \
  apps/trainers/api/urls.py \
  apps/trainers/management/commands/check_trainer_application_readiness.py \
  tests/test_admin_trainer_application_readiness.py

python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py check_trainer_application_readiness --json

pytest -q tests/test_admin_trainer_application_readiness.py
pytest -q tests/test_trainer_onboarding_production_flow.py
pytest -q
```
