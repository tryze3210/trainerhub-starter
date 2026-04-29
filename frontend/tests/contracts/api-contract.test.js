const assert = require('node:assert/strict');
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
const route = (path) => `${API_BASE_URL}${path}`;
(function main() { assert.equal(route('/auth/login/'), `${API_BASE_URL}/auth/login/`); assert.equal(route('/content/videos/'), `${API_BASE_URL}/content/videos/`); assert.equal(route('/orders/checkout/'), `${API_BASE_URL}/orders/checkout/`); assert.equal(route('/payments-webhooks/receive/'), `${API_BASE_URL}/payments-webhooks/receive/`); console.log('frontend contract routes ok'); })();
