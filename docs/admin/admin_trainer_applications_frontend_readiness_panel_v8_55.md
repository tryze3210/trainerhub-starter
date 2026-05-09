# v8.55 — Admin trainer applications frontend readiness panel

This patch adds a frontend readiness panel to the admin trainer applications screen.

## Scope

- Adds API types and client method for `GET /api/v1/trainers/admin/applications/readiness/`.
- Adds a readiness panel to `/admin/trainers/applications` through the existing `AdminTrainerApplicationsDashboard` component.
- Keeps the backend from v8.54 untouched.
- Keeps trainer onboarding candidate pages untouched.

## UI behavior

The admin can now see:

- overall readiness status;
- total applications;
- review queue count;
- approved vs dashboard-ready trainers;
- critical/warning/info counts;
- checks for review queue, access sync, slug integrity and review audit metadata;
- readiness issues with remediation text;
- one-click sync-access for approved access/profile gaps.

## Safety

This is frontend-only and additive. It does not alter Django models, migrations, payout logic, subscription logic, onboarding backend review logic, or existing trainer dashboard routes.

## Verification

```bash
cd frontend
npm run typecheck
npm run build
node tests/contracts/admin-trainer-applications-readiness-contract.test.js
```
