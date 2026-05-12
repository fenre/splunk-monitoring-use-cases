// Tests for the recommender.js AMD module produced by
// python3 -m splunk_uc generate-recommender-app. We run them against the
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

// ---------------------------------------------------------------------------
// Build 14 — relevance overhaul. Switching from "anything that mentions an
// app you have installed" to a tiered signal model where actual data
// (sourcetypes, CIM models) outweighs nominal app-installation matches.
// ---------------------------------------------------------------------------

test('matchUseCases: sourcetype EXACT match dominates app token match (build 14 weight)', () => {
  const { matchUseCases } = loadRecommender();
  const indexes = {
    sourcetypes: { 'meraki:devices': ['UC-ST'] },
    cim: {},
    apps: { 'Splunk_TA_cisco_meraki': ['UC-APP'] },
    thin: {
      'UC-ST':  { id: 'UC-ST',  title: 'sourcetype', criticality: 'high' },
      'UC-APP': { id: 'UC-APP', title: 'app',        criticality: 'high' },
    },
  };
  const inv = [
    { type: 'sourcetype', name: 'meraki:devices' },
    { type: 'app',        name: 'Cisco Meraki Add-on for Splunk', extras: 'Splunk_TA_cisco_meraki' },
  ];
  const res = matchUseCases(inv, indexes);
  const stHit  = res.find((r) => r.id === 'UC-ST');
  const appHit = res.find((r) => r.id === 'UC-APP');
  // Build 14: sourcetype exact = +10, app folder-exact = +3.
  assert.ok(stHit && appHit, 'both UCs must surface');
  assert.ok(
    stHit._score >= 10,
    `sourcetype exact must score ≥ 10 (got ${stHit._score})`,
  );
  assert.ok(
    stHit._score > appHit._score,
    'sourcetype exact must outrank app folder-exact',
  );
});

test('matchUseCases: CIM model present (not_accelerated) awards +0.5 (build 15)', () => {
  // Build 13 only awarded when ``extras === 'accelerated'``. Build 14
  // bumped unaccelerated to +1 to reward "CIM defined" as intent.
  // Build 15 halves that to +0.5 because real-world deployments often
  // ship with all 27 CIM models defined-but-not-accelerated, making the
  // +1 a flat noise floor that lifts every CIM-touching UC equally.
  // Accelerated stays at +3.
  const { matchUseCases } = loadRecommender();
  const indexes = {
    sourcetypes: {},
    cim: {
      'Authentication': ['UC-AUTH-1'],
      'Network_Traffic': ['UC-NET'],
    },
    apps: {},
    thin: {
      'UC-AUTH-1': { id: 'UC-AUTH-1', title: 'auth-defined', criticality: 'high' },
      'UC-NET':    { id: 'UC-NET',    title: 'net-accel',    criticality: 'high' },
    },
  };
  const inv = [
    { type: 'cim_model', name: 'Authentication',  extras: 'not_accelerated' },
    { type: 'cim_model', name: 'Network_Traffic', extras: 'accelerated'     },
  ];
  const res = matchUseCases(inv, indexes);
  const auth = res.find((r) => r.id === 'UC-AUTH-1');
  const net  = res.find((r) => r.id === 'UC-NET');
  assert.ok(auth, 'unaccelerated CIM must still surface its UCs');
  assert.equal(auth._score, 0.5,
    `CIM defined (unaccelerated) must score +0.5 in build 15, got ${auth._score}`);
  assert.equal(net._score, 3,
    `CIM accelerated must remain +3, got ${net._score}`);
});

