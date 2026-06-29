# v164 — Premium Trainer Business, Onboarding and Application Status Workbenches

v164 finishes the remaining trainer-facing business and application screens as premium workbenches.

## Updated Pages

- `/trainer/business`
- `/trainer/onboarding`
- `/trainer/application-status`

## Business Cockpit

The business page now uses a dedicated `trainer-business-*` layout with:

- hero summary for revenue, orders, customers and average order value;
- KPI deck for revenue, orders, customers, payout balance and active payout requests;
- business readiness cards with localized readiness status labels;
- content/product inventory with Russian labels and a direct product studio action;
- revenue timeline with localized empty state;
- top product rail with localized product type labels;
- payout request sidebar with localized payout statuses and masked destination fallback;
- moderation/risk sidebar with localized moderation state.

Removed visible English/technical labels include `Available payout`, `Reserved payout`, `Lifetime earned`, `Active payouts`, `Business readiness`, `Content inventory`, `Drafts`, `Published`, `Pending review`, `Order items`, `Top products`, `Latest payout requests`, `destination not set`, `Moderation & risk`, `Open cases` and `Risk flags`.

## Onboarding Workbench

The trainer onboarding checklist now uses a dedicated `trainer-onboarding-*` workbench:

- hero with progress, application status, dashboard access and role;
- KPI deck for progress, application, dashboard and role;
- application form with Russian labels;
- premium moderation note;
- readiness steps as premium step cards;
- localized save and submit actions;
- localized loading, error and empty states.

Removed visible English/technical labels include `Progress`, `Application`, `Dashboard`, `Role`, `Trainer application`, `Brand name`, `Legal name`, `Phone`, `Experience years`, `Country`, `City`, `Positioning / bio`, `Specialties`, `Links`, `Production readiness steps`, `Completed`, `Blocked`, `Open`, `Draft`, `Submitted`, `Under review`, `Approved`, `Changes requested` and `Rejected`.

## Application Status Workbench

The application status page now uses a dedicated `trainer-status-*` layout:

- hero with current application status;
- KPI deck for review, dashboard access, progress and next step;
- result card with localized status and moderation note;
- primary actions to edit the application or open products after unlock;
- readiness timeline with localized step states.

Raw backend statuses are no longer used as primary visible text. Statuses are mapped through local helper functions.

## Helper Mappers

v164 adds local helper mappers where the pages need them:

- `formatMoney`
- `formatDateTime`
- `formatPercent`
- `mapTrainerApplicationStatusLabel`
- `mapReadinessStatusLabel`
- `mapStepStatusLabel`
- `mapRoleLabel`
- `mapProductTypeLabel`
- `mapPayoutStatusLabel`
- `mapModerationStatusLabel`
- `getBadgeTone`
- `shortId`

## Scope

Backend and API contracts were not changed. Existing loading, error, empty, save, submit and retry behavior remains in place.

## Visual Checks

Open these routes on desktop and mobile:

- `/trainer/business`
- `/trainer/onboarding`
- `/trainer/application-status`

Expected result:

- desktop shows hero, KPI deck and two-column workbench layout;
- mobile collapses to one column;
- no nested vertical scroll containers;
- long titles, links, masked destinations and IDs wrap safely without breaking the grid.
