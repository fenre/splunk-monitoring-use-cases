// Phase 4.4 deliverable.  Boots the inline JavaScript in
// scorecard.html against a minimal DOM/fetch shim and asserts that
// every render section populates from the real static JSON sources
// (reports/compliance-coverage.json, reports/compliance-gaps.json,
// scorecard.json, data/regulations.json) without a browser.
//
// This is the headless drift guard for scorecard.html: if the page's
// JavaScript is edited in a way that breaks against the committed
// JSON reports (missing field, bad selector, syntax error, etc.)
// CI fails here instead of only in production.

import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, '..', '..');
const SCORECARD_HTML = path.join(REPO_ROOT, 'scorecard.html');

function extractInlineScript() {
  const html = fs.readFileSync(SCORECARD_HTML, 'utf8');
  const matches = html.match(/<script>([\s\S]*?)<\/script>/g);
  assert.ok(matches && matches.length > 0, 'scorecard.html must contain inline <script>');
  // The last <script> is the boot + render logic; the page only ships one.
  return matches[matches.length - 1]
    .replace(/^<script>/, '')
    .replace(/<\/script>$/, '');
}

function createStubEl() {
  const el = {};
  el.classList = {
    _set: new Set(),
    add() { for (const c of arguments) el.classList._set.add(c); },
    remove() { for (const c of arguments) el.classList._set.delete(c); },
    toggle(c) {
      if (el.classList._set.has(c)) el.classList._set.delete(c);
      else el.classList._set.add(c);
    },
    contains(c) { return el.classList._set.has(c); },
  };
  el.dataset = {};
  el.style = {};
  el._value = '';
  Object.defineProperty(el, 'value', {
    get() { return el._value; },
    set(v) { el._value = v; },
  });
  el._html = '';
  Object.defineProperty(el, 'innerHTML', {
    get() { return el._html; },
    set(v) { el._html = v; },
  });
  el._text = '';
  Object.defineProperty(el, 'textContent', {
    get() { return el._text; },
    set(v) { el._text = v; },
  });
  el._cls = '';
  Object.defineProperty(el, 'className', {
    get() { return el._cls; },
    set(v) { el._cls = v; },
  });
  el.insertAdjacentHTML = () => {};
  el.addEventListener = () => {};
  el.querySelectorAll = () => [];
  el.querySelector = () => null;
  return el;
}

function buildDomShim() {
  const registry = {};
  const ensure = (id) => (registry[id] = registry[id] || createStubEl());
  const documentStub = {
    documentElement: createStubEl(),
    getElementById: (id) => ensure(id),
    querySelector: () => ensure('main'),
    querySelectorAll: () => [],
  };
  return { registry, documentStub };
}

