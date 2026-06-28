# v156 — Premium Customer Cabinet and All Customer Sections

## Scope

v156 turns the post-purchase customer area into a unified premium workspace.

Covered routes:

- `/cabinet`
- `/customer/hub`
- `/learning`
- `/entitlements`
- `/orders`
- `/payments`
- `/subscriptions`
- `/billing`
- `/messages`

## Shared Shell

New shared customer cabinet components:

- `customer-cabinet-shell.tsx`
- `customer-cabinet-nav.tsx`
- `customer-dashboard-card.tsx`
- `customer-status-badge.tsx`
- `customer-empty-state.tsx`
- `customer-loading-state.tsx`
- `customer-error-state.tsx`
- `customer-metric-card.tsx`
- `customer-section-header.tsx`

The shell provides the internal customer navigation, premium dark workspace surface and responsive mobile scroll navigation.

## Customer UX

- `/cabinet` is now the main premium customer dashboard.
- `/learning` is a student learning area with course list, lesson panel, materials and progress.
- `/entitlements` is now “Мои доступы” with human-readable access cards.
- `/orders`, `/payments`, `/subscriptions` and `/billing` use Russian commercial copy and customer-friendly statuses.
- `/messages` is now a premium inbox layout with conversation list, thread and composer.

## Contract

The design-system contract now guards customer shell files, required CSS fragments and removal of common technical customer labels.
