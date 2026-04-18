// Phase 4.5f perf + a11y gate — drift guard tests.
//
// This file is the Node-side companion to scripts/audit_perf_a11y.py.
// It deliberately does NOT re-run axe-core (the Python orchestrator
// already handles that via tests/a11y/run-axe.mjs).  Instead, it
// verifies a handful of invariants on the committed report so that
// reviewers cannot merge a PR that forgot to regenerate it, and so a
// hand-edit or non-deterministic serialiser change is caught the
// moment it is committed.
//
// Invariants tested:
//
//   1. reports/perf-a11y.json exists, parses as JSON, and has the
//      expected top-level shape (perf, a11y, summary blocks).
//   2. Every perf budget entry reports an actual byte count that
//      matches the real file on disk.  This is the language-
//      agnostic cross-check: if anybody regenerates data.js locally
//      and forgets to regenerate the perf report, this test fails.
//   3. Every perf budget entry is in {"ok","over-budget","missing"}.
//      No budget can report "ok" if actual_bytes > budget_bytes,
//      and none can report "over-budget" if actual_bytes <=
//      budget_bytes.  Catches logic bugs in the Python orchestrator.
//   4. The a11y pages_audited list is non-empty and every referenced
//      page exists on disk — prevents typos in the hardcoded
//      scorecard.html / index.html list from silently becoming
//      no-ops.
//   5. Every a11y violation carries a "disposition" field and the
//      disposition bucketing in the summary reconciles with the
//      per-record counters.  Prevents the Python orchestrator from
//      drifting off the shared severity contract.
//   6. Report is canonically serialised — JSON.parse + JSON.stringify
//      with sorted keys produces the same bytes committed.  This is
//      the same canonicalisation the OSCAL round-trip gate uses and
//      matches Python's json.dumps(..., indent=2, sort_keys=True,
//      ensure_ascii=False).
//
// Run with:
//     node --test tests/a11y/perfa11y.test.mjs
//
// Prerequisite: reports/perf-a11y.json has been regenerated recently
// (validate.yml does this as part of the Phase 4.5 QA gate).

import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO = path.resolve(__dirname, '..', '..');
const REPORT_PATH = path.join(REPO, 'reports', 'perf-a11y.json');

const ALLOWED_PERF_STATUSES = new Set(['ok', 'over-budget', 'missing']);
const ALLOWED_PERF_TIERS = new Set(['critical-path', 'generated-data']);
const ALLOWED_A11Y_DISPOSITIONS = new Set([
  'hard-fail',
  'warning',
  'allowlisted',
]);
const ALLOWED_A11Y_IMPACTS = new Set([
  'critical',
  'serious',
  'moderate',
  'minor',
  'unknown',
  null,
]);

function loadReport() {
  assert.ok(
    fs.existsSync(REPORT_PATH),
    `${path.relative(REPO, REPORT_PATH)} missing — run scripts/audit_perf_a11y.py`,
  );
  const raw = fs.readFileSync(REPORT_PATH, 'utf8');
  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (err) {
    assert.fail(`perf-a11y.json is not valid JSON: ${err.message}`);
  }
  return {raw, parsed};
}

// Recursively rewrite an object's keys in lexical order so that
// JSON.stringify(value, null, 2) emits the same byte sequence as
// Python's json.dumps(value, indent=2, sort_keys=True).  Arrays are
// preserved in-order (Python's sort_keys=True does not sort arrays).
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

test('perf-a11y report: top-level shape', () => {
  const {parsed} = loadReport();
  assert.equal(typeof parsed, 'object');
  assert.ok(parsed && !Array.isArray(parsed), 'report must be a plain object');
  for (const key of ['$comment', 'a11y', 'axe_runner_error', 'perf', 'summary']) {
    assert.ok(
      key in parsed,
      `top-level key ${JSON.stringify(key)} missing from report`,
    );
  }
  assert.equal(typeof parsed.summary, 'object');
  for (const key of [
    'a11y_hard_failures',
    'a11y_warnings',
    'hard_failures',
    'perf_hard_failures',
    'runner_error',
  ]) {
    assert.ok(
      key in parsed.summary,
      `summary key ${JSON.stringify(key)} missing`,
    );
  }
});