test('matchUseCases: evidence-pack synthetic key "App (NNNN)" gets a 0.4x discount', () => {
  // Build 14 ev-pack penalty. Catalogue keys like
  //   ``Splunk Add-on for Unix and Linux (833)``
  // are regulatory documentation citations, NOT actionable installs.
  // Their score is multiplied by 0.4 so a substring-match through them
  // contributes 0.4 instead of 1.
  const { matchUseCases } = loadRecommender();
  const indexes = {
    sourcetypes: {},
    cim: {},
    apps: {
      // Vanilla key — plain display name. Full weight.
      'Splunk Add-on for Unix and Linux':                  ['UC-VANILLA'],
      // Evidence-pack synthetic — Splunkbase ID in parentheses.
      'Splunk Add-on for Unix and Linux (833)':            ['UC-EVPACK-1'],
      'Splunk Add-on for Unix and Linux (Splunkbase 833)': ['UC-EVPACK-2'],
    },
    thin: {
      'UC-VANILLA':  { id: 'UC-VANILLA',  title: 'vanilla', criticality: 'high' },
      'UC-EVPACK-1': { id: 'UC-EVPACK-1', title: 'ev1',     criticality: 'high' },
      'UC-EVPACK-2': { id: 'UC-EVPACK-2', title: 'ev2',     criticality: 'high' },
    },
  };
  // Realistic inventory shape — display name in ``name``, folder in ``extras``.
  const inv = [{
    type: 'app',
    name: 'Splunk Add-on for Unix and Linux',
    extras: 'Splunk_TA_nix',
  }];
  const res = matchUseCases(inv, indexes);
  const vanilla = res.find((r) => r.id === 'UC-VANILLA');
  const ev1     = res.find((r) => r.id === 'UC-EVPACK-1');
  const ev2     = res.find((r) => r.id === 'UC-EVPACK-2');
  assert.ok(vanilla, 'vanilla key UC must surface at full +3 weight (exact match)');
  assert.equal(vanilla._score, 3);
  assert.ok(ev1, 'evidence-pack key must still match (substring)');
  assert.ok(ev2, 'evidence-pack key must still match (substring)');
  // Evidence-pack matches contribute 1 × 0.4 = 0.4 (substring match).
  assert.ok(
    ev1._score < 1,
    `evidence-pack (NNNN) hit must be < 1 after 0.4x discount, got ${ev1._score}`,
  );
  assert.ok(
    ev2._score < 1,
    `evidence-pack (Splunkbase NNNN) hit must be < 1, got ${ev2._score}`,
  );
});

