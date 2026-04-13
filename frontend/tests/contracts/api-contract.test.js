const assert = require('node:assert/strict');

function buildRoutes() {
  return {
    runtimeHealth: '/api/v1/runtime/health/',
    runtimeReadiness: '/api/v1/runtime/readiness/',
    accessSnapshot: '/api/v1/access/snapshot/',
    workflowDefinitions: '/api/v1/workflows/definitions/',
  };
}

(function main() {
  const routes = buildRoutes();
  assert.equal(routes.runtimeHealth, '/api/v1/runtime/health/');
  assert.ok(routes.accessSnapshot.includes('/api/v1/access/'));
  console.log('frontend contract routes ok');
})();
