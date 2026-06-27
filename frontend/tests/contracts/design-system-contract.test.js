const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..', '..');

const requiredFiles = [
  'src/app/globals.css',
  'src/design-system/tokens.ts',
  'src/design-system/components.tsx',
  'src/design-system/feedback.tsx',
  'src/design-system/layouts.tsx',
  'src/design-system/library.tsx',
  'src/design-system/theme.tsx',
  'src/design-system/index.ts',
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
];

for (const file of requiredFiles) {
  const absolutePath = path.resolve(root, file);
  if (!fs.existsSync(absolutePath)) {
    throw new Error(`Missing design system contract file: ${file}`);
  }
}

const globals = fs.readFileSync(path.join(root, 'src/app/globals.css'), 'utf8');
const tokens = fs.readFileSync(path.join(root, 'src/design-system/tokens.ts'), 'utf8');
const components = fs.readFileSync(path.join(root, 'src/design-system/components.tsx'), 'utf8');
const feedback = fs.readFileSync(path.join(root, 'src/design-system/feedback.tsx'), 'utf8');
const layouts = fs.readFileSync(path.join(root, 'src/design-system/layouts.tsx'), 'utf8');
const library = fs.readFileSync(path.join(root, 'src/design-system/library.tsx'), 'utf8');
const theme = fs.readFileSync(path.join(root, 'src/design-system/theme.tsx'), 'utf8');

for (const fragment of [
  '--color-primary',
  '--color-accent',
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
  'prefers-reduced-motion',
  'max-width: 480px',
  'scroll-snap-type: x proximity',
  'overflow-x: hidden',
  '.skeleton',
  '.focus-ring',
]) {
  if (!globals.includes(fragment)) {
    throw new Error(`globals.css missing design token/class: ${fragment}`);
  }
}

for (const fragment of ['designTokens', 'color', 'spacing', 'typography', 'radius']) {
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

console.log('v131-v150 design system contract ok');
