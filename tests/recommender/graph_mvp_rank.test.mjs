// Behavioural tests for graph-recommend.js — the ranking engine shared by
// graph-mvp.html and (eventually) VISTA. These run against the REAL built
// catalogue so the assertions describe what a user actually sees, not what a
// fixture pretends they see.
//
// The three defects these tests pin down, all observed in the first MVP:
//   1. Score ties collapsed the ranking. A stack of cisco_ise + linux + vmware
//      produced eight results all scoring exactly 99, so the tiebreak (UC id)
//      sorted by category number and category 19 took 7 of 8 slots.
//   2. A selected product could be entirely absent from the results.
//   3. Catch-all slugs (security_essentials tags 2142 UCs) ranked equally with
//      product-specific ones.

import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..', '..');
const ENGINE = path.join(ROOT, 'graph-recommend.js');
const CATALOG = path.join(ROOT, 'dist', 'catalog.json');

const { default: engine } = await import(`file://${ENGINE}`);
const catalog = JSON.parse(fs.readFileSync(CATALOG, 'utf8'));
const index = engine.buildIndex(catalog);
const PROFILES = path.join(ROOT, 'graph-recommend.json');
if (fs.existsSync(PROFILES)) {
  engine.attachProfiles(JSON.parse(fs.readFileSync(PROFILES, 'utf8')));
  engine.bindProfiles(index);
}

const STACK = ['cisco_ise', 'linux', 'vmware'];

test('buildIndex reaches products that are missing from the EQUIPMENT registry', () => {
  const registry = new Set((catalog.EQUIPMENT || []).map((e) => e.id));
  // Juniper, Arista and Splunk ES are referenced by hundreds of use cases but
  // absent from the curated registry the first MVP searched against.
  for (const slug of ['juniper', 'arista', 'splunk-es']) {
    assert.ok(!registry.has(slug), `${slug} should be absent from the registry`);
    assert.ok(index.products[slug], `${slug} must still be selectable`);
    assert.ok(index.products[slug].count > 0);
  }
  assert.ok(
    index.productList.length > registry.size,
    'index must expose more products than the registry alone',
  );
});

test('every product with matches is represented in Start here', () => {
  const picks = engine.startHere(index, STACK, 9);
  const represented = new Set(picks.map((p) => p.slug));
  for (const slug of STACK) {
    assert.ok(
      represented.has(slug),
      `${slug} was selected but never appears in the results`,
    );
  }
});

test('no single product monopolises Start here', () => {
  const picks = engine.startHere(index, STACK, 9);
  const perProduct = new Map();
  for (const p of picks) perProduct.set(p.slug, (perProduct.get(p.slug) || 0) + 1);
  const cap = Math.ceil(picks.length / STACK.length) + 1;
  for (const [slug, n] of perProduct) {
    assert.ok(n <= cap, `${slug} took ${n} of ${picks.length} slots (cap ${cap})`);
  }
});

test('Start here is diversified across categories', () => {
  const picks = engine.startHere(index, STACK, 12);
  const cats = new Set(picks.map((p) => String(p.uc.i).split('.')[0]));
  assert.ok(
    cats.size >= 3,
    `expected >=3 categories in 12 results, got ${cats.size}: ${[...cats]}`,
  );
});

test('scores no longer collapse into ties', () => {
  const ranked = engine.rankForProduct(index, 'linux', 20);
  const distinct = new Set(ranked.map((r) => r.score.toFixed(3)));
  assert.ok(
    distinct.size >= 15,
    `expected >=15 distinct scores in top 20, got ${distinct.size}`,
  );
});

test('a product-specific use case outranks an equally-rated generic one', () => {
  // Same tier, wave, criticality, difficulty and quality score. The only
  // difference is how specifically each one targets the product.
  const shared = { _qt: 'gold', wv: 'crawl', c: 'critical', f: 'beginner', _qs: 90 };
  const specific = { ...shared, i: '1.1.1', n: 'Specific', e: ['acme_widget'] };
  const generic = {
    ...shared,
    i: '1.1.2',
    n: 'Generic',
    e: ['acme_widget', ...Array.from({ length: 16 }, (_, k) => `other_${k}`)],
  };
  const synthetic = engine.buildIndex({
    EQUIPMENT: [],
    DATA: [{ n: 'Cat', s: [{ n: 'Sub', u: [specific, generic] }] }],
  });
  const ranked = engine.rankForProduct(synthetic, 'acme_widget', 2);
  assert.equal(ranked[0].uc.n, 'Specific');
  assert.ok(ranked[0].score > ranked[1].score);
});

test('a catch-all slug is discounted against a focused slug', () => {
  // security_essentials tags 2142 UCs; it is a bucket, not a product.
  const broad = index.products['security_essentials'];
  const focused = index.products['cisco_ise'];
  assert.ok(broad && focused);
  assert.ok(
    broad.specificity < focused.specificity,
    'catch-all slug must carry lower specificity than a focused product slug',
  );
});

test('rankForProduct always returns the best available even with no crawl content', () => {
  // windows has 230 UCs but zero in the crawl wave. It must still produce a
  // populated, ordered shortlist rather than an empty one.
  const ranked = engine.rankForProduct(index, 'windows', 5);
  assert.equal(ranked.length, 5);
  for (let i = 1; i < ranked.length; i += 1) {
    assert.ok(ranked[i - 1].score >= ranked[i].score, 'results must be ordered');
  }
});

test('single-product Guided keeps cited cores instead of category-capping them out', () => {
  const picks = engine.startHere(index, ['cisco_ise'], 8);
  const ids = picks.map((p) => String(p.uc.i));
  for (const id of ['17.1.13', '17.1.77', '17.1.28', '17.1.31', '17.1.29']) {
    assert.ok(ids.includes(id), `expected core ${id} in single-product Guided, got ${ids}`);
  }
});

test('every ranked result carries a human-readable reason', () => {
  for (const pick of engine.startHere(index, STACK, 9)) {
    assert.equal(typeof pick.reason, 'string');
    assert.ok(pick.reason.length > 0, `UC-${pick.uc.i} has no reason`);
  }
});

test('ranking is deterministic', () => {
  const a = engine.startHere(index, STACK, 12).map((p) => p.uc.i);
  const b = engine.startHere(index, STACK, 12).map((p) => p.uc.i);
  assert.deepEqual(a, b);
});

test('perProduct returns a shortlist for each selected product', () => {
  const groups = engine.perProduct(index, STACK, 5);
  assert.equal(groups.length, STACK.length);
  for (const group of groups) {
    assert.ok(STACK.includes(group.slug));
    assert.ok(group.items.length > 0, `${group.slug} produced an empty shortlist`);
    assert.ok(group.total >= group.items.length);
    assert.ok(typeof group.label === 'string' && group.label.length > 0);
  }
});
