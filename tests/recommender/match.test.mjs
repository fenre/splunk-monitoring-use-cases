// Tests for the recommender.js AMD module produced by
// scripts/generate_recommender_app.py. We run them against the
// generated file (not a copy) so that any change to the scoring or
// the URL sanitiser is exercised in CI.
//
// Strategy: stub the minimal globals the module touches at import
// time (`window`, `document`, `require`, `fetch`, `navigator`,
// `localStorage`), eval the file, then poke it via
// ``window.__uc_recommender__`` (the helper export it carries for
// exactly this purpose).

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

function loadRecommender() {
  const src = fs.readFileSync(RECOMMENDER_JS, 'utf8');
  // Minimal DOM surface the module touches at import time.
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
  const sandbox = {
    window: fakeWindow,
    document: fakeDoc,
    navigator: { clipboard: { writeText: async () => {} } },
    fetch: async () => {
      throw new Error('network disabled in tests');
    },
    setTimeout,
    URL,
    Promise,
    console,
  };
  sandbox.globalThis = sandbox;
  sandbox.self = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(src, sandbox, { filename: 'recommender.js' });
  return {
    ...sandbox.window.__uc_recommender__,
    helpers: sandbox.window.__uc_recommender_helpers__,
  };
}

test('safeLinkHref accepts http, https, and mailto', () => {
  const { safeLinkHref } = loadRecommender();
  assert.equal(safeLinkHref('https://example.com/a'), 'https://example.com/a');
  assert.equal(safeLinkHref('http://example.com'), 'http://example.com');
  assert.equal(safeLinkHref('mailto:alice@example.com'), 'mailto:alice@example.com');
  assert.equal(safeLinkHref('  HTTPS://example.com '), 'HTTPS://example.com');
});

test('safeLinkHref rejects dangerous schemes', () => {
  const { safeLinkHref } = loadRecommender();
  assert.equal(safeLinkHref('javascript:alert(1)'), null);
  assert.equal(safeLinkHref('JAVASCRIPT:alert(1)'), null);
  assert.equal(safeLinkHref('data:text/html,<script>alert(1)</script>'), null);
  assert.equal(safeLinkHref('vbscript:msgbox'), null);
  assert.equal(safeLinkHref(''), null);
  assert.equal(safeLinkHref(undefined), null);
  assert.equal(safeLinkHref(42), null);
});

test('validOrigin rejects non-allowlisted origins', () => {
  const { validOrigin } = loadRecommender();
  assert.equal(validOrigin('https://fenre.github.io/splunk-monitoring-use-cases/api/v1'), true);
  assert.equal(validOrigin('https://evil.example/x'), false);
  assert.equal(validOrigin('http://fenre.github.io'), false); // not https
  assert.equal(validOrigin('not a url'), false);
});

test('matchUseCases surfaces exact sourcetype match above fuzzy', () => {
  const { matchUseCases } = loadRecommender();
  const indexes = {
    sourcetypes: {
      'wineventlog:security': ['UC-A'],
      'wineventlog': ['UC-B'],
    },
    cim: {},
    apps: {},
    thin: {
      'UC-A': { id: 'UC-A', title: 'Exact', criticality: 'high' },
      'UC-B': { id: 'UC-B', title: 'Fuzzy', criticality: 'high' },
    },
  };
  const inventory = [
    { type: 'sourcetype', name: 'WinEventLog:Security', extras: '' },
  ];
  const res = matchUseCases(inventory, indexes);
  assert.ok(res.length >= 2, 'expected at least two matches');
  const aScore = res.find((r) => r.id === 'UC-A')._score;
  const bScore = res.find((r) => r.id === 'UC-B')._score;
  assert.ok(aScore > bScore, 'exact match must outrank fuzzy match');
  assert.equal(res[0].id, 'UC-A');
});

test('matchUseCases weighs CIM + sourcetype over app-only match', () => {
  const { matchUseCases } = loadRecommender();
  const indexes = {
    sourcetypes: {
      'cisco:asa': ['UC-NET'],
    },
    cim: {
      'Network_Traffic': ['UC-NET'],
    },
    apps: {
      'Splunk_TA_cisco_asa': ['UC-APP'],
    },
    thin: {
      'UC-NET': { id: 'UC-NET', title: 'Net', criticality: 'high' },
      'UC-APP': { id: 'UC-APP', title: 'App', criticality: 'medium' },
    },
  };
  const inventory = [
    { type: 'sourcetype', name: 'cisco:asa', extras: '' },
    { type: 'cim_model', name: 'Network_Traffic', extras: 'accelerated' },
    { type: 'app', name: 'Splunk_TA_cisco_asa', extras: '' },
  ];
  const res = matchUseCases(inventory, indexes);
  assert.equal(res[0].id, 'UC-NET', 'UC with CIM + sourcetype should rank first');
  assert.ok(res[0]._score > 3, `expected combined score to exceed 3, got ${res[0]._score}`);
});

test('matchUseCases tolerates inventory rows without matches', () => {
  const { matchUseCases } = loadRecommender();
  const res = matchUseCases(
    [{ type: 'sourcetype', name: 'nothing:known', extras: '' }],
    { sourcetypes: {}, cim: {}, apps: {}, thin: {} },
  );
  // VM-isolated arrays are not reference-equal to host [], so inspect
  // the shape instead of using deepEqual.
  assert.equal(res.length, 0);
  assert.equal(Array.isArray(res) || typeof res.length === 'number', true);
});

