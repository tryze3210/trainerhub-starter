# v148 Realtime Notifications UI

v148 adds shared UI primitives for realtime status and notification streams.

Scope:

- live connection indicator;
- notification feed item layout;
- unread notification state;
- tone-aware feed indicators;
- responsive feed behavior for mobile dashboards;
- contract coverage for realtime notification UI exports and classes.

Primary files:

- `frontend/src/design-system/feedback.tsx`
- `frontend/src/app/globals.css`
- `frontend/tests/contracts/design-system-contract.test.js`

Implementation notes:

- The UI layer does not open WebSocket, SSE or polling connections.
- Feature modules own transport, retry policy, authorization and persistence.
- `DSLiveIndicator` represents connection state from the caller.
- `DSNotificationFeed` renders already-normalized notification items.

Status:

- v148 is complete at the shared feedback/component-library layer.
