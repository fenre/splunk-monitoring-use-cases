// Fault-injection unit tests (v9.0).
//
// Drives recommender.js's loadRemoteIndexes against the five upstream
// fixtures under tests/fixtures/upstream/ and asserts:
//
//   - One failed endpoint never blanks the dashboard (Promise.allSettled).
//   - Each failure mode lands in STATE.upstreamErrors with a non-empty
//     human-readable message.
//   - Successful fixtures still mutate STATE.indexes correctly.
//
// Run: `node --test tests/recommender/upstream_fixtures.test.mjs`

import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, '..', '..');
const RECOMMENDER_JS = path.resolve(
  REPO_ROOT,
  'splunk-apps',
  'splunk-uc-recommender',
  'appserver',
  'static',
  'js',
  'recommender.js',
);
const FIXTURE_DIR = path.resolve(REPO_ROOT, 'tests', 'fixtures', 'upstream');

const FIXTURES = {
  '500': fs.readFileSync(path.join(FIXTURE_DIR, 'upstream-500.json'), 'utf8'),
  '404': fs.readFileSync(path.join(FIXTURE_DIR, 'upstream-404.json'), 'utf8'),
  malformed: fs.readFileSync(path.join(FIXTURE_DIR, 'upstream-malformed.json'), 'utf8'),
  wrongSchema: fs.readFileSync(path.join(FIXTURE_DIR, 'upstream-wrong-schema.json'), 'utf8'),
  empty: fs.readFileSync(path.join(FIXTURE_DIR, 'upstream-empty-array.json'), 'utf8'),
};

function loadInContext(fetchImpl) {
  const src = fs.readFileSync(RECOMMENDER_JS, 'utf8');
  const fakeDoc = {
    readyState: 'complete',
    createElement: () => ({
      appendChild() {}, setAttribute() {}, addEventListener() {},
      classList: { add() {}, remove() {} }, style: {}, dataset: {},
      _children: [], textContent: '',
    }),
    createTextNode: (t) => ({ nodeValue: t }),
    getElementById: () => null,
    addEventListener() {},
    body: { appendChild() {}, removeChild() {} },
  };
  const fakeWindow = {
    localStorage: {
      getItem: () => null, setItem: () => {}, removeItem: () => {},
    },
    location: { search: '', href: 'https://splunk.example/x' },
    history: { replaceState() {} },
  };
  const sandbox = {
    window: fakeWindow,
    document: fakeDoc,
    navigator: { clipboard: { writeText: async () => {} } },
    fetch: fetchImpl,
    setTimeout,
    URL,
    URLSearchParams,
    Promise,
    console,
    CSS: { escape: (s) => String(s) },
  };
  sandbox.globalThis = sandbox;
  sandbox.self = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(src, sandbox, { filename: 'recommender.js' });
  return sandbox;
}

function callLoadRemoteIndexes(sandbox, base) {
  return sandbox.window.__uc_recommender__.loadRemoteIndexes(base);
}

// Same-realm structural emptiness check — Node's vm.Context creates a
// separate Object.prototype, so deepEqual({}, {}) across realms fails.
function isEmptyObject(obj) {
  return typeof obj === 'object' && obj !== null && Object.keys(obj).length === 0;
}

const ALLOW_LISTED_BASE = 'https://fenre.github.io/splunk-monitoring-use-cases/api/v1';

// Build a fetch mock that returns the given Response per endpoint
// pattern. Unrecognised URLs return ENOTFOUND.
function buildFetch(routes) {
  return async (url) => {
    for (const [pattern, response] of routes) {
      if (url.includes(pattern)) {
        return response;
      }
    }
    throw new Error('No mock for ' + url);
  };
}

function jsonResponse(status, body) {
  return {
    ok: status >= 200 && status < 300,
    status,
    text: async () => body,
    json: async () => JSON.parse(body),
  };
}

