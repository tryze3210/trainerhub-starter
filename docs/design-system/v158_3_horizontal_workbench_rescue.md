# v158.3 - Horizontal Workbench Rescue

v158.3 replaces cramped product/video column layouts with horizontal trainer workbenches.

Updated areas:

- Product builder now uses a wide workbench with hero actions, compact metrics, horizontal product rail, full-width editor and bottom support panels.
- Video studio now uses workbench tabs, full-width upload zone, horizontal content rail, full-width editor panel and bottom preview/status panels.
- Product/content rail cards avoid long descriptions and keep metadata compact.
- Shared `.trainer-workbench-*` CSS adds safe width, rail scrolling, text wrapping and mobile fallbacks.
- Contract tests guard against returning to `trainer-product-builder-grid` and `trainer-content-studio-grid` in rewritten components.

Verification:

- `npm run typecheck`
- `npm run test:contracts`
- `git diff --check`

`npm run build` remains blocked locally by `.next/trace` file permissions.
