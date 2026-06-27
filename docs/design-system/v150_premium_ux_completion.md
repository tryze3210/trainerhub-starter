# v150 Premium UX Completion

v150 closes the premium UX block with shared collaboration and activity primitives.

Scope:

- collaborator presence stack;
- collaborator online, away and offline states;
- activity timeline for recent team actions;
- tone-aware activity indicators;
- mobile-safe collaboration layout;
- contract coverage for v150 exports and CSS classes.

Primary files:

- `frontend/src/design-system/feedback.tsx`
- `frontend/src/app/globals.css`
- `frontend/tests/contracts/design-system-contract.test.js`

Implementation notes:

- The UI layer does not own realtime transport or authorization.
- Feature modules provide normalized presence and activity data.
- `DSPresenceStack` is intended for shared workspaces and record-level collaboration.
- `DSActivityTimeline` is intended for dashboards, audit-adjacent views and collaborative surfaces.

Status:

- v150 completes the v146-v150 premium UX block.
