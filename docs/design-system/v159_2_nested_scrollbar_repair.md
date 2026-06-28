# v159.2 — Remove Nested Scrollbars and Polish Profile Workbench

v159.2 removes nested vertical scroll containers from profile workbench pages and keeps the browser page as the only vertical scrolling surface.

## Scope

- Added hard profile/workbench overflow overrides for vertical scroll repair.
- Hidden rough horizontal scrollbars in profile navigation.
- Kept thin horizontal scrollbars for rail lists only.
- Widened the profile workbench container to support product and video editing flows.
- Converted the trainer product builder header into a local header.
- Replaced the product rail empty state panel with a rail-sized empty card.
- Prevented editor panels from becoming internal scroll windows.
- Added design-system contract checks for the scrollbar repair.

## Verification

- `npm run typecheck`
- `npm run build`
- `npm run test:contracts`