// Lock in the v9.x app-matcher behaviour: exact-match on the folder
// name (`extras` field, populated by the saved-search inventory job
// from `/services/apps/local::title`) outranks display-name fuzzy
// matches. Regression test for the "Recommend tab shows nothing
// despite Scan tab finding 90 apps" bug fixed in the v9.0 build.
test('matchUseCases: exact match on folder-name (extras) outranks fuzzy display match', () => {
  const { matchUseCases } = loadRecommender();
  const indexes = {
    sourcetypes: {},
    cim: {},
    apps: {
      // Two ways the catalogue might list the same TA — folder name
      // (high signal, exact) and a verbose display name (lower signal,
      // fuzzy substring at best).
      'Splunk_TA_paloalto': ['UC-FOLDER'],
      'Splunk Add-on for Palo Alto Networks (2757)': ['UC-DISPLAY'],
    },
    thin: {
      'UC-FOLDER': { id: 'UC-FOLDER', title: 'Folder', criticality: 'high' },
      'UC-DISPLAY': { id: 'UC-DISPLAY', title: 'Display', criticality: 'medium' },
    },
  };
  // Inventory row mirrors what the savedsearch produces:
  //   name    = label (display)
  //   extras  = title (folder slug, used for exact match)
  const inventory = [
    {
      type: 'app',
      name: 'Splunk Add-on for Palo Alto Networks',
      extras: 'Splunk_TA_paloalto',
    },
  ];
  const res = matchUseCases(inventory, indexes);
  assert.ok(res.length >= 1, 'expected at least one match');
  assert.equal(res[0].id, 'UC-FOLDER', 'folder-exact should outrank display-fuzzy');
});

// Verify the matcher silently drops garbage app-index keys that
// somehow leak through the upstream filter — a defence-in-depth check.
test('matchUseCases ignores unbalanced-paren garbage keys in apps', () => {
  const { matchUseCases } = loadRecommender();
  const indexes = {
    sourcetypes: {},
    cim: {},
    apps: {
      'Splunk_TA_nix': ['UC-OK'],
      // These should never reach the matcher in v9.x but defence in
      // depth — the JS-side ``looksLikeAppKey`` filter must drop them.
      '(optional) Splunk_TA_nix for foo': ['UC-PROSE-1'],
      'or equivalent firewall TA': ['UC-PROSE-2'],
      'this use case requires a custom HEC poller (props': ['UC-PROSE-3'],
    },
    thin: {
      'UC-OK': { id: 'UC-OK', title: 'OK', criticality: 'high' },
      'UC-PROSE-1': { id: 'UC-PROSE-1', title: 'Bad1', criticality: 'high' },
      'UC-PROSE-2': { id: 'UC-PROSE-2', title: 'Bad2', criticality: 'high' },
      'UC-PROSE-3': { id: 'UC-PROSE-3', title: 'Bad3', criticality: 'high' },
    },
  };
  const inventory = [
    {
      type: 'app',
      name: '*nix',
      extras: 'Splunk_TA_nix',
    },
  ];
  const res = matchUseCases(inventory, indexes);
  const ids = res.map((r) => r.id);
  assert.ok(ids.includes('UC-OK'), 'real folder match must surface');
  assert.equal(
    ids.filter((id) => id.startsWith('UC-PROSE-')).length,
    0,
    'no UC sourced from a garbage key may surface',
  );
});

test('looksLikeAppKey accepts canonical TA folder + display names', () => {
  const { helpers } = loadRecommender();
  assert.ok(helpers, 'helpers must be exposed');
  assert.equal(helpers.looksLikeAppKey('Splunk_TA_nix'), true);
  assert.equal(helpers.looksLikeAppKey('Splunk_TA_paloalto'), true);
  assert.equal(helpers.looksLikeAppKey('splunk_app_db_connect'), true);
  assert.equal(helpers.looksLikeAppKey('Splunk Add-on for AWS (1876)'), true);
  assert.equal(helpers.looksLikeAppKey('Splunk Enterprise Security'), true);
});

test('looksLikeAppKey rejects unbalanced-paren prose fragments', () => {
  const { helpers } = loadRecommender();
  assert.equal(
    helpers.looksLikeAppKey('this use case requires a custom HEC poller (props'),
    false,
  );
  assert.equal(
    helpers.looksLikeAppKey('Splunk Add-on for Salesforce (Splunk_TA_salesforce'),
    false,
  );
  assert.equal(helpers.looksLikeAppKey('Wiz)'), false);
});

test('appNameTokens lowercases and drops short tokens', () => {
  const { helpers } = loadRecommender();
  // Tokens shorter than 3 chars are dropped; punctuation is split on.
  const out = helpers.appNameTokens('Splunk Add-on for AWS (1876)');
  assert.ok(out.includes('splunk'));
  assert.ok(out.includes('add'));
  assert.ok(out.includes('aws'));
  assert.ok(out.includes('1876'));
  // 'on' is 2-char so it's filtered. ``appNameTokens`` itself is a
  // pure tokeniser; stop-word filtering happens inside matchUseCases
  // (see ``matchUseCases respects APP_TOKEN_STOPWORDS`` test).
  assert.ok(!out.includes('on'));
});

test('appNameTokens handles non-string inputs without throwing', () => {
  const { helpers } = loadRecommender();
  // VM-isolated arrays are not reference-equal to host []. Inspect
  // length + Array shape instead.
  const u = helpers.appNameTokens(undefined);
  const n = helpers.appNameTokens(null);
  const num = helpers.appNameTokens(42);
  assert.equal(u.length, 0);
  assert.equal(n.length, 0);
  assert.equal(num.length, 0);
});
