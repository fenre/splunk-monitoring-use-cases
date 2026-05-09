// Backwards-compat test (v9.0).
//
// Asserts that the v9.0 catalogue payloads remain parseable by a
// pre-v9.0 client shape. Closes the additive-only contract: older
// recommender.js installs (still polling fenre.github.io) must keep
// working after the v9.0 release.
//
// The "legacy" client is a hand-written shape under
// tests/fixtures/legacy_recommender/legacy_v7_3_shape.mjs — see the
// notes there for what it deliberately ignores.
//
// Run: `node --test tests/recommender/backcompat.test.mjs`

import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { legacyLoadRemoteIndexes } from '../fixtures/legacy_recommender/legacy_v7_3_shape.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, '..', '..');
const API_DIR = path.resolve(REPO_ROOT, 'api', 'v1', 'recommender');

function loadJson(file) {
  const raw = fs.readFileSync(path.join(API_DIR, file), 'utf8');
  return JSON.parse(raw);
}

function makeFetch(map) {
  return async (url) => {
    for (const [pattern, body] of Object.entries(map)) {
      if (url.includes(pattern)) {
        return {
          ok: true,
          status: 200,
          json: async () => body,
        };
      }
    }
    return { ok: false, status: 404 };
  };
}

test('v9.0 uc-thin payload still carries every legacy key required by v7.3-shaped clients', () => {
  const thin = loadJson('uc-thin.json');
  assert.ok(Array.isArray(thin.useCases),
    'v9.0 must keep the useCases array on uc-thin.json');
  thin.useCases.slice(0, 50).forEach((row) => {
    // Legacy contract: every row carries id / title / criticality.
    assert.ok(typeof row.id === 'string' && row.id.length > 0,
      'each row must keep `id` (UC ID): ' + JSON.stringify(row).slice(0, 120));
    assert.ok(typeof row.title === 'string',
      'each row must keep `title`: ' + row.id);
    assert.ok(typeof row.criticality === 'string',
      'each row must keep `criticality`: ' + row.id);
  });
});

test('legacy v7.3 client loads v9.0 payloads without throwing on unknown sb keys', async () => {
  const sourcetype = loadJson('sourcetype-index.json');
  const cim = loadJson('cim-index.json');
  const app = loadJson('app-index.json');
  const thin = loadJson('uc-thin.json');
  const fetchMock = makeFetch({
    'sourcetype-index.json': sourcetype,
    'cim-index.json': cim,
    'app-index.json': app,
    'uc-thin.json': thin,
  });
  const result = await legacyLoadRemoteIndexes(
    'https://fenre.github.io/splunk-monitoring-use-cases/api/v1',
    fetchMock,
  );
  // Sanity: every shape we expect is present.
  assert.equal(typeof result.sourcetypes, 'object');
  assert.equal(typeof result.cim, 'object');
  assert.equal(typeof result.apps, 'object');
  assert.equal(typeof result.thin, 'object');
  // The thin index is an object keyed by UC id.
  const ids = Object.keys(result.thin);
  assert.ok(ids.length > 0, 'expected at least one UC in thin index');
  ids.slice(0, 25).forEach((id) => {
    const row = result.thin[id];
    assert.ok(row.id, 'legacy client must surface row.id');
    assert.ok(row.title, 'legacy client must surface row.title');
    assert.ok(row.criticality, 'legacy client must surface row.criticality');
  });
});

test('cim-index payload still uses cimModels (legacy key)', () => {
  const cim = loadJson('cim-index.json');
  assert.ok(typeof cim.cimModels === 'object',
    'cim-index.json must keep `cimModels` key for v7.3-shaped clients');
});

test('app-index payload still uses apps (legacy key)', () => {
  const app = loadJson('app-index.json');
  assert.ok(typeof app.apps === 'object',
    'app-index.json must keep `apps` key for v7.3-shaped clients');
});

test('sourcetype-index payload still uses sourcetypes (legacy key)', () => {
  const st = loadJson('sourcetype-index.json');
  assert.ok(typeof st.sourcetypes === 'object',
    'sourcetype-index.json must keep `sourcetypes` key for v7.3-shaped clients');
});
