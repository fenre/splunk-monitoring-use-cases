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

// ---------------------------------------------------------------------------
// Build 13 — three fixes for cat-22 over-dominance in the recommend list.
// Live data simulation showed 100/100 of the top-100 were cat-22 because
// (a) generic tokens like "splunk" / "for" / "add" caused token-overlap
// fuzzy matches across hundreds of catalogue keys, (b) one inventory row
// could pile +20 points onto a single UC by hitting many synthetic
// "App Name (NNNN)" cat-22 evidence-pack keys, and (c) no diversification
// ceiling let cat-22 sweep the slice(0,100). These tests pin all three
// fixes so the same regression can never recur silently.
// ---------------------------------------------------------------------------

test('matchUseCases respects APP_TOKEN_STOPWORDS in token-overlap fallback', () => {
  // Two inventory rows both share only the generic Splunk-marketing
  // tokens "splunk" / "add" / "for". The catalogue key shares the
  // same generic tokens but is otherwise unrelated. Without a stop-word
  // filter, the user's "Splunk Get Data In" inventory app would
  // fuzzy-token-match "Splunk Add-on for ServiceNow" → spam its UC.
  const { matchUseCases } = loadRecommender();
  const indexes = {
    sourcetypes: {},
    cim: {},
    apps: {
      // Both keys share zero meaningful tokens with the inventory rows;
      // they share only stop-word-class tokens "splunk" / "add" / "for".
      'Splunk Add-on for ServiceNow': ['UC-NOISE-1'],
      'Splunk Add-on for Microsoft Azure': ['UC-NOISE-2'],
      // Real meaningful match — shares "linux" with inventory.
      'Splunk Add-on for Unix and Linux': ['UC-REAL'],
    },
    thin: {
      'UC-NOISE-1': { id: 'UC-NOISE-1', title: 'noise', criticality: 'high' },
      'UC-NOISE-2': { id: 'UC-NOISE-2', title: 'noise', criticality: 'high' },
      'UC-REAL':    { id: 'UC-REAL',    title: 'real',  criticality: 'high' },
    },
  };
  const inventory = [
    {
      type: 'app',
      name: 'Splunk Get Data In',
      extras: 'splunk_get_data_in',
    },
    {
      type: 'app',
      name: 'Splunk Add-on for Linux',
      extras: 'Splunk_TA_nix',
    },
  ];
  const res = matchUseCases(inventory, indexes);
  const ids = res.map((r) => r.id);
  assert.ok(ids.includes('UC-REAL'), 'meaningful "linux" overlap must surface');
  assert.ok(
    !ids.includes('UC-NOISE-1'),
    'must NOT match ServiceNow UC purely on stop-word "splunk"/"add"/"for" overlap',
  );
  assert.ok(
    !ids.includes('UC-NOISE-2'),
    'must NOT match Azure UC purely on stop-word "splunk"/"add"/"for" overlap',
  );
});

