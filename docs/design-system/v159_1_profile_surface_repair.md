# v159.1 — Premium Profile Background and Surface Repair

v159.1 fixes the visual surface layer for profile workbench pages without changing backend contracts or public storefront pages.

## Scope

- Added a profile-specific dark scene through `.premium-main:has(.profile-workbench)`.
- Added fallback dark surfaces on `.profile-workbench-customer`, `.profile-workbench-trainer`, and `.profile-workbench-admin`.
- Strengthened hero, navigation, metrics, rails, panels, editor sections, form controls, buttons, and support panels.
- Kept the horizontal profile navigation model from v159.
- Added contract checks for the full `profile-workbench-*` CSS surface set.

## Verification

- `npm run typecheck`
- `npm run build`
- `npm run test:contracts`
