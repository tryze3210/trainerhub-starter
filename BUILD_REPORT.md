# BUILD REPORT — TrainerHub v167.0

## Summary

- Current version: v167.0
- Goal: Production Optimization Foundation.
- Scope completed in this pass: baseline quality gates, backend dependency split, production Docker baseline, CSS layer decomposition, production env/security hardening, documentation update.

## Baseline File Sizes

Captured before changing large files:

```text
238755 frontend/src/app/globals.css
  6048 frontend/src/app/profile-workbench.css
  6535 frontend/src/app/trainer-operations.css
  7996 frontend/src/app/trainer-finance-analytics.css
  4122 frontend/src/lib/api-client.ts
   622 frontend/tsconfig.json
   514 backend/requirements.txt
   780 backend/pyproject.toml
  2997 docker-compose.yml
   463 deploy/backend/Dockerfile
   216 deploy/frontend/Dockerfile
269048 total
```

## v167.0 Baseline Quality Gate

Added:

- `scripts/quality/backend_check.sh`
- `scripts/quality/frontend_check.sh`
- `scripts/quality/full_check.sh`
- `make backend-check`
- `make frontend-check`
- `make full-check`

CI now calls the same quality scripts instead of duplicating backend/frontend commands inline.

Results in this workspace:

```text
bash -n scripts/quality/*.sh: passed
bash scripts/quality/backend_check.sh: failed at makemigrations --check --dry-run due existing migration drift
bash scripts/quality/frontend_check.sh: typecheck/contracts passed, build blocked by .next permission
bash scripts/quality/full_check.sh: stopped on backend migration drift
```

Backend gate details:

```text
python manage.py check: passed
python manage.py makemigrations --check --dry-run: failed, pending migrations reported for assignments, booking, cohorts, disputes, finance_documents, gamification, legal_compliance, progress, promotions, reviews
```

No migrations were generated automatically because v167 explicitly avoids blind schema/business changes.

Frontend gate details:

```text
npm ci: passed
npm run typecheck: passed
npm run test:contracts: passed
npm run build: failed before useful build output because frontend/.next/cache/.rscinfo is not writable by the active user
```

## Dependency Sync Result

- `backend/requirements.txt` now contains runtime dependencies only.
- `backend/requirements-dev.txt` contains pytest, mypy, flake8 and stubs.
- `backend/pyproject.toml` documents that production installs are driven by `requirements.txt` and aligns dev tooling metadata.
- CI backend dependency install uses `requirements.txt` + `requirements-dev.txt` before running the backend quality gate.

## Docker Result

- `deploy/backend/Dockerfile` is multi-stage with a wheel builder and non-root runtime user.
- `deploy/frontend/Dockerfile` builds Next standalone output and runs `node server.js`.
- `docker-compose.yml` no longer uses source bind mounts or postgres/redis host ports for production services.
- `docker-compose.dev.yml` contains dev ports and bind mounts.

Docker build was not run in this environment.

## CSS Size Before/After

Before:

```text
238755 frontend/src/app/globals.css
```

After v167 CSS layering:

```text
   459 frontend/src/app/globals.css
    95 frontend/src/styles/00-reset.css
   114 frontend/src/styles/01-tokens.css
   111 frontend/src/styles/02-layout.css
   119 frontend/src/styles/03-premium-shell.css
  7918 frontend/src/styles/04-public-storefront.css
   117 frontend/src/styles/05-customer-cabinet.css
 20643 frontend/src/styles/06-trainer-cabinet.css
   114 frontend/src/styles/07-admin-ops.css
238625 frontend/src/styles/08-components.css
   137 frontend/src/styles/09-responsive.css
268452 total
```

Additional layer files are present under `frontend/src/styles/`.

## Tests Result

Passed:

```bash
cd frontend
npm run typecheck
npm run test:contracts
git diff --check
backend/.venv/bin/python -m pytest backend/tests/test_production_env_v167.py -q
backend/.venv/bin/python backend/manage.py check
backend/.venv/bin/python -m flake8 backend/config/env.py backend/config/settings/base.py backend/tests/test_production_env_v167.py
```

Blocked / not fully passed:

- Backend full gate: blocked by pre-existing migration drift.
- Frontend build in workspace: blocked by `.next` ownership/permission.
- Docker compose build/up: not executed in this environment.

## Known Local Limitations

- API route matrix, frontend API client strict typing and backend performance baseline remain follow-up work for the next v167.x slices.
- `.next` cleanup requires correcting filesystem ownership outside this session.
- Migration drift must be resolved deliberately with review of affected apps.

## v167.4 Production Env/Security Hardening

Added:

- Central production environment validation in `backend/config/env.py`.
- Active Django settings integration in `backend/config/settings/base.py`.
- Explicit production requirements for `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS` and VK/S3 credentials.
- Cookie, SSL redirect, HSTS, content-type nosniff and frame protection defaults that become strict when `APP_ENV=production`.
- Regression coverage in `backend/tests/test_production_env_v167.py`.

This was implemented without changing the current sqlite fallback used by local/test settings.
