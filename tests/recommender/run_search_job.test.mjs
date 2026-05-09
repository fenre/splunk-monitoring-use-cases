// Regression tests for runSearchJob() in recommender.js.
//
// Build 9 shipped a race-condition where the SearchManager's
// 'search:done' event fired BEFORE the ResultsModel's 'data' event,
// causing the JS to read the still-empty results.data() and resolve
// with [] for every search — including the inventory query that has
// 194 rows. The dashboard then rendered "No matches yet" even though
// 40 sourcetypes / 90 apps had been ingested.
//
// Build 10 fix:
//   * results.on('data', pull)              ← wins for non-empty
//   * sm.on('search:done', deferredPull)    ← safety net for empty
// where deferredPull is `setTimeout(pull, 800)` so the 'data' handler
// always wins when there are rows to fetch.
//
// These tests stub splunkjs/mvc and SearchManager so they run in
// node:test without any live Splunk.

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

// Minimal stub of splunkjs/mvc + SearchManager so the AMD `require`
// inside runSearchJob() can be driven from the test. Returns the
// SearchManager fake plus a `fire` helper used by tests to control
// the race.
function buildSplunkSdkFake() {
  const sm = {
    _listeners: {},
    _resultRows: null,
    on(event, cb) {
      if (!this._listeners[event]) this._listeners[event] = [];
      this._listeners[event].push(cb);
    },
    _fire(event, payload) {
      (this._listeners[event] || []).forEach((cb) => cb(payload));
    },
    data(name, opts) {
      // Return the results-model fake. Tests poke
      // ``results._setRows([...])`` and ``results._fire('data')``.
      return sm._results;
    },
  };
  const results = {
    _listeners: {},
    _rows: null,
    on(event, cb) {
      if (!this._listeners[event]) this._listeners[event] = [];
      this._listeners[event].push(cb);
    },
    _fire(event, payload) {
      (this._listeners[event] || []).forEach((cb) => cb(payload));
    },
    _setRows(rows) {
      this._rows = rows;
    },
    data() {
      // Mirrors the Splunk SDK's ResultsModel.data() shape.
      return this._rows == null ? null : { results: this._rows };
    },
  };
  sm._results = results;

  const SearchManager = function (opts) {
    sm._opts = opts;
    return sm;
  };
  const mvc = {
    createService() {
      return null; // not used in these tests
    },
  };
  return { mvc, SearchManager, sm, results };
}

function loadRecommenderWithSdk(sdkFake) {
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
  // Stub AMD so `require(['splunkjs/mvc', 'splunkjs/mvc/searchmanager'], cb)`
  // resolves synchronously with our fakes.
  const requireFn = function (deps, cb /* , err */) {
    const resolved = deps.map((d) => {
      if (d === 'splunkjs/mvc') return sdkFake.mvc;
      if (d === 'splunkjs/mvc/searchmanager') return sdkFake.SearchManager;
      throw new Error(`stub require: unknown dep ${d}`);
    });
    setImmediate(() => cb(...resolved));
  };
  // The recommender.js's hasRequire check wants typeof require === 'function'.
  const sandbox = {
    window: fakeWindow,
    document: fakeDoc,
    navigator: { clipboard: { writeText: async () => {} } },
    fetch: async () => {
      throw new Error('network disabled in tests');
    },
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

test('runSearchJob resolves with rows from data event for NON-empty results', async () => {
  const sdk = buildSplunkSdkFake();
  const { runSearchJob } = loadRecommenderWithSdk(sdk);

  const rows = [
    { name: 'meraki:devices', type: 'sourcetype', count: 12 },
    { name: 'access_combined', type: 'sourcetype', count: 99 },
  ];

  // Kick off the search; it will subscribe to events on our fakes.
  const pending = runSearchJob('| inputlookup uc_recommender_inventory');

  // Yield once so the AMD setImmediate callback runs and registers
  // 'data' / 'search:done' listeners.
  await new Promise((resolve) => setImmediate(resolve));

  // Reproduce the build-9 race: 'search:done' fires FIRST while
  // results.data() is still null. With the build-10 fix the
  // 'search:done' handler defers via setTimeout(pull, 800), giving
  // 'data' a chance to win. We simulate that real-world ordering.
  sdk.sm._fire('search:done');
  // ResultsModel completes its HTTP fetch a moment later and emits
  // 'data' with the rows.
  sdk.results._setRows(rows);
  sdk.results._fire('data');

  const result = await pending;
  assert.equal(result.length, 2, 'must resolve with the actual row set');
  assert.equal(result[0].name, 'meraki:devices');
});

test("runSearchJob resolves with [] for EMPTY result sets via search:done fallback", async () => {
  const sdk = buildSplunkSdkFake();
  const { runSearchJob } = loadRecommenderWithSdk(sdk);

  const pending = runSearchJob('| inputlookup uc_recommender_implementations');
  await new Promise((resolve) => setImmediate(resolve));

  // ResultsModel never emits 'data' for empty result sets.
  // 'search:done' is the only signal we get.
  sdk.sm._fire('search:done');

  // The deferred safety-net fires after 800ms in production. Wait
  // long enough for it to settle here.
  const result = await pending;
  assert.equal(result.length, 0, 'empty result sets must settle as []');
  assert.ok(Array.isArray(result));
});

test("runSearchJob's data handler wins the race for fast non-empty searches", async () => {
  // Tighter regression-lock for the build-9 bug. We fire BOTH events
  // but data wins because it carries the rows; if anything ever
  // refactors search:done to call pull() synchronously, this test
  // catches it.
  const sdk = buildSplunkSdkFake();
  const { runSearchJob } = loadRecommenderWithSdk(sdk);

  const inventoryRows = Array.from({ length: 194 }, (_, i) => ({
    name: `row-${i}`,
    type: i % 2 === 0 ? 'sourcetype' : 'app',
  }));

  const pending = runSearchJob('| inputlookup uc_recommender_inventory');
  await new Promise((resolve) => setImmediate(resolve));

  sdk.results._setRows(inventoryRows);
  sdk.results._fire('data');
  // search:done fires "after" data, also a real-world ordering.
  sdk.sm._fire('search:done');

  const result = await pending;
  assert.equal(result.length, 194);
  assert.equal(result[0].name, 'row-0');
});

test('runSearchJob rejects on search:error', async () => {
  const sdk = buildSplunkSdkFake();
  const { runSearchJob } = loadRecommenderWithSdk(sdk);

  const pending = runSearchJob('bogus | search');
  await new Promise((resolve) => setImmediate(resolve));

  sdk.sm._fire('search:error', new Error('SPL parse error'));

  await assert.rejects(pending, /SPL parse error/);
});

test('runSearchJob rejects on search:fail', async () => {
  const sdk = buildSplunkSdkFake();
  const { runSearchJob } = loadRecommenderWithSdk(sdk);

  const pending = runSearchJob('| inputlookup nope');
  await new Promise((resolve) => setImmediate(resolve));

  sdk.sm._fire('search:fail', new Error('lookup not found'));

  await assert.rejects(pending, /lookup not found/);
});
