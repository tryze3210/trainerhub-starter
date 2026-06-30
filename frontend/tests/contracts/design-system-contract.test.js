const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..', '..');
const repoRoot = path.resolve(root, '..');

function readUtf8(...parts) {
  return fs.readFileSync(path.join(...parts), 'utf8');
}

function assertNonEmptyFragments(label, fragments) {
  for (const fragment of fragments) {
    if (typeof fragment !== 'string' || fragment.trim().length === 0) {
      throw new Error(`${label} contains empty contract fragment`);
    }
  }
}

function assertIncludes(source, fragment, label) {
  if (!source.includes(fragment)) {
    throw new Error(`${label} missing fragment: ${fragment}`);
  }
}

function assertNotIncludes(source, fragment, label) {
  if (source.includes(fragment)) {
    throw new Error(`${label} contains forbidden fragment: ${fragment}`);
  }
}

function assertIncludesAll(source, fragments, label) {
  assertNonEmptyFragments(label, fragments);
  for (const fragment of fragments) {
    assertIncludes(source, fragment, label);
  }
}

function assertExcludesAll(source, fragments, label) {
  assertNonEmptyFragments(label, fragments);
  for (const fragment of fragments) {
    assertNotIncludes(source, fragment, label);
  }
}

const requiredFiles = [
  'src/app/globals.css',
  'src/app/profile-workbench.css',
  'src/app/trainer-operations.css',
  'src/app/trainer-finance-analytics.css',
  'src/design-system/tokens.ts',
  'src/design-system/components.tsx',
  'src/design-system/feedback.tsx',
  'src/design-system/layouts.tsx',
  'src/design-system/library.tsx',
  'src/design-system/theme.tsx',
  'src/design-system/animated.tsx',
  'src/design-system/use-count-up.ts',
  'src/design-system/index.ts',
  'src/design-system/profile-workbench.tsx',
  '../docs/design-system/v131_ui_design_system.md',
  '../docs/design-system/v132_layout_system.md',
  '../docs/design-system/v133_component_library.md',
  '../docs/design-system/v134_theme_engine.md',
  '../docs/design-system/v135_motion_ui_polish.md',
  '../docs/design-system/v146_premium_charts.md',
  '../docs/design-system/v147_drag_drop_kanban.md',
  '../docs/design-system/v148_realtime_notifications_ui.md',
  '../docs/design-system/v149_command_palette.md',
  '../docs/design-system/v150_premium_ux_completion.md',
  '../docs/design-system/v151_premium_brand_foundation.md',
  '../docs/design-system/v152_premium_marketing_home_page.md',
  '../docs/design-system/v153_premium_storefront_stabilization.md',
  '../docs/design-system/v154_prep_marketplace_catalog_premium_foundation.md',
  '../docs/design-system/v154_premium_product_detail_landing_pages.md',
  '../docs/design-system/v155_premium_app_shell_checkout.md',
  '../docs/design-system/v156_premium_customer_cabinet.md',
  '../docs/design-system/v157_premium_trainer_cabinet.md',
  '../docs/design-system/v158_premium_trainer_product_builder.md',
  '../docs/design-system/v158_1_product_builder_video_studio_repair.md',
  '../docs/design-system/v158_2_product_video_usability_repair.md',
  '../docs/design-system/v158_3_horizontal_workbench_rescue.md',
  '../docs/design-system/v159_premium_profile_workbench.md',
  '../docs/design-system/v159_1_profile_surface_repair.md',
  '../docs/design-system/v159_2_nested_scrollbar_repair.md',
  '../docs/design-system/v160_media_library_picker.md',
  '../docs/design-system/v160_1_media_picker_integration.md',
  '../docs/design-system/v160_2_product_video_flow_stabilization.md',
  '../docs/design-system/v160_3_product_media_picker_cleanup.md',
  '../docs/design-system/v160_4_product_media_single_source.md',
  '../docs/design-system/v161_premium_trainer_operations.md',
  '../docs/design-system/v162_premium_trainer_finance_analytics.md',
  '../docs/design-system/v163_premium_trainer_education_reviews_payouts.md',
  '../docs/design-system/v164_premium_trainer_business_onboarding_status.md',
  '../docs/design-system/v165_premium_trainer_dashboard_video_route_qa.md',
  '../docs/design-system/v166_production_visual_hardening.md',
  'src/modules/trainer-operations/format.ts',
  'src/modules/trainer-products/components/trainer-product-media-picker.tsx',
  'src/modules/trainer-products/components/trainer-selected-media-list.tsx',
  'src/modules/trainer-products/components/trainer-product-advanced-id-field.tsx',
  'src/modules/trainer-products/types/product-media.ts',
  'src/modules/upload/components/trainer-content-studio.tsx',
  'src/modules/upload/components/trainer-video-upload-card.tsx',
  'src/modules/upload/components/trainer-content-card.tsx',
  'src/modules/upload/components/trainer-upload-format.ts',
  'src/components/session-nav.tsx',
  'src/app/checkout/page.tsx',
  'src/app/checkout/success/page.tsx',
  'src/app/checkout/cancel/page.tsx',
  'src/modules/checkout/components/checkout-page.tsx',
  'src/modules/checkout/components/checkout-order-summary.tsx',
  'src/modules/checkout/components/checkout-payment-method.tsx',
  'src/modules/checkout/components/checkout-trust-panel.tsx',
  'src/modules/checkout/components/checkout-state-card.tsx',
  'src/modules/customer-cabinet/components/customer-cabinet-shell.tsx',
  'src/modules/customer-cabinet/components/customer-cabinet-nav.tsx',
  'src/modules/customer-cabinet/components/customer-dashboard-card.tsx',
  'src/modules/customer-cabinet/components/customer-status-badge.tsx',
  'src/modules/customer-cabinet/components/customer-empty-state.tsx',
  'src/modules/customer-cabinet/components/customer-loading-state.tsx',
  'src/modules/customer-cabinet/components/customer-error-state.tsx',
  'src/modules/customer-cabinet/components/customer-metric-card.tsx',
  'src/modules/customer-cabinet/components/customer-section-header.tsx',
  'src/modules/trainer-cabinet/components/trainer-cabinet-shell.tsx',
  'src/modules/trainer-cabinet/components/trainer-cabinet-nav.tsx',
  'src/modules/trainer-cabinet/components/trainer-format.ts',
  'src/modules/trainer-dashboard/components/trainer-dashboard-shell.tsx',
  'src/modules/public-storefront/components/marketing-home-page.tsx',
  'src/modules/public-storefront/components/hero-business-console.tsx',
  'src/modules/public-storefront/components/platform-map-section.tsx',
  'src/modules/public-storefront/components/role-workspace-section.tsx',
  'src/modules/public-storefront/components/commercial-proof-band.tsx',
  'src/modules/public-storefront/components/product-experience-timeline.tsx',
  'src/modules/public-storefront/components/final-premium-cta.tsx',
  'src/modules/public-storefront/components/premium-marketplace-card.tsx',
  'src/modules/public-storefront/components/content-detail-page.tsx',
  'src/modules/public-storefront/components/product-landing-hero.tsx',
  'src/modules/public-storefront/components/product-purchase-panel.tsx',
  'src/modules/public-storefront/components/product-includes-section.tsx',
  'src/modules/public-storefront/components/product-access-section.tsx',
];

for (const file of requiredFiles) {
  const absolutePath = path.resolve(root, file);
  if (!fs.existsSync(absolutePath)) {
    throw new Error(`Missing design system contract file: ${file}`);
  }
}

const globals = readUtf8(root, 'src/app/globals.css');
const profileWorkbenchCss = readUtf8(root, 'src/app/profile-workbench.css');
const trainerOperationsCss = readUtf8(root, 'src/app/trainer-operations.css');
const trainerFinanceAnalyticsCss = readUtf8(root, 'src/app/trainer-finance-analytics.css');
const tokens = readUtf8(root, 'src/design-system/tokens.ts');
const components = readUtf8(root, 'src/design-system/components.tsx');
const feedback = readUtf8(root, 'src/design-system/feedback.tsx');
const layouts = readUtf8(root, 'src/design-system/layouts.tsx');
const library = readUtf8(root, 'src/design-system/library.tsx');
const theme = readUtf8(root, 'src/design-system/theme.tsx');
const animated = readUtf8(root, 'src/design-system/animated.tsx');
const countUp = readUtf8(root, 'src/design-system/use-count-up.ts');

