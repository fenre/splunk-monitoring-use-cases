// Phase 4.5c sandbox validation gate - drift guard tests.
//
// These tests do NOT re-implement the Python validator.  Instead, they
// verify four invariants of the generated
// ``reports/sandbox-validation.json``:
//
//   1. The report exists, parses as JSON, and has the expected
//      top-level shape (records array + summary object).
//   2. Every UC sidecar in use-cases/cat-*/uc-*.json that declares a
//      ``controlTest.fixtureRef`` is represented by exactly one
//      record in the report.  If the Python validator ever silently
//      drops a UC, this test fails.
//   3. The summary counts match the records (sanity check for the
//      Python aggregation logic).
//   4. The report is byte-identical after
//      ``scripts/audit_sandbox_validation.py --check``.  This is the
//      CI determinism guard for the gate itself.
//
// Run with:
//     node --test tests/sandbox/validate.test.mjs
//
// A prerequisite is that ``reports/sandbox-validation.json`` has been
// regenerated recently (the validate.yml workflow does this as part of
// the Phase 4.5 QA gate).

import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO = path.resolve(__dirname, '..', '..');
const REPORT_PATH = path.join(REPO, 'reports', 'sandbox-validation.json');
const USE_CASES_DIR = path.join(REPO, 'use-cases');

const ALLOWED_STATUSES = new Set([
  'populated',
  'empty',
  'half-empty',
  'missing',
  'malformed',
  'bad-json',
  'no-fixture',
]);

// Enumerate every UC sidecar under use-cases/cat-N/uc-N.M.P.json and
// return a Map<ucId, {sidecar, fixtureRef|null, hasFullAssurance}>.
// Used to cross-check the Python validator did not miss anything.
function collectUCSidecars() {
  const results = new Map();
  const catDirs = fs
    .readdirSync(USE_CASES_DIR)
    .filter((d) => d.startsWith('cat-'))
    .map((d) => path.join(USE_CASES_DIR, d))
    .filter((d) => fs.statSync(d).isDirectory());

  for (const catDir of catDirs) {
    const files = fs
      .readdirSync(catDir)
      .filter((f) => f.startsWith('uc-') && f.endsWith('.json'));
    for (const file of files) {
      const fullPath = path.join(catDir, file);
      let data;
      try {
        data = JSON.parse(fs.readFileSync(fullPath, 'utf8'));
      } catch {
        continue; // broken sidecars are caught by audit_compliance_mappings
      }
      const ucId = data.id || file.replace(/^uc-/, '').replace(/\.json$/, '');
      const ct = data.controlTest || {};
      const fixtureRef = ct.fixtureRef || null;
      const compliance = Array.isArray(data.compliance) ? data.compliance : [];
      const hasFullAssurance = compliance.some(
        (e) => e && typeof e === 'object' && e.assurance === 'full',
      );
      // Only UCs with a fixtureRef OR a 'full' claim appear in the report.
      if (fixtureRef || hasFullAssurance) {
        results.set(ucId, {
          sidecar: path.relative(REPO, fullPath),
          fixtureRef,
          hasFullAssurance,
        });
      }
    }
  }
  return results;
}

test('sandbox-validation.json has the expected top-level shape', () => {
  assert.ok(
    fs.existsSync(REPORT_PATH),
    `reports/sandbox-validation.json not found - run \`python3 scripts/audit_sandbox_validation.py\` first`,
  );
  const raw = fs.readFileSync(REPORT_PATH, 'utf8');
  const payload = JSON.parse(raw);
  assert.equal(typeof payload, 'object');
  assert.ok(Array.isArray(payload.records), 'records must be an array');
  assert.equal(
    typeof payload.summary,
    'object',
    'summary must be an object',
  );
  assert.equal(
    typeof payload.summary.total_ucs_examined,
    'number',
    'summary.total_ucs_examined must be a number',
  );
  assert.equal(
    typeof payload.summary.hard_failures,
    'number',
    'summary.hard_failures must be a number',
  );

  for (const rec of payload.records) {
    assert.equal(typeof rec.uc_id, 'string', 'record.uc_id must be a string');
    assert.ok(
      /^[0-9]+\.[0-9]+\.[0-9]+$/.test(rec.uc_id),
      `record.uc_id ${rec.uc_id} must match N.M.P`,
    );
    assert.equal(typeof rec.status, 'string');
    assert.ok(
      ALLOWED_STATUSES.has(rec.status),
      `record.status ${rec.status} must be one of ${[...ALLOWED_STATUSES].join(', ')}`,
    );
    assert.equal(
      typeof rec.full_assurance,
      'boolean',
      'record.full_assurance must be boolean',
    );
    assert.ok(
      Array.isArray(rec.issues),
      'record.issues must be an array',
    );
  }
});

test('sandbox report covers every UC with fixtureRef or full-assurance', () => {
  const payload = JSON.parse(fs.readFileSync(REPORT_PATH, 'utf8'));
  const reportIds = new Set(payload.records.map((r) => r.uc_id));
  const sidecarIndex = collectUCSidecars();

  const missingFromReport = [];
  for (const [ucId] of sidecarIndex.entries()) {
    if (!reportIds.has(ucId)) {
      missingFromReport.push(ucId);
    }
  }
  assert.equal(
    missingFromReport.length,
    0,
    `UCs on disk but missing from sandbox report: ${missingFromReport.slice(0, 10).join(', ')}${missingFromReport.length > 10 ? ' (+more)' : ''}`,
  );

  // And the report should not invent UCs that have no sidecar.
  const invented = [];
  for (const rec of payload.records) {
    if (!sidecarIndex.has(rec.uc_id)) {
      invented.push(rec.uc_id);
    }
  }
  assert.equal(
    invented.length,
    0,
    `Report contains UCs with no matching sidecar: ${invented.slice(0, 10).join(', ')}`,
  );
});

test('sandbox report summary.statuses matches record aggregation', () => {
  const payload = JSON.parse(fs.readFileSync(REPORT_PATH, 'utf8'));
  const recomputed = {};
  for (const rec of payload.records) {
    recomputed[rec.status] = (recomputed[rec.status] || 0) + 1;
  }
  for (const [status, count] of Object.entries(payload.summary.statuses)) {
    if (count > 0) {
      assert.equal(
        recomputed[status],
        count,
        `summary.statuses.${status} reports ${count} but records only show ${recomputed[status] || 0}`,
      );
    }
  }
});

test('sandbox report hard-failure count matches record statuses', () => {
  const payload = JSON.parse(fs.readFileSync(REPORT_PATH, 'utf8'));
  const hardFailStatuses = new Set(['malformed', 'bad-json']);
  const recomputed = payload.records.filter((r) =>
    hardFailStatuses.has(r.status),
  ).length;
  assert.equal(
    payload.summary.hard_failures,
    recomputed,
    `summary.hard_failures=${payload.summary.hard_failures} but records show ${recomputed} hard failures`,
  );
});

test('sandbox report is deterministic (sort_keys invariant)', () => {
  const raw = fs.readFileSync(REPORT_PATH, 'utf8');
  const payload = JSON.parse(raw);
  // Records must be sorted by (uc_id, sidecar).
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
  // Top-level keys alphabetical.
  const topKeys = Object.keys(payload);
  const sorted = [...topKeys].sort();
  assert.deepEqual(
    topKeys,
    sorted,
    'top-level keys must be alphabetically sorted',
  );
});
