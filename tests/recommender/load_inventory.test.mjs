// Regression tests for loadInventory() / loadImplementations() in
// recommender.js (build 12+).
//
// Builds 9–11 used a SearchManager-driven runSearchJob() path with
// an event-ordering race that resolved with [] on fast searches.
// The user-visible failure was the Recommend tab showing "No matches
// yet" while the dashboard tiles (Simple XML's own SearchManager)
// showed 40 sourcetypes / 90 apps.
//
// Build 12 swapped these two loaders to a direct REST GET against the
// Splunk Web ``/splunkd/__raw`` proxy. Same data, no SearchManager,
// no race. These tests pin that contract:
//   * loadInventory()      hits the inventory KV proxy URL
//   * loadImplementations() hits the implementations KV proxy URL
//   * Both normalise the KV row shape correctly
//   * Both fall back to /en-US/splunkd/__raw if the bare path fails
//   * Both fall back to runSearchJob if both fetches fail
//
// We stub global ``fetch`` so the JS sees a deterministic response.

import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const RECOMMENDER_JS = path.resolve(
  __dirname,
  '..',
  '..',
  'splunk-apps',
  'splunk-uc-recommender',
  'appserver',
  'static',
  'js',
  'recommender.js',
);

function loadRecommenderWithFetch(fetchImpl) {
  const src = fs.readFileSync(RECOMMENDER_JS, 'utf8');
  const fakeDoc = {
    readyState: 'complete',
    createElement: () => ({
      appendChild() {},
      setAttribute() {},
      addEventListener() {},
      classList: { add() {}, remove() {} },
      style: {},
      textContent: '',
    }),
    createTextNode: (text) => ({ nodeValue: text }),
    getElementById: () => null,
    addEventListener() {},
  };
  const fakeWindow = {
    localStorage: {
      getItem: () => null,
      setItem: () => {},
      removeItem: () => {},
    },
  };
  // AMD require should never be reached on the happy path, but stub
  // it anyway so the recommender's hasRequire branch initialises.
  const requireFn = function (deps, cb) {
    setImmediate(() => cb({}, function () {}));
  };
  const sandbox = {
    window: fakeWindow,
    document: fakeDoc,
    navigator: { clipboard: { writeText: async () => {} } },
    fetch: fetchImpl,
    require: requireFn,
    setTimeout,
    clearTimeout,
    setImmediate,
    URL,
    Promise,
    console,
  };
  sandbox.globalThis = sandbox;
  sandbox.self = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(src, sandbox, { filename: 'recommender.js' });
  return sandbox.window.__uc_recommender__;
}

function jsonResponse(body, ok = true, status = 200) {
  return {
    ok,
    status,
    json: async () => body,
  };
}

test('loadInventory hits /splunkd/__raw KV proxy and normalises rows', async () => {
  const calls = [];
  const fetchImpl = async (url /* , opts */) => {
    calls.push(url);
    return jsonResponse([
      { _key: 'app::Splunk_TA_nix', type: 'app', name: 'Splunk_TA_nix', count: 1, extras: 'Splunk_TA_nix' },
      { _key: 'sourcetype::cisco:asa', type: 'sourcetype', name: 'cisco:asa', count: 42 },
    ]);
  };
  const { loadInventory } = loadRecommenderWithFetch(fetchImpl);

  const rows = await loadInventory();

  assert.equal(rows.length, 2);
  assert.equal(rows[0].type, 'app');
  assert.equal(rows[0].name, 'Splunk_TA_nix');
  assert.equal(rows[0].extras, 'Splunk_TA_nix', 'extras must carry folder name (build 12)');
  assert.equal(rows[1].type, 'sourcetype');
  assert.equal(rows[1].count, 42);
  assert.equal(calls.length, 1, 'must succeed on the first /splunkd/__raw URL');
  assert.ok(
    calls[0].indexOf('/splunkd/__raw/servicesNS/nobody/') === 0,
    `must hit splunkd __raw proxy, got ${calls[0]}`
  );
  assert.ok(
    calls[0].indexOf('/storage/collections/data/uc_recommender_inventory') !== -1,
    'must target the inventory KV collection'
  );
});

test('loadInventory falls back to /en-US/splunkd/__raw when the bare path fails', async () => {
  const calls = [];
  const fetchImpl = async (url) => {
    calls.push(url);
    if (url.indexOf('/en-US/') === -1) {
      return jsonResponse({}, false, 404);
    }
    return jsonResponse([{ type: 'app', name: 'A', count: 1, extras: 'A' }]);
  };
  const { loadInventory } = loadRecommenderWithFetch(fetchImpl);
  const rows = await loadInventory();
  assert.equal(rows.length, 1);
  assert.equal(calls.length, 2, 'must try bare path then /en-US/ fallback');
  assert.ok(calls[0].indexOf('/en-US/') === -1);
  assert.ok(calls[1].indexOf('/en-US/splunkd/__raw') === 0);
});

test('loadInventory tolerates non-array KV responses without throwing', async () => {
  const fetchImpl = async () => jsonResponse({ entry: [] });
  const { loadInventory } = loadRecommenderWithFetch(fetchImpl);
  const rows = await loadInventory();
  assert.equal(rows.length, 0);
});

test('loadImplementations hits the implementations KV proxy and indexes by uc_id', async () => {
  const calls = [];
  const fetchImpl = async (url) => {
    calls.push(url);
    return jsonResponse([
      { _key: '5.1.1', uc_id: '5.1.1', status: 'in_progress' },
      { _key: '7.2.3', uc_id: '7.2.3', status: 'implemented' },
    ]);
  };
  const { loadImplementations } = loadRecommenderWithFetch(fetchImpl);

  const map = await loadImplementations();
  assert.equal(map['5.1.1'].status, 'in_progress');
  assert.equal(map['7.2.3'].status, 'implemented');
  assert.ok(
    calls[0].indexOf('/storage/collections/data/uc_recommender_implementations') !== -1,
    'must target the implementations KV collection'
  );
});

test('loadInventory uses cache:no-store + same-origin credentials', async () => {
  let observed = null;
  const fetchImpl = async (url, opts) => {
    observed = opts || {};
    return jsonResponse([]);
  };
  const { loadInventory } = loadRecommenderWithFetch(fetchImpl);
  await loadInventory();
  assert.equal(observed.credentials, 'same-origin', 'must ride the splunkd cookie session');
  assert.equal(observed.cache, 'no-store', 'must bypass HTTP cache');
});
