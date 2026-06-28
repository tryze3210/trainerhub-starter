# v160.3 — Product Media Picker Cleanup and CSS Layer Stabilization

v160.3 stabilizes the product media picker before CRM and schedule work.

## Scope

- Centralized product video library loading in the product builder.
- Removed duplicate `listMyVideos` calls from media picker and selected media list.
- Added shared `TrainerProductMediaVideo` helpers.
- Removed technical selected-media fallback labels.
- Added `profile-workbench.css` as the first extracted profile/workbench/media-picker CSS layer.
- Imported the extracted CSS from `globals.css`.
- Preserved no-nested-scroll behavior.

## Verification

- `npm run typecheck` passes.
- `npm run test:contracts` passes.
- `git diff --check` passes.
- `npm run build` is blocked in the local workspace by `EACCES` on `frontend/.next/trace`.
