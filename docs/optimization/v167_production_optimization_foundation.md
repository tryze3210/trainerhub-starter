# v167.0 Production Optimization Foundation

## What Changed

- Added shared local/CI quality gates in `scripts/quality`.
- Split backend runtime and dev dependencies into `requirements.txt` and `requirements-dev.txt`.
- Reworked backend Dockerfile into a multi-stage runtime image without build tooling.
- Reworked frontend Dockerfile to build and run Next standalone output.
- Moved dev bind mounts and service ports into `docker-compose.dev.yml`.
- Split frontend CSS entrypoint into explicit files under `frontend/src/styles`.
- Added CSS layer contract coverage.

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
- Backend quality gate: blocked by existing migration drift at `makemigrations --check --dry-run`.
- Frontend build: blocked locally by stale `.next` ownership/permissions.

## Known Limitations

- The CSS split is a production structure foundation. Some selectors remain mechanically grouped in `08-components.css`; future passes should move namespaces into narrower layers or CSS Modules.
- Docker build was not completed in this session.
- Env/security hardening, frontend API strict typing and backend performance baseline should be completed in follow-up v167.x slices.

## Next Stage v168

- Resolve migration drift.
- Finish production env readiness checks and tests.
- Move route-specific frontend CSS into route/module chunks where safe.
- Add API route matrix and remove verified redundant fallback paths.