for (const fragment of [
  '--color-primary',
  '--color-accent',
  '--color-foreground',
  '--color-muted',
  '--color-muted-foreground',
  '--color-surface-elevated',
  '--color-surface-glass',
  '--radius-xl',
  '--shadow-soft',
  '--shadow-medium',
  '--shadow-glow',
  '--container-max-width',
  '--font-size-h1',
  '--space-md',
  '--radius-md',
  '.ds-modal',
  '.ds-command-palette',
  '.ds-command-palette__search',
  '.ds-command-palette__item',
  '.ds-layout-shell',
  '.ds-layout-sidebar',
  '.ds-page-header',
  '.ds-mobile-action-bar',
  '.ds-chart',
  '.ds-premium-chart',
  '.ds-line-chart',
  '.ds-donut-chart',
  '.ds-calendar',
  '.ds-kanban',
  '.ds-kanban--draggable',
  '.ds-kanban__column--dropzone',
  '.ds-kanban__card--draggable',
  '.ds-file-upload',
  '.ds-rich-text',
  '.ds-video-player',
  '.ds-stats-grid',
  '.ds-theme-root',
  'data-theme="dark"',
  'data-brand="studio"',
  'data-brand="academy"',
  'data-brand="wellness"',
  '.ds-toast',
  '.ds-toast-stack',
  '.ds-live-indicator',
  '.ds-live-indicator__pulse',
  '.ds-notification-feed',
  '.ds-notification-feed__item--unread',
  '.ds-presence-stack',
  '.ds-presence-stack__avatar',
  '.ds-activity-timeline',
  '.ds-empty-state',
  '.ds-transition-panel',
  '.ds-status-dot',
  '.premium-landing',
  '.premium-container',
  '.premium-hero-grid',
  '.premium-hero-title',
  '.premium-hero-subtitle',
  '.premium-actions',
  '.premium-primary-button',
  '.premium-secondary-button',
  '.premium-console',
  '.premium-console-card',
  '.premium-console-glow',
  '.premium-console-row',
  '.premium-console-row-enter',
  '.premium-section',
  '.premium-section-header',
  '.premium-editorial-grid',
  '.premium-row-list',
  '.premium-platform-map',
  '.premium-platform-module',
  '.premium-platform-module-active',
  '.premium-role-grid',
  '.premium-role-card',
  '.premium-timeline-line',
  '.premium-timeline-line-fill',
  '.premium-timeline-step',
  '.premium-timeline-step-active',
  '.premium-proof-band',
  '.premium-final-cta',
  '.premium-eyebrow',
  '.premium-metric-card',
  '.premium-count',
  '.premium-progress',
  '.premium-progress-fill',
  '.premium-hero',
  '.animated-section',
  '.animated-section-visible',
  '.animated-card',
  '.animated-card-visible',
  '.animated-metric',
  '.animated-metric-visible',
  '.premium-catalog-page',
  '.premium-catalog-hero',
  '.premium-catalog-hero-grid',
  '.premium-catalog-preview',
  '.premium-featured-product',
  '.premium-featured-product-grid',
  '.premium-product-grid',
  '.premium-marketplace-card',
  '.premium-marketplace-card-cover',
  '.premium-marketplace-card-body',
  '.premium-marketplace-card-meta',
  '.premium-marketplace-card-price',
  '.premium-marketplace-card-actions',
  '.premium-filter-bar',
  '.premium-filter-chip',
  '.premium-filter-chip-active',
  '.premium-trust-panel',
  '.premium-state-card',
  '.premium-skeleton-card',
  '.premium-product-page',
  '.premium-product-layout',
  '.premium-product-hero',
  '.premium-product-hero-copy',
  '.premium-product-title',
  '.premium-product-subtitle',
  '.premium-product-meta',
  '.premium-product-facts',
  '.premium-product-fact',
  '.premium-purchase-panel',
  '.premium-purchase-panel-sticky',
  '.premium-purchase-price',
  '.premium-purchase-trust',
  '.premium-product-section',
  '.premium-product-section-header',
  '.premium-product-includes-grid',
  '.premium-product-include-card',
  '.premium-product-outcome-grid',
  '.premium-product-outcome-card',
  '.premium-product-trainer-card',
  '.premium-access-timeline',
  '.premium-access-step',
  '.premium-mobile-purchase-bar',
  '.premium-product-state',
  '.premium-product-skeleton',
  '.app-shell',
  '.premium-main',
  '.premium-site-header',
  '.premium-site-header__inner',
  '.premium-brand',
  '.premium-brand__mark',
  '.premium-brand__text',
  '.premium-nav',
  '.premium-nav__link',
  '.premium-nav__link-active',
  '.premium-header-actions',
  '.premium-header-user',
  '.premium-header-cta',
  '.premium-header-ghost',
  '.premium-site-footer',
  '.premium-site-footer__inner',
  '.premium-site-footer__brand',
  '.premium-site-footer__grid',
  '.premium-site-footer__column',
  '.premium-site-footer__title',
  '.premium-site-footer__links',
  '.premium-site-footer__bottom',
  '.premium-footer-link',
  '.premium-checkout-page',
  '.premium-checkout-layout',
  '.premium-checkout-hero',
  '.premium-checkout-summary',
  '.premium-checkout-panel',
  '.premium-checkout-panel-sticky',
  '.premium-checkout-row',
  '.premium-checkout-total',
  '.premium-checkout-trust',
  '.premium-checkout-provider',
  '.premium-checkout-state',
  '.premium-checkout-error',
  '.premium-checkout-success',
  '.premium-checkout-actions',
  '.customer-cabinet-shell',
  '.customer-cabinet-layout',
  '.customer-cabinet-sidebar',
  '.customer-cabinet-sidebar-card',
  '.customer-cabinet-nav',
  '.customer-cabinet-nav-link',
  '.customer-cabinet-nav-link-active',
  '.customer-cabinet-content',
  '.customer-cabinet-topbar',
  '.customer-page-hero',
  '.customer-page-title',
  '.customer-page-subtitle',
  '.customer-page-actions',
  '.customer-dashboard-grid',
  '.customer-dashboard-card',
  '.customer-metric-grid',
  '.customer-metric-card',
  '.customer-section-card',
  '.customer-section-header',
  '.customer-status-badge',
  '.customer-status-success',
  '.customer-status-warning',
  '.customer-status-danger',
  '.customer-status-neutral',
  '.customer-empty-state',
  '.customer-loading-state',
  '.customer-error-state',
  '.customer-learning-page',
  '.customer-learning-continue-card',
  '.customer-learning-grid',
  '.customer-learning-list',
  '.customer-learning-item',
  '.customer-learning-item-active',
  '.customer-lesson-panel',
  '.customer-lesson-row',
  '.customer-materials-grid',
  '.customer-material-card',
  '.customer-progress-bar',
  '.customer-progress-fill',
  '.customer-access-grid',
  '.customer-access-card',
  '.customer-commerce-list',
  '.customer-commerce-card',
  '.customer-billing-tabs',
  '.customer-message-layout',
  '.customer-conversation-list',
  '.customer-conversation-card',
  '.customer-conversation-card-active',
  '.customer-message-thread',
  '.customer-message-bubble',
  '.customer-message-composer',
  '.trainer-cabinet-shell',
  '.trainer-cabinet-layout',
  '.trainer-cabinet-sidebar',
  '.trainer-cabinet-sidebar-card',
  '.trainer-cabinet-nav',
  '.trainer-cabinet-nav-link',
  '.trainer-cabinet-nav-link-active',
  '.trainer-cabinet-content',
  '.trainer-cabinet-topbar',
  '.trainer-page-hero',
  '.trainer-page-title',
  '.trainer-page-subtitle',
  '.trainer-page-actions',
  '.trainer-metric-grid',
  '.trainer-metric-card',
  '.trainer-dashboard-grid',
  '.trainer-dashboard-card',
  '.trainer-section-card',
  '.trainer-section-header',
  '.trainer-status-badge',
  '.trainer-status-success',
  '.trainer-status-warning',
  '.trainer-status-danger',
  '.trainer-status-neutral',
  '.trainer-empty-state',
  '.trainer-loading-state',
  '.trainer-error-state',
  '.trainer-business-grid',
  '.trainer-revenue-list',
  '.trainer-product-list',
  '.trainer-review-grid',
  '.trainer-review-card',
  '.trainer-review-reply',
  '.trainer-upload-context',
  '.trainer-product-builder',
  '.trainer-product-builder-hero',
  '.trainer-product-builder-metrics',
  '.trainer-product-list',
  '.trainer-product-list-card',
  '.trainer-product-list-card-active',
  '.trainer-product-editor',
  '.trainer-product-form',
  '.trainer-product-field',
  '.trainer-product-preview',
  '.trainer-product-readiness',
  '.trainer-product-readiness-list',
  '.trainer-product-readiness-item',
  '.trainer-product-actions',
  '.trainer-product-danger-action',
  '.trainer-assignment-page',
  '.trainer-assignment-grid',
  '.trainer-assignment-card',
  '.trainer-submission-card',
  '.trainer-sales-page',
  '.trainer-sales-grid',
  '.trainer-sales-card',
  '.trainer-sales-table-card',
  '.trainer-crm-page',
  '.trainer-crm-grid',
  '.trainer-crm-customer-card',
  '.trainer-crm-detail-panel',
  '.trainer-content-studio',
  '.trainer-content-studio-tabs',
  '.trainer-content-studio-tab',
  '.trainer-content-studio-tab-active',
  '.trainer-content-editor',
  '.trainer-content-list',
  '.trainer-content-card',
  '.trainer-content-card-active',
  '.trainer-content-card-meta',
  '.trainer-content-form',
  '.trainer-content-actions',
  '.trainer-content-preview',
  '.trainer-content-field',
  '.trainer-content-input',
  'v159.2 — Profile nested scrollbar repair',
  '.profile-workbench-nav::-webkit-scrollbar',
  '.profile-workbench-rail::-webkit-scrollbar',
  '.trainer-workbench-local-header',
  '.trainer-product-workbench',
  'overflow-y: visible !important',
  'max-height: none !important',
  'scrollbar-width: none',
  '.trainer-workbench-empty-rail-card',
  '.trainer-product-media-picker',
  '.trainer-media-picker-rail',
  '.trainer-media-picker-card',
  '.trainer-media-picker-card-active',
  '.trainer-selected-media-list',
  '.trainer-selected-media-row',
  '.trainer-product-advanced-field',
  '.trainer-product-materials-panel',
  'v160.1 — Product media picker integration',
  '.trainer-product-materials-panel-highlighted',
  '.trainer-editor-section-header',
  '.trainer-product-materials-hint',
  'v160.2 — Product media picker visual contract',
  'v160.2 — Product media picker visual stabilization',
  '.trainer-product-upload-bridge',
  '.trainer-product-workbench',
  '.trainer-video-workbench',
  '.trainer-workbench-local-header',
  '.trainer-media-picker-card-status',
  'overflow-y: visible !important',
  '.trainer-content-textarea',
  '.trainer-content-select',
  '.trainer-content-button',
  '.trainer-content-button-secondary',
  '.trainer-upload-dropzone',
  '.trainer-upload-dropzone-active',
  '.trainer-lesson-editor',
  '.trainer-lesson-list',
  '.trainer-lesson-card',
  '.trainer-bundle-editor',
  '.trainer-bundle-item-card',
  '.trainer-workbench',
  '.trainer-workbench-hero',
  '.trainer-workbench-metrics',
  '.trainer-workbench-metric',
  '.trainer-workbench-rail-section',
  '.trainer-workbench-rail',
  '.trainer-workbench-rail-card',
  '.trainer-workbench-editor-panel',
  '.trainer-editor-section',
  '.trainer-editor-field-grid',
  '.trainer-workbench-support-panels',
  '.trainer-workbench-panel',
  '.trainer-workbench-tabs',
  '.trainer-workbench-tab',
  '.trainer-video-upload-zone',
  'prefers-reduced-motion',
  'max-width: 480px',
  'scroll-snap-type: x proximity',
  'overflow-x: hidden',
  'overflow-wrap: anywhere',
  'min-width: 0',
  'white-space: normal',
  'minmax(min(100%, 280px), 1fr)',
  '.skeleton',
  '.focus-ring',
  '.profile-workbench',
  '.premium-main:has(.profile-workbench)',
  '.profile-workbench-customer',
  '.profile-workbench-trainer',
  '.profile-workbench::before',
  '.profile-workbench-hero',
  '.profile-workbench-hero-copy',
  '.profile-workbench-hero-actions',
  '.profile-workbench-nav',
  '.profile-workbench-nav-link',
  '.profile-workbench-nav-link-active',
  '.profile-workbench-metrics',
  '.profile-workbench-metric',
  '.profile-workbench-rail',
  '.profile-workbench-rail-card',
  '.profile-workbench-rail-card-active',
  '.profile-workbench-editor-panel',
  '.profile-workbench-support-panels',
  '.profile-workbench-panel',
  '.profile-workbench-section-header',
  '.profile-workbench-actions',
  '.profile-workbench-content',
  '.profile-editor-field-grid',
  'rgba(7,10,15',
  'backdrop-filter: blur(18px)',
  '.trainer-content-input',
  '.customer-workbench',
  '.customer-workbench-hero',
  '.customer-workbench-nav',
  '.customer-workbench-rail',
  '.customer-workbench-editor-panel',
  '.trainer-workbench-nav',
]) {
  if (!globals.includes(fragment)) {
    throw new Error(`globals.css missing design token/class: ${fragment}`);
  }
}