test('matchUseCases caps a single inventory row\'s contribution to one UC', () => {
  // Build 13 cap: one inventory row matching N catalogue keys that all
  // point at the SAME UC must not pile up N×weight on that UC. The cap
  // is +3 per (inventory_row, UC) pair so that one badly-chosen row
  // can't dominate the leaderboard. This is exactly what the cat-22
  // evidence-pack synthetic keys (e.g. "Splunk_TA_nix" + "Splunk_TA_nix
  // (833)" + "Splunk_TA_nix (Splunkbase 833)") were doing.
  const { matchUseCases } = loadRecommender();
  const indexes = {
    sourcetypes: {},
    cim: {},
    apps: {
      // Five cat-22 catalogue keys that all cite UC-DUP — i.e. the
      // synthetic "App (NNNN)" pattern visible in the live API.
      'Splunk_TA_nix':                            ['UC-DUP'],
      'Splunk_TA_nix (833)':                      ['UC-DUP'],
      'Splunk_TA_nix (Splunkbase 833)':           ['UC-DUP'],
      'Splunk Add-on for Unix and Linux':         ['UC-DUP'],
      'Splunk Add-on for Unix and Linux (833)':   ['UC-DUP'],
      // One vanilla key citing UC-NORMAL for comparison.
      'Splunk_TA_paloalto':                       ['UC-NORMAL'],
    },
    thin: {
      'UC-DUP':    { id: 'UC-DUP',    title: 'dup',    criticality: 'high' },
      'UC-NORMAL': { id: 'UC-NORMAL', title: 'normal', criticality: 'high' },
    },
  };
  const inventory = [
    { type: 'app', name: '*nix',           extras: 'Splunk_TA_nix' },
    { type: 'app', name: 'Palo Alto',      extras: 'Splunk_TA_paloalto' },
  ];
  const res = matchUseCases(inventory, indexes);
  const dupHit    = res.find((r) => r.id === 'UC-DUP');
  const normalHit = res.find((r) => r.id === 'UC-NORMAL');
  assert.ok(dupHit && normalHit, 'both UCs must surface');
  // Pre-fix: dup score would be ~3 + 1 + 1 + 1 + 1 = 7 (or higher).
  // Post-fix: per-(row,UC) cap holds it to a single ``+3`` exact bump.
  assert.ok(
    dupHit._score <= 3,
    `single inv row must contribute at most +3 to a UC; got ${dupHit._score}`,
  );
  assert.ok(
    dupHit._score >= 3,
    'must still award the strongest single match (+3 exact)',
  );
});

test('matchUseCases diversifies the top slice across categories', () => {
  // Build 13 diversification: when the unbounded top-N would be 100%
  // one category (the live cat-22 case), enforce a per-category cap
  // so the user sees a representative mix. Uses synthetic UCs across
  // four categories: cat-22 with very high scores, cat-10 medium,
  // cat-5 medium, cat-1 lower. Without diversification, cat-22 would
  // sweep the top-N. With it, every category that scored anything
  // should appear.
  const { matchUseCases } = loadRecommender();
  const indexes = { sourcetypes: {}, cim: {}, apps: {}, thin: {} };
  // Build up a synthetic catalogue: 200 cat-22 UCs, 50 cat-10, 30 cat-5,
  // 20 cat-1. Each one is reachable through one app key the user has.
  const inv = [{ type: 'app', name: 'Splunk_TA_universal', extras: 'Splunk_TA_universal' }];
  function addUcs(prefix, n, score_keys) {
    for (var i = 1; i <= n; i++) {
      var id = prefix + '.1.' + i;
      indexes.thin[id] = { id, title: `${prefix} UC ${i}`, criticality: 'high' };
      // ``score_keys`` keys all cite the same UC, simulating the
      // live cat-22 synthetic-key effect.
      for (var k = 0; k < score_keys; k++) {
        var key = `Splunk_TA_universal-cat${prefix}-${i}-${k}`;
        indexes.apps[key] = (indexes.apps[key] || []).concat(id);
      }
    }
  }
  addUcs('22', 200, 5);
  addUcs('10', 50,  2);
  addUcs('5',  30,  2);
  addUcs('1',  20,  2);
  const res = matchUseCases(inv, indexes);
  const top100 = res.slice(0, 100);
  const cats = new Set(top100.map((r) => r.id.split('.')[0]));
  assert.ok(top100.length >= 100, 'must produce at least 100 results');
  assert.ok(cats.has('22'), 'cat-22 still represented (it scored highest)');
  assert.ok(cats.has('10'), 'cat-10 must also be represented (diversification)');
  assert.ok(cats.has('5'),  'cat-5 must also be represented (diversification)');
  // No single category may exceed 50% of the top-100 unless the others
  // are exhausted. With 200/50/30/20 = 300 candidates, no exhaustion.
  const cat22Count = top100.filter((r) => r.id.startsWith('22.')).length;
  assert.ok(
    cat22Count <= 50,
    `cat-22 capped at 50% of top-100; got ${cat22Count}`,
  );
});
