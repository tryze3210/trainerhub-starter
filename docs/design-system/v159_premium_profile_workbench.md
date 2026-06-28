# v159 - Premium Profile Workbench

v159 introduces the shared premium profile workbench layer for customer and trainer spaces.

Updated areas:

- Added `frontend/src/design-system/profile-workbench.tsx` with semantic workbench wrappers.
- Added `.profile-workbench-*` CSS contract for hero, horizontal nav, metrics, rails, wide editor panels and support panels.
- Customer cabinet shell now uses horizontal profile navigation instead of a left sidebar.
- Trainer cabinet shell now uses horizontal profile navigation instead of a left sidebar.
- Product builder and video studio use `profile-workbench` naming while preserving the horizontal workbench model.
- Learning and messages pages no longer use the old tight customer grid/message layout classes.

Verification:

- `npm run typecheck`
- `npm run test:contracts`
- `git diff --check`

`npm run build` remains blocked locally by `.next/trace` file permissions.