for (const forbiddenFragment of [
  '.profile-workbench { overflow-y: auto',
  '.trainer-workbench { overflow-y: auto',
  '.profile-workbench-panel { overflow-y: auto',
  '.profile-workbench-editor-panel { overflow-y: auto',
  '.trainer-workbench-editor-panel { overflow-y: auto',
]) {
  if (globals.includes(forbiddenFragment)) {
    throw new Error(`globals.css contains nested vertical scrollbar fragment: ${forbiddenFragment}`);
  }
}

if (!globals.includes("@import './profile-workbench.css'")) {
  throw new Error('globals.css missing profile-workbench.css import');
}

if (!globals.includes("@import './trainer-operations.css'")) {
  throw new Error('globals.css missing trainer-operations.css import');
}

if (!globals.includes("@import './trainer-finance-analytics.css'")) {
  throw new Error('globals.css missing trainer-finance-analytics.css import');
}

for (const fragment of [
  '.profile-workbench',
  '.profile-workbench-content',
  '.trainer-product-media-picker',
  '.trainer-product-media-picker-state',
  '.trainer-media-picker-card',
  '.trainer-selected-media-list',
  'overflow-y: visible !important',
]) {
  if (!profileWorkbenchCss.includes(fragment)) {
    throw new Error(`profile-workbench.css missing fragment: ${fragment}`);
  }
}

for (const fragment of ['.trainer-operations-page', '.trainer-operations-rail', '.trainer-operations-detail-panel', 'overflow-y: visible !important']) {
  if (!trainerOperationsCss.includes(fragment)) {
    throw new Error(`trainer-operations.css missing fragment: ${fragment}`);
  }
}

for (const fragment of ['.trainer-finance-workbench', '.trainer-finance-hero', '.trainer-finance-kpi-grid', '.trainer-finance-rail', '.trainer-finance-timeline', '.trainer-sales-workbench', '.trainer-sales-hero', '.trainer-analytics-workbench', '.trainer-analytics-hero', '.trainer-analytics-content-grid', 'overflow-y: visible !important']) {
  if (!trainerFinanceAnalyticsCss.includes(fragment)) {
    throw new Error(`trainer-finance-analytics.css missing fragment: ${fragment}`);
  }
}

for (const fragment of [
  'designTokens',
  'color',
  'spacing',
  'typography',
  'radius',
  'surfaceElevated',
  'surfaceGlass',
  'shadow',
  'containerMaxWidth',
]) {
  if (!tokens.includes(fragment)) {
    throw new Error(`tokens.ts missing fragment: ${fragment}`);
  }
}

for (const fragment of [
  'DSButton',
  'DSCard',
  'DSBadge',
  'DSTextField',
  'DSTextArea',
  'DSSelect',
  'DSModalShell',
  'DSCommandPalette',
  'DSCommandPaletteItem',
  'DSDataTable',
  'DSStatCard',
]) {
  if (!components.includes(fragment)) {
    throw new Error(`components.tsx missing primitive: ${fragment}`);
  }
}

for (const fragment of [
  'DSShell',
  'DSAdminLayout',
  'DSTrainerLayout',
  'DSStudentLayout',
  'DSPublicLayout',
  'DSPageHeader',
  'DSSection',
  'DSLayoutNav',
  'DSMobileActionBar',
]) {
  if (!layouts.includes(fragment)) {
    throw new Error(`layouts.tsx missing primitive: ${fragment}`);
  }
}

for (const fragment of [
  'DSBarChart',
  'DSPremiumLineChart',
  'DSDonutChart',
  'DSInsightChartCard',
  'DSCalendar',
  'DSKanbanBoard',
  'DSKanbanMoveEvent',
  'onCardMove',
  'KANBAN_DRAG_TYPE',
  'DSFileUpload',
  'DSRichTextEditor',
  'DSVideoPlayer',
  'DSStatsGrid',
  'DSComponentPreview',
  'DSDataTable',
  'DSStatCard',
]) {
  if (!library.includes(fragment)) {
    throw new Error(`library.tsx missing component: ${fragment}`);
  }
}

for (const fragment of [
  'DSThemeProvider',
  'useDSTheme',
  'DSThemeMode',
  'DSBrandName',
  'DSWhiteLabelTheme',
  'dsBrandPalettes',
  'getWhiteLabelThemeStyle',
]) {
  if (!theme.includes(fragment)) {
    throw new Error(`theme.tsx missing theme engine fragment: ${fragment}`);
  }
}

for (const fragment of [
  'DSSkeleton',
  'DSEmptyState',
  'DSToast',
  'DSToastStack',
  'DSLiveIndicator',
  'DSNotificationFeed',
  'DSNotificationFeedItem',
  'DSPresenceStack',
  'DSPresenceUser',
  'DSActivityTimeline',
  'DSActivityTimelineItem',
  'DSTransitionPanel',
  'DSStatusDot',
  'aria-live="polite"',
]) {
  if (!feedback.includes(fragment)) {
    throw new Error(`feedback.tsx missing motion/ui polish fragment: ${fragment}`);
  }
}

for (const fragment of ['AnimatedSection', 'AnimatedCard', 'AnimatedMetric', 'IntersectionObserver', 'prefers-reduced-motion']) {
  if (!animated.includes(fragment)) {
    throw new Error(`animated.tsx missing fragment: ${fragment}`);
  }
}

for (const fragment of ['useCountUp', 'requestAnimationFrame', 'durationMs', 'formatter', 'prefers-reduced-motion']) {
  if (!countUp.includes(fragment)) {
    throw new Error(`use-count-up.ts missing fragment: ${fragment}`);
  }
}

