const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..', '..');
const tsconfig = JSON.parse(fs.readFileSync(path.join(root, 'tsconfig.json'), 'utf8'));
const compilerOptions = tsconfig.compilerOptions || {};

assert.equal(compilerOptions.allowJs, false, 'frontend TypeScript must not allow JS sources');
assert.equal(compilerOptions.strict, true, 'frontend TypeScript strict mode must stay enabled');
assert.equal(compilerOptions.strictNullChecks, true, 'strict null checks must stay enabled');
assert.equal(compilerOptions.noEmit, true, 'typecheck must not emit build artifacts');
assert.equal(compilerOptions.isolatedModules, true, 'Next.js isolated module checking must stay enabled');

console.log('frontend tsconfig contract ok');
