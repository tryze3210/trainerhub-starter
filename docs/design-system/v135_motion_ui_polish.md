# v135 Motion / UI Polish

v135 closes the first UX redesign foundation block with shared feedback and motion primitives.

## Scope

Feedback and motion files:

- `frontend/src/design-system/feedback.tsx`
- `frontend/src/app/globals.css`

Contract coverage:

- `frontend/tests/contracts/design-system-contract.test.js`

## Components

- `DSSkeleton`
- `DSEmptyState`
- `DSToast`
- `DSToastStack`
- `DSTransitionPanel`
- `DSStatusDot`

## CSS Coverage

- Shared skeleton stack.
- Toast stack and toast tones.
- Empty-state polish.
- Transition panel enter state.
- Status dots.
- Reduced-motion guard through `prefers-reduced-motion`.

## Rules

- Motion must support reduced-motion users.
- Toasts must use `role="status"` and `aria-live="polite"`.
- Business screens should use these primitives for loading, empty, success, warning and error states before adding one-off UI.