const marketingHome = fs.readFileSync(path.join(root, 'src/modules/public-storefront/components/marketing-home-page.tsx'), 'utf8');
const contentDetail = fs.readFileSync(path.join(root, 'src/modules/public-storefront/components/content-detail-page.tsx'), 'utf8');
const sessionNav = fs.readFileSync(path.join(root, 'src/components/session-nav.tsx'), 'utf8');
const checkoutPage = fs.readFileSync(path.join(root, 'src/modules/checkout/components/checkout-page.tsx'), 'utf8');
const checkoutSuccess = fs.readFileSync(path.join(root, 'src/app/checkout/success/page.tsx'), 'utf8');
const checkoutCancel = fs.readFileSync(path.join(root, 'src/app/checkout/cancel/page.tsx'), 'utf8');
const customerCabinet = fs.readFileSync(path.join(root, 'src/app/cabinet/page.tsx'), 'utf8');
const customerCabinetShell = fs.readFileSync(path.join(root, 'src/modules/customer-cabinet/components/customer-cabinet-shell.tsx'), 'utf8');
const customerCabinetNav = fs.readFileSync(path.join(root, 'src/modules/customer-cabinet/components/customer-cabinet-nav.tsx'), 'utf8');
const customerHub = fs.readFileSync(path.join(root, 'src/app/customer/hub/page.tsx'), 'utf8');
const learningPage = fs.readFileSync(path.join(root, 'src/app/learning/page.tsx'), 'utf8');
const messagesPage = fs.readFileSync(path.join(root, 'src/app/messages/page.tsx'), 'utf8');
const billingPage = fs.readFileSync(path.join(root, 'src/app/billing/page.tsx'), 'utf8');
const subscriptionsPage = fs.readFileSync(path.join(root, 'src/app/subscriptions/page.tsx'), 'utf8');
const entitlementsPage = fs.readFileSync(path.join(root, 'src/app/entitlements/page.tsx'), 'utf8');
const trainerShell = fs.readFileSync(path.join(root, 'src/modules/trainer-dashboard/components/trainer-dashboard-shell.tsx'), 'utf8');
const trainerCabinetShell = fs.readFileSync(path.join(root, 'src/modules/trainer-cabinet/components/trainer-cabinet-shell.tsx'), 'utf8');
const trainerCabinetNav = fs.readFileSync(path.join(root, 'src/modules/trainer-cabinet/components/trainer-cabinet-nav.tsx'), 'utf8');
const trainerCrmDashboard = fs.readFileSync(path.join(root, 'src/modules/trainer-crm/components/trainer-crm-dashboard.tsx'), 'utf8');
const trainerBookingDashboard = fs.readFileSync(path.join(root, 'src/modules/trainer-booking/components/trainer-booking-dashboard.tsx'), 'utf8');
const trainerOperationsFormat = fs.readFileSync(path.join(root, 'src/modules/trainer-operations/format.ts'), 'utf8');
const trainerSalesDashboard = fs.readFileSync(path.join(root, 'src/modules/trainer-sales/components/trainer-sales-dashboard.tsx'), 'utf8');
const trainerRevenueDashboard = fs.readFileSync(path.join(root, 'src/modules/trainer-revenue/components/trainer-revenue-dashboard.tsx'), 'utf8');
const trainerAnalyticsDashboard = fs.readFileSync(path.join(root, 'src/modules/trainer-analytics/components/trainer-content-analytics-dashboard.tsx'), 'utf8');
const trainerPayoutRequestDashboard = fs.readFileSync(path.join(root, 'src/modules/trainer-payouts/components/trainer-payout-request-dashboard.tsx'), 'utf8');
const profileWorkbench = fs.readFileSync(path.join(root, 'src/design-system/profile-workbench.tsx'), 'utf8');
const trainerFormat = fs.readFileSync(path.join(root, 'src/modules/trainer-cabinet/components/trainer-format.ts'), 'utf8');
const trainerDashboardPage = fs.readFileSync(path.join(root, 'src/app/trainer/dashboard/page.tsx'), 'utf8');
const trainerBusinessPage = fs.readFileSync(path.join(root, 'src/app/trainer/business/page.tsx'), 'utf8');
const trainerVideosPage = fs.readFileSync(path.join(root, 'src/app/trainer/videos/page.tsx'), 'utf8');
const trainerOnboardingPage = fs.readFileSync(path.join(root, 'src/app/trainer/onboarding/page.tsx'), 'utf8');
const trainerOnboardingChecklist = fs.readFileSync(path.join(root, 'src/modules/trainer-onboarding/components/trainer-onboarding-checklist.tsx'), 'utf8');
const trainerApplicationStatusPage = fs.readFileSync(path.join(root, 'src/app/trainer/application-status/page.tsx'), 'utf8');
const trainerReviewsPage = fs.readFileSync(path.join(root, 'src/app/trainer/reviews/page.tsx'), 'utf8');
const trainerProductBuilder = fs.readFileSync(path.join(root, 'src/modules/trainer-products/components/trainer-product-builder-dashboard.tsx'), 'utf8');
const trainerProductMediaPicker = fs.readFileSync(path.join(root, 'src/modules/trainer-products/components/trainer-product-media-picker.tsx'), 'utf8');
const trainerSelectedMediaList = fs.readFileSync(path.join(root, 'src/modules/trainer-products/components/trainer-selected-media-list.tsx'), 'utf8');
const trainerProductAdvancedIdField = fs.readFileSync(path.join(root, 'src/modules/trainer-products/components/trainer-product-advanced-id-field.tsx'), 'utf8');
const trainerUploadPanel = fs.readFileSync(path.join(root, 'src/modules/upload/components/trainer-upload-panel.tsx'), 'utf8');
const trainerContentStudio = fs.readFileSync(path.join(root, 'src/modules/upload/components/trainer-content-studio.tsx'), 'utf8');
const trainerVideoUploadCard = fs.readFileSync(path.join(root, 'src/modules/upload/components/trainer-video-upload-card.tsx'), 'utf8');
const trainerContentCard = fs.readFileSync(path.join(root, 'src/modules/upload/components/trainer-content-card.tsx'), 'utf8');
const trainerUploadFormat = fs.readFileSync(path.join(root, 'src/modules/upload/components/trainer-upload-format.ts'), 'utf8');
const trainerAssignmentsPage = fs.readFileSync(path.join(root, 'src/app/trainer/dashboard/assignments/page.tsx'), 'utf8');
const readme = readUtf8(repoRoot, 'README.md');
const buildReport = readUtf8(repoRoot, 'BUILD_REPORT.md');
const v165Doc = readUtf8(repoRoot, 'docs/design-system/v165_premium_trainer_dashboard_video_route_qa.md');
const v166Doc = readUtf8(repoRoot, 'docs/design-system/v166_production_visual_hardening.md');
const contractSource = readUtf8(root, 'tests/contracts/design-system-contract.test.js');
const productLanding = [
  contentDetail,
  fs.readFileSync(path.join(root, 'src/modules/public-storefront/components/product-purchase-panel.tsx'), 'utf8'),
  fs.readFileSync(path.join(root, 'src/modules/public-storefront/components/product-includes-section.tsx'), 'utf8'),
  fs.readFileSync(path.join(root, 'src/modules/public-storefront/components/product-access-section.tsx'), 'utf8'),
].join('\n');

for (const fragment of [
  'MarketingHomePage',
  'HeroBusinessConsole',
  'PlatformMapSection',
  'RoleWorkspaceSection',
  'CommercialProofBand',
  'ProductExperienceTimeline',
  'FinalPremiumCta',
  'Превратите тренерскую экспертизу',
  'Начать как тренер',
  'Посмотреть каталог',
]) {
  if (!marketingHome.includes(fragment)) {
    throw new Error(`marketing-home-page.tsx missing fragment: ${fragment}`);
  }
}

for (const fragment of [
  'ProductLandingHero',
  'ProductPurchasePanel',
  'ProductIncludesSection',
  'ProductAccessSection',
  'Купить доступ',
  'Что входит в доступ',
  'Что происходит после оплаты',
]) {
  if (!productLanding.includes(fragment)) {
    throw new Error(`content detail premium UI missing fragment: ${fragment}`);
  }
}

for (const fragment of [
  'premium-nav',
  'Каталог',
  'Тренеры',
  'Моё обучение',
  'Кабинет тренера',
  'Операции',
  'Финансы',
  'Стать тренером',
]) {
  if (!sessionNav.includes(fragment)) {
    throw new Error(`session-nav.tsx missing premium header fragment: ${fragment}`);
  }
}

for (const forbidden of ['Billing', 'Payouts', 'Admin cockpit', 'Payment ops', 'Trainer dashboard']) {
  if (sessionNav.includes(forbidden)) {
    throw new Error(`session-nav.tsx still contains crowded header label: ${forbidden}`);
  }
}

for (const fragment of [
  'CheckoutOrderSummary',
  'CheckoutPaymentMethod',
  'CheckoutTrustPanel',
  'checkoutApi.checkoutOneTime',
  'idempotency_key',
  'Оформление доступа',
  'Подтвердить покупку',
  'Создаём заказ...',
  'Чтобы оформить доступ, войдите в аккаунт',
]) {
  if (!checkoutPage.includes(fragment)) {
    throw new Error(`checkout page missing v155 fragment: ${fragment}`);
  }
}

for (const fragment of ['Доступ оформлен', 'Перейти к моим доступам', 'Вернуться в каталог']) {
  if (!checkoutSuccess.includes(fragment)) {
    throw new Error(`checkout success missing v155 fragment: ${fragment}`);
  }
}

for (const fragment of ['Покупка не завершена', 'Вернуться в каталог', 'Открыть заказ']) {
  if (!checkoutCancel.includes(fragment)) {
    throw new Error(`checkout cancel missing v155 fragment: ${fragment}`);
  }
}

for (const forbidden of ['Checkout success', 'Checkout cancelled', 'Commercial metadata']) {
  if ([checkoutSuccess, checkoutCancel, contentDetail].some((source) => source.includes(forbidden))) {
    throw new Error(`premium storefront still contains technical copy: ${forbidden}`);
  }
}

for (const [fileName, source] of [
  ['cabinet/page.tsx', customerCabinet],
  ['customer/hub/page.tsx', customerHub],
  ['learning/page.tsx', learningPage],
  ['messages/page.tsx', messagesPage],
  ['billing/page.tsx', billingPage],
  ['subscriptions/page.tsx', subscriptionsPage],
  ['entitlements/page.tsx', entitlementsPage],
]) {
  if (!source.includes('CustomerCabinetShell')) {
    throw new Error(`${fileName} must use CustomerCabinetShell`);
  }
}

for (const fragment of ['Личный кабинет', 'Ваши программы, доступы, заказы, подписки и сообщения']) {
  if (!customerCabinet.includes(fragment)) {
    throw new Error(`cabinet/page.tsx missing customer dashboard fragment: ${fragment}`);
  }
}

for (const fragment of ['Моё обучение', 'profile-workbench-support-panels', 'Продолжить', 'Открыть урок', 'Завершить урок']) {
  if (!learningPage.includes(fragment)) {
    throw new Error(`learning/page.tsx missing premium learning fragment: ${fragment}`);
  }
}

for (const fragment of ['Сообщения', 'profile-workbench-rail-section', 'Новый диалог', 'Получатель', 'Первое сообщение']) {
  if (!messagesPage.includes(fragment)) {
    throw new Error(`messages/page.tsx missing premium inbox fragment: ${fragment}`);
  }
}

