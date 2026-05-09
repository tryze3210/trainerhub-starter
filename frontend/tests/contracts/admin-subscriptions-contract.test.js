const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..', '..');
const requiredFiles = [
  'src/app/admin/subscriptions/page.tsx',
  'src/app/admin/subscriptions/[subscriptionId]/page.tsx',
  'src/modules/admin-subscriptions/api.ts',
  'src/modules/admin-subscriptions/components/admin-subscription-operations-dashboard.tsx',
  'src/modules/admin-subscriptions/components/admin-subscription-detail-page.tsx',
];

for (const file of requiredFiles) {
  const absolutePath = path.join(root, file);
  if (!fs.existsSync(absolutePath)) {
    throw new Error(`Missing admin subscriptions contract file: ${file}`);
  }
}

const apiSource = fs.readFileSync(path.join(root, 'src/modules/admin-subscriptions/api.ts'), 'utf8');
const expectedApiFragments = [
  '/subscriptions/admin/overview/',
  '/subscriptions/admin/items/',
  '/subscriptions/admin/lifecycle-policy/',
  '/subscriptions/admin/lifecycle-summary/',
  '/subscriptions/admin/expire-due/',
  '/subscriptions/admin/reconcile-entitlements/',
  '/admin/mark-past-due/',
  '/admin/sync-entitlements/',
  '/renewal-projection/',
];

for (const fragment of expectedApiFragments) {
  if (!apiSource.includes(fragment)) {
    throw new Error(`Admin subscriptions API contract missing fragment: ${fragment}`);
  }
}

console.log('admin subscription contract routes ok');
