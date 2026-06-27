# v149 Command Palette

v149 adds a shared command palette primitive for fast search and keyboard-driven actions.

Scope:

- controlled command palette shell;
- grouped action/search results;
- shortcut labels;
- disabled command state;
- tone-aware command items;
- mobile command palette layout;
- contract coverage for command palette exports and CSS classes.

Primary files:

- `frontend/src/design-system/components.tsx`
- `frontend/src/app/globals.css`
- `frontend/tests/contracts/design-system-contract.test.js`

Implementation notes:

- The component does not fetch data.
- Feature modules own search sources, permissions, routing and analytics.
- The caller controls query state and selection behavior.
- The UI is suitable for Ctrl+K style app-wide search and quick actions.

Status:

- v149 is complete at the shared component-library layer.