for (const fragment of ['Финансы и документы', 'Покупки', 'Чеки и документы', 'Активные доступы']) {
  if (!billingPage.includes(fragment)) {
    throw new Error(`billing/page.tsx missing finance fragment: ${fragment}`);
  }
}

for (const fragment of ['Мои доступы', 'Номер доступа', 'Перейти к обучению']) {
  if (!entitlementsPage.includes(fragment)) {
    throw new Error(`entitlements/page.tsx missing access fragment: ${fragment}`);
  }
}

for (const [fileName, source, forbiddenFragments] of [
  ['billing/page.tsx', billingPage, ['<h1>Billing</h1>', '>Billing<', 'Customer billing', 'Загрузка billing center']],
  ['subscriptions/page.tsx', subscriptionsPage, ['Sync access', 'Lifecycle policy', 'Readiness', 'v8.46', 'virtual statuses', 'customer_self_service']],
  ['messages/page.tsx', messagesPage, ['recipient user id', 'Unread', 'Role', 'Selected', 'notification hooks', 'trainer ↔ student']],
  ['entitlements/page.tsx', entitlementsPage, ['Entitlement ID', '<th>ID</th>', '>Bundle<']],
]) {
  for (const forbiddenFragment of forbiddenFragments) {
    if (source.includes(forbiddenFragment)) {
      throw new Error(`${fileName} still contains customer technical label: ${forbiddenFragment}`);
    }
  }
}

for (const fragment of ['TrainerCabinetShell', 'Кабинет тренера']) {
  if (!trainerShell.includes(fragment) && !trainerCabinetShell.includes(fragment)) {
    throw new Error(`trainer shell missing fragment: ${fragment}`);
  }
}

for (const fragment of ['Обзор', 'Бизнес', 'Продукты', 'Видео', 'Ученики', 'Выплаты', 'Отзывы']) {
  if (!trainerCabinetNav.includes(fragment)) {
    throw new Error(`trainer nav missing Russian label: ${fragment}`);
  }
}

for (const fragment of ['formatTrainerMoney', 'trainerStatusLabel', 'trainerPayoutStatusLabel', 'trainerOrderStatusLabel']) {
  if (!trainerFormat.includes(fragment)) {
    throw new Error(`trainer-format.ts missing helper: ${fragment}`);
  }
}

for (const [fileName, source, forbiddenFragments] of [
  ['trainer-dashboard-shell.tsx', trainerShell, ['DSTrainerLayout', 'DSLayoutNav', "label: 'Dashboard'", "label: 'Onboarding'", "label: 'Payouts'", 'Trainer area', 'Production trainer flow']],
  ['trainer/dashboard/page.tsx', trainerDashboardPage, ['All visible orders', 'Gross payment volume', 'Payment records', 'Draft videos', 'Published videos', 'Pending review', 'Sales count', 'slug:', 'Headline', 'Bio']],
  ['trainer/business/page.tsx', trainerBusinessPage, ['Available payout', 'Business readiness', 'Revenue trend', 'Top products', 'destination not set', 'Moderation & risk']],
  ['trainer/reviews/page.tsx', trainerReviewsPage, ['Quality</span>', '<h2>Readiness</h2>', '>ok<', '>attention<']],
]) {
  for (const forbiddenFragment of forbiddenFragments) {
    if (source.includes(forbiddenFragment)) {
      throw new Error(`${fileName} still contains trainer technical label: ${forbiddenFragment}`);
    }
  }
}

if (!trainerShell.includes('TrainerCabinetShell')) {
  throw new Error('trainer-dashboard-shell.tsx must wrap TrainerCabinetShell');
}

for (const forbiddenFragment of ['DSDataTable', 'DSSection', 'DSRichTextEditor', 'CRM Core', 'Search customer', 'Save note', 'Pinned note', 'Select segment', 'Assign segment']) {
  if (trainerCrmDashboard.includes(forbiddenFragment)) {
    throw new Error(`trainer CRM dashboard still contains technical fragment: ${forbiddenFragment}`);
  }
}

for (const fragment of ['trainer-operations-page', 'Ученики', 'Заметки тренера', 'Сегменты']) {
  if (!trainerCrmDashboard.includes(fragment)) {
    throw new Error(`trainer CRM dashboard missing v161 fragment: ${fragment}`);
  }
}

for (const forbiddenFragment of ['DSDataTable', 'DSCalendar', 'Booking / Schedule', 'Refresh', 'Add rule', 'Generate', 'Check-in', 'Check-out', 'No-show', 'Cancel', 'Waitlist']) {
  if (trainerBookingDashboard.includes(forbiddenFragment)) {
    throw new Error(`trainer booking dashboard still contains technical fragment: ${forbiddenFragment}`);
  }
}

for (const fragment of ['trainer-operations-page', 'Расписание', 'Правила доступности', 'Создание слотов']) {
  if (!trainerBookingDashboard.includes(fragment)) {
    throw new Error(`trainer booking dashboard missing v161 fragment: ${fragment}`);
  }
}

for (const fragment of ['trainerOperationStatusLabel', 'trainerOperationStatusTone']) {
  if (!trainerOperationsFormat.includes(fragment)) {
    throw new Error(`trainer operations format missing fragment: ${fragment}`);
  }
}

for (const [fileName, source, forbiddenFragments] of [
  ['trainer-sales-dashboard.tsx', trainerSalesDashboard, ['table-wrap', '<table', 'grid-4', 'Net revenue', 'Gross revenue', 'Purchases', 'Views', 'Direction', 'Source', 'Payout requests', 'source_type:', 'source_id:', 'v8.43']],
  ['trainer-revenue-dashboard.tsx', trainerRevenueDashboard, ['table-wrap', '<table', 'grid-4', 'Net revenue', 'Gross revenue', 'Purchases', 'Views', 'Direction', 'Source', 'Payout requests', 'source_type:', 'source_id:', 'v8.43']],
  ['trainer-content-analytics-dashboard.tsx', trainerAnalyticsDashboard, ['table-wrap', '<table', 'grid-4', 'Net revenue', 'Gross revenue', 'Purchases', 'Views', 'Direction', 'Source', 'Payout requests', 'Content performance analytics', 'Order item matching', 'UUID/slug', 'v8.43']],
]) {
  for (const forbiddenFragment of forbiddenFragments) {
    if (source.includes(forbiddenFragment)) {
      throw new Error(`${fileName} still contains v162 forbidden fragment: ${forbiddenFragment}`);
    }
  }
}

for (const fragment of ['trainer-sales-workbench', 'trainer-sales-hero', 'Выручка', 'Лучшие продукты', 'Последние продажи', 'Возвраты и риски', 'Доступ учеников']) {
  if (!trainerSalesDashboard.includes(fragment)) {
    throw new Error(`trainer sales dashboard missing v162 fragment: ${fragment}`);
  }
}

for (const fragment of ['trainer-finance-workbench', 'trainer-finance-hero', 'Финансы', 'Wallet cockpit', 'Источники дохода', 'Движение средств', 'Заявки на выплаты', 'sourceLabel', 'directionLabel']) {
  if (!trainerRevenueDashboard.includes(fragment)) {
    throw new Error(`trainer revenue dashboard missing v162 fragment: ${fragment}`);
  }
}

for (const fragment of ['trainer-analytics-workbench', 'trainer-analytics-hero', 'Аналитика контента', 'Лучший контент', 'Последние продажи', 'Качество данных', 'trainer-analytics-progress']) {
  if (!trainerAnalyticsDashboard.includes(fragment)) {
    throw new Error(`trainer analytics dashboard missing v162 fragment: ${fragment}`);
  }
}

for (const [fileName, source, forbiddenFragments] of [
  ['trainer/dashboard/assignments/page.tsx', trainerAssignmentsPage, ['grid-4', 'list-item', 'style={{', 'ID продукта', 'ID урока', 'placeholder="оценка"', 'Сохранить ревью', 'Published']],
  ['trainer-payout-request-dashboard.tsx', trainerPayoutRequestDashboard, ['table-wrap', '<table', 'payout flow', 'available balance', 'locked balance', 'Payout requests', '<th>Amount</th>', '<th>Status</th>', '<th>Destination</th>', '<th>Lifecycle</th>', 'Bank card', 'SBP']],
  ['trainer/reviews/page.tsx', trainerReviewsPage, ['<h2>Quality', '<h2>Readiness', 'style={{', 'raw status']],
]) {
  for (const forbiddenFragment of forbiddenFragments) {
    if (source.includes(forbiddenFragment)) {
      throw new Error(`${fileName} still contains v163 forbidden fragment: ${forbiddenFragment}`);
    }
  }
}

for (const fragment of ['trainer-education-workbench', 'trainer-education-hero', 'Новое задание', 'Опубликованные задания', 'Ответы учеников', 'mapAssignmentStatusLabel', 'mapSubmissionStatusLabel', 'mapContentTypeLabel']) {
  if (!trainerAssignmentsPage.includes(fragment)) {
    throw new Error(`trainer assignments page missing v163 fragment: ${fragment}`);
  }
}

for (const fragment of ['trainer-payout-workbench', 'trainer-payout-hero', 'Новая заявка на выплату', 'Как проходит выплата', 'История заявок', 'mapPayoutStatusLabel']) {
  if (!trainerPayoutRequestDashboard.includes(fragment)) {
    throw new Error(`trainer payout request dashboard missing v163 fragment: ${fragment}`);
  }
}

for (const fragment of ['trainer-review-workbench', 'trainer-review-hero', 'Отзывы', 'Готовность к продажам', 'Ответ тренера', 'mapReviewStatusLabel', 'mapReadinessTone']) {
  if (!trainerReviewsPage.includes(fragment)) {
    throw new Error(`trainer reviews page missing v163 fragment: ${fragment}`);
  }
}

