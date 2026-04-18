// Phase 4.5d ATT&CK simulation gate - drift guard tests.
//
// These tests do NOT re-run the Python simulator.  They verify that
// the committed ``reports/attack-simulation.json`` is structurally
// consistent with the UC sidecars and MITRE crosswalks on disk:
//
//   1. The report exists, parses as JSON, and has the expected
//      top-level shape (records array + summary object).
//   2. Every UC sidecar carrying a ``controlTest`` block is
//      represented by exactly one record in the report.
//   3. Every ATT&CK technique ID in the report parses against the
//      canonical ``T####`` / ``T####.###`` grammar, matching the
//      Python regex.
//   4. The summary counts reconcile with the records (sanity check).
//   5. Records are sorted by ``(uc_id, sidecar)`` and top-level keys
//      are alphabetised — the determinism invariants the Python
//      generator commits to.
//
// Run with:
//     node --test tests/attack/simulate.test.mjs

import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO = path.resolve(__dirname, '..', '..');
const REPORT_PATH = path.join(REPO, 'reports', 'attack-simulation.json');
const USE_CASES_DIR = path.join(REPO, 'use-cases');

const ALLOWED_STATUSES = new Set([
  'simulated',
  'pending_fixture',
  'no_fixture_declared',
  'polarity_mismatch',
  'spl_fixture_mismatch',
]);

const ATTACK_ID_RE = /^T\d{4}(?:\.\d{3})?$/;

function collectUCsWithControlTest() {
  const results = new Map();
  const catDirs = fs
    .readdirSync(USE_CASES_DIR)
    .filter((d) => d.startsWith('cat-'))
    .map((d) => path.join(USE_CASES_DIR, d))
    .filter((d) => fs.statSync(d).isDirectory());
  for (const dir of catDirs) {
    const files = fs
      .readdirSync(dir)
      .filter((f) => f.startsWith('uc-') && f.endsWith('.json'));
    for (const file of files) {
      const full = path.join(dir, file);
      let data;
      try {
        data = JSON.parse(fs.readFileSync(full, 'utf8'));
      } catch {
        continue;
      }
      const ct = data.controlTest;
      if (ct && typeof ct === 'object') {
        const ucId = data.id || file.replace(/^uc-/, '').replace(/\.json$/, '');
        results.set(ucId, {
          sidecar: path.relative(REPO, full),
          hasAttack:
            (typeof ct.attackTechnique === 'string' && ct.attackTechnique) ||
            (Array.isArray(ct.attackTechnique) && ct.attackTechnique.length > 0) ||
            (Array.isArray(data.mitreAttack) && data.mitreAttack.length > 0),
        });
      }
    }
  }
  return results;
}

test('attack-simulation.json has the expected top-level shape', () => {
  assert.ok(
    fs.existsSync(REPORT_PATH),
    `reports/attack-simulation.json not found - run \`python3 scripts/simulate_controltest.py\` first`,
  );
  const raw = fs.readFileSync(REPORT_PATH, 'utf8');
  const payload = JSON.parse(raw);
  assert.ok(Array.isArray(payload.records), 'records must be an array');
  assert.equal(typeof payload.summary, 'object');
  for (const rec of payload.records) {
    assert.equal(typeof rec.uc_id, 'string');
    assert.ok(
      /^[0-9]+\.[0-9]+\.[0-9]+$/.test(rec.uc_id),
      `uc_id ${rec.uc_id} must match N.M.P`,
    );
    assert.equal(typeof rec.status, 'string');
    assert.ok(
      ALLOWED_STATUSES.has(rec.status),
      `status ${rec.status} must be one of ${[...ALLOWED_STATUSES].join(', ')}`,
    );
    assert.ok(Array.isArray(rec.attack_techniques));
    assert.ok(Array.isArray(rec.bad_technique_format));
    assert.ok(Array.isArray(rec.unknown_techniques));
    assert.ok(Array.isArray(rec.polarity_issues));
    assert.ok(Array.isArray(rec.coherence_warnings));
    assert.equal(typeof rec.pos_events, 'number');
    assert.equal(typeof rec.neg_events, 'number');
  }
});

