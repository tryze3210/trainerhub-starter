# v132 — Layout System

This pass adds shared layout primitives for the redesign block.

## Scope

- Admin layout: sidebar shell, page header and section wrapper.
- Trainer layout: sidebar shell with trainer/accent tone.
- Student layout: optional sidebar and student/accent tone.
- Public layout: simple full-width content shell.
- Mobile layout: responsive sidebar collapse and sticky action bar.

## Files

- `frontend/src/design-system/layouts.tsx`
- `frontend/src/design-system/index.ts`
- `frontend/src/app/globals.css`
- `frontend/tests/contracts/design-system-contract.test.js`

## Primitives

- `DSShell`
- `DSAdminLayout`
- `DSTrainerLayout`
- `DSStudentLayout`
- `DSPublicLayout`
- `DSPageHeader`
- `DSSection`
- `DSLayoutNav`
- `DSMobileActionBar`

## Migration Rule

Feature screens should migrate to these primitives gradually. Business logic and API calls should stay inside feature modules; layout primitives own only page structure, navigation zones, mobile behavior and visual rhythm.