test('perf-a11y report: perf budgets match disk size and status logic', () => {
  const {parsed} = loadReport();
  assert.ok(Array.isArray(parsed.perf.budgets), 'perf.budgets must be array');
  assert.ok(
    parsed.perf.budgets.length >= 1,
    'at least one perf budget expected',
  );
  let reconstructedHardFailures = 0;
  let overBudget = 0;
  let missing = 0;
  for (const rec of parsed.perf.budgets) {
    assert.equal(typeof rec, 'object', 'budget record must be object');
    for (const key of ['file', 'budget_bytes', 'tier', 'status']) {
      assert.ok(key in rec, `budget record missing key ${JSON.stringify(key)}`);
    }
    assert.ok(
      ALLOWED_PERF_TIERS.has(rec.tier),
      `budget tier ${JSON.stringify(rec.tier)} not in allowed set`,
    );
    assert.ok(
      ALLOWED_PERF_STATUSES.has(rec.status),
      `budget status ${JSON.stringify(rec.status)} not in allowed set`,
    );
    assert.equal(typeof rec.file, 'string');
    assert.ok(rec.budget_bytes > 0, `budget_bytes must be positive`);

    const abs = path.resolve(REPO, rec.file);
    if (!fs.existsSync(abs)) {
      assert.equal(
        rec.status,
        'missing',
        `file ${rec.file} is absent on disk but the report claims status=${rec.status}`,
      );
      assert.equal(rec.actual_bytes, null, 'actual_bytes must be null when file is missing');
      missing += 1;
      reconstructedHardFailures += 1;
      continue;
    }

    // File is present: actual_bytes must match disk size exactly.
    const actual = fs.statSync(abs).size;
    assert.equal(
      rec.actual_bytes,
      actual,
      `actual_bytes drift for ${rec.file}: report says ${rec.actual_bytes}, disk is ${actual}`,
    );
    assert.equal(
      rec.headroom_bytes,
      rec.budget_bytes - actual,
      `headroom_bytes mismatch for ${rec.file}`,
    );
    // Note: headroom percentage is intentionally NOT serialised into
    // the report because Python's json.dumps(55.0) emits "55.0" but
    // JavaScript's JSON.stringify(55.0) emits "55" — floats with a
    // zero fractional part cannot be rendered identically in both
    // languages, and the drift test's byte-equality invariant would
    // fail.  Consumers who need a percentage derive it on the fly
    // from headroom_bytes / budget_bytes.
    assert.equal(
      'headroom_pct' in rec,
      false,
      `headroom_pct must not be written into the report — consumers derive it from bytes`,
    );
    if (actual > rec.budget_bytes) {
      assert.equal(
        rec.status,
        'over-budget',
        `file ${rec.file} is ${actual}/${rec.budget_bytes} but status=${rec.status}`,
      );
      overBudget += 1;
      reconstructedHardFailures += 1;
    } else {
      assert.equal(
        rec.status,
        'ok',
        `file ${rec.file} is ${actual}/${rec.budget_bytes} but status=${rec.status}`,
      );
    }
  }
  assert.equal(
    parsed.perf.summary.over_budget_count,
    overBudget,
    'perf.summary.over_budget_count does not reconcile with per-record statuses',
  );
  assert.equal(
    parsed.perf.summary.missing_count,
    missing,
    'perf.summary.missing_count does not reconcile with per-record statuses',
  );
  assert.equal(
    parsed.perf.summary.hard_failures,
    reconstructedHardFailures,
    'perf.summary.hard_failures does not reconcile with per-record statuses',
  );
  assert.equal(
    parsed.perf.summary.total_files,
    parsed.perf.budgets.length,
    'perf.summary.total_files does not match budget record count',
  );
});

test('perf-a11y report: a11y pages_audited exist on disk', () => {
  const {parsed} = loadReport();
  assert.ok(
    Array.isArray(parsed.a11y.pages_audited),
    'a11y.pages_audited must be array',
  );
  assert.ok(
    parsed.a11y.pages_audited.length >= 1,
    'at least one a11y page expected',
  );
  for (const rel of parsed.a11y.pages_audited) {
    const abs = path.resolve(REPO, rel);
    assert.ok(
      fs.existsSync(abs),
      `a11y page ${rel} listed in report but absent from disk`,
    );
  }
  // pages_audited must match the order of a11y.results.
  const resultFiles = parsed.a11y.results.map((r) => r.file);
  assert.deepEqual(
    parsed.a11y.pages_audited,
    resultFiles,
    'a11y.pages_audited must equal order of a11y.results[].file',
  );
});

