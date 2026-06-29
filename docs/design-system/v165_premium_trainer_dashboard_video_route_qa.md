# v165 / v165.1 / v165.2 — Premium Trainer Dashboard, Video Studio and Route QA Pass

## 1. Scope

v165 started the premium trainer dashboard and video/content studio pass. v165.1 aligned the route-level video shell and `compactHero` flow. v165.2 closes the remaining repair work by synchronizing README versioning, the scoped CSS contract, trainer upload cards and route-level QA documentation.

Backend and API contracts are intentionally unchanged. Existing load, save, publish, upload, delete, move and retry actions remain wired to the same frontend APIs.

## 2. Why v165.2 Was Needed

v165 and v165.1 left a few contract gaps:

- version metadata could drift from the implemented UI state;
- trainer dashboard and studio classes were present but not fully explicit as a stable CSS contract;
- video route shell, content studio, cards and upload card needed final class names for route QA;
- documentation needed to describe the actual checks for overflow, nested scroll, Russian labels and raw status/type/ID display.

v165.2 fixes those gaps before the roadmap moves to v166.

## 3. Updated Files

- `README.md`
- `MANIFEST.md`
- `BUILD_REPORT.md`
- `docs/design-system/v165_premium_trainer_dashboard_video_route_qa.md`
- `frontend/src/app/trainer/dashboard/page.tsx`
- `frontend/src/app/trainer/videos/page.tsx`
- `frontend/src/modules/upload/components/trainer-upload-panel.tsx`
- `frontend/src/modules/upload/components/trainer-content-studio.tsx`
- `frontend/src/modules/upload/components/trainer-content-card.tsx`
- `frontend/src/modules/upload/components/trainer-video-upload-card.tsx`
- `frontend/src/app/globals.css`
- `frontend/tests/contracts/design-system-contract.test.js`

## 4. Trainer Dashboard Cockpit

`/trainer/dashboard` uses the premium trainer home contract:

- `.trainer-home-workbench`
- `.trainer-home-hero`
- `.trainer-home-hero-actions`
- `.trainer-home-hero-metric`
- `.trainer-home-alert`
- `.trainer-home-loading`
- `.trainer-home-kpi-grid`
- `.trainer-home-kpi-card`
- `.trainer-home-layout`
- `.trainer-home-main`
- `.trainer-home-sidebar`
- `.trainer-home-panel`
- `.trainer-home-action-grid`
- `.trainer-home-action-card`
- `.trainer-home-timeline`
- `.trainer-home-timeline-item`
- `.trainer-home-product-rail`
- `.trainer-home-product-card`
- `.trainer-home-profile-card`
- `.trainer-home-status-grid`
- `.trainer-home-status-item`

The page does not use the old generic `TrainerDashboardCard`, `TrainerMetricCard`, `TrainerEmptyState`, `TrainerErrorState`, `TrainerLoadingState` or `TrainerStatusBadge` UI as its final surface. Application status is mapped to Russian text before display. Loading and error states are premium panels with Russian copy and retry.

## 5. Video Studio Route Shell

`/trainer/videos` owns the page-level context:

- title: `Видео и материалы`
- description: `Загрузка видео, сборка программ и подготовка материалов к продаже`
- `.trainer-video-studio-workbench`
- `.trainer-video-studio-hero`
- `.trainer-video-studio-hero-content`
- `.trainer-video-studio-actions`

The route renders `<TrainerUploadPanel compactHero />`, so the page has one large hero and the studio below it renders as a compact working area. `intent=upload` still routes the user to the video tab and highlighted upload block through the existing `TrainerContentStudio` search param logic.

## 6. TrainerContentStudio Polish

`TrainerUploadPanel` is a typed wrapper:

```ts
type TrainerUploadPanelProps = {
  compactHero?: boolean;
};
```

`TrainerContentStudio` accepts the same `compactHero` intent and exposes:

- `.trainer-content-workbench`
- `.trainer-content-workbench--compact`
- `.trainer-content-toolbar`
- `.trainer-content-tabs`
- `.trainer-content-tab`
- `.trainer-content-tab--active`
- `.trainer-content-kpi-grid`
- `.trainer-content-kpi-card`
- `.trainer-content-alert`
- `.trainer-content-alert--success`
- `.trainer-content-alert--danger`
- `.trainer-content-layout`
- `.trainer-content-library`
- `.trainer-content-editor`
- `.trainer-content-preview`

When compact, the title is `Рабочая область` and the subtitle is `Выберите материал, обновите описание или подготовьте публикацию.` Tabs remain `Видео`, `Программы`, `Наборы`; KPI labels remain `Видео`, `Программы`, `Наборы`, `На проверке`.

Upload steps use Russian ellipsis:

- `Подготавливаем загрузку…`
- `Загружаем файл…`
- `Завершаем обработку…`

Empty states are Russian for videos, programs, bundles, lessons and bundle items.

## 7. TrainerContentCard And TrainerVideoUploadCard Polish

`TrainerContentCard` exposes:

- `.trainer-content-card`
- `.trainer-content-card--active`
- `.trainer-content-card-header`
- `.trainer-content-card-title`
- `.trainer-content-card-meta`
- `.trainer-content-card-actions`

The card keeps Russian metadata: `Адрес настроен` / `Адрес не указан` and the localized materials label. Titles are clamped, price wraps safely and actions flex-wrap.

`TrainerVideoUploadCard` exposes:

- `.trainer-content-upload-card`
- `.trainer-content-upload-dropzone`
- `.trainer-content-upload-dropzone--highlighted`
- `.trainer-content-file-name`
- `.trainer-content-upload-step`

The helper copy is `Сначала загрузите файл, затем сохраните описание и отправьте материал на проверку.` File names wrap safely and mobile actions do not overlap.

## 8. Scoped CSS Contract

v165.2 adds a dedicated `/* v165.2 trainer dashboard/video studio scoped polish */` CSS block. It covers:

- trainer dashboard classes: `.trainer-home-*`
- video route classes: `.trainer-video-studio-*`
- content studio/card/upload classes: `.trainer-content-*`

Safety rules:

- grid/flex children that can shrink use `min-width: 0`;
- long titles, slugs, URLs, IDs and file names use `overflow-wrap: anywhere`;
- descriptions and titles use line clamp where appropriate;
- cards and panels avoid nested vertical scroll;
- horizontal rails use `overflow-x: auto`, `overflow-y: hidden`, `scroll-snap-type: x mandatory`;
- mobile breakpoints at `1024px` and `720px` collapse layouts to one column and wrap actions.

No Tailwind, UI library or global reset rules were added.

## 9. Route QA Checklist

Trainer routes covered by code/CSS contract:

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

For each route, QA checks:

- no nested vertical scroll containers inside cards/panels;
- no text overflow from cards, buttons, slugs, URLs or IDs;
- no incoherent text overlap;
- no English user-facing labels in the updated trainer cockpit/studio routes;
- no raw UUID/status/type as primary display text;
- loading, error and empty states are Russian;
- mobile layout collapses to one column;
- horizontal rails do not create page overflow;
- nav/header does not create extra right-side scroll.

## 10. Backend/API Scope

Backend was not touched. API field names, request paths and payload contracts were not changed. Existing save/publish/upload/delete/move/retry handlers remain intact.

## 11. Verification

Expected local checks:

```bash
cd frontend
npm run typecheck
npm run test:contracts
npm run build
git diff --check
```

The design-system contract includes v165.2 fragments for README/docs sync, dashboard class contract, video route shell, compact content studio, content card and upload card.

## 12. Known Limitation

`npm run build` can fail before compilation if the existing `.next/trace` file has ownership/cache permissions from another user. In that case the expected local failure is an `EACCES` error opening `frontend/.next/trace`; typecheck, contract and diff-check results should be reported separately, and build must not be marked as passed.