test('matchUseCases: user index names contribute a low-weight signal (build 14)', () => {
  // Build 14 adds matching on inventory rows of type=``index``. The
  // user's index names (e.g. ``meraki``, ``edge_hub_opcua``, ``linux``)
  // are real evidence of data flowing — but they're a weaker signal
  // than sourcetypes (which carry the actual event shape). Awarded as
  // a +1 bump per matching catalogue key, capped by the per-row dedup.
  const { matchUseCases } = loadRecommender();
  const indexes = {
    sourcetypes: { 'splunk:edge_hub:opcua': ['UC-OPC'] },
    cim: {},
    apps: { 'Splunk Connect for Edge Hub': ['UC-EDGE'] },
    thin: {
      'UC-OPC':  { id: 'UC-OPC',  title: 'opcua', criticality: 'high' },
      'UC-EDGE': { id: 'UC-EDGE', title: 'edge',  criticality: 'high' },
    },
  };
  const inv = [
    // Only an INDEX, no sourcetype/app entries
    { type: 'index', name: 'edge_hub_opcua' },
  ];
  const res = matchUseCases(inv, indexes);
  // UC-OPC reachable via sourcetype name fuzzy substring match on
  // "opcua" (index ↔ sourcetype "splunk:edge_hub:opcua")
  // UC-EDGE reachable via app key containing "edge"
  // Both should surface but at the low index-tier weight.
  assert.ok(res.length >= 1, 'at least one UC reachable through index name');
  res.forEach((r) => {
    assert.ok(r._score > 0 && r._score <= 3,
      `index-only matches should yield a small positive score (got ${r._score} for ${r.id})`);
  });
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

// ---------------------------------------------------------------------------
// Build 15 — relevance overhaul phase 2. Live-data simulation against a
// real production-shape inventory (Cisco Meraki + Pi-hole + Edge Hub +
// ITSI shop with ~90 apps, 27 CIM models, 37 indexes, 40 sourcetypes)
// showed that even with Build 13/14 fixes, app-token overlap was still
// the single largest score contributor (12,269 points) — driven by ITSI
// Content Pack apps, internal ITSI indexes, and Splunk-auto-classified
// junk sourcetypes (`_json`, `stash`, `*-too_small`). These tests pin the
// six guards that suppress that noise.
// ---------------------------------------------------------------------------

test('Build 15: ITSI / module / monitoring / content / pack stop-words filter token-only matches', () => {
  // The user's inventory has 11 "ITSI Module for X" apps, 16 Content
  // Packs, and "Monitoring Microsoft Windows" / "Monitoring Citrix" / etc.
  // Without expanded stop-words, every ITSI Content Pack token-matched
  // every catalogue UC mentioning "itsi" / "module" / "monitoring" /
  // "content" / "pack" — flooding the leaderboard.
  const { matchUseCases } = loadRecommender();
  const indexes = {
    sourcetypes: {},
    cim: {},
    apps: {
      // Catalogue keys whose ONLY shared token is one of the new
      // stop-words. Without the guard, these match the inventory rows.
      'ITSI Service Catalog':                  ['UC-NOISE-A'],
      'Splunk ITSI Content Pack for VMware':   ['UC-NOISE-B'],
      'Monitoring Console (1306)':             ['UC-NOISE-C'],
      'Splunk Dashboard Pack for Workplace':   ['UC-NOISE-D'],
      // Real meaningful match — shares "windows" with inventory.
      'Monitoring Microsoft Windows for Splunk': ['UC-REAL'],
    },
    thin: {
      'UC-NOISE-A': { id: 'UC-NOISE-A', title: 'noise-itsi',       criticality: 'high' },
      'UC-NOISE-B': { id: 'UC-NOISE-B', title: 'noise-content',    criticality: 'high' },
      'UC-NOISE-C': { id: 'UC-NOISE-C', title: 'noise-monitoring', criticality: 'high' },
      'UC-NOISE-D': { id: 'UC-NOISE-D', title: 'noise-pack',       criticality: 'high' },
      'UC-REAL':    { id: 'UC-REAL',    title: 'real',             criticality: 'high' },
    },
  };
  const inventory = [
    { type: 'app', name: 'ITSI Module for Database Systems', extras: 'DA-ITSI-DATABASE' },
    { type: 'app', name: 'Content Pack for ServiceNow',      extras: 'DA-ITSI-CP-SERVICENOW' },
    { type: 'app', name: 'Monitoring Microsoft Windows',     extras: 'DA-ITSI-CP-windows' },
  ];
  const res = matchUseCases(inventory, indexes);
  const ids = res.map((r) => r.id);
  assert.ok(ids.includes('UC-REAL'), 'meaningful "windows" / "microsoft" overlap must surface');
  assert.ok(!ids.includes('UC-NOISE-A'),
    'must NOT match ITSI catalogue entry purely on stop-word "itsi" overlap');
  assert.ok(!ids.includes('UC-NOISE-B'),
    'must NOT match ITSI Content Pack entry purely on "itsi"/"content"/"pack"');
  assert.ok(!ids.includes('UC-NOISE-C'),
    'must NOT match Monitoring Console purely on "monitoring"');
  assert.ok(!ids.includes('UC-NOISE-D'),
    'must NOT match Dashboard Pack purely on "pack"/"dashboard"');
});

test('Build 15: Splunk-auto-classified junk sourcetypes contribute zero score', () => {
  // The user's saved-search inventory includes Splunk-auto-classified
  // sourcetypes that don't represent real monitored data domains:
  //   _json, stash, learned, config_file, *-too_small, dpkg-N,
  //   alternatives-N, history-N, bare metric names like "cpu" / "disk"
  // These should not contribute to recommendation scores. A user who
  // happens to have any of these does not have signal about real UCs.
  const { matchUseCases } = loadRecommender();
  const indexes = {
    sourcetypes: {
      '_json':                  ['UC-JUNK-1'],
      'stash':                  ['UC-JUNK-2'],
      'config_file':            ['UC-JUNK-3'],
      'dpkg-9':                 ['UC-JUNK-4'],
      'alternatives-too_small': ['UC-JUNK-5'],
      'history-too_small':      ['UC-JUNK-6'],
      'cpu':                    ['UC-JUNK-7'],   // bare auto-classified name, length ≤ 4
      // Real sourcetype, must still score normally.
      'meraki:devices':         ['UC-REAL'],
    },
    cim: {},
    apps: {},
    thin: {
      'UC-JUNK-1': { id: 'UC-JUNK-1', title: 'junk', criticality: 'high' },
      'UC-JUNK-2': { id: 'UC-JUNK-2', title: 'junk', criticality: 'high' },
      'UC-JUNK-3': { id: 'UC-JUNK-3', title: 'junk', criticality: 'high' },
      'UC-JUNK-4': { id: 'UC-JUNK-4', title: 'junk', criticality: 'high' },
      'UC-JUNK-5': { id: 'UC-JUNK-5', title: 'junk', criticality: 'high' },
      'UC-JUNK-6': { id: 'UC-JUNK-6', title: 'junk', criticality: 'high' },
      'UC-JUNK-7': { id: 'UC-JUNK-7', title: 'junk', criticality: 'high' },
      'UC-REAL':   { id: 'UC-REAL',   title: 'real', criticality: 'high' },
    },
  };
  const inventory = [
    { type: 'sourcetype', name: '_json' },
    { type: 'sourcetype', name: 'stash' },
    { type: 'sourcetype', name: 'config_file' },
    { type: 'sourcetype', name: 'dpkg-9' },
    { type: 'sourcetype', name: 'alternatives-too_small' },
    { type: 'sourcetype', name: 'history-too_small' },
    { type: 'sourcetype', name: 'cpu' },
    { type: 'sourcetype', name: 'meraki:devices' },
  ];
  const res = matchUseCases(inventory, indexes);
  const ids = res.map((r) => r.id);
  assert.ok(ids.includes('UC-REAL'), 'meraki:devices must surface');
  for (let i = 1; i <= 7; i++) {
    assert.ok(!ids.includes('UC-JUNK-' + i),
      `junk sourcetype #${i} must not contribute to scoring`);
  }
});

test('Build 15: Splunk-system / ITSI-internal indexes contribute zero score', () => {
  // The user's index list includes Splunk-system / ITSI-internal
  // indexes whose names are not signals of monitored data:
  //   main, summary, history, learned, _internal, _audit,
  //   cim_modactions, anomaly_detection, snmptrapd, itsi_*
  // These should be filtered out before tokenisation so they don't
  // generate token-overlap matches against the catalogue.
  const { matchUseCases } = loadRecommender();
  const indexes = {
    sourcetypes: {
      // Catalogue sourcetypes whose tokens overlap with ITSI internal
      // index names — these must NOT match anything from the user's
      // itsi_* / main / summary / learned indexes.
      'itsi:notable':        ['UC-NOISE-1'],
      'splunk:summary':      ['UC-NOISE-2'],
      'splunk:learned':      ['UC-NOISE-3'],
      // Real index → sourcetype overlap on "meraki" must still match.
      'meraki:wireless':     ['UC-REAL'],
    },
    cim: {},
    apps: {},
    thin: {
      'UC-NOISE-1': { id: 'UC-NOISE-1', title: 'itsi-noise',    criticality: 'high' },
      'UC-NOISE-2': { id: 'UC-NOISE-2', title: 'summary-noise', criticality: 'high' },
      'UC-NOISE-3': { id: 'UC-NOISE-3', title: 'learned-noise', criticality: 'high' },
      'UC-REAL':    { id: 'UC-REAL',    title: 'real',          criticality: 'high' },
    },
  };
  const inventory = [
    { type: 'index', name: 'itsi_summary' },
    { type: 'index', name: 'itsi_notable_audit' },
    { type: 'index', name: 'main' },
    { type: 'index', name: 'summary' },
    { type: 'index', name: 'history' },
    { type: 'index', name: 'learned' },
    { type: 'index', name: 'cim_modactions' },
    { type: 'index', name: 'anomaly_detection' },
    { type: 'index', name: '_internal' },
    { type: 'index', name: 'meraki' },   // real, keep
  ];
  const res = matchUseCases(inventory, indexes);
  const ids = res.map((r) => r.id);
  assert.ok(ids.includes('UC-REAL'),
    'meraki index must still match meraki:wireless via shared "meraki" token');
  assert.ok(!ids.includes('UC-NOISE-1'),
    'itsi_* internal index must not match itsi:notable purely on "itsi"');
  assert.ok(!ids.includes('UC-NOISE-2'),
    'summary index must not match splunk:summary purely on "summary"');
  assert.ok(!ids.includes('UC-NOISE-3'),
    'learned index must not match splunk:learned purely on "learned"');
});

test('Build 15: ITSI Content-Pack / Module apps get a 0.4x discount on their matches', () => {
  // Inventory rows whose ``extras`` (folder name) matches DA-ITSI-CP-*,
  // DA-ITSI-*, or SA-ITSI-* are ITSI internals (Content Packs, Modules,
  // supporting addons). Installing them reflects ITSI plumbing, not a
  // user data domain, so the matches they generate are scaled by the
  // same EVIDENCE_PACK_DISCOUNT (0.4×) we already use for synthetic
  // catalogue keys.
  const { matchUseCases } = loadRecommender();
  // Two completely separate token universes so each inventory row only
  // matches one of the two UCs — no overlap, no per-(row,UC) cap
  // interaction muddying the score we want to inspect.
  const indexes = {
    sourcetypes: {},
    cim: {},
    apps: {
      // Match for the vanilla inventory row only — shares "vmware".
      'VMware Operations Manager':   ['UC-VANILLA'],
      // Match for the Content-Pack inventory row only — shares "citrix".
      'Citrix Appliance Monitor':    ['UC-DISCOUNTED'],
    },
    thin: {
      'UC-VANILLA':    { id: 'UC-VANILLA',    title: 'vanilla',    criticality: 'high' },
      'UC-DISCOUNTED': { id: 'UC-DISCOUNTED', title: 'discounted', criticality: 'high' },
    },
  };
  const inv = [
    // Vanilla user-installed app — no Content Pack discount.
    { type: 'app', name: 'VMware ESXi monitoring',  extras: 'splunk_app_vmw' },
    // Content Pack — must be discounted via DA-ITSI-CP-* heuristic.
    { type: 'app', name: 'Citrix XenApp data',      extras: 'DA-ITSI-CP-citrix' },
  ];
  const res = matchUseCases(inv, indexes);
  const vanilla    = res.find((r) => r.id === 'UC-VANILLA');
  const discounted = res.find((r) => r.id === 'UC-DISCOUNTED');
  assert.ok(vanilla, 'vanilla app match must surface');
  assert.ok(discounted, 'discounted app match must still surface');
  // Token-overlap weight = 0.5 (build 14). With CP discount (0.4×):
  //   vanilla    = 0.5
  //   discounted = 0.5 × 0.4 = 0.2
  assert.ok(
    Math.abs(vanilla._score - 0.5) < 0.01,
    `vanilla token-overlap match should score 0.5, got ${vanilla._score}`,
  );
  assert.ok(
    Math.abs(discounted._score - 0.2) < 0.01,
    `Content-Pack token-overlap match should score 0.2 (0.5×0.4), got ${discounted._score}`,
  );
});

test('Build 15: fuzzy sourcetype weight scales with substring length ratio', () => {
  // Live data showed 24 Meraki sourcetypes (`meraki:devices`,
  // `meraki:airmarshal`, …) all fuzzy-matching the single short
  // catalogue key `meraki` at the same flat +4 weight, producing
  // 41 UCs tied at the exact same score (98.40) with no granularity
  // inside cat-5. Build 15 weights fuzzy matches by
  //   4 × min(invLen, keyLen) / max(invLen, keyLen)
  // so a long inventory name `meraki:wirelessdevicespacketloss…` (39
  // chars) matching catalogue `meraki` (6 chars) gets ~0.6, while
  // a closer pair like `meraki:wireless` (15) ↔ `meraki:wireless`
  // (15) still goes through the EXACT path at +10.
  const { matchUseCases } = loadRecommender();
  const indexes = {
    sourcetypes: {
      'meraki':          ['UC-SHORT'],
      'meraki:wireless': ['UC-CLOSE'],
    },
    cim: {},
    apps: {},
    thin: {
      'UC-SHORT': { id: 'UC-SHORT', title: 'short', criticality: 'high' },
      'UC-CLOSE': { id: 'UC-CLOSE', title: 'close', criticality: 'high' },
    },
  };
  // Single inventory row whose name is much longer than `meraki`
  // and shares a much smaller substring ratio with it than with
  // `meraki:wireless`.
  const inv = [{ type: 'sourcetype', name: 'meraki:wirelessdevicespacketlossbydevice' }];
  const res = matchUseCases(inv, indexes);
  const short = res.find((r) => r.id === 'UC-SHORT');
  const close = res.find((r) => r.id === 'UC-CLOSE');
  assert.ok(short && close, 'both UCs must surface (both fuzzy-match the inventory)');
  // Build 14 would tie short._score === close._score === 4.
  // Build 15: closer-length pair must score higher than far-length pair.
  assert.ok(
    close._score > short._score,
    `close-length fuzzy must outrank far-length fuzzy: ` +
    `got close=${close._score} short=${short._score}`,
  );
  // Sanity: long-vs-short ratio (6/40 = 0.15) caps the score below
  // the original flat +4 build-14 weight.
  assert.ok(
    short._score < 4,
    `far-length fuzzy must be < 4 in build 15, got ${short._score}`,
  );
});

test('Build 15: matchUseCases output includes equipment + equipmentModels for UI sort/filter', () => {
  // Build 15 surfaces equipment + equipmentModels on the recommendation
  // shape so the UI can filter / sort / chip on them without an extra
  // catalog lookup. They come from `thin` directly (compact uc-thin.json
  // already carries them since v8.0).
  const { matchUseCases } = loadRecommender();
  const indexes = {
    sourcetypes: { 'meraki:devices': ['UC-A'] },
    cim: {},
    apps: {},
    thin: {
      'UC-A': {
        id: 'UC-A',
        title: 'has equipment',
        criticality: 'high',
        equipment: ['cisco', 'meraki'],
        equipmentModels: ['Meraki MR'],
      },
    },
  };
  const res = matchUseCases([{ type: 'sourcetype', name: 'meraki:devices' }], indexes);
  const hit = res.find((r) => r.id === 'UC-A');
  assert.ok(hit, 'UC must surface');
  assert.deepEqual(hit.equipment, ['cisco', 'meraki'],
    'equipment array must be propagated from thin to the rec output');
  assert.deepEqual(hit.equipmentModels, ['Meraki MR'],
    'equipmentModels must be propagated');
});
