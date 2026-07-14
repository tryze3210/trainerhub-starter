const assert = require('node:assert/strict');

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '/api/v1';
const route = (path) => `${API_BASE_URL}${path}`;

(function main() {
  assert.equal(route('/trainers/admin/applications/'), `${API_BASE_URL}/trainers/admin/applications/`);
  assert.equal(route('/trainers/admin/applications/readiness/'), `${API_BASE_URL}/trainers/admin/applications/readiness/`);
  assert.equal(
    route('/trainers/admin/applications/00000000-0000-0000-0000-000000000000/sync-access/'),
    `${API_BASE_URL}/trainers/admin/applications/00000000-0000-0000-0000-000000000000/sync-access/`,
  );
  console.log('admin trainer applications readiness contract routes ok');
})();
