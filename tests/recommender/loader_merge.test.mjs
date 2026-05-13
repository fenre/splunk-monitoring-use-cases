// Tests for src/scripts/00-loader.js — specifically the lazy-bootstrap
// pipeline (catalog-index → __ensureFullCategory → _mergeCategoryFull).
//
// This was added when an end-to-end probe revealed that clicking a UC
// link from compliance-story.html landed on the detail panel with the
// SPL / implementation / markdown / references / visualization
// sections missing. Root cause: cat-22.json intentionally emits
// duplicate sub entries for tier-1 regulations (DORA + DORA-extended,
// SOC 2 + SOC 2-extended, etc.) and the merge crashed on the second
// occurrence because it had already deleted its scratch _ucMap. The
// crash rejected the lazy-load promise, which prevented the detail
// pane from re-rendering with the (already-merged) heavy fields.
//
// The fix moves the _ucMap cleanup to a single end-of-function pass
// and the lazy-load callback now uses .then(cb, cb) so the panel still
// re-renders even if the merge surfaces a partial failure. These
// tests pin both invariants.

import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const LOADER_JS = path.resolve(
  __dirname,
  '..',
  '..',
  'src',
  'scripts',
  '00-loader.js',
);

function loadLoader({ catalogIndex, catFulls = {} } = {}) {
  const events = [];
  const handlers = {};

  const fakeWindow = {
    addEventListener(name, fn) { handlers[name] = fn; },
    dispatchEvent(ev) { events.push(ev && ev.type); },
    Set,
  };
  const fetched = [];
  const fetchImpl = async (url) => {
    fetched.push(url);
    if (url.endsWith('/catalog-index.json')) {
      if (!catalogIndex) {
        return { ok: false, status: 404, json: async () => ({}) };
      }
      return { ok: true, status: 200, json: async () => catalogIndex };
    }
    const m = url.match(/\/cat-(\d+)\.json$/);
    if (m) {
      const cid = parseInt(m[1], 10);
      const payload = catFulls[cid];
      if (!payload) {
        return { ok: false, status: 404, json: async () => ({}) };
      }
      return { ok: true, status: 200, json: async () => payload };
    }
    throw new Error('unexpected fetch ' + url);
  };

  const sandbox = {
    window: fakeWindow,
    fetch: fetchImpl,
    Event: function (type) { this.type = type; },
    document: {
      createEvent() { return { initEvent(t) { this.type = t; } }; },
    },
    console: { error: () => {} },
    Promise,
    Set,
  };
  sandbox.globalThis = sandbox;
  sandbox.self = sandbox;
  vm.createContext(sandbox);

  const src = fs.readFileSync(LOADER_JS, 'utf8');
  vm.runInContext(src, sandbox, { filename: '00-loader.js' });
  return { sandbox, fetched, events, handlers };
}

test('catalog-index bootstrap groups all UCs into the canonical sub bucket', async () => {
  // Two stub subs share id "22.3" — _populateGlobalsFromIndex should
  // mirror the production behaviour: the LAST occurrence wins as the
  // bucket for every UC stub on that id, and the first occurrence
  // becomes a ghost (zero UCs). This matches what the live loader
  // already does and is the contract _mergeCategoryFull relies on.
  const idx = {
    categories: [
      {
        i: 22,
        n: 'Regulatory compliance',
        subs: [
          { i: '22.3', n: 'DORA' },
          { i: '22.3', n: '— DORA (extended clauses)' },
        ],
      },
    ],
    ucs: [
      { i: '22.3.1', n: 'A', cat: 22, sub: '22.3' },
      { i: '22.3.41', n: 'B', cat: 22, sub: '22.3' },
    ],
  };
  const { sandbox } = loadLoader({ catalogIndex: idx });
  await sandbox.window.__catalogReady;

  const data = sandbox.window.DATA;
  assert.equal(data.length, 1);
  const cat = data[0];
  assert.equal(cat.s.length, 2, 'both duplicate sub entries are preserved in DATA');
  // Compare via JSON because the arrays come from the VM sandbox and
  // have a different Array prototype than the host realm.
  const ucBuckets = cat.s.map((s) => s.u.map((u) => u.i));
  assert.equal(JSON.stringify(ucBuckets[0]), '[]');
  assert.equal(
    JSON.stringify(ucBuckets[1].slice().sort()),
    JSON.stringify(['22.3.1', '22.3.41']),
  );
});

