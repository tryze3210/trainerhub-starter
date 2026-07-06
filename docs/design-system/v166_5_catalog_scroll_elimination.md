# v166.5 / v166.5.1 — Catalog Scroll Elimination and Premium Page Scrollbar Styling

## Scope

v166.5 убирает лишний scroll в каталоге и фиксирует no-extra-scroll policy по продукту.

v166.5.1 styles the main document/page scrollbar for `/catalog` so the visible right-side scrollbar matches the dark premium UI. The catalog remains longer than the viewport and keeps natural document scrolling.

## Root Cause

- Лишняя прокрутка появилась в `.premium-catalog-filter-row`.
- Mobile CSS превращал фильтры в horizontal rail через `overflow-x: auto`.
- Для текущего premium каталога это лишний UI-шум.
- Фильтры должны переноситься в несколько строк.

## Fixed Areas

- `/catalog`
- Marketplace filters
- Marketplace cards
- Catalog hero/proof row
- Featured product block
- Final CTA
- App shell/header navigation

## Scrollbar Policy

1. В каталоге не должно быть внутренних vertical scrollbars.
2. В фильтрах каталога не должно быть видимой горизонтальной прокрутки.
3. Фильтры должны переноситься.
4. Горизонтальный scroll допустим только для явно нужных rails и таблиц, не для catalog filter chips.
5. Карточки не должны расширять страницу.
6. CTA rows должны переноситься.
7. Длинные title/slug/url/file names должны переноситься безопасно.
8. Body/html overflow-x hidden не использовать как основной фикс.
9. The main document/page scrollbar may be visible and must be styled dark/thin for premium surfaces.
10. `.premium-main` must not become an internal vertical scroll container for catalog.

## v166.5.1 Page Scrollbar Styling

- The visible right-side scrollbar on `/catalog` is the main document/page scrollbar.
- It is styled through `:root`, `html::-webkit-scrollbar` and `body::-webkit-scrollbar`.
- The scrollbar thumb uses muted slate on a near-black track.
- `.premium-main`, `.premium-landing` and `.premium-catalog-page` keep `overflow-y: visible`.
- `.premium-catalog-page` uses `overflow-x: clip` only to prevent accidental horizontal bleed.
- Catalog filter chips wrap and do not create a separate horizontal or vertical scroller.

## Catalog QA Checklist

- Проверить desktop 1440px.
- Проверить laptop 1280px.
- Проверить tablet 768px.
- Проверить mobile 390px.
- Нет правого горизонтального scroll.
- Нет второго vertical scrollbar.
- Filter chips wrap.
- Cards stay inside grid.
- Featured product does not overflow.
- Final CTA buttons wrap.
- Header/nav does not create overflow.

## Overflow Audit

Intentional scroll areas left in place:

- command palette results use `overflow-y: auto`;
- modal panels use `overflow-y: auto` on small screens;
- profile/workbench nav rails keep horizontal overflow behavior where they are explicit navigation rails;
- product/video studio media rails keep horizontal overflow behavior where rail scrolling is intentional.

Catalog filter chips are not an intentional rail and must wrap instead.

## Backend/API Scope

Backend unchanged.
API unchanged.
Only CSS/className/docs/contracts/copy changed.

## Verification

```bash
cd frontend
npm run typecheck
npm run test:contracts
npm run build
git diff --check
```

## Known Limitation

Build may fail due to existing `.next/trace` ownership/cache issue. If this happens, show the exact error and do not claim build passed.
