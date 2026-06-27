# v131 — UI Design System

This pass introduces the shared UI foundation before screen redesign work.

## Scope

- Colors: semantic CSS variables and backward-compatible aliases.
- Typography: shared font family and heading/body scale tokens.
- Spacing: shared spacing scale from `--space-2xs` to `--space-3xl`.
- Buttons: primary, secondary, ghost, danger and size variants.
- Forms: field wrappers for input, textarea and select.
- Tables: shared table wrapper and table classes.
- Cards: neutral and status card tones.
- Modals: reusable modal shell classes and React primitive.
- Loading polish: skeleton loader class and focus ring.

## Files

- `frontend/src/app/globals.css`
- `frontend/src/design-system/tokens.ts`
- `frontend/src/design-system/components.tsx`
- `frontend/src/design-system/index.ts`
- `frontend/tests/contracts/design-system-contract.test.js`

## Principles

- Keep existing class names working.
- Add design tokens first, then migrate screens gradually.
- Keep cards at 8px radius by default for operational surfaces.
- Prefer semantic tones over hard-coded colors in feature screens.
- Avoid one-note color palettes; use neutral surfaces with blue primary and teal accent.
