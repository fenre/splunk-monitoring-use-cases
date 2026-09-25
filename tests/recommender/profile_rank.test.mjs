// Profile-backed ranking: cited core packs must surface in the top of
// each pilot product's shortlist. Falls back to catalog-only ranking
// when graph-recommend.json is missing (generator not yet run).

import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..', '..');
const ENGINE = path.join(ROOT, 'graph-recommend.js');
const CATALOG = path.join(ROOT, 'dist', 'catalog.json');
const PROFILES = path.join(ROOT, 'graph-recommend.json');

const { default: engine } = await import(`file://${ENGINE}`);

const ANCHORS = {
  cisco_ise: ['17.1.13', '17.1.77', '17.1.28', '17.1.31', '17.1.29'],
  vmware: ['2.1.3', '2.1.42', '2.1.5', '2.1.22', '2.1.7'],
  paloalto: ['10.11.19', '10.11.131', '10.11.94', '10.11.93', '10.11.28'],
  aws: ['4.1.30', '10.7.104', '4.1.8', '4.1.66', '4.1.2'],
  kubernetes: ['3.2.10', '3.2.19', '3.2.3', '3.2.47', '13.7.1'],
  linux: ['1.1.1', '1.1.2', '1.1.3', '1.1.8', '1.1.80'],
};

if (!fs.existsSync(CATALOG) || !fs.existsSync(PROFILES)) {
  test('profile ranking skipped until catalog and graph-recommend.json exist', () => {
    assert.ok(true);
  });
} else {
  const catalog = JSON.parse(fs.readFileSync(CATALOG, 'utf8'));
  const profiles = JSON.parse(fs.readFileSync(PROFILES, 'utf8'));
  const index = engine.buildIndex(catalog);
  engine.attachProfiles(profiles);
  engine.bindProfiles(index);

  test('every profile ucId resolves in the catalogue index', () => {
    for (const [slug, profile] of Object.entries(profiles.profiles || {})) {
      for (const core of profile.core) {
        assert.ok(index.byId[core.i], `${slug} core ${core.i} missing from catalogue`);
      }
    }
  });

  for (const [slug, ids] of Object.entries(ANCHORS)) {
    test(`zero-context ${slug} top 5 contains cited anchors`, () => {
      const ranked = engine.rankForProduct(index, slug, 5, {});
      const got = ranked.map((r) => String(r.uc.i));
      for (const id of ids.slice(0, 5)) {
        assert.ok(got.includes(id), `${slug}: expected ${id} in top 5, got ${got}`);
      }
    });

    test(`${slug} top 10 keeps anchors under guided context`, () => {
      const ranked = engine.rankForProduct(index, slug, 10, {
        roles: ['platform'],
        outcomes: ['availability'],
      });
      const got = ranked.map((r) => String(r.uc.i));
      for (const id of ids) {
        assert.ok(got.includes(id), `${slug}: expected ${id} in top 10, got ${got}`);
      }
    });

    test(`${slug} blocked inventory classifies high-value as unblock-first`, () => {
      const blocked = Object.fromEntries(ids.map((id) => [id, false]));
      const ranked = engine.rankForProduct(index, slug, 5, { inventoryReady: blocked });
      assert.ok(
        ranked.some((r) => r.presentationClass === 'high_value_blocked'),
        `${slug} should surface blocked high-value UCs`,
      );
    });
  }

  test('zero-context copy is a best-practice starting point', () => {
    const ranked = engine.rankForProduct(index, 'cisco_ise', 1, {});
    assert.match(ranked[0].reason, /Best-practice starting point/);
  });

  test('ranking remains deterministic with profiles', () => {
    const a = engine.startHere(index, ['cisco_ise', 'paloalto'], 8).map((p) => p.uc.i);
    const b = engine.startHere(index, ['cisco_ise', 'paloalto'], 8).map((p) => p.uc.i);
    assert.deepEqual(a, b);
  });

  test('contextFromWizard maps suites and outcomes', () => {
    const ctx = engine.contextFromWizard({
      desiredOutcomes: ['availability'],
      premiumSuites: ['itsi', 'enterprise_security'],
      implementationWave: 'crawl',
    });
    assert.deepEqual(ctx.outcomes, ['availability']);
    assert.ok(ctx.suites.includes('itsi'));
    assert.ok(ctx.suites.includes('es'));
    assert.equal(ctx.maturity, 'crawl');
  });
}
