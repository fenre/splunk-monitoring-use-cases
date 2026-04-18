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
  return sandbox.window.__uc_recommender__;
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