test('_mergeCategoryFull handles duplicate sub-id entries in catFull.s', async () => {
  // Reproduces the cat-22 shape: catalog-index has two "22.3" subs and
  // cat-22.json also has two "22.3" subs (one with the original UCs,
  // one with the extended-clauses UCs). Pre-fix, the merge crashed on
  // the second occurrence because _ucMap had been deleted at the end
  // of the first iteration — leaving extended-clause UCs un-merged.
  const idx = {
    categories: [
      {
        i: 22,
        n: 'Regulatory compliance',
        subs: [
          { i: '22.3', n: 'DORA' },
          { i: '22.3', n: '— DORA (extended clauses)' },
        ],
      },
    ],
    ucs: [
      { i: '22.3.1', n: 'A', cat: 22, sub: '22.3' },
      { i: '22.3.12', n: 'B', cat: 22, sub: '22.3' },
      { i: '22.3.41', n: 'C', cat: 22, sub: '22.3' },
      { i: '22.3.42', n: 'D', cat: 22, sub: '22.3' },
    ],
  };
  const cat22Full = {
    i: 22,
    n: 'Regulatory compliance',
    s: [
      {
        i: '22.3',
        n: 'DORA',
        u: [
          { i: '22.3.1', n: 'A', q: 'index=risk earliest=-30d', m: 'impl-A' },
          { i: '22.3.12', n: 'B', q: 'index=audit', m: 'impl-B' },
        ],
      },
      {
        i: '22.3',
        n: '— DORA (extended clauses)',
        u: [
          { i: '22.3.41', n: 'C', q: 'index=cloud', m: 'impl-C' },
          { i: '22.3.42', n: 'D', q: 'index=ldap', m: 'impl-D' },
        ],
      },
    ],
  };
  const { sandbox } = loadLoader({
    catalogIndex: idx,
    catFulls: { 22: cat22Full },
  });
  await sandbox.window.__catalogReady;

  // Force the lazy-load merge for any UC in cat-22 — __ensureFullUC
  // resolves once cat-22.json has been merged into DATA.
  await sandbox.window.__ensureFullUC('22.3.41');

  // Every stub UC must now carry its heavy fields (q, m). Pre-fix the
  // second-occurrence iteration crashed before it could merge UCs C/D,
  // and the rejection prevented the panel from re-rendering with the
  // partial result that A/B did get.
  const allUcs = sandbox.window.DATA[0].s
    .reduce((acc, sub) => acc.concat(sub.u), [])
    .sort((a, b) => a.i.localeCompare(b.i, undefined, { numeric: true }));
  assert.equal(allUcs.length, 4, 'every stub is preserved');
  for (const uc of allUcs) {
    assert.ok(uc.q, `UC ${uc.i} should have full SPL after merge`);
    assert.ok(uc.m, `UC ${uc.i} should have full implementation after merge`);
  }

  // The _ucMap scratch field must be removed from EVERY sub (including
  // the shadowed first occurrence) so subsequent merge passes — and
  // anything iterating cat.s — see a clean shape.
  for (const sub of sandbox.window.DATA[0].s) {
    assert.ok(!('_ucMap' in sub), `sub ${sub.i} must not retain _ucMap after merge`);
  }
});

test('_mergeCategoryFull is idempotent for repeated calls', async () => {
  const idx = {
    categories: [{
      i: 7,
      n: 'Cat',
      subs: [{ i: '7.1', n: 'Sub' }],
    }],
    ucs: [{ i: '7.1.1', n: 'X', cat: 7, sub: '7.1' }],
  };
  const cat7Full = {
    i: 7,
    n: 'Cat',
    s: [{ i: '7.1', n: 'Sub', u: [{ i: '7.1.1', n: 'X', q: 'index=foo' }] }],
  };
  const { sandbox } = loadLoader({
    catalogIndex: idx,
    catFulls: { 7: cat7Full },
  });
  await sandbox.window.__catalogReady;
  await sandbox.window.__ensureFullUC('7.1.1');
  await sandbox.window.__ensureFullUC('7.1.1'); // second call is a cached no-op
  const uc = sandbox.window.DATA[0].s[0].u[0];
  assert.equal(uc.q, 'index=foo');
  assert.equal(uc.i, '7.1.1');
});
