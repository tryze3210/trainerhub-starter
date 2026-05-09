const assert = require('node:assert/strict');

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
const route = (path) => `${API_BASE_URL}${path}`;

(function main() {
  assert.equal(route('/auth/login/'), `${API_BASE_URL}/auth/login/`);
  assert.equal(route('/content/videos/'), `${API_BASE_URL}/content/videos/`);
  assert.equal(route('/content/programs/'), `${API_BASE_URL}/content/programs/`);
  assert.equal(route('/content/bundles/'), `${API_BASE_URL}/content/bundles/`);
  assert.equal(route('/content/videos/demo-video/'), `${API_BASE_URL}/content/videos/demo-video/`);
  assert.equal(route('/content/programs/demo-program/'), `${API_BASE_URL}/content/programs/demo-program/`);
  assert.equal(route('/content/bundles/demo-bundle/'), `${API_BASE_URL}/content/bundles/demo-bundle/`);
  assert.equal(route('/trainers/'), `${API_BASE_URL}/trainers/`);
  assert.equal(route('/trainers/demo-trainer/'), `${API_BASE_URL}/trainers/demo-trainer/`);

  assert.equal(route('/orders/checkout/'), `${API_BASE_URL}/orders/checkout/`);
  assert.equal(route('/payments-webhooks/receive/'), `${API_BASE_URL}/payments-webhooks/receive/`);

  assert.equal(route('/trainers/me/revenue/summary/'), `${API_BASE_URL}/trainers/me/revenue/summary/`);
  assert.equal(route('/trainers/me/revenue/transactions/'), `${API_BASE_URL}/trainers/me/revenue/transactions/`);
  assert.equal(route('/trainers/me/revenue/payouts/'), `${API_BASE_URL}/trainers/me/revenue/payouts/`);
  assert.equal(route('/trainers/me/analytics/overview/'), `${API_BASE_URL}/trainers/me/analytics/overview/`);
  assert.equal(route('/trainers/me/analytics/content/'), `${API_BASE_URL}/trainers/me/analytics/content/`);
  assert.equal(route('/trainers/me/analytics/sales/'), `${API_BASE_URL}/trainers/me/analytics/sales/`);
  assert.equal(route('/trainers/me/onboarding/status/'), `${API_BASE_URL}/trainers/me/onboarding/status/`);
  assert.equal(route('/trainers/me/application-status/'), `${API_BASE_URL}/trainers/me/application-status/`);
  assert.equal(route('/trainers/admin/applications/'), `${API_BASE_URL}/trainers/admin/applications/`);

  assert.equal(route('/payouts/my/balance/'), `${API_BASE_URL}/payouts/my/balance/`);
  assert.equal(route('/payouts/my/request/'), `${API_BASE_URL}/payouts/my/request/`);
  assert.equal(route('/payouts/my/'), `${API_BASE_URL}/payouts/my/`);
  assert.equal(route('/payouts/admin/overview/'), `${API_BASE_URL}/payouts/admin/overview/`);
  assert.equal(route('/payouts/admin/'), `${API_BASE_URL}/payouts/admin/`);
  assert.equal(route('/payouts/admin/demo-payout/'), `${API_BASE_URL}/payouts/admin/demo-payout/`);
  assert.equal(route('/payouts/admin/demo-payout/approve/'), `${API_BASE_URL}/payouts/admin/demo-payout/approve/`);
  assert.equal(route('/payouts/admin/demo-payout/processing/'), `${API_BASE_URL}/payouts/admin/demo-payout/processing/`);
  assert.equal(route('/payouts/admin/demo-payout/mark-paid/'), `${API_BASE_URL}/payouts/admin/demo-payout/mark-paid/`);
  assert.equal(route('/payouts/admin/demo-payout/reject/'), `${API_BASE_URL}/payouts/admin/demo-payout/reject/`);
  assert.equal(route('/payouts/admin/bulk-transition/'), `${API_BASE_URL}/payouts/admin/bulk-transition/`);
  assert.equal(route('/payouts/admin/projection-health/'), `${API_BASE_URL}/payouts/admin/projection-health/`);
  assert.equal(route('/payouts/admin/project-outbox/'), `${API_BASE_URL}/payouts/admin/project-outbox/`);
  assert.equal(route('/payouts/admin/risk-holds/'), `${API_BASE_URL}/payouts/admin/risk-holds/`);
  assert.equal(route('/payouts/admin/risk-holds/summary/'), `${API_BASE_URL}/payouts/admin/risk-holds/summary/`);
  assert.equal(route('/payouts/admin/risk-holds/release/'), `${API_BASE_URL}/payouts/admin/risk-holds/release/`);
  assert.equal(route('/payouts/admin/reconciliation/'), `${API_BASE_URL}/payouts/admin/reconciliation/`);
  assert.equal(route('/payouts/admin/reconciliation/repair/'), `${API_BASE_URL}/payouts/admin/reconciliation/repair/`);

  assert.equal(route('/products/trainer/'), `${API_BASE_URL}/products/trainer/`);
  assert.equal(route('/subscriptions/lifecycle-policy/'), `${API_BASE_URL}/subscriptions/lifecycle-policy/`);
  assert.equal(route('/subscriptions/lifecycle-summary/'), `${API_BASE_URL}/subscriptions/lifecycle-summary/`);
  assert.equal(route('/subscriptions/admin/reconcile-entitlements/'), `${API_BASE_URL}/subscriptions/admin/reconcile-entitlements/`);
  assert.equal(route('/entitlements/me/access-check/'), `${API_BASE_URL}/entitlements/me/access-check/`);

  assert.equal(route('/ops/admin/operations-dashboard/'), `${API_BASE_URL}/ops/admin/operations-dashboard/`);
  assert.equal(route('/ops/admin/operations-hub/'), `${API_BASE_URL}/ops/admin/operations-hub/`);
  assert.equal(route('/ops/admin/operations-readiness/'), `${API_BASE_URL}/ops/admin/operations-readiness/`);
  assert.equal(route('/ops/admin/commerce-readiness/'), `${API_BASE_URL}/ops/admin/commerce-readiness/`);

  assert.equal(route('/ops/admin/reconciliation-snapshots/'), `${API_BASE_URL}/ops/admin/reconciliation-snapshots/`);
  assert.equal(route('/ops/admin/reconciliation-snapshots/latest/'), `${API_BASE_URL}/ops/admin/reconciliation-snapshots/latest/`);
  assert.equal(route('/ops/admin/reconciliation-snapshots/compare/'), `${API_BASE_URL}/ops/admin/reconciliation-snapshots/compare/`);
  assert.equal(route('/ops/admin/reconciliation-snapshots/metrics/'), `${API_BASE_URL}/ops/admin/reconciliation-snapshots/metrics/`);
  assert.equal(route('/ops/admin/reconciliation-snapshots/schedule/'), `${API_BASE_URL}/ops/admin/reconciliation-snapshots/schedule/`);
  assert.equal(route('/ops/admin/reconciliation-snapshots/retention/'), `${API_BASE_URL}/ops/admin/reconciliation-snapshots/retention/`);
  assert.equal(route('/ops/admin/reconciliation-snapshots/issues/'), `${API_BASE_URL}/ops/admin/reconciliation-snapshots/issues/`);

  console.log('frontend contract routes ok');
})();
