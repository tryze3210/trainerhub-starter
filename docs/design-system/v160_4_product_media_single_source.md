# v160.4 — Product Media Single Source of Truth

v160.4 finishes the product media picker cleanup with the product builder as the only video library owner.

## Scope

- Added a safe `normalizeMediaVideos` helper for array and paginated video payloads.
- Kept `loadMediaVideos`, loading state and error state in `TrainerProductBuilderDashboard`.
- Passed the same `mediaVideos` collection into the media picker and selected media list.
- Removed local async ownership from media picker and selected media list.
- Added `videoById` lookup for selected media rendering.
- Added the missing `.trainer-product-media-picker-state` CSS surface.

## Verification

- `npm run typecheck`
- `npm run test:contracts`
- `git diff --check`
- `npm run build` is expected to run in CI; local workspace can be blocked by existing `.next/trace` ownership.