for (const fragment of ['.trainer-education-workbench', '.trainer-review-workbench', '.trainer-payout-workbench', '.trainer-education-hero', '.trainer-review-hero', '.trainer-payout-hero', '.trainer-payout-timeline', 'overflow-y: visible !important']) {
  if (!globals.includes(fragment)) {
    throw new Error(`globals.css missing v163 fragment: ${fragment}`);
  }
}

for (const [fileName, source, forbiddenFragments] of [
  ['trainer/business/page.tsx', trainerBusinessPage, ['Available payout', 'Reserved payout', 'Lifetime earned', 'Active payouts', 'Business readiness', 'Content inventory', 'Content studio', 'Drafts', 'Published', 'Pending review', 'Order items', 'Top products', 'Latest payout requests', 'destination not set', 'Moderation & risk', 'Open cases', 'Risk flags', 'className="card', 'className="stack', 'className="row', 'style={{']],
  ['trainer-onboarding-checklist.tsx', trainerOnboardingChecklist, ['<span className="stat-label">Progress</span>', '<span className="stat-label">Application</span>', '<span className="stat-label">Dashboard</span>', '<span className="stat-label">Role</span>', 'Trainer application', 'Brand name', 'Legal name', 'Experience years', 'Positioning / bio', 'Production readiness steps', 'Сохранить draft', 'Under review', 'Changes requested', 'className="card', 'className="stack', 'className="row', 'style={{']],
  ['trainer/application-status/page.tsx', trainerApplicationStatusPage, ['Статус заявки тренера', 'className="card', 'className="stack', 'className="row', 'style={{', 'trainerStatusLabel']],
]) {
  for (const forbiddenFragment of forbiddenFragments) {
    if (source.includes(forbiddenFragment)) {
      throw new Error(`${fileName} still contains v164 forbidden fragment: ${forbiddenFragment}`);
    }
  }
}

for (const fragment of ['trainer-business-workbench', 'trainer-business-hero', 'trainer-business-kpi-grid', 'trainer-business-layout', 'Готовность бизнеса', 'Контент и продукты', 'Динамика выручки', 'Лучшие продукты', 'Последние заявки на выплаты', 'Риски и модерация', 'mapReadinessStatusLabel', 'mapPayoutStatusLabel', 'mapModerationStatusLabel']) {
  if (!trainerBusinessPage.includes(fragment)) {
    throw new Error(`trainer business page missing v164 fragment: ${fragment}`);
  }
}

for (const fragment of ['Профиль тренера', 'Заявка, публичное позиционирование и готовность кабинета']) {
  if (!trainerOnboardingPage.includes(fragment)) {
    throw new Error(`trainer onboarding page missing v164 fragment: ${fragment}`);
  }
}

for (const fragment of ['trainer-onboarding-workbench', 'trainer-onboarding-hero', 'trainer-onboarding-kpi-grid', 'trainer-onboarding-layout', 'Заявка тренера', 'Шаги готовности', 'Сохранить черновик', 'Отправить на проверку', 'Смотреть статус проверки', 'mapTrainerApplicationStatusLabel', 'mapStepStatusLabel', 'mapRoleLabel']) {
  if (!trainerOnboardingChecklist.includes(fragment)) {
    throw new Error(`trainer onboarding checklist missing v164 fragment: ${fragment}`);
  }
}

for (const fragment of ['trainer-status-workbench', 'trainer-status-hero', 'trainer-status-kpi-grid', 'trainer-status-layout', 'Результат проверки', 'Шаги готовности', 'Редактировать заявку', 'Перейти к продуктам', 'mapTrainerApplicationStatusLabel', 'mapStepStatusLabel', 'mapRoleLabel']) {
  if (!trainerApplicationStatusPage.includes(fragment)) {
    throw new Error(`trainer application status page missing v164 fragment: ${fragment}`);
  }
}

for (const fragment of ['.trainer-business-workbench', '.trainer-business-hero', '.trainer-business-kpi-grid', '.trainer-business-layout', '.trainer-business-main', '.trainer-business-sidebar', '.trainer-business-panel', '.trainer-business-card', '.trainer-business-timeline', '.trainer-business-timeline-item', '.trainer-business-readiness-card', '.trainer-business-risk-card', '.trainer-onboarding-workbench', '.trainer-onboarding-hero', '.trainer-onboarding-kpi-grid', '.trainer-onboarding-layout', '.trainer-onboarding-main', '.trainer-onboarding-sidebar', '.trainer-onboarding-form-card', '.trainer-onboarding-step-card', '.trainer-onboarding-status-card', '.trainer-onboarding-field', '.trainer-onboarding-actions', '.trainer-onboarding-alert', '.trainer-onboarding-empty', '.trainer-status-workbench', '.trainer-status-hero', '.trainer-status-kpi-grid', '.trainer-status-layout', '.trainer-status-panel', '.trainer-status-step-card', '.trainer-status-result-card', '.trainer-status-timeline']) {
  if (!globals.includes(fragment)) {
    throw new Error(`globals.css missing v164 fragment: ${fragment}`);
  }
}

for (const [fileName, source, forbiddenFragments] of [
  ['trainer/dashboard/page.tsx', trainerDashboardPage, ['TrainerDashboardCard', 'TrainerMetricCard', 'TrainerEmptyState', 'TrainerLoadingState', 'TrainerErrorState', 'trainer-metric-grid', 'trainer-dashboard-grid', 'Следующее действие', 'Публичный профиль', 'Все видимые заказы', 'Записи оплат', 'Executive cockpit', 'className="card', 'className="stack', 'className="row', 'style={{']],
  ['trainer/videos/page.tsx', trainerVideosPage, ['<TrainerUploadPanel />']],
  ['trainer-content-studio.tsx', trainerContentStudio, ['profile-workbench-hero-copy', 'profile-workbench-hero-actions', 'Подготавливаем загрузку...', 'Загружаем файл...', 'Завершаем обработку...', 'Описание урока', 'Порядок</span>', 'Видеофайл</span>', 'Открытый урок для просмотра']],
]) {
  for (const forbiddenFragment of forbiddenFragments) {
    if (source.includes(forbiddenFragment)) {
      throw new Error(`${fileName} still contains v165 forbidden fragment: ${forbiddenFragment}`);
    }
  }
}

for (const fragment of ['trainer-home-workbench', 'trainer-home-hero', 'trainer-home-hero-actions', 'trainer-home-hero-metric', 'trainer-home-alert', 'trainer-home-loading', 'trainer-home-kpi-grid', 'trainer-home-kpi-card', 'trainer-home-layout', 'trainer-home-main', 'trainer-home-sidebar', 'trainer-home-panel', 'trainer-home-action-grid', 'trainer-home-action-card', 'trainer-home-timeline', 'trainer-home-timeline-item', 'trainer-home-product-rail', 'trainer-home-product-card', 'trainer-home-profile-card', 'trainer-home-status-grid', 'trainer-home-status-item', 'Кабинет тренера', 'Что сделать дальше', 'Динамика выручки', 'Лучшие продукты', 'Профиль и доступ']) {
  if (!trainerDashboardPage.includes(fragment)) {
    throw new Error(`trainer dashboard page missing v165 fragment: ${fragment}`);
  }
}

for (const fragment of ['trainer-video-studio-workbench', 'trainer-video-studio-hero', 'trainer-video-studio-hero-content', 'trainer-video-studio-actions', 'СТУДИЯ МАТЕРИАЛОВ', 'Видео и материалы', 'Загрузить видео', 'Создать продукт', 'Посмотреть аналитику', 'compactHero']) {
  if (!trainerVideosPage.includes(fragment)) {
    throw new Error(`trainer videos page missing v165 fragment: ${fragment}`);
  }
}

for (const fragment of ['TrainerContentStudio({ compactHero = false }', 'trainer-content-workbench', 'trainer-content-workbench--compact', 'trainer-content-toolbar', 'trainer-content-tabs', 'trainer-content-tab', 'trainer-content-tab--active', 'trainer-content-kpi-grid', 'trainer-content-kpi-card', 'trainer-content-alert', 'trainer-content-alert--success', 'trainer-content-alert--danger', 'trainer-content-layout', 'trainer-content-library', 'trainer-content-editor', 'trainer-content-preview', 'trainer-video-studio-frame', 'trainer-video-studio-toolbar', 'Рабочая область', 'Новый видеоурок', 'Новая программа', 'Новый набор', 'Сначала загрузите файл, затем сохраните описание и отправьте материал на проверку.', 'Подготавливаем загрузку…', 'Загружаем файл…', 'Завершаем обработку…', 'Видео из библиотеки', 'Бесплатный предпросмотр', 'Добавьте видео или программу, чтобы собрать набор.']) {
  if (!trainerContentStudio.includes(fragment) && !trainerVideoUploadCard.includes(fragment)) {
    throw new Error(`trainer content studio/upload missing v165 fragment: ${fragment}`);
  }
}

for (const fragment of ['trainer-content-card', 'trainer-content-card--active', 'trainer-content-card-header', 'trainer-content-card-title', 'trainer-content-card-meta', 'trainer-content-card-actions', 'trainer-content-rail-card-premium-active', 'Адрес настроен', 'Адрес не указан']) {
  if (!trainerContentCard.includes(fragment)) {
    throw new Error(`trainer content card missing v165 fragment: ${fragment}`);
  }
}

