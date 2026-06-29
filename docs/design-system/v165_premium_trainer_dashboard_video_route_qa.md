# v165 — Premium Trainer Dashboard, Video Studio and Route QA Pass

## Updated Pages

- `/trainer/dashboard`
- `/trainer/videos`
- `TrainerContentStudio`
- `TrainerContentCard`
- `TrainerVideoUploadCard`

## Trainer Dashboard Cockpit

The trainer dashboard now works as the executive cockpit for the trainer workspace:

- hero with primary financial/readiness signal;
- KPI deck for profile readiness, orders, payments, turnover, published materials, drafts, available payout and payout requests;
- two-column desktop layout with mobile one-column fallback;
- next-action cards for profile, products, sales, payouts and analytics;
- revenue timeline with Russian empty state;
- top product rail with safe wrapping;
- profile/access panel with role warning and application status action.

## Video Studio Shell

`/trainer/videos` now provides a premium video studio frame above `TrainerContentStudio`:

- page title and description are aligned with the trainer shell;
- top hero explains material upload, program assembly and catalog publishing;
- actions link to video upload, product creation and analytics;
- the inner studio uses a compact toolbar to avoid duplicate large heroes.

## TrainerContentStudio Polish

The studio keeps the existing API and business logic, but improves the UI layer:

- compact toolbar with `Новый видеоурок`, `Новая программа`, `Новый набор`;
- KPI deck for videos, programs, bundles and review queue;
- video upload helper text and localized upload steps;
- program lesson labels use `Название урока`, `Описание`, `Позиция`, `Видео из библиотеки`, `Бесплатный предпросмотр`;
- bundle item labels use `Тип материала`, `Материал`, `Позиция`;
- content cards keep Russian status labels and use premium active styling;
- upload dropzone and selected file text wrap safely.

## Route QA Checklist

Trainer routes checked by code and scoped CSS rules:

- `/trainer/dashboard`
- `/trainer/business`
- `/trainer/dashboard/products`
- `/trainer/videos`
- `/trainer/dashboard/crm`
- `/trainer/dashboard/assignments`
- `/trainer/dashboard/schedule`
- `/trainer/dashboard/sales`
- `/trainer/dashboard/revenue`
- `/trainer/dashboard/payouts`
- `/trainer/dashboard/analytics`
- `/trainer/reviews`
- `/trainer/onboarding`
- `/trainer/application-status`

QA rules:

- no nested vertical scroll containers inside cards or panels;
- long titles, slugs, IDs and links wrap safely;
- loading, error and empty states are Russian;
- mobile routes collapse to one column;
- horizontal rails use `overflow-x: auto`, `overflow-y: hidden` and scroll snap;
- trainer CTAs keep the same premium level.

## CSS Safety Rules

v165 adds scoped CSS only:

- `trainer-home-*`
- `trainer-video-studio-*`
- targeted improvements for existing `trainer-content-*` upload/card classes.

Rules include `min-width: 0`, `overflow-wrap: anywhere`, line clamps for long descriptions and no vertical scroll containers inside cards.

## Backend/API Scope

Backend and API contracts were not changed. Existing loading, error, empty, save, publish, upload, delete and move actions remain intact.

## Visual Checks

Open the trainer routes listed above on desktop and mobile. Expected result:

- `/trainer/dashboard` shows hero, KPI deck, action cards, revenue timeline, product rail and sidebar panels;
- `/trainer/videos` shows one page-level hero and a compact material studio;
- content rails scroll horizontally without page overflow;
- forms, upload dropzone, lesson rows and bundle rows wrap safely on mobile.

## Known Limitation

`npm run build` may fail because of the existing `.next/trace` ownership/cache issue in this workspace. If that happens, use the exact build error in the final report and do not mark build as passed.