test('attack-simulation report covers every UC with a controlTest', () => {
  const payload = JSON.parse(fs.readFileSync(REPORT_PATH, 'utf8'));
  const reportIds = new Set(payload.records.map((r) => r.uc_id));
  const sidecarIndex = collectUCsWithControlTest();
  const missing = [];
  for (const [ucId] of sidecarIndex.entries()) {
    if (!reportIds.has(ucId)) {
      missing.push(ucId);
    }
  }
  assert.equal(
    missing.length,
    0,
    `UCs with controlTest but no record in the simulation report: ${missing.slice(0, 10).join(', ')}${missing.length > 10 ? ' (+more)' : ''}`,
  );
  const invented = payload.records
    .map((r) => r.uc_id)
    .filter((id) => !sidecarIndex.has(id));
  assert.equal(
    invented.length,
    0,
    `Report contains UCs with no matching controlTest: ${invented.slice(0, 10).join(', ')}`,
  );
});

test('every ATT&CK technique ID in the report matches the canonical grammar', () => {
  const payload = JSON.parse(fs.readFileSync(REPORT_PATH, 'utf8'));
  const malformed = [];
  for (const rec of payload.records) {
    for (const id of rec.attack_techniques) {
      if (!ATTACK_ID_RE.test(id)) {
        malformed.push({ uc: rec.uc_id, id });
      }
    }
  }
  assert.equal(
    malformed.length,
    0,
    `Non-canonical ATT&CK IDs leaked through the Python validator: ${JSON.stringify(malformed)}`,
  );
});

test('attack-simulation summary reconciles with record aggregates', () => {
  const payload = JSON.parse(fs.readFileSync(REPORT_PATH, 'utf8'));
  const recomputedStatuses = {};
  let badFormatTotal = 0;
  let unknownTotal = 0;
  let ucsWithAttack = 0;
  let attackRefsTotal = 0;
  const distinctTechs = new Set();
  for (const rec of payload.records) {
    recomputedStatuses[rec.status] =
      (recomputedStatuses[rec.status] || 0) + 1;
    badFormatTotal += rec.bad_technique_format.length;
    unknownTotal += rec.unknown_techniques.length;
    if (rec.has_attack_ref) ucsWithAttack += 1;
    attackRefsTotal += rec.attack_techniques.length;
    for (const t of rec.attack_techniques) {
      if (ATTACK_ID_RE.test(t)) distinctTechs.add(t);
    }
  }
  for (const [status, count] of Object.entries(payload.summary.statuses)) {
    if (count > 0) {
      assert.equal(
        recomputedStatuses[status],
        count,
        `summary.statuses.${status}=${count} but records show ${recomputedStatuses[status] || 0}`,
      );
    }
  }
  assert.equal(
    payload.summary.bad_technique_format_total,
    badFormatTotal,
    'bad_technique_format_total drift',
  );
  assert.equal(
    payload.summary.unknown_technique_total,
    unknownTotal,
    'unknown_technique_total drift',
  );
  assert.equal(
    payload.summary.total_ucs_with_attack_ref,
    ucsWithAttack,
    'total_ucs_with_attack_ref drift',
  );
  assert.equal(
    payload.summary.total_attack_refs,
    attackRefsTotal,
    'total_attack_refs drift',
  );
  assert.deepEqual(
    payload.summary.distinct_attack_techniques,
    [...distinctTechs].sort(),
    'distinct_attack_techniques drift',
  );
});

test('attack-simulation report is deterministic (sort invariants)', () => {
  const raw = fs.readFileSync(REPORT_PATH, 'utf8');
  const payload = JSON.parse(raw);
  for (let i = 1; i < payload.records.length; i++) {
    const prev = payload.records[i - 1];
    const curr = payload.records[i];
    const prevKey = `${prev.uc_id}\u0000${prev.sidecar}`;
    const currKey = `${curr.uc_id}\u0000${curr.sidecar}`;
    assert.ok(
      prevKey <= currKey,
      `records not sorted at index ${i}: ${prevKey} > ${currKey}`,
    );
  }
  const topKeys = Object.keys(payload);
  assert.deepEqual(
    topKeys,
    [...topKeys].sort(),
    'top-level keys must be alphabetically sorted',
  );
});
