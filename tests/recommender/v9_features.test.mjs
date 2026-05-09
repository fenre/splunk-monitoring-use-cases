// v9.0 implementation-tracking + Splunkbase install guidance tests.
//
// Mirrors the vm-sandbox pattern used by tests/recommender/match.test.mjs
// — same trade-offs (minimal DOM stub, no real layout) but no extra
// dependency. We exercise:
//   * Status enum + label coverage
//   * safeSplunkbaseUrl allow-list (XSS / spoofing defense)
//   * statusOf fallback behavior
//   * renderStatusBadge a11y (text content always present)
//   * renderRequiredSplunkbase rendering + URL filtering
//
// Run: `node --test tests/recommender/v9_features.test.mjs`

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

// Build a tiny but DOM-shaped element factory. Tracks children, text,
// attrs, and dataset so the render functions can be inspected without
// jsdom.
function makeElement(tagName) {
  const el = {
    tagName,
    children: [],
    attrs: Object.create(null),
    dataset: Object.create(null),
    _text: '',
    style: {},
    classList: { add() {}, remove() {} },
    appendChild(child) {
      this.children.push(child);
      child.parentNode = this;
      return child;
    },
    setAttribute(k, v) {
      this.attrs[k] = String(v);
      // Mirror data-* into dataset for badge tests.
      if (k.indexOf('data-') === 0) {
        this.dataset[k.slice(5)] = String(v);
      }
      if (k === 'class') this._class = String(v);
    },
    getAttribute(k) {
      return Object.prototype.hasOwnProperty.call(this.attrs, k) ? this.attrs[k] : null;
    },
    addEventListener() {},
    set textContent(v) { this._text = v; },
    get textContent() {
      // Mimic the DOM spec — combine direct text + descendant text.
      const parts = [];
      if (this._text) parts.push(this._text);
      this.children.forEach((c) => {
        if (c.tagName) parts.push(c.textContent);
      });
      return parts.join('');
    },
    querySelector(sel) {
      // Minimal class+tag selector support: '.foo', 'tag.foo', or 'tag'.
      const stack = [...this.children];
      while (stack.length) {
        const node = stack.shift();
        if (matches(node, sel)) return node;
        if (node.children) stack.push(...node.children);
      }
      return null;
    },
    querySelectorAll(sel) {
      const out = [];
      const stack = [...this.children];
      while (stack.length) {
        const node = stack.shift();
        if (matches(node, sel)) out.push(node);
        if (node.children) stack.push(...node.children);
      }
      return out;
    },
  };
  return el;
}

function matches(node, sel) {
  if (!sel || !node || !node.tagName) return false;
  // Strip any descendant combinators — we only need leaf-class checks.
  const last = sel.split(/\s+/).pop();
  if (last.startsWith('.')) {
    const cls = last.slice(1);
    return node._class && node._class.split(/\s+/).indexOf(cls) !== -1;
  }
  if (last.indexOf('.') > 0) {
    const [tag, cls] = last.split('.');
    return node.tagName.toLowerCase() === tag.toLowerCase()
      && node._class && node._class.split(/\s+/).indexOf(cls) !== -1;
  }
  return node.tagName.toLowerCase() === last.toLowerCase();
}

