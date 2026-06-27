const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..', '..');

const requiredFiles = [
  'src/app/globals.css',
  'src/design-system/tokens.ts',
  'src/design-system/components.tsx',
  'src/design-system/layouts.tsx',
  'src/design-system/library.tsx',
  'src/design-system/theme.tsx',
  'src/design-system/index.ts',
  '../docs/design-system/v131_ui_design_system.md',
  '../docs/design-system/v132_layout_system.md',
  '../docs/design-system/v133_component_library.md',
  '../docs/design-system/v134_theme_engine.md',
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
  '.ds-layout-shell',
  '.ds-layout-sidebar',
  '.ds-page-header',
  '.ds-mobile-action-bar',
  '.ds-chart',
  '.ds-calendar',
  '.ds-kanban',
  '.ds-file-upload',
  '.ds-rich-text',
  '.ds-video-player',
  '.ds-stats-grid',
  '.ds-theme-root',
  'data-theme="dark"',
  'data-brand="studio"',
  'data-brand="academy"',
  'data-brand="wellness"',
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
  'DSCalendar',
  'DSKanbanBoard',
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

console.log('v131-v134 design system contract ok');
