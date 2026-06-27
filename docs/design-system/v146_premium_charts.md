# v146 Premium Charts

v146 adds premium chart primitives to the shared frontend design system.

Scope:

- reusable line chart for trend views;
- reusable donut chart for distribution views;
- insight chart card wrapper for dashboard metrics;
- responsive chart behavior for mobile screens;
- design-system contract coverage for the new chart classes and exports.

Primary files:

- `frontend/src/design-system/library.tsx`
- `frontend/src/app/globals.css`
- `frontend/tests/contracts/design-system-contract.test.js`

Implementation notes:

- Charts do not introduce a new runtime dependency.
- The components are presentational and do not own business logic.
- Colors use semantic design tokens and existing tone names.
- Mobile behavior keeps charts readable without horizontal layout overflow.

Status:

- v146 is complete at the shared component-library layer.