function loadRecommender() {
  const src = fs.readFileSync(RECOMMENDER_JS, 'utf8');
  const fakeDoc = {
    readyState: 'complete',
    createElement: (tag) => makeElement(tag),
    createTextNode: (text) => ({ nodeValue: String(text) }),
    getElementById: () => null,
    addEventListener() {},
    body: makeElement('body'),
  };
  const fakeWindow = {
    localStorage: {
      getItem: () => null,
      setItem: () => {},
      removeItem: () => {},
    },
    location: { search: '', href: 'https://splunk.example/x' },
    history: { replaceState() {} },
  };
  const sandbox = {
    window: fakeWindow,
    document: fakeDoc,
    navigator: { clipboard: { writeText: async () => {} } },
    fetch: async () => { throw new Error('network disabled'); },
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
  return { helpers: sandbox.window.__uc_recommender__, document: fakeDoc };
}

test('STATUS_LABELS covers all five v9.0 enum values', () => {
  const { helpers } = loadRecommender();
  const expected = ['not_started', 'in_progress', 'implemented', 'needs_review', 'decommissioned'];
  expected.forEach((status) => {
    assert.ok(helpers.STATUS_LABELS[status],
      `STATUS_LABELS missing ${status}`);
    assert.ok(helpers.STATUS_LABELS[status].length >= 3,
      `${status} label too short: ${helpers.STATUS_LABELS[status]}`);
  });
});

test('DESTRUCTIVE_STATUSES contains only decommissioned', () => {
  const { helpers } = loadRecommender();
  assert.equal(helpers.DESTRUCTIVE_STATUSES.length, 1);
  assert.equal(helpers.DESTRUCTIVE_STATUSES[0], 'decommissioned');
});

test('REQUIRED_CAPABILITY is edit_uc_implementations', () => {
  const { helpers } = loadRecommender();
  assert.equal(helpers.REQUIRED_CAPABILITY, 'edit_uc_implementations');
});

test('safeSplunkbaseUrl accepts canonical Splunkbase URLs', () => {
  const { helpers } = loadRecommender();
  assert.equal(
    helpers.safeSplunkbaseUrl('https://splunkbase.splunk.com/app/1234/'),
    'https://splunkbase.splunk.com/app/1234/',
  );
  assert.equal(
    helpers.safeSplunkbaseUrl('https://splunkbase.splunk.com/app/9999'),
    'https://splunkbase.splunk.com/app/9999',
  );
});

test('safeSplunkbaseUrl rejects everything outside the allow-list', () => {
  const { helpers } = loadRecommender();
  assert.equal(helpers.safeSplunkbaseUrl('http://splunkbase.splunk.com/app/1234/'), null);
  assert.equal(helpers.safeSplunkbaseUrl('https://splunkbase.splunk.com/app/1234/details'), null);
  assert.equal(helpers.safeSplunkbaseUrl('https://splunkbase.evil.com/app/1234/'), null);
  assert.equal(helpers.safeSplunkbaseUrl('https://evil.com/splunkbase.splunk.com/app/1234/'), null);
  assert.equal(helpers.safeSplunkbaseUrl('javascript:alert(1)'), null);
  assert.equal(helpers.safeSplunkbaseUrl('data:text/html,<script>'), null);
  assert.equal(helpers.safeSplunkbaseUrl(undefined), null);
  assert.equal(helpers.safeSplunkbaseUrl(null), null);
  assert.equal(helpers.safeSplunkbaseUrl(42), null);
});

test('statusOf returns not_started when implementations is null', () => {
  const { helpers } = loadRecommender();
  helpers.state.implementations = null;
  assert.equal(helpers.statusOf('1.2.3'), 'not_started');
});

test('statusOf returns the stored status for a tracked UC', () => {
  const { helpers } = loadRecommender();
  helpers.state.implementations = {
    '1.2.3': { uc_id: '1.2.3', status: 'implemented' },
  };
  assert.equal(helpers.statusOf('1.2.3'), 'implemented');
  assert.equal(helpers.statusOf('9.9.9'), 'not_started');
});

test('statusOf falls back to not_started when status is unknown', () => {
  const { helpers } = loadRecommender();
  helpers.state.implementations = {
    '1.2.3': { uc_id: '1.2.3', status: 'bogus_value' },
  };
  // Defends against catalogue/JS drift — never trust upstream blindly.
  assert.equal(helpers.statusOf('1.2.3'), 'not_started');
});

test('renderStatusBadge always emits text content (a11y, never colour-only)', () => {
  const { helpers, document } = loadRecommender();
  helpers.state.implementations = {
    '1.2.3': { uc_id: '1.2.3', status: 'implemented' },
  };
  const parent = document.createElement('div');
  helpers.renderStatusBadge(parent, '1.2.3');
  const badge = parent.querySelector('.uc-status-badge');
  assert.ok(badge, 'badge was not rendered');
  // WCAG 2.1 AA: status must be conveyed by more than colour.
  assert.equal(badge.textContent.trim(), 'Live');
  assert.equal(badge.getAttribute('role'), 'status');
  assert.equal(badge.getAttribute('data-status'), 'implemented');
});

test('renderStatusBadge defaults unknown UCs to "Not Started"', () => {
  const { helpers, document } = loadRecommender();
  helpers.state.implementations = {};
  const parent = document.createElement('div');
  helpers.renderStatusBadge(parent, 'unknown-uc');
  const badge = parent.querySelector('.uc-status-badge');
  assert.equal(badge.textContent.trim(), 'Not Started');
  assert.equal(badge.getAttribute('data-status'), 'not_started');
});

test('renderRequiredSplunkbase produces a checklist when sb is non-empty', () => {
  const { helpers, document } = loadRecommender();
  helpers.state.splunkbaseIndex = {
    '1234': {
      displayName: 'Splunk Add-on for Acme',
      url: 'https://splunkbase.splunk.com/app/1234/',
      cloudVetted: true,
    },
  };
  const parent = document.createElement('div');
  helpers.renderRequiredSplunkbase(parent, [
    { id: '1234', name: 'Splunk Add-on for Acme', minVersion: '2.0', role: 'required' },
  ]);
  const items = parent.querySelectorAll('.uc-sb-item');
  assert.equal(items.length, 1);
  const link = items[0].querySelector('a');
  assert.ok(link, 'expected a link to the Splunkbase entry');
  assert.equal(link.getAttribute('target'), '_blank');
  assert.equal(link.getAttribute('rel'), 'noopener noreferrer');
  assert.equal(link.getAttribute('href'), 'https://splunkbase.splunk.com/app/1234/');
});

test('renderRequiredSplunkbase shows a graceful message for empty sb arrays', () => {
  const { helpers, document } = loadRecommender();
  helpers.state.splunkbaseIndex = { '1': { displayName: 'x' } };
  const parent = document.createElement('div');
  helpers.renderRequiredSplunkbase(parent, []);
  const empty = parent.querySelector('.uc-sb-none');
  assert.ok(empty, 'empty-state node missing');
  assert.equal(empty.textContent, 'No Splunkbase apps required.');
});

test('renderRequiredSplunkbase signals catalogue degradation when index is missing', () => {
  const { helpers, document } = loadRecommender();
  helpers.state.splunkbaseIndex = null;
  const parent = document.createElement('div');
  helpers.renderRequiredSplunkbase(parent, []);
  const empty = parent.querySelector('.uc-sb-none');
  assert.ok(empty);
  assert.match(empty.textContent, /metadata unavailable/);
});

test('renderRequiredSplunkbase rejects spoofed meta URLs and falls back to the canonical URL', () => {
  const { helpers, document } = loadRecommender();
  helpers.state.splunkbaseIndex = {
    '1234': {
      displayName: 'Pwned',
      // Spoofed meta URL — must be filtered by safeSplunkbaseUrl.
      url: 'javascript:alert(1)',
    },
  };
  const parent = document.createElement('div');
  helpers.renderRequiredSplunkbase(parent, [
    { id: '1234', name: 'Pwned', role: 'required' },
  ]);
  const item = parent.querySelector('.uc-sb-item');
  const link = item.querySelector('a');
  assert.ok(link, 'expected the canonical fallback link');
  assert.match(link.getAttribute('href'),
    /^https:\/\/splunkbase\.splunk\.com\/app\/1234\//,
    'href must be the canonical /app/<id>/ form, never the javascript: payload');
});
