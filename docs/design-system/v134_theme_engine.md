# v134 Theme Engine

v134 adds the theme engine for the UX redesign block. It keeps the design system token-based while allowing runtime mode, brand and white-label changes.

## Scope

Theme engine files:

- `frontend/src/design-system/theme.tsx`
- `frontend/src/design-system/tokens.ts`
- `frontend/src/app/globals.css`

Contract coverage:

- `frontend/tests/contracts/design-system-contract.test.js`

## Features

- Light mode through default semantic CSS variables.
- Dark mode through `data-theme="dark"`.
- Brand palettes through `data-brand`.
- White-label overrides through `DSWhiteLabelTheme` and CSS custom properties.
- `DSThemeProvider` and `useDSTheme` for React screens that need runtime theme switching.

## Supported Brands

- `trainerhub`
- `studio`
- `academy`
- `wellness`

## Rules

- Business screens should read semantic variables, not raw colors.
- Tenant/brand data should map into `DSWhiteLabelTheme`.
- Theme changes must not alter API permissions, tenant scope or entitlement rules.
- Future v136-v145 redesign screens should use `DSThemeProvider` only at layout boundaries.
