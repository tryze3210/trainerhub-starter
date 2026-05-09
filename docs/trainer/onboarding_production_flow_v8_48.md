# v8.48 — Trainer onboarding production flow

## Goal

Turn trainer onboarding into a real production workflow:

1. A regular authenticated user can apply to become a trainer.
2. Admin reviews the application.
3. Approval grants trainer role, syncs legacy trainer profile and public trainer profile.
4. Trainer dashboard/content/product flow is unlocked only after approval.

## Backend endpoints

```http
GET  /api/v1/trainers/me/onboarding/status/
GET  /api/v1/trainers/me/application-status/
GET  /api/v1/trainers/me/application/
PATCH /api/v1/trainers/me/application/
POST /api/v1/trainers/me/application/submit/

GET  /api/v1/trainers/admin/applications/
GET  /api/v1/trainers/admin/applications/{application_id}/
POST /api/v1/trainers/admin/applications/{application_id}/review/
POST /api/v1/trainers/admin/applications/{application_id}/sync-access/
```

## Frontend routes

```text
/trainer/onboarding
/trainer/application-status
/admin/trainers/applications
```

## Admin decisions

```json
{ "decision": "approve", "reviewer_note": "Approved." }
{ "decision": "request_changes", "reviewer_note": "Add proof links and clearer positioning." }
{ "decision": "reject", "reviewer_note": "Rejected reason is required." }
{ "decision": "under_review", "reviewer_note": "Escalated for manual check." }
```

## Safety notes

- No migrations.
- Existing revenue and analytics trainer routes are preserved in `trainers/api/urls.py`.
- Approval delegates to the existing `TrainerApplicationService.apply_moderation_decision` and `sync_approved_application_access`.
- Reject/request changes require `reviewer_note`.
- Regular customer users can now submit trainer applications; trainer role is not required before approval.

## Verification

```bash
cd backend
python -m py_compile \
  apps/trainers/onboarding_flow.py \
  apps/trainers/api/onboarding_serializers.py \
  apps/trainers/api/onboarding_views.py \
  apps/trainers/api/urls.py \
  tests/test_trainer_onboarding_production_flow.py

python manage.py check
python manage.py makemigrations --check --dry-run
pytest -q tests/test_trainer_onboarding_production_flow.py
pytest -q tests/test_trainer_content_analytics.py
pytest -q tests/test_trainer_revenue_dashboard.py
pytest -q

cd ../frontend
npm run typecheck
npm run build
npm run test:contracts
```
