# v167.0 Production Optimization Foundation

## What Changed

- Added shared local/CI quality gates in `scripts/quality`.
- Split backend runtime and dev dependencies into `requirements.txt` and `requirements-dev.txt`.
- Reworked backend Dockerfile into a multi-stage runtime image without build tooling.
- Reworked frontend Dockerfile to build and run Next standalone output.
- Moved dev bind mounts and service ports into `docker-compose.dev.yml`.
- Split frontend CSS entrypoint into explicit files under `frontend/src/styles`.
- Added CSS layer contract coverage.
- Added production env/security validation and active Django settings integration.

## What Was Not Touched

- Payments, payouts and entitlements business logic.
- Response contracts and public API behavior.
- Existing legacy modules.
- Database migrations were not generated automatically.

## Verification Commands

```bash
bash scripts/quality/backend_check.sh
bash scripts/quality/frontend_check.sh
bash scripts/quality/full_check.sh

cd frontend
npm run typecheck
npm run test:contracts
```

## Results

- Frontend typecheck: passed.
- Frontend contracts: passed.
- Backend `manage.py check`: passed.
- Backend production env tests: passed.
- Backend changed-file flake8: passed.
- Backend quality gate: blocked by existing migration drift at `makemigrations --check --dry-run`.
- Frontend build: blocked locally by stale `.next` ownership/permissions.

## Known Limitations

- The CSS split is a production structure foundation. Some selectors remain mechanically grouped in `08-components.css`; future passes should move namespaces into narrower layers or CSS Modules.
- Docker build was not completed in this session.
- Frontend API strict typing and backend performance baseline should be completed in follow-up v167.x slices.

## v167.4 Env/Security Slice

Production mode now fails early when the environment is unsafe:

- `DEBUG=1` is rejected for `APP_ENV=production`.
- Placeholder or short `SECRET_KEY` values are rejected.
- Wildcard or empty `ALLOWED_HOSTS` is rejected.
- Empty `CSRF_TRUSTED_ORIGINS` or `CORS_ALLOWED_ORIGINS` is rejected.
- Missing placeholder VK/S3 credentials are rejected.

The active `config.settings.base` keeps local/test defaults intact, but applies strict cookie, SSL redirect, HSTS, nosniff and frame protection defaults in production.

## Next Stage v168

- Resolve migration drift.
- Move route-specific frontend CSS into route/module chunks where safe.
- Add API route matrix and remove verified redundant fallback paths.