for (const fragment of ['/* v165.2 trainer dashboard/video studio scoped polish */', '.trainer-home-workbench', '.trainer-home-hero', '.trainer-home-hero-actions', '.trainer-home-hero-metric', '.trainer-home-alert', '.trainer-home-loading', '.trainer-home-kpi-grid', '.trainer-home-kpi-card', '.trainer-home-layout', '.trainer-home-main', '.trainer-home-sidebar', '.trainer-home-panel', '.trainer-home-action-grid', '.trainer-home-action-card', '.trainer-home-timeline', '.trainer-home-timeline-item', '.trainer-home-product-rail', '.trainer-home-product-card', '.trainer-home-profile-card', '.trainer-home-status-grid', '.trainer-home-status-item', '.trainer-video-studio-workbench', '.trainer-video-studio-hero', '.trainer-video-studio-hero-content', '.trainer-video-studio-actions', '.trainer-video-studio-frame', '.trainer-video-studio-toolbar', '.trainer-video-upload-helper', '.trainer-content-workbench', '.trainer-content-workbench--compact', '.trainer-content-toolbar', '.trainer-content-tabs', '.trainer-content-tab', '.trainer-content-tab--active', '.trainer-content-kpi-grid', '.trainer-content-kpi-card', '.trainer-content-alert', '.trainer-content-alert--success', '.trainer-content-alert--danger', '.trainer-content-layout', '.trainer-content-library', '.trainer-content-editor', '.trainer-content-preview', '.trainer-content-card', '.trainer-content-card--active', '.trainer-content-card-header', '.trainer-content-card-title', '.trainer-content-card-meta', '.trainer-content-card-actions', '.trainer-content-upload-card', '.trainer-content-upload-dropzone', '.trainer-content-upload-dropzone--highlighted', '.trainer-content-file-name', '.trainer-content-upload-step', '.trainer-content-rail-card-premium-active', 'overflow-y: hidden', 'scroll-snap-type: x mandatory']) {
  if (!globals.includes(fragment)) {
    throw new Error(`globals.css missing v165 fragment: ${fragment}`);
  }
}

for (const fragment of ['v165.3 | Trainer Dashboard and Video Studio CSS Contract Lock | Done', 'v165.3 — Trainer Dashboard and Video Studio CSS Contract Lock']) {
  if (!readme.includes(fragment)) {
    throw new Error(`README.md missing v165.3 fragment: ${fragment}`);
  }
}

for (const fragment of ['v165.3', 'Why v165.3 Was Needed', 'trainer-home', 'trainer-video-studio', 'trainer-content']) {
  if (!v165Doc.includes(fragment)) {
    throw new Error(`v165 design-system doc missing v165.3 fragment: ${fragment}`);
  }
}

for (const fragment of ['TrainerContentStudio', 'compactHero={compactHero}']) {
  if (!trainerUploadPanel.includes(fragment)) {
    throw new Error(`trainer upload panel missing v165.3 fragment: ${fragment}`);
  }
}

for (const fragment of ['trainer-video-studio-workbench', '<TrainerUploadPanel compactHero />']) {
  if (!trainerVideosPage.includes(fragment)) {
    throw new Error(`trainer videos page missing v165.3 fragment: ${fragment}`);
  }
}

for (const fragment of ['trainer-home-workbench', 'trainer-home-hero', 'trainer-home-kpi-grid', 'trainer-home-layout', 'trainer-home-main', 'trainer-home-sidebar']) {
  if (!trainerDashboardPage.includes(fragment)) {
    throw new Error(`trainer dashboard page missing v165.3 fragment: ${fragment}`);
  }
}

for (const fragment of ['trainer-content-workbench', 'trainer-content-workbench--compact', 'trainer-content-toolbar', 'trainer-content-tabs', 'trainer-content-kpi-grid', 'trainer-content-layout']) {
  if (!trainerContentStudio.includes(fragment)) {
    throw new Error(`trainer content studio missing v165.3 fragment: ${fragment}`);
  }
}

for (const fragment of ['trainer-content-card', 'trainer-content-card--active', 'trainer-content-card-header', 'trainer-content-card-title', 'trainer-content-card-meta', 'trainer-content-card-actions']) {
  if (!trainerContentCard.includes(fragment)) {
    throw new Error(`trainer content card missing v165.3 fragment: ${fragment}`);
  }
}

for (const fragment of ['trainer-content-upload-card', 'trainer-content-upload-dropzone', 'trainer-content-upload-dropzone--highlighted', 'trainer-content-file-name', 'trainer-content-upload-step']) {
  if (!trainerVideoUploadCard.includes(fragment)) {
    throw new Error(`trainer video upload card missing v165.3 fragment: ${fragment}`);
  }
}

for (const fragment of ['v165.3 trainer dashboard/video studio CSS contract lock', '.trainer-home-workbench', '.trainer-home-hero', '.trainer-home-kpi-grid', '.trainer-home-layout', '.trainer-video-studio-workbench', '.trainer-video-studio-hero', '.trainer-content-workbench', '.trainer-content-workbench--compact', '.trainer-content-card--active', '.trainer-content-upload-dropzone', '.trainer-content-file-name', '@media (max-width: 1024px)', '@media (max-width: 720px)', 'overflow-wrap: anywhere', 'scroll-snap-type: x mandatory']) {
  if (!globals.includes(fragment)) {
    throw new Error(`globals.css missing v165.3 fragment: ${fragment}`);
  }
}

assertIncludesAll(readme, ['v166 | Production Visual Hardening Pass | Done', 'v166 — Production Visual Hardening Pass'], 'README.md v166');

assertIncludesAll(
  readme,
  [
    'current version v166.2',
    'v166.1 | Production Visual Hardening CSS and Contract Lock | Done',
    'v166.2 | Contract Gate Repair and Documentation Formatting Lock | Current',
    'v151-v166.2 premium storefront, customer workspace and trainer workspace block',
    'v166.2 — Contract Gate Repair and Documentation Formatting Lock',
  ],
  'README.md v166.2',
);

assertIncludesAll(
  v166Doc,
  [
    'v166 / v166.1 / v166.2',
    'Why v166.1 Was Needed',
    'Why v166.2 Was Needed',
    'Contract Gate Repair',
    'Route QA Matrix',
    'Public storefront',
    'Customer',
    'Trainer',
    'Admin/Ops',
    'Backend unchanged',
    '.next/trace',
  ],
  'v166 design-system doc',
);

assertIncludesAll(v166Doc, ['/catalog', '/checkout', '/customer/hub', '/learning', '/trainer/dashboard', '/trainer/videos', '/admin'], 'v166 route QA doc');

assertIncludesAll(
  buildReport,
  [
    'v166.2',
    'Contract Gate Repair and Documentation Formatting Lock',
    'test:contracts',
    'npm run build',
    '.next/trace',
  ],
  'BUILD_REPORT.md v166.2',
);

assertIncludesAll(
  globals,
  [
    'v166 production visual hardening',
    'min-width: 0',
    'overflow-wrap: anywhere',
    'scroll-snap-type: x mandatory',
    '@media (max-width: 1180px)',
    '@media (max-width: 1024px)',
    '@media (max-width: 768px)',
    '@media (max-width: 640px)',
    '.premium-empty-state',
    '.premium-loading-state',
    '.premium-error-state',
    '.premium-alert',
  ],
  'globals.css v166',
);

assertIncludesAll(
  globals,
  [
    'v166.1 production visual hardening CSS and contract lock',
    'overflow-wrap: anywhere',
    'word-break: normal',
    'scroll-snap-type: x mandatory',
    '@media (max-width: 1180px)',
    '@media (max-width: 1024px)',
    '@media (max-width: 768px)',
    '@media (max-width: 640px)',
    '.trainer-home-workbench',
    '.trainer-video-studio-workbench',
    '.trainer-content-upload-dropzone',
    '.trainer-content-card--active',
    '.premium-empty-state',
    '.premium-error-state',
    '.premium-loading-state',
    '[class*="customer-"]',
    '[class*="trainer-"]',
    '[class*="admin-"]',
    '[class*="checkout-"]',
    '[class*="marketplace-"]',
    '[class*="product-"]',
    '[class*="learning-"]',
  ],
  'globals.css v166.1',
);

assertExcludesAll(
  contractSource,
  [
    '[' + "''" + ']',
    '[' + '""' + ']',
    "for (const fragment of [" + "''" + '])',
    'for (const fragment of [' + '""' + '])',
  ],
  'design-system-contract.test.js',
);

for (const fragment of ['v165.3', 'Why v165.3 Was Needed', 'v165.3 trainer dashboard/video studio CSS contract lock', '.trainer-home-workbench', '.trainer-video-studio-workbench', '.trainer-content-upload-dropzone', '.trainer-content-card--active']) {
  if (!`${readme}\n${v165Doc}\n${globals}\n${fs.readFileSync(__filename, 'utf8')}`.includes(fragment)) {
    throw new Error(`v165.3 contract fragment lost during v166: ${fragment}`);
  }
}

for (const fragment of ['v165.3']) {
  if (!v165Doc.includes(fragment)) {
    throw new Error(`v165 doc missing preservation fragment: ${fragment}`);
  }
}

for (const fragment of ['compactHero={compactHero}']) {
  if (!trainerUploadPanel.includes(fragment)) {
    throw new Error(`trainer upload panel missing v166.1 preservation fragment: ${fragment}`);
  }
}

for (const fragment of ['<TrainerUploadPanel compactHero />']) {
  if (!trainerVideosPage.includes(fragment)) {
    throw new Error(`trainer videos page missing v166.1 preservation fragment: ${fragment}`);
  }
}

for (const fragment of ['trainer-home-workbench']) {
  if (!trainerDashboardPage.includes(fragment)) {
    throw new Error(`trainer dashboard page missing v166.1 preservation fragment: ${fragment}`);
  }
}

for (const fragment of ['trainer-content-card--active']) {
  if (!trainerContentCard.includes(fragment)) {
    throw new Error(`trainer content card missing v166.1 preservation fragment: ${fragment}`);
  }
}

for (const fragment of ['trainer-content-upload-dropzone']) {
  if (!trainerVideoUploadCard.includes(fragment)) {
    throw new Error(`trainer video upload card missing v166.1 preservation fragment: ${fragment}`);
  }
}


