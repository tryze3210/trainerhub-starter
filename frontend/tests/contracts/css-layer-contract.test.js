const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..', '..');
const globalsPath = path.join(root, 'src/app/globals.css');
const trainerRouteCssPath = path.join(root, 'src/app/trainer/trainer-route.css');
const stylesDir = path.join(root, 'src/styles');

const expectedLayers = [
  '00-reset.css',
  '01-tokens.css',
  '02-layout.css',
  '03-premium-shell.css',
  '04-public-storefront.css',
  '05-customer-cabinet.css',
  '06-trainer-cabinet.css',
  '07-admin-ops.css',
  '08-components.css',
  '09-responsive.css',
];

const globals = fs.readFileSync(globalsPath, 'utf8');
const globalsLines = globals.split(/\r?\n/).filter((line) => line.trim().length > 0);

if (!globalsLines[0].includes('v167 production CSS layers')) {
  throw new Error('globals.css missing v167 CSS layer header comment');
}

for (const line of globalsLines.slice(1)) {
  if (!line.startsWith('@import "../styles/') || !line.endsWith('";')) {
    throw new Error(`globals.css must remain import-only, found: ${line}`);
  }
}

for (const layer of expectedLayers) {
  const importLine = `@import "../styles/${layer}";`;
  if (!globals.includes(importLine)) {
    throw new Error(`globals.css missing layer import: ${layer}`);
  }
  if (!fs.existsSync(path.join(stylesDir, layer))) {
    throw new Error(`missing CSS layer file: ${layer}`);
  }
}

const combinedCss = expectedLayers
  .map((layer) => fs.readFileSync(path.join(stylesDir, layer), 'utf8'))
  .concat(fs.readFileSync(trainerRouteCssPath, 'utf8'))
  .join('\n');

for (const fragment of [
  'premium-main',
  'premium-landing',
  'premium-catalog-page',
  'trainer-cabinet',
  'customer-cabinet',
  'profile-workbench',
  'trainer-video-studio',
]) {
  if (!combinedCss.includes(fragment)) {
    throw new Error(`combined CSS layers missing key fragment: ${fragment}`);
  }
}

console.log('v167 css layer contract ok');