function filesystemFetch(resourcePath) {
  // Strip any leading "/" or "./".
  const normalized = resourcePath.replace(/^\.\//, '').replace(/^\//, '');
  const absolute = path.resolve(REPO_ROOT, normalized);
  if (!absolute.startsWith(REPO_ROOT + path.sep) && absolute !== REPO_ROOT) {
    return Promise.resolve({
      ok: false,
      status: 403,
      statusText: 'Forbidden (outside repo root)',
      json: () => Promise.reject(new Error('forbidden')),
    });
  }
  try {
    const data = fs.readFileSync(absolute, 'utf8');
    return Promise.resolve({
      ok: true,
      status: 200,
      statusText: 'OK',
      json: () => Promise.resolve(JSON.parse(data)),
    });
  } catch (e) {
    return Promise.resolve({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: () => Promise.reject(e),
    });
  }
}

function bootInlineScript(scriptSrc) {
  const { registry, documentStub } = buildDomShim();
  const localStorageStub = {
    _m: {},
    getItem(k) { return this._m[k] || null; },
    setItem(k, v) { this._m[k] = v; },
    removeItem(k) { delete this._m[k]; },
  };

  const sandbox = {
    window: { matchMedia: () => ({ matches: false }) },
    document: documentStub,
    localStorage: localStorageStub,
    fetch: filesystemFetch,
    console,
    setTimeout,
    clearTimeout,
    Promise,
    JSON,
    Math,
    Date,
    Number,
    String,
    Boolean,
    Array,
    Object,
    Error,
    // isFinite / isNaN global functions used by helpers
    isNaN,
    isFinite,
  };
  vm.createContext(sandbox);
  vm.runInContext(scriptSrc, sandbox, { filename: 'scorecard.html::inline' });

  // boot() returns immediately but resolves asynchronously.  We wait for
  // the IIFE to settle by flushing microtasks a few times.
  return new Promise((resolve) => {
    const flush = (iterations) => {
      if (iterations === 0) return resolve(registry);
      setImmediate(() => flush(iterations - 1));
    };
    flush(10);
  });
}

test('scorecard.html renders global rollup, tables, and findings from static JSON', async () => {
  const scriptSrc = extractInlineScript();
  const registry = await bootInlineScript(scriptSrc);

  const expectations = [
    [
      'sc-audit-status',
      (el) => typeof el._text === 'string' && el._text.length > 0,
      'audit status badge should be populated',
    ],
    [
      'sc-hero-meta',
      (el) => typeof el._html === 'string' && el._html.includes('Generated'),
      'hero meta should include "Generated ..." timestamp',
    ],
    [
      'sc-global-metrics',
      (el) => typeof el._html === 'string' && el._html.includes('Clause coverage'),
      'global metric cards should render "Clause coverage"',
    ],
    [
      'sc-tier-grid',
      (el) => typeof el._html === 'string' && el._html.includes('Tier 1'),
      'tier grid should render Tier 1 card',
    ],
    [
      'sc-reg-tbody',
      (el) => typeof el._html === 'string' && el._html.length > 100,
      'per-regulation tbody should render at least one row',
    ],
    [
      'sc-cat-tbody',
      (el) => typeof el._html === 'string' && el._html.length > 100,
      'per-category tbody should render at least one row',
    ],
    [
      'sc-grade-dist',
      (el) => typeof el._html === 'string' && el._html.includes('Gold'),
      'grade distribution strip should render Gold card',
    ],
    [
      'sc-findings-grid',
      (el) => typeof el._html === 'string' && el._html.includes('Golden'),
      'findings grid should render Golden-tests metric',
    ],
    [
      'sc-reg-count',
      (el) => typeof el._text === 'string' && el._text.includes('regulations'),
      'regulation counter should render "... regulations"',
    ],
    [
      'sc-cat-count',
      (el) => typeof el._text === 'string' && el._text.includes('categories'),
      'category counter should render "... categories"',
    ],
  ];

  const failures = [];
  for (const [id, assertion, message] of expectations) {
    const el = registry[id];
    if (!el) {
      failures.push(`${id}: element never rendered — ${message}`);
      continue;
    }
    if (!assertion(el)) {
      failures.push(`${id}: ${message} (html="${String(el._html || '').slice(0, 120)}" text="${String(el._text || '').slice(0, 120)}")`);
    }
  }
  assert.deepEqual(failures, [], failures.join('\n'));
});

test('scorecard.html inline script exposes no obvious XSS sinks in dynamic HTML', async () => {
  // Phase 4.4 threat model: the page only fetches same-origin JSON files
  // and renders them through escapeHtml-wrapped template strings.  This
  // test fails if someone ever inlines an un-escaped field directly.
  const scriptSrc = extractInlineScript();
  const dangerousPatterns = [
    /innerHTML\s*=\s*[^;]*?\btier_key\b/i,          // example: raw ID back into HTML
    /innerHTML\s*\+=\s*`[^`]*\$\{[^}]*\.name\}/,    // unescaped name interpolation
    /document\.write/i,
    /eval\s*\(/,
    /new\s+Function\s*\(/,
  ];
  const hits = [];
  for (const p of dangerousPatterns) {
    if (p.test(scriptSrc)) hits.push(String(p));
  }
  assert.deepEqual(hits, [], `Dangerous DOM patterns found in scorecard.html inline script: ${hits.join(', ')}`);
});