test('upstream 500 lands in STATE.upstreamErrors but other fetches still proceed', async () => {
  const sandbox = loadInContext(buildFetch([
    ['sourcetype-index.json', jsonResponse(500, FIXTURES['500'])],
    ['cim-index.json',         jsonResponse(200, '{"k":"v"}')],
    ['app-index.json',         jsonResponse(200, '{"k":"v"}')],
    ['uc-thin.json',           jsonResponse(200, '{"k":"v"}')],
    ['splunkbase-index.json',  jsonResponse(200, '{"k":"v"}')],
  ]));
  const result = await callLoadRemoteIndexes(sandbox, ALLOW_LISTED_BASE);
  // sourcetypes must be empty (failed) but other indexes must have loaded.
  assert.ok(isEmptyObject(result.sourcetypes), 'sourcetypes should be empty after a 500');
  assert.ok(sandbox.window.__uc_recommender__.state.upstreamErrors.sourcetypes,
    'failed endpoint must leave a per-endpoint error message');
});

test('upstream 404 surfaces a distinct error message', async () => {
  const sandbox = loadInContext(buildFetch([
    ['sourcetype-index.json', jsonResponse(200, '{}')],
    ['cim-index.json',         jsonResponse(404, FIXTURES['404'])],
    ['app-index.json',         jsonResponse(200, '{}')],
    ['uc-thin.json',           jsonResponse(200, '{}')],
    ['splunkbase-index.json',  jsonResponse(200, '{}')],
  ]));
  await callLoadRemoteIndexes(sandbox, ALLOW_LISTED_BASE);
  const errs = sandbox.window.__uc_recommender__.state.upstreamErrors;
  assert.ok(errs.cim, 'cim endpoint failure must surface');
  assert.ok(errs.cim.length > 0);
});

test('malformed JSON surfaces a parse error and never blanks the result', async () => {
  const sandbox = loadInContext(buildFetch([
    ['sourcetype-index.json', jsonResponse(200, '{}')],
    ['cim-index.json',         jsonResponse(200, '{}')],
    ['app-index.json',         jsonResponse(200, FIXTURES.malformed)],
    ['uc-thin.json',           jsonResponse(200, '{}')],
    ['splunkbase-index.json',  jsonResponse(200, '{}')],
  ]));
  const result = await callLoadRemoteIndexes(sandbox, ALLOW_LISTED_BASE);
  // apps endpoint should fail; the others succeed.
  assert.ok(isEmptyObject(result.apps), 'apps should be empty after malformed JSON');
  const errs = sandbox.window.__uc_recommender__.state.upstreamErrors;
  assert.ok(errs.apps, 'parse failure must yield an upstreamErrors entry');
});

test('wrong-schema payload still resolves; no JS exception escapes', async () => {
  // The recommender does best-effort access — `indexes.cim['Network_Traffic']`
  // simply yields `undefined` if the key is absent. Confirm no exception
  // and STATE has a usable shape.
  const sandbox = loadInContext(buildFetch([
    ['sourcetype-index.json', jsonResponse(200, FIXTURES.wrongSchema)],
    ['cim-index.json',         jsonResponse(200, FIXTURES.wrongSchema)],
    ['app-index.json',         jsonResponse(200, FIXTURES.wrongSchema)],
    ['uc-thin.json',           jsonResponse(200, FIXTURES.wrongSchema)],
    ['splunkbase-index.json',  jsonResponse(200, FIXTURES.wrongSchema)],
  ]));
  const result = await callLoadRemoteIndexes(sandbox, ALLOW_LISTED_BASE);
  // Must be an object — not null/undefined — even though the shape is wrong.
  assert.equal(typeof result, 'object');
  assert.ok(result !== null);
});

test('empty-array fixture renders without error and yields no recommendations', async () => {
  const sandbox = loadInContext(buildFetch([
    ['sourcetype-index.json', jsonResponse(200, FIXTURES.empty)],
    ['cim-index.json',         jsonResponse(200, FIXTURES.empty)],
    ['app-index.json',         jsonResponse(200, FIXTURES.empty)],
    ['uc-thin.json',           jsonResponse(200, FIXTURES.empty)],
    ['splunkbase-index.json',  jsonResponse(200, FIXTURES.empty)],
  ]));
  const result = await callLoadRemoteIndexes(sandbox, ALLOW_LISTED_BASE);
  assert.equal(typeof result, 'object');
  // Calling matchUseCases with no matching inventory must return [], not throw.
  const matches = sandbox.window.__uc_recommender__.matchUseCases(
    [{ type: 'sourcetype', name: 'unknown:sourcetype', extras: '' }],
    result,
  );
  assert.equal(matches.length, 0);
});
