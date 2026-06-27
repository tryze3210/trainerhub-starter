# v153 Premium Storefront Stabilization

v153 stabilizes the premium homepage foundation and extends the same visual direction to the public marketplace catalog.

Scope:

- homepage className/CSS contract stabilization;
- animated design-system primitive exports;
- reduced-motion fallback coverage;
- premium catalog hero;
- featured product section;
- premium marketplace product cards;
- frontend-only filter bar;
- loading, empty and error states;
- trust/access explanation panel.

Primary files:

- `frontend/src/app/page.tsx`
- `frontend/src/app/globals.css`
- `frontend/src/design-system/animated.tsx`
- `frontend/src/design-system/use-count-up.ts`
- `frontend/src/modules/public-storefront/components/marketplace-catalog-page.tsx`
- `frontend/src/modules/public-storefront/components/premium-marketplace-card.tsx`
- `frontend/tests/contracts/design-system-contract.test.js`

Status:

- v153 is complete as the premium storefront stabilization pass.
