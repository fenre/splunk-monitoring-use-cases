// Phase 4.5e OSCAL round-trip gate - drift guard tests.
//
// These tests do NOT re-implement the Python validator.  Instead, they
// verify four invariants of the generated
// ``reports/oscal-roundtrip.json``:
//
//   1. The report exists, parses as JSON, and has the expected
//      top-level shape (records array + summary object + schema block).
//   2. Every component-definition file under
//      ``api/v1/oscal/component-definitions/*.json`` (except
//      ``index.json``) is represented by exactly one record in the
//      report.  If the Python validator ever silently drops a file,
//      this test fails.
//   3. The summary counts reconcile with the records (statuses bucket
//      aggregation, roundtrip-drift count, schema-violation count,
//      hard-failure count).  This catches aggregation bugs in the
//      Python side without re-running validation here.
//   4. The report is deterministically sorted (records by uc_id, and
//      top-level keys alphabetical under sort_keys=True).  This is the
//      CI determinism contract for the gate.
//
// The test also performs a cheap, language-agnostic byte-equality
// canonicalisation check on every component-definition file: we parse
// the file as JSON and re-serialise it with JSON.stringify(value, null, 2)
// plus a trailing newline.  If that output diverges from what's on
// disk, either the file drifted or the Python canonical serialiser
// does not match the JSON spec (a regression we want to catch early).
// Because JSON.stringify on V8 preserves insertion order, we compare
// using the same sort-then-emit strategy as Python's sort_keys=True.
//
// Run with:
//     node --test tests/oscal/roundtrip.test.mjs
//
// A prerequisite is that ``reports/oscal-roundtrip.json`` has been
// regenerated recently (the validate.yml workflow does this as part
// of the Phase 4.5 QA gate).

import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO = path.resolve(__dirname, '..', '..');
const REPORT_PATH = path.join(REPO, 'reports', 'oscal-roundtrip.json');
const CDEF_DIR = path.join(
  REPO,
  'api',
  'v1',
  'oscal',
  'component-definitions',
);

const ALLOWED_STATUSES = new Set([
  'ok',
  'bad-filename',
  'bad-json',
  'schema-violation',
  'roundtrip-drift',
  'wrong-oscal-version',
  'missing-source',
]);

const HARD_FAIL_STATUSES = new Set([
  'bad-filename',
  'bad-json',
  'schema-violation',
  'roundtrip-drift',
  'wrong-oscal-version',
  'missing-source',
]);

// Recursively rewrite an object's keys in lexical order so that
// JSON.stringify(value, null, 2) emits the same byte sequence as
// Python's json.dumps(value, indent=2, sort_keys=True).  Arrays are
// preserved in their existing order (matching Python behaviour; arrays
// are not sorted under sort_keys=True).
function canonicalOrder(value) {
  if (Array.isArray(value)) {
    return value.map(canonicalOrder);
  }
  if (value && typeof value === 'object') {
    const out = {};
    for (const key of Object.keys(value).sort()) {
      out[key] = canonicalOrder(value[key]);
    }
    return out;
  }
  return value;
}

function listComponentDefinitionFiles() {
  if (!fs.existsSync(CDEF_DIR)) {
    return [];
  }
  return fs
    .readdirSync(CDEF_DIR)
    .filter((name) => name.endsWith('.json') && name !== 'index.json')
    .map((name) => path.join(CDEF_DIR, name))
    .sort();
}

test('oscal-roundtrip.json has the expected top-level shape', () => {
  assert.ok(
    fs.existsSync(REPORT_PATH),
    `reports/oscal-roundtrip.json not found - run \`python3 scripts/audit_oscal_roundtrip.py\` first`,
  );
  const raw = fs.readFileSync(REPORT_PATH, 'utf8');
  const payload = JSON.parse(raw);
  assert.equal(typeof payload, 'object', 'payload must be an object');
  assert.ok(Array.isArray(payload.records), 'records must be an array');
  assert.equal(
    typeof payload.summary,
    'object',
    'summary must be an object',
  );
  assert.equal(
    typeof payload.schema,
    'object',
    'schema must be an object',
  );
  assert.equal(
    payload.schema.oscal_version,
    '1.1.1',
    'schema.oscal_version must be 1.1.1',
  );
  assert.equal(
    typeof payload.summary.total_files_examined,
    'number',
    'summary.total_files_examined must be a number',
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
    assert.equal(typeof rec.file, 'string');
    assert.equal(typeof rec.status, 'string');
    assert.ok(
      ALLOWED_STATUSES.has(rec.status),
      `record.status ${rec.status} must be one of ${[...ALLOWED_STATUSES].join(', ')}`,
    );
    assert.equal(
      typeof rec.roundtrip_drift,
      'boolean',
      'record.roundtrip_drift must be boolean',
    );
    assert.ok(
      Array.isArray(rec.issues),
      'record.issues must be an array',
    );
    assert.ok(
      Array.isArray(rec.schema_errors),
      'record.schema_errors must be an array',
    );
  }
});