for (const fragment of ['Продукты', 'Готовность к публикации', 'Предпросмотр в каталоге', 'Новый продукт', '/trainer/videos?tab=videos&intent=upload', 'Загрузить видео']) {
  if (!trainerProductBuilder.includes(fragment)) {
    throw new Error(`trainer product builder missing fragment: ${fragment}`);
  }
}

for (const fragment of ['loadMediaVideos', 'normalizeMediaVideos', 'mediaVideos', 'mediaVideosLoading', 'mediaVideosError', 'TrainerProductMediaPicker', 'TrainerSelectedMediaList', 'TrainerProductAdvancedIdField', 'useSearchParams', "/trainer/videos?tab=videos&intent=upload", "intent') === 'attach-video", 'videos={mediaVideos}', 'onRetry={loadMediaVideos}', 'Выберите загруженное видео', 'trainer-product-materials-panel-highlighted', 'trainer-product-materials-hint']) {
  if (!trainerProductBuilder.includes(fragment)) {
    throw new Error(`trainer product builder missing v160 media picker fragment: ${fragment}`);
  }
}

if (trainerProductBuilder.includes('<span>ID видео из библиотеки</span>')) {
  throw new Error('trainer product builder still shows raw video ids as the main materials label');
}

if (trainerProductMediaPicker.includes('uploadApi.listMyVideos')) {
  throw new Error('trainer product media picker still fetches its own video library');
}

for (const forbiddenFragment of ['useEffect', 'useState']) {
  if (trainerProductMediaPicker.includes(forbiddenFragment)) {
    throw new Error(`trainer product media picker still owns local async state: ${forbiddenFragment}`);
  }
}

for (const fragment of ['videos:', 'onRetry', 'Библиотека видео', 'Загрузить видео', 'trainer-product-media-picker-state', 'trainer-media-picker-card', 'trainer-media-picker-card-status', 'Видео пока нет', 'Выбрать', 'Выбрано', 'Файл добавлен', 'Файл не добавлен']) {
  if (!trainerProductMediaPicker.includes(fragment)) {
    throw new Error(`trainer product media picker missing fragment: ${fragment}`);
  }
}

if (trainerSelectedMediaList.includes('uploadApi.listMyVideos')) {
  throw new Error('trainer selected media list still fetches its own video library');
}

for (const forbiddenFragment of ['useEffect', 'useState']) {
  if (trainerSelectedMediaList.includes(forbiddenFragment)) {
    throw new Error(`trainer selected media list still owns local async state: ${forbiddenFragment}`);
  }
}

if (trainerSelectedMediaList.includes('Видео из библиотеки')) {
  throw new Error('trainer selected media list still contains technical fallback label');
}

for (const fragment of ['videoById', 'Выбранные материалы', 'Материалы ещё не выбраны', 'Выбранное видео', 'Видео уже добавлено в продукт', 'Убрать']) {
  if (!trainerSelectedMediaList.includes(fragment)) {
    throw new Error(`trainer selected media list missing fragment: ${fragment}`);
  }
}

for (const fragment of ['Расширенная настройка', 'Показать поле ID', 'Скрыть поле ID', 'ID видео', 'Один ID на строку']) {
  if (!trainerProductAdvancedIdField.includes(fragment)) {
    throw new Error(`trainer product advanced id field missing fragment: ${fragment}`);
  }
}

for (const forbiddenFragment of ['description', 'Публичный адрес:']) {
  if (trainerContentCard.includes(forbiddenFragment)) {
    throw new Error(`trainer content card still contains overloaded rail fragment: ${forbiddenFragment}`);
  }
}

for (const fragment of ['/trainer/dashboard/products?intent=attach-video', 'Перейти к продуктам', 'Видеоурок сохранён. Теперь его можно добавить в продукт.']) {
  if (!trainerContentStudio.includes(fragment)) {
    throw new Error(`trainer content studio missing product return path fragment: ${fragment}`);
  }
}

for (const fragment of ['Адрес настроен', 'Адрес не указан']) {
  if (!trainerContentCard.includes(fragment)) {
    throw new Error(`trainer content card missing simplified address fragment: ${fragment}`);
  }
}

for (const fragment of ['trainer-workbench-local-header', 'trainer-workbench-local-header-actions', 'trainer-workbench-empty-rail-card']) {
  if (!trainerProductBuilder.includes(fragment)) {
    throw new Error(`trainer product builder missing v159.2 fragment: ${fragment}`);
  }
}

for (const forbiddenFragment of ['trainer-workbench-hero', 'trainer-workbench-hero-actions']) {
  if (trainerProductBuilder.includes(forbiddenFragment)) {
    throw new Error(`trainer product builder still contains nested hero fragment: ${forbiddenFragment}`);
  }
}

for (const fragment of ['profile-workbench', 'profile-workbench-rail', 'profile-workbench-editor-panel', 'profile-workbench-support-panels']) {
  if (!trainerProductBuilder.includes(fragment)) {
    throw new Error(`trainer product builder missing workbench fragment: ${fragment}`);
  }
}

for (const fragment of ['profile-workbench', 'profile-workbench-rail', 'profile-workbench-editor-panel', 'trainer-video-upload-zone', 'profile-workbench-support-panels']) {
  if (!trainerContentStudio.includes(fragment)) {
    throw new Error(`trainer content studio missing workbench fragment: ${fragment}`);
  }
}

for (const fragment of ['TrainerUploadPanel', 'TrainerContentStudio']) {
  if (!trainerUploadPanel.includes(fragment)) {
    throw new Error(`trainer upload panel missing wrapper fragment: ${fragment}`);
  }
}

for (const fragment of ['Загрузить видеоурок', 'Видеофайл', 'Файл выбран', 'Видео', 'Программы', 'Наборы', 'Уроки программы']) {
  if (!`${trainerContentStudio}\n${trainerVideoUploadCard}`.includes(fragment)) {
    throw new Error(`trainer content studio missing fragment: ${fragment}`);
  }
}

for (const fragment of ['TrainerContentCard', 'trainerContentStatusLabel', 'trainerContentFileSize']) {
  if (!`${trainerContentCard}\n${trainerUploadFormat}\n${trainerVideoUploadCard}`.includes(fragment)) {
    throw new Error(`trainer upload split files missing fragment: ${fragment}`);
  }
}

for (const fragment of ['ProfileWorkbench', 'ProfileWorkbenchHero', 'ProfileWorkbenchNav', 'ProfileWorkbenchMetrics', 'ProfileWorkbenchRail', 'ProfileWorkbenchEditorPanel', 'ProfileWorkbenchSupportPanels']) {
  if (!profileWorkbench.includes(fragment)) {
    throw new Error(`profile-workbench.tsx missing export fragment: ${fragment}`);
  }
}

for (const fragment of ['profile-workbench profile-workbench-${tone}', 'showDescriptions = false']) {
  if (!profileWorkbench.includes(fragment)) {
    throw new Error(`profile-workbench.tsx missing v159.1 surface fragment: ${fragment}`);
  }
}

for (const [fileName, source, requiredFragments] of [
  ['customer-cabinet-shell.tsx', customerCabinetShell, ['profile-workbench', 'ProfileWorkbenchHero', 'CustomerCabinetNav variant="horizontal"', 'profile-workbench-content']],
  ['trainer-cabinet-shell.tsx', trainerCabinetShell, ['profile-workbench', 'ProfileWorkbenchHero', 'TrainerCabinetNav variant="horizontal"', 'profile-workbench-content']],
  ['customer-cabinet-nav.tsx', customerCabinetNav, ['profile-workbench-nav', 'profile-workbench-nav-link']],
  ['trainer-cabinet-nav.tsx', trainerCabinetNav, ['profile-workbench-nav', 'profile-workbench-nav-link']],
  ['trainer-content-studio.tsx', trainerContentStudio, ['profile-workbench', 'profile-workbench-rail', 'profile-workbench-editor-panel']],
  ['trainer-product-builder-dashboard.tsx', trainerProductBuilder, ['profile-workbench', 'profile-workbench-rail', 'profile-workbench-editor-panel']],
]) {
  for (const fragment of requiredFragments) {
    if (!source.includes(fragment)) {
      throw new Error(`${fileName} missing v159 profile workbench fragment: ${fragment}`);
    }
  }
}

for (const [fileName, source, forbiddenFragments] of [
  ['customer-cabinet-shell.tsx', customerCabinetShell, ['customer-cabinet-sidebar']],
  ['trainer-cabinet-shell.tsx', trainerCabinetShell, ['trainer-cabinet-sidebar']],
  ['learning/page.tsx', learningPage, ['customer-learning-grid']],
  ['messages/page.tsx', messagesPage, ['customer-message-layout']],
  ['trainer-product-builder-dashboard.tsx', trainerProductBuilder, ['Draft, publish and archive', 'Product type', 'Single video', 'Video bundle', 'Access type', 'One-time purchase', 'Subscription access', 'Video ids', 'Save product', 'Create draft', 'Readiness checks', 'trainer-product-builder-grid']],
  ['trainer-content-studio.tsx', `${trainerContentStudio}\n${trainerVideoUploadCard}`, ['Video draft editor', 'Program draft editor', 'Lessons editor', 'Bundle draft editor', 'Bundle composition editor', 'video asset', 'metadata draft', 'storefront', 'New draft', 'Edit lesson', '>Published<', '>Under review<', '>Draft<', 'trainer-content-studio-grid']],
  ['assignments/page.tsx', trainerAssignmentsPage, ['content id', 'lesson id, optional', 'placeholder="score"', 'Сохранить ревью', 'Published']],
]) {
  for (const forbiddenFragment of forbiddenFragments) {
    if (source.includes(forbiddenFragment)) {
      throw new Error(`${fileName} still contains v158 technical label: ${forbiddenFragment}`);
    }
  }
}

console.log('v131-v166.2 design system contract ok');
