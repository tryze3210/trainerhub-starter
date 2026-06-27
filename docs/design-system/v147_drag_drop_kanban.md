# v147 Drag And Drop Kanban

v147 adds drag-and-drop support to the shared Kanban primitive.

Scope:

- typed Kanban move payload;
- draggable card behavior;
- dropzone behavior on Kanban columns;
- visual hover/active states for draggable cards;
- contract coverage for drag/drop API and CSS classes.

Primary files:

- `frontend/src/design-system/library.tsx`
- `frontend/src/app/globals.css`
- `frontend/tests/contracts/design-system-contract.test.js`

Implementation notes:

- The component does not mutate column state internally.
- Business screens receive `onCardMove` with `cardId`, `fromColumnId` and `toColumnId`.
- Persistence, optimistic updates and authorization remain owned by feature modules.
- Native browser drag-and-drop is used to avoid adding a dependency before a concrete workflow requires one.

Status:

- v147 is complete at the shared component-library layer.