test('oscal-roundtrip report covers every component-definition file', () => {
  const payload = JSON.parse(fs.readFileSync(REPORT_PATH, 'utf8'));
  const reportFiles = new Set(payload.records.map((r) => r.file));

  const onDiskFiles = listComponentDefinitionFiles().map((p) =>
    path.relative(REPO, p),
  );

  const missingFromReport = onDiskFiles.filter((f) => !reportFiles.has(f));
  assert.equal(
    missingFromReport.length,
    0,
    `component-definition files on disk but missing from report: ${missingFromReport.join(', ')}`,
  );

  const invented = [...reportFiles].filter((f) => !onDiskFiles.includes(f));
  assert.equal(
    invented.length,
    0,
    `report contains files not present on disk: ${invented.join(', ')}`,
  );
});

test('oscal-roundtrip summary.statuses matches record aggregation', () => {
  const payload = JSON.parse(fs.readFileSync(REPORT_PATH, 'utf8'));
  const recomputed = {};
  for (const rec of payload.records) {
    recomputed[rec.status] = (recomputed[rec.status] || 0) + 1;
  }
  for (const [status, count] of Object.entries(payload.summary.statuses)) {
    if (status === 'schema-hash-mismatch') {
      // schema-hash-mismatch is attributed to the gate itself, not
      // any individual record, so it cannot be rehydrated from the
      // records array.  Just assert it's a non-negative integer.
      assert.ok(
        Number.isInteger(count) && count >= 0,
        `schema-hash-mismatch count is not a non-negative integer: ${count}`,
      );
      continue;
    }
    if (count > 0) {
      assert.equal(
        recomputed[status],
        count,
        `summary.statuses.${status} reports ${count} but records only show ${recomputed[status] || 0}`,
      );
    }
  }
});

test('oscal-roundtrip hard-failure count matches record statuses', () => {
  const payload = JSON.parse(fs.readFileSync(REPORT_PATH, 'utf8'));
  let recomputed = payload.records.filter((r) =>
    HARD_FAIL_STATUSES.has(r.status),
  ).length;
  if (payload.summary.schema_hash_mismatch) {
    recomputed += 1; // schema-hash-mismatch is counted at the gate level
  }
  assert.equal(
    payload.summary.hard_failures,
    recomputed,
    `summary.hard_failures=${payload.summary.hard_failures} but records+gate show ${recomputed}`,
  );
});

test('oscal-roundtrip roundtrip_drift_count reconciles with records', () => {
  const payload = JSON.parse(fs.readFileSync(REPORT_PATH, 'utf8'));
  const recomputed = payload.records.filter((r) => r.roundtrip_drift).length;
  assert.equal(
    payload.summary.roundtrip_drift_count,
    recomputed,
    `summary.roundtrip_drift_count=${payload.summary.roundtrip_drift_count} but records show ${recomputed}`,
  );
});

test('oscal-roundtrip records are deterministically sorted', () => {
  const payload = JSON.parse(fs.readFileSync(REPORT_PATH, 'utf8'));
  for (let i = 1; i < payload.records.length; i++) {
    const prev = payload.records[i - 1];
    const curr = payload.records[i];
    const prevKey = `${prev.uc_id || ''}\u0000${prev.file}`;
    const currKey = `${curr.uc_id || ''}\u0000${curr.file}`;
    assert.ok(
      prevKey <= currKey,
      `records not sorted at index ${i}: ${prevKey} > ${currKey}`,
    );
  }
  const topKeys = Object.keys(payload);
  const sorted = [...topKeys].sort();
  assert.deepEqual(
    topKeys,
    sorted,
    'top-level keys are not alphabetically sorted (sort_keys=True invariant broken)',
  );
});

test('every component-definition file is itself canonically serialised', () => {
  // This duplicates the Python round-trip check in Node so a regression
  // in the Python canonicaliser (or a rogue manual edit committed over
  // the top) is caught by the Node test harness as well.
  const files = listComponentDefinitionFiles();
  assert.ok(
    files.length > 0,
    'no component-definition files found on disk',
  );
  for (const file of files) {
    const original = fs.readFileSync(file, 'utf8');
    const parsed = JSON.parse(original);
    const canonical = `${JSON.stringify(canonicalOrder(parsed), null, 2)}\n`;
    assert.equal(
      original,
      canonical,
      `${path.relative(REPO, file)} is not byte-equal to its canonical serialisation (run scripts/audit_oscal_roundtrip.py)`,
    );
  }
});

test('oscal-roundtrip schema block records hash provenance', () => {
  const payload = JSON.parse(fs.readFileSync(REPORT_PATH, 'utf8'));
  const { schema } = payload;
  assert.equal(
    typeof schema.path,
    'string',
    'schema.path must be a string',
  );
  assert.equal(
    typeof schema.observed_sha256,
    'string',
    'schema.observed_sha256 must be a string',
  );
  assert.ok(
    /^[0-9a-f]{64}$/.test(schema.observed_sha256),
    `schema.observed_sha256 is not a 64-char hex string: ${schema.observed_sha256}`,
  );
  if (schema.expected_sha256) {
    assert.ok(
      /^[0-9a-f]{64}$/.test(schema.expected_sha256),
      `schema.expected_sha256 is not a 64-char hex string: ${schema.expected_sha256}`,
    );
    assert.equal(
      schema.expected_matches_observed,
      schema.observed_sha256 === schema.expected_sha256,
      'schema.expected_matches_observed disagrees with the hash comparison',
    );
  }
});