test('perf-a11y report: a11y dispositions and summary reconcile', () => {
  const {parsed} = loadReport();
  assert.ok(Array.isArray(parsed.a11y.results), 'a11y.results must be array');

  let totalViolations = 0;
  let totalHardFailures = 0;
  let totalWarnings = 0;
  let pagesWithErrors = 0;
  for (const res of parsed.a11y.results) {
    assert.equal(typeof res, 'object');
    for (const key of [
      'error',
      'file',
      'hard_failure_count',
      'incomplete',
      'status',
      'summary',
      'violations',
      'warning_count',
    ]) {
      assert.ok(key in res, `a11y result missing key ${JSON.stringify(key)}`);
    }
    if (res.status === 'error') {
      pagesWithErrors += 1;
      totalHardFailures += 1;
      continue;
    }
    assert.equal(res.status, 'ok', `unexpected a11y result status: ${res.status}`);

    let perFileHard = 0;
    let perFileWarn = 0;
    for (const v of res.violations) {
      assert.ok(
        ALLOWED_A11Y_DISPOSITIONS.has(v.disposition),
        `violation ${v.id} on ${res.file} has bad disposition ${v.disposition}`,
      );
      assert.ok(
        ALLOWED_A11Y_IMPACTS.has(v.impact),
        `violation ${v.id} on ${res.file} has unknown impact ${v.impact}`,
      );
      if (v.disposition === 'hard-fail') perFileHard += 1;
      else if (v.disposition === 'warning') perFileWarn += 1;
      totalViolations += 1;
    }
    assert.equal(
      res.hard_failure_count,
      perFileHard,
      `hard_failure_count for ${res.file} does not match per-violation dispositions`,
    );
    assert.equal(
      res.warning_count,
      perFileWarn,
      `warning_count for ${res.file} does not match per-violation dispositions`,
    );
    totalHardFailures += perFileHard;
    totalWarnings += perFileWarn;
  }

  const s = parsed.a11y.summary;
  assert.equal(s.hard_failures, totalHardFailures, 'a11y.summary.hard_failures mismatch');
  assert.equal(s.warnings, totalWarnings, 'a11y.summary.warnings mismatch');
  assert.equal(
    s.total_violations,
    totalViolations,
    'a11y.summary.total_violations mismatch',
  );
  assert.equal(
    s.pages_with_errors,
    pagesWithErrors,
    'a11y.summary.pages_with_errors mismatch',
  );

  // Top-level summary must reconcile too.
  const top = parsed.summary;
  assert.equal(
    top.a11y_hard_failures,
    totalHardFailures,
    'summary.a11y_hard_failures mismatch',
  );
  assert.equal(
    top.a11y_warnings,
    totalWarnings,
    'summary.a11y_warnings mismatch',
  );
  assert.equal(
    top.perf_hard_failures,
    parsed.perf.summary.hard_failures,
    'summary.perf_hard_failures mismatch',
  );
  const runnerErrorBonus = parsed.axe_runner_error ? 1 : 0;
  assert.equal(
    top.hard_failures,
    parsed.perf.summary.hard_failures + totalHardFailures + runnerErrorBonus,
    'summary.hard_failures mismatch with perf+a11y+runner totals',
  );
});

test('perf-a11y report: is canonically serialised', () => {
  const {raw, parsed} = loadReport();
  const canonical = JSON.stringify(canonicalOrder(parsed), null, 2) + '\n';
  assert.equal(
    raw,
    canonical,
    'reports/perf-a11y.json is not canonically serialised — regenerate with scripts/audit_perf_a11y.py',
  );
});

test('perf-a11y report: a11y config documents the disabled rules', () => {
  const {parsed} = loadReport();
  const cfg = parsed.a11y.config;
  assert.ok(Array.isArray(cfg.disabled_rules));
  // Whatever exact list we ship, it must include color-contrast —
  // jsdom cannot evaluate that rule and leaving it enabled causes
  // flaky results.  This is the single most important disabled rule
  // and we assert it explicitly so nobody accidentally turns it back
  // on without thinking about the jsdom layout engine gap.
  assert.ok(
    cfg.disabled_rules.includes('color-contrast'),
    'color-contrast must be disabled for jsdom-based axe runs',
  );
  assert.ok(Array.isArray(cfg.run_only?.values));
  assert.ok(
    cfg.run_only.values.some((v) => /wcag2(1)?aa/.test(v)),
    'a11y run_only must target WCAG AA',
  );
});
