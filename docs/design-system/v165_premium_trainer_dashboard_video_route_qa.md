# v165 / v165.1 — Premium Trainer Dashboard, Video Studio and Route QA Pass

## 1. Scope

v165 upgrades the trainer dashboard and video studio into premium trainer workbenches. v165.1 finalizes the unfinished sync between README, code and documentation: the trainer dashboard cockpit, video studio route shell, upload/card polish and route-level QA documentation now describe the same implemented state.

Backend and API contracts are intentionally unchanged. Existing load, retry, save, upload, publish, delete and move actions remain wired to the same frontend APIs.

## 2. Updated Files

- `README.md`
- `docs/design-system/v165_premium_trainer_dashboard_video_route_qa.md`
- `frontend/src/app/trainer/dashboard/page.tsx`
- `frontend/src/app/trainer/videos/page.tsx`
- `frontend/src/modules/upload/components/trainer-upload-panel.tsx`
- `frontend/src/modules/upload/components/trainer-content-studio.tsx`
- `frontend/src/modules/upload/components/trainer-content-card.tsx`
- `frontend/src/modules/upload/components/trainer-video-upload-card.tsx`
- `frontend/src/app/globals.css`
- `frontend/tests/contracts/design-system-contract.test.js`

## 3. Trainer Dashboard Cockpit

`/trainer/dashboard` no longer uses the old generic trainer dashboard cards as the main UI. The page uses:

- `ProtectedPage`;
- `TrainerDashboardShell`;
- `.trainer-home-workbench`;
- `.trainer-home-hero`;
- `.trainer-home-kpi-grid`;
- `.trainer-home-layout`;
- `.trainer-home-main`;
- `.trainer-home-sidebar`.

The hero shows the primary state in this priority:

- available payout amount;
- gross revenue;
- profile readiness.

The KPI deck covers profile readiness, orders, payments, turnover, published materials, drafts, available payout and payout request count. The left column contains next actions, revenue timeline and top products. The right column contains profile/access, quick actions and account state. Application status is mapped to Russian labels and is not shown as a raw backend status.

Loading and error states are premium panels with Russian copy and retry.

## 4. Video Studio Route Shell

`/trainer/videos` now owns the page-level context:

- title: `Видео и материалы`;
- description: `Загрузка видео, сборка программ и подготовка материалов к продаже`;
- `.trainer-video-studio-workbench`;
- `.trainer-video-studio-hero`;
- actions for upload, product creation and analytics.

The route passes `compactHero` to `TrainerUploadPanel`, so `TrainerContentStudio` renders as a compact working area instead of duplicating a second large hero.

## 5. TrainerContentStudio Polish

`TrainerContentStudio` accepts:

```ts
type TrainerContentStudioProps = {
  compactHero?: boolean;
};
```

When compact, it renders `Рабочая область` with the subtitle `Выберите материал, обновите описание или подготовьте публикацию.` It keeps the core actions:

- `Новый видеоурок`;
- `Новая программа`;
- `Новый набор`.

The studio uses scoped classes:

- `.trainer-content-workbench`;
- `.trainer-content-toolbar`;
- `.trainer-content-kpi-grid`;
- `.trainer-content-layout`;
- `.trainer-content-library`;
- `.trainer-content-editor`;
- `.trainer-content-preview`.

Tabs remain Russian: `Видео`, `Программы`, `Наборы`. KPI cards remain Russian: `Видео`, `Программы`, `Наборы`, `На проверке`.

Upload steps use the Russian ellipsis:

- `Подготавливаем загрузку…`;
- `Загружаем файл…`;
- `Завершаем обработку…`.

Empty states:

- videos: `Загрузите первый видеоурок, чтобы использовать его в программах и продуктах.`;
- programs: `Создайте программу и добавьте уроки из библиотеки видео.`;
- bundles: `Соберите несколько видео или программ в один платный набор.`;
- lessons: `Сначала загрузите видеоурок, затем добавьте его в программу.`;
- bundle items: `Добавьте видео или программу, чтобы собрать набор.`;

## 6. TrainerContentCard and UploadCard Polish

`TrainerContentCard` now exposes:

- `.trainer-content-card`;
- `.trainer-content-card--active`;
- status and price header row;
- title line clamp;
- metadata row with `Адрес настроен` / `Адрес не указан`;
- wrapped action row.

`TrainerVideoUploadCard` now exposes:

- `.trainer-content-upload-dropzone`;
- `.trainer-content-upload-dropzone--highlighted`;
- `.trainer-content-file-name`.

The helper copy is:

`Сначала загрузите файл, затем сохраните описание и отправьте материал на проверку.`

## 7. Route QA Checklist

Trainer-facing routes checked by code and CSS contract:

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
- no text overflow from cards, rails, buttons, slugs, URLs or IDs;
- no incoherent text overlap;
- no English user-facing labels in the updated trainer cockpit/studio routes;
- no raw UUID/status/type as primary display text;
- loading, error and empty states are Russian;
- mobile layout collapses to one column;
- horizontal rails use scoped `overflow-x: auto`, `overflow-y: hidden` and scroll snap;
- header/nav should not create extra right-side page scroll.

## 8. CSS Safety Rules

v165.1 uses scoped trainer classes only:

- `.trainer-home-*`;
- `.trainer-video-studio-*`;
- `.trainer-content-*`.

Rules include:

- `min-width: 0` for grid/flex children;
- `overflow-wrap: anywhere` for long titles, slugs, IDs and URLs;
- line clamp for long titles/descriptions;
- no `overflow-y: auto` inside cards/panels;
- horizontal rails use `overflow-x: auto`, `overflow-y: hidden`, `scroll-snap-type`;
- responsive guards for `1024px` and `720px`;
- actions wrap without overlap.

No Tailwind, no new UI libraries and no global resets were added.

## 9. Backend/API Scope

Backend code was not changed. API request paths and payload contracts were not changed. Existing save/publish/upload/delete/move/retry handlers remain in place.

## 10. Verification

Expected local checks:

```bash
cd frontend
npm run typecheck
npm run test:contracts
npm run build
git diff --check
```

The design-system contract includes v165/v165.1 fragments for:

- dashboard cockpit classes;
- video studio shell classes;
- compact content studio classes;
- upload/card polish classes;
- README/documentation sync.

## 11. Known Limitation

`npm run build` can fail in this workspace before compilation if the existing `.next/trace` file is owned by another user or has stale cache permissions. In that case the expected error is an `EACCES` failure opening `frontend/.next/trace`; typecheck and contract results should be reported separately and build must not be marked as passed.
