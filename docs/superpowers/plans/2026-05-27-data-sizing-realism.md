# Data-Sizing Realism Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the data-sizing tool's flat single-bytes-per-event scaling and constant `0.5` compression with a driver-based v2 catalogue (each source declares its real-world parameters), a pure-function compute registry, a two-component on-disk model (rawdata + tsidx), cluster-aware RF/SF/SmartStore math, and explicit `calibrated`/`pending` tiers — 25 hand-calibrated Tier-1+2 sources at launch out of 206.

**Architecture:** Three plain-JS files (no toolchain) under `tools/data-sizing/`: `ot-data-sources.js` (v2 catalogue with new schema), `compute-functions.js` (NEW — named pure-function registry), `app.js` (rewritten — driver-aware engine + UI). A JSON Schema at `tools/data-sizing/schemas/data-source.schema.json` enforces shape and the conditional citation rule. CI runs a Python validator + `node --test` unit tests + an advisory calibration-coverage report.

**Tech Stack:** ES2017 JavaScript (browser, `<script>`-loaded, no bundler); Python 3.11+ stdlib + `jsonschema` for validation; Node 20 built-in `node --test` for unit tests (no extra deps).

**Spec:** [`docs/superpowers/specs/2026-05-22-data-sizing-realism-design.md`](../specs/2026-05-22-data-sizing-realism-design.md). Sections referenced below as "spec §N".

**Worktree:** None — staying on `main` per established project convention (PR-1, PR-2, PR-3 all landed directly on main; see the lift-loop plan for precedent). The full work ships as ONE PR per spec §12 ("Single PR, three phases, all merged together").

**Cadence:** Frequent intermediate commits during development (one per task = 40 commits on the branch is acceptable); the user squash-merges to one commit on `main` if they prefer one-PR shape, or merges all commits if they prefer detailed history.

---

## File structure

### Files to create

| Path | Responsibility |
| --- | --- |
| `tools/data-sizing/schemas/data-source.schema.json` | JSON Schema 2020-12 for one source object; enforces calibration-citation conditional. Authority for v2 shape. |
| `tools/data-sizing/compute-functions.js` | Named pure-function registry. `COMPUTE_FUNCTIONS[<id>_vN]` returns `{eps, bytesPerEvent}`. Two legacy fallbacks (`endpoint_legacy_v1`, `protocol_legacy_v1`) plus one bespoke function per Tier-1+2 calibrated source. |
| `tools/data-sizing/scripts/validate-catalogue.py` | CI gate. Extracts the catalogue array via a Node one-liner, validates each entry against the schema, asserts every `compute` reference resolves, asserts `id` uniqueness, asserts every `related_uc_ids` entry resolves in `catalog.json`. |
| `tools/data-sizing/scripts/calibration-coverage.py` | Advisory (exit 0). Emits the per-category coverage report shown in spec §9.1 to stdout and `dist/data-sizing-coverage.json` for the README to embed. |
| `tools/data-sizing/scripts/migrate-v1-to-v2.js` | One-shot migrator. Reads `ot-data-sources.js` (treats `OT_DATA_SOURCES` as v1) and emits the same path rewritten as v2. Run once during Task 2, then deleted in the final cleanup task. |
| `tools/data-sizing/__tests__/compute-functions.test.js` | Node built-in `node --test` suite. One `describe()` per named function. Three tests minimum per function (typical / edge-low / edge-high). |
| `tools/data-sizing/__tests__/catalogue-snapshot.json` | Frozen `{eps, bytesPerEvent}` per source under default driver values + "typical" profile. Regression guard — diff fails CI; intentional updates regenerate in the same PR as the calibration change. |
| `tools/data-sizing/__tests__/catalogue-snapshot.test.js` | Loader + comparator for the snapshot file. Runs under `node --test`. |

### Files to modify

| Path | Change |
| --- | --- |
| `tools/data-sizing/ot-data-sources.js` | Replaced wholesale. v2 schema for all 206 sources. Filename preserved per spec §4 reason #1 (no link breakage). |
| `tools/data-sizing/app.js` | Rewritten. Engine pipeline (spec §7), UI cards (§8.1), driver inputs (§8.2), disclosure (§8.3), sizing-assumptions panel (§8.4), structured summary (§8.5), catalogue browser updates (§8.6), methodology pane (§8.7), CSV + share URL (§8.8). |
| `tools/data-sizing/index.html` | New `<div>` skeleton for per-source cards (replaces `<table>`), new sizing-assumptions panel, new summary sections, new methodology pane. Adds `<script src="compute-functions.js"></script>` BEFORE `<script src="app.js"></script>`. |
| `tools/data-sizing/styles.css` | Adds card layout, calibration badges (green/yellow), disclosure styles, methodology pane styles. No theme/color overhaul. |
| `tools/data-sizing/README.md` | Documents v2 architecture, citation policy, calibration coverage, browser smoke checklist, and notes the legacy-filename rationale. |
| `tools/data-sizing/mapping.js` | NO CHANGE expected (it maps catalog UC IDs and equipment IDs to data-sizing source IDs; source IDs are preserved in v2). Task 41 explicitly verifies this. |
| `docs/inventory-and-sizing.md` | Updated to document the new UI (cards, driver inputs, disclosure, methodology pane) and new math (two-component compression, RF/SF, burst-vs-headroom). |
| `.github/workflows/validate.yml` | New job `data-sizing-catalogue` (spec §11) wiring `validate-catalogue.py` (gating), `node --test` (gating), `calibration-coverage.py` (advisory). |
| `VERSION` | User-chosen bump. Recommend `8.7.0` (minor — new feature). Asked before commit. |
| `CHANGELOG.md` | Top "Added" entry mirroring the release-notes HTML. |
| `index.html` | New `<div class="rn-version">` block at the top of the `rn-overlay` (inserted right after `<div class="c-modal-hd" id="rn-title">Release Notes</div>` at line 1605). |

---

## Task 1: JSON Schema for v2 source shape

**Files:**
- Create: `tools/data-sizing/schemas/data-source.schema.json`

### Step 1: Create the schema directory

Run:

```bash
mkdir -p tools/data-sizing/schemas
```

### Step 2: Write the schema verbatim from spec §10

Create `tools/data-sizing/schemas/data-source.schema.json` with the full JSON Schema 2020-12 document shown in spec §10 (lines 796-898 of the spec). Do not paraphrase — copy character-for-character including the `additionalProperties: false`, the `allOf`/`if`/`then` conditional citation rule, the `$defs.driver` sub-schema (`type: enum|number`, `default: {}`, `options`, `profilePresets`), and the `$defs.citation` sub-schema (`type: enum [vendor-sizing, splunkbase-ta, lantern, industry-report, vendor-blog, rfc]`, `url: format uri`, `accessed: format date`).

### Step 3: Validate the schema is itself valid JSON Schema

Run:

```bash
python3 -c "
import json
from jsonschema import Draft202012Validator
schema = json.load(open('tools/data-sizing/schemas/data-source.schema.json'))
Draft202012Validator.check_schema(schema)
print('Schema is valid JSON Schema 2020-12.')
"
```

Expected output: `Schema is valid JSON Schema 2020-12.`

### Step 4: Smoke-test the schema against the Palo Alto example from spec §5.1

Run:

```bash
python3 -c "
import json
from jsonschema import Draft202012Validator
schema = json.load(open('tools/data-sizing/schemas/data-source.schema.json'))
example = {
  'id': 'fw_palo_alto_ngfw',
  'name': 'Palo Alto NGFW',
  'category': 'Security Sources',
  'subcategory': 'Firewalls',
  'calibration': 'calibrated',
  'drivers': [
    {'id': 'throughput_gbps', 'label': 'Sustained throughput',
     'unit': 'Gbps', 'type': 'number',
     'default': 1.0, 'min': 0.01, 'max': 100,
     'profilePresets': {'low': 0.3, 'typical': 1.0, 'high': 4.0}}
  ],
  'compute': 'fw_palo_alto_ngfw_v1',
  'uncertainty': {'low': 0.6, 'typical': 1.0, 'high': 1.8},
  'realism': {
    'rawdata_compression_typical': 0.18,
    'tsidx_overhead_typical':      0.40,
    'filterable_fraction_typical': 0.20
  },
  'citations': [
    {'type': 'vendor-sizing', 'url': 'https://example.com',
     'accessed': '2026-05-22'}
  ]
}
errors = list(Draft202012Validator(schema).iter_errors(example))
assert not errors, errors
print('Calibrated example validates.')
"
```

Expected output: `Calibrated example validates.`

### Step 5: Smoke-test the schema catches a calibrated source with empty citations

Run:

```bash
python3 -c "
import json
from jsonschema import Draft202012Validator
schema = json.load(open('tools/data-sizing/schemas/data-source.schema.json'))
bad = {
  'id': 'fw_bad',
  'name': 'Bad',
  'category': 'Security Sources',
  'subcategory': 'Firewalls',
  'calibration': 'calibrated',
  'drivers': [{'id': 'x', 'label': 'X', 'type': 'number', 'default': 1}],
  'compute': 'x_v1',
  'uncertainty': {'low': 1, 'typical': 1, 'high': 1},
  'realism': {'rawdata_compression_typical': 0.1, 'tsidx_overhead_typical': 0.1, 'filterable_fraction_typical': 0.1},
  'citations': []
}
errors = list(Draft202012Validator(schema).iter_errors(bad))
assert errors, 'expected schema to reject calibrated source with empty citations'
print('Calibrated-with-empty-citations correctly rejected.')
"
```

Expected output: `Calibrated-with-empty-citations correctly rejected.`

### Step 6: Commit

```bash
git add tools/data-sizing/schemas/data-source.schema.json
git commit -m "feat(data-sizing): add v2 source JSON Schema with calibration/citation rule"
```

---

## Task 2: Legacy compute functions + mechanical migrator + v2 catalogue (all pending)

**Files:**
- Create: `tools/data-sizing/compute-functions.js` (initial — two legacy functions only)
- Create: `tools/data-sizing/__tests__/compute-functions.test.js` (initial — tests for the two legacy functions)
- Create: `tools/data-sizing/scripts/migrate-v1-to-v2.js`
- Modify: `tools/data-sizing/ot-data-sources.js` (overwritten by the migrator)

### Step 1: Create `compute-functions.js` with the two legacy functions

Create `tools/data-sizing/compute-functions.js`:

```javascript
/**
 * Data-Sizing v2 compute-function registry.
 *
 * Each function is a pure (driverValues, profile) -> {eps, bytesPerEvent}.
 * No DOM, no network, no Date.now(), no Math.random().
 *
 * Versioning: a formula change ships as _vN+1; the old _vN stays in this
 * file so saved share URLs that explicitly pin a version keep computing.
 */
window.COMPUTE_FUNCTIONS = (function () {
  // ── Legacy fallbacks used by `calibration: "pending"` sources ────────
  // These mechanically re-implement v1's math so the migrator produces a
  // v2 catalogue that numerically matches v1 for un-calibrated entries.

  function endpoint_legacy_v1(d, profile) {
    // v1 endpoint math: totalEps = endpoints * eps_per_endpoint[profile]
    //                   bytesPerEvent = bytes_per_event[profile]
    // The pending entries store the profile table in the `default` of an
    // `enum` driver named `eps_profile`, and the per-endpoint bytes/eps
    // tables in a custom `_v1_tables` driver hint (see migrator output).
    var t = d._v1_tables || {};
    var p = d.eps_profile || profile || "typical";
    var epsPer = (t.eps_per_endpoint || {})[p];
    var bpe    = (t.bytes_per_event   || {})[p];
    if (epsPer === undefined) epsPer = (t.eps_per_endpoint || {}).typical || 1;
    if (bpe    === undefined) bpe    = (t.bytes_per_event   || {}).typical || 500;
    var endpoints = (d.endpoints !== undefined ? d.endpoints : 1);
    return { eps: endpoints * epsPer, bytesPerEvent: bpe };
  }

  function protocol_legacy_v1(d, profile) {
    // v1 protocol math: EPS = tags / poll_interval_sec
    //                   bytesPerEvent = bytes_per_tag[profile]
    var t = d._v1_tables || {};
    var p = profile || "typical";
    var bpe = (t.bytes_per_tag || {})[p];
    if (bpe === undefined) bpe = (t.bytes_per_tag || {}).typical || 300;
    var tags = (d.tag_count !== undefined ? d.tag_count : 1);
    var poll = (d.poll_interval_sec !== undefined && d.poll_interval_sec > 0
                  ? d.poll_interval_sec : 60);
    var dedup = (d.deadband_ratio !== undefined ? (1 - d.deadband_ratio) : 1.0);
    return { eps: (tags / poll) * dedup, bytesPerEvent: bpe };
  }

  return {
    endpoint_legacy_v1: endpoint_legacy_v1,
    protocol_legacy_v1: protocol_legacy_v1
  };
})();

// Node test environment shim — `module.exports` lets `node --test` import.
if (typeof module !== "undefined" && module.exports) {
  module.exports = global.COMPUTE_FUNCTIONS || window.COMPUTE_FUNCTIONS;
}
```

Note: the file uses `window.COMPUTE_FUNCTIONS = ...` for the browser AND a `module.exports` shim for Node test mode. The Node test sets `global.window = {}` before `require()`'ing the file.

### Step 2: Create the test harness for compute functions

Create `tools/data-sizing/__tests__/compute-functions.test.js`:

```javascript
/* node --test runner. Loads compute-functions.js in a fake-browser env. */
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

global.window = {};
require(path.join(__dirname, '..', 'compute-functions.js'));
const COMPUTE = global.window.COMPUTE_FUNCTIONS;

test('endpoint_legacy_v1 typical', () => {
  const out = COMPUTE.endpoint_legacy_v1({
    endpoints: 10,
    eps_profile: 'typical',
    _v1_tables: {
      eps_per_endpoint: { low: 1, typical: 5, high: 50 },
      bytes_per_event:  { low: 200, typical: 800, high: 3000 }
    }
  }, 'typical');
  assert.equal(out.eps, 50);
  assert.equal(out.bytesPerEvent, 800);
});

test('endpoint_legacy_v1 edge-low (1 endpoint, low profile)', () => {
  const out = COMPUTE.endpoint_legacy_v1({
    endpoints: 1,
    eps_profile: 'low',
    _v1_tables: {
      eps_per_endpoint: { low: 1, typical: 5, high: 50 },
      bytes_per_event:  { low: 200, typical: 800, high: 3000 }
    }
  }, 'low');
  assert.equal(out.eps, 1);
  assert.equal(out.bytesPerEvent, 200);
});

test('endpoint_legacy_v1 edge-high (100 endpoints, high profile)', () => {
  const out = COMPUTE.endpoint_legacy_v1({
    endpoints: 100,
    eps_profile: 'high',
    _v1_tables: {
      eps_per_endpoint: { low: 1, typical: 5, high: 50 },
      bytes_per_event:  { low: 200, typical: 800, high: 3000 }
    }
  }, 'high');
  assert.equal(out.eps, 5000);
  assert.equal(out.bytesPerEvent, 3000);
});

test('protocol_legacy_v1 typical', () => {
  const out = COMPUTE.protocol_legacy_v1({
    tag_count: 100,
    poll_interval_sec: 10,
    deadband_ratio: 0.0,
    _v1_tables: { bytes_per_tag: { low: 100, typical: 250, high: 500 } }
  }, 'typical');
  assert.equal(out.eps, 10);
  assert.equal(out.bytesPerEvent, 250);
});

test('protocol_legacy_v1 edge-low (1 tag, 5-min poll, no dedup)', () => {
  const out = COMPUTE.protocol_legacy_v1({
    tag_count: 1, poll_interval_sec: 300, deadband_ratio: 0.0,
    _v1_tables: { bytes_per_tag: { low: 100, typical: 250, high: 500 } }
  }, 'low');
  assert.ok(out.eps > 0 && out.eps < 0.01);
  assert.equal(out.bytesPerEvent, 100);
});

test('protocol_legacy_v1 edge-high (10k tags, 1-s poll, no dedup)', () => {
  const out = COMPUTE.protocol_legacy_v1({
    tag_count: 10000, poll_interval_sec: 1, deadband_ratio: 0.0,
    _v1_tables: { bytes_per_tag: { low: 100, typical: 250, high: 500 } }
  }, 'high');
  assert.equal(out.eps, 10000);
  assert.equal(out.bytesPerEvent, 500);
});

test('protocol_legacy_v1 deadband halves output at 0.5 ratio', () => {
  const base = COMPUTE.protocol_legacy_v1({
    tag_count: 100, poll_interval_sec: 10, deadband_ratio: 0.0,
    _v1_tables: { bytes_per_tag: { typical: 250 } }
  }, 'typical');
  const halved = COMPUTE.protocol_legacy_v1({
    tag_count: 100, poll_interval_sec: 10, deadband_ratio: 0.5,
    _v1_tables: { bytes_per_tag: { typical: 250 } }
  }, 'typical');
  assert.equal(halved.eps, base.eps / 2);
});
```

### Step 3: Run the tests, confirm pass

Run:

```bash
node --test tools/data-sizing/__tests__/
```

Expected: `# pass 7` (or equivalent). All seven tests pass.

### Step 4: Write the mechanical migrator

Create `tools/data-sizing/scripts/migrate-v1-to-v2.js`:

```javascript
#!/usr/bin/env node
/**
 * One-shot migrator: rewrites tools/data-sizing/ot-data-sources.js from v1
 * shape (eps_per_endpoint / bytes_per_event for endpoints;
 * bytes_per_tag / default_tags / default_poll_sec / poll_presets for
 * protocols) to v2 shape (drivers / compute / uncertainty / realism /
 * citations). All migrated entries carry `calibration: "pending"`.
 *
 * Delete this file after the migration commit (Task 40 cleanup).
 */
const fs   = require('fs');
const path = require('path');
const SRC  = path.join(__dirname, '..', 'ot-data-sources.js');

// Load v1 by stripping `const ` declarations and eval'ing.
const v1Text = fs.readFileSync(SRC, 'utf8')
  .replace(/^const /gm, '');
eval(v1Text);
const v1 = OT_DATA_SOURCES;

function commaList(opts) {
  return opts.map(v =>
    typeof v === 'string'
      ? `        { value: ${JSON.stringify(v)}, label: ${JSON.stringify(v)} }`
      : `        { value: ${v}, label: ${JSON.stringify(v >= 60 ? (v / 60) + ' min' : v + ' s')} }`
  ).join(',\n');
}

function migrateEndpoint(s) {
  const drivers = [
    {
      id: 'endpoints',
      label: 'Number of endpoints',
      unit: 'devices',
      type: 'number',
      default: s.default_endpoints || 1,
      min: 1, max: 100000,
      profilePresets: { low: 1, typical: s.default_endpoints || 1, high: (s.default_endpoints || 1) * 10 }
    },
    {
      id: 'eps_profile',
      label: 'Activity profile',
      type: 'enum',
      default: 'typical',
      options: [
        { value: 'low',     label: 'Low' },
        { value: 'typical', label: 'Typical' },
        { value: 'high',    label: 'High' }
      ]
    }
  ];
  return {
    id: s.id, name: s.name, category: s.category, subcategory: s.subcategory,
    description: s.description, vendor_examples: s.vendor_examples,
    protocol: s.protocol, ingest_method: s.ingest_method,
    splunk_sourcetype: s.splunk_sourcetype,
    calibration: 'pending',
    drivers: drivers,
    compute: 'endpoint_legacy_v1',
    uncertainty: { low: 0.5, typical: 1.0, high: 2.0 },
    realism: {
      rawdata_compression_typical: 0.15,
      tsidx_overhead_typical:      0.35,
      filterable_fraction_typical: 0.15
    },
    citations: [],
    related_uc_ids: s.related_uc_ids || [],
    _v1_tables: {
      eps_per_endpoint: s.eps_per_endpoint,
      bytes_per_event:  s.bytes_per_event
    }
  };
}

function migrateProtocol(s) {
  const drivers = [
    {
      id: 'tag_count',
      label: 'Number of tags / topics / OIDs',
      unit: 'tags',
      type: 'number',
      default: s.default_tags || 100,
      min: 1, max: 1000000,
      profilePresets: {
        low: Math.max(1, Math.round((s.default_tags || 100) * 0.2)),
        typical: s.default_tags || 100,
        high: (s.default_tags || 100) * 10
      }
    },
    {
      id: 'poll_interval_sec',
      label: 'Polling / publish interval',
      unit: 'seconds',
      type: 'enum',
      default: s.default_poll_sec || 30,
      options: (s.poll_presets || [1, 5, 10, 30, 60, 300]).map(v => ({
        value: v,
        label: v >= 60 ? (v / 60) + ' min' : v + ' s'
      }))
    },
    {
      id: 'deadband_ratio',
      label: 'Value-change filter (deadband)',
      unit: 'fraction',
      type: 'number',
      default: 0.0,
      min: 0.0, max: 0.95,
      profilePresets: { low: 0.0, typical: 0.0, high: 0.0 },
      help: 'Fraction of polls deduplicated at the gateway when register value didn\u2019t change. Default 0 for pending sources; calibrated sources tune per protocol.'
    }
  ];
  return {
    id: s.id, name: s.name, category: s.category, subcategory: s.subcategory,
    description: s.description, vendor_examples: s.vendor_examples,
    protocol: s.protocol, ingest_method: s.ingest_method,
    splunk_sourcetype: s.splunk_sourcetype,
    calibration: 'pending',
    drivers: drivers,
    compute: 'protocol_legacy_v1',
    uncertainty: { low: 0.5, typical: 1.0, high: 2.0 },
    realism: {
      rawdata_compression_typical: 0.15,
      tsidx_overhead_typical:      0.35,
      filterable_fraction_typical: 0.15
    },
    citations: [],
    related_uc_ids: s.related_uc_ids || [],
    _v1_tables: { bytes_per_tag: s.bytes_per_tag }
  };
}

const v2 = v1.map(s => s.source_type === 'protocol' ? migrateProtocol(s) : migrateEndpoint(s));

const out =
`/**
 * Data-Sizing v2 catalogue. See tools/data-sizing/schemas/data-source.schema.json.
 *
 * Calibration tiers:
 *   - "calibrated": vendor-cited drivers + dedicated compute function in
 *     compute-functions.js. Citations array must be non-empty (CI gate).
 *   - "pending":    mechanically ported from v1; numbers approximate.
 *                   Uses endpoint_legacy_v1 or protocol_legacy_v1 with the
 *                   original v1 tables preserved in the _v1_tables field.
 */
window.OT_DATA_SOURCES = ${JSON.stringify(v2, null, 2)};

if (typeof module !== "undefined" && module.exports) {
  module.exports = global.OT_DATA_SOURCES || window.OT_DATA_SOURCES;
}
`;

fs.writeFileSync(SRC, out);
console.log('Migrated ' + v1.length + ' sources -> v2 (all calibration: pending).');
```

### Step 5: Run the migrator

Run:

```bash
node tools/data-sizing/scripts/migrate-v1-to-v2.js
```

Expected output: `Migrated 206 sources -> v2 (all calibration: pending).`

### Step 6: Spot-check the migrated catalogue

Run:

```bash
node -e "
global.window = {};
require('./tools/data-sizing/ot-data-sources.js');
const ds = global.window.OT_DATA_SOURCES;
console.log('count:', ds.length);
console.log('first:', JSON.stringify(ds[0], null, 2).slice(0, 500));
console.log('pending count:', ds.filter(s => s.calibration === 'pending').length);
console.log('compute distribution:', Object.fromEntries(
  Object.entries(ds.reduce((acc, s) => { acc[s.compute] = (acc[s.compute]||0)+1; return acc; }, {}))
));"
```

Expected: count=206, pending count=206, compute distribution shows `endpoint_legacy_v1` + `protocol_legacy_v1` totalling 206.

### Step 7: Commit (catalogue + compute scaffolding + tests + migrator together)

```bash
git add tools/data-sizing/compute-functions.js \
        tools/data-sizing/__tests__/compute-functions.test.js \
        tools/data-sizing/scripts/migrate-v1-to-v2.js \
        tools/data-sizing/ot-data-sources.js
git commit -m "feat(data-sizing): mechanical v1->v2 catalogue migration (206 pending sources)"
```

---

## Task 3: Catalogue + compute validator script

**Files:**
- Create: `tools/data-sizing/scripts/validate-catalogue.py`

### Step 1: Write the validator

Create `tools/data-sizing/scripts/validate-catalogue.py`:

```python
#!/usr/bin/env python3
"""Validate tools/data-sizing/ot-data-sources.js against the v2 schema.

Checks performed:
  1. Schema validation of every source object.
  2. Every `compute` reference resolves in compute-functions.js.
  3. Every `id` is unique.
  4. Every `related_uc_ids` entry resolves in catalog.json.

Exit non-zero on any failure. Designed for CI use.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import jsonschema

REPO = Path(__file__).resolve().parents[3]
TOOL = REPO / "tools" / "data-sizing"
SCHEMA = TOOL / "schemas" / "data-source.schema.json"
CATALOGUE = TOOL / "ot-data-sources.js"
COMPUTE = TOOL / "compute-functions.js"
CATALOG_JSON = REPO / "catalog.json"


def extract_catalogue() -> list:
    """Extract OT_DATA_SOURCES via a Node one-liner (same pattern as
    non-technical-view.js validation elsewhere in the repo)."""
    proc = subprocess.run(
        ["node", "-e",
         "global.window = {};"
         f"require({json.dumps(str(CATALOGUE))});"
         "process.stdout.write(JSON.stringify(global.window.OT_DATA_SOURCES));"],
        capture_output=True, check=True, text=True,
    )
    return json.loads(proc.stdout)


def extract_compute_names() -> set[str]:
    """Find all top-level COMPUTE function names by regex."""
    text = COMPUTE.read_text(encoding="utf-8")
    return set(re.findall(r"\bfunction\s+([a-z0-9_]+_v\d+)\s*\(", text))


def known_uc_ids() -> set[str]:
    """Load UC IDs from the published catalog.json (built artefact)."""
    if not CATALOG_JSON.exists():
        # In a fresh checkout `make build` hasn't run; skip the UC check
        # rather than failing CI.
        return set()
    data = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
    return {uc["i"] for cat in data["DATA"].values() for sub in cat["s"].values() for uc in sub.get("u", [])}


def main() -> int:
    sources = extract_catalogue()
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)

    failures: list[str] = []

    # 1. Schema validation per source.
    for s in sources:
        errs = list(validator.iter_errors(s))
        for e in errs:
            failures.append(f"[{s.get('id', '<no-id>')}] schema: {e.message}")

    # 2. Compute references resolve.
    compute_names = extract_compute_names()
    for s in sources:
        if s.get("compute") and s["compute"] not in compute_names:
            failures.append(f"[{s['id']}] compute reference '{s['compute']}' "
                            f"not found in compute-functions.js")

    # 3. Unique IDs.
    seen: dict[str, int] = {}
    for s in sources:
        sid = s.get("id")
        if not sid:
            continue
        seen[sid] = seen.get(sid, 0) + 1
    for sid, count in seen.items():
        if count > 1:
            failures.append(f"duplicate id: {sid} ({count} entries)")

    # 4. related_uc_ids resolve in catalog.json (if available).
    valid_ucs = known_uc_ids()
    if valid_ucs:
        for s in sources:
            for uc in s.get("related_uc_ids") or []:
                if uc not in valid_ucs:
                    failures.append(f"[{s['id']}] related_uc_ids '{uc}' "
                                    f"does not exist in catalog.json")

    if failures:
        print(f"FAIL: {len(failures)} validation errors:")
        for f in failures[:50]:
            print(f"  - {f}")
        if len(failures) > 50:
            print(f"  ... and {len(failures) - 50} more")
        return 1

    print(f"PASS: {len(sources)} sources validate against the v2 schema.")
    print(f"      {len(compute_names)} compute functions registered.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### Step 2: Run the validator against the migrated catalogue

Run:

```bash
python3 tools/data-sizing/scripts/validate-catalogue.py
```

Expected: `PASS: 206 sources validate against the v2 schema.` and `2 compute functions registered.`

### Step 3: Commit

```bash
git add tools/data-sizing/scripts/validate-catalogue.py
git commit -m "feat(data-sizing): CI validator for v2 catalogue + compute references"
```

---

## Task 4: Calibration-coverage advisory script

**Files:**
- Create: `tools/data-sizing/scripts/calibration-coverage.py`

### Step 1: Write the coverage script

Create `tools/data-sizing/scripts/calibration-coverage.py`:

```python
#!/usr/bin/env python3
"""Emit per-category calibration coverage for the data-sizing catalogue.

Always exit 0 (advisory). The `--check N` mode (where N is a minimum
overall coverage percentage) is reserved for future gating.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CATALOGUE = REPO / "tools" / "data-sizing" / "ot-data-sources.js"
COVERAGE_OUT = REPO / "dist" / "data-sizing-coverage.json"


def extract_catalogue() -> list:
    proc = subprocess.run(
        ["node", "-e",
         "global.window = {};"
         f"require({json.dumps(str(CATALOGUE))});"
         "process.stdout.write(JSON.stringify(global.window.OT_DATA_SOURCES));"],
        capture_output=True, check=True, text=True,
    )
    return json.loads(proc.stdout)


def coverage(sources: list) -> dict:
    overall_total = len(sources)
    overall_calibrated = sum(1 for s in sources if s.get("calibration") == "calibrated")

    by_cat: dict[str, dict[str, int]] = OrderedDict()
    for s in sources:
        cat = s.get("category", "<uncategorised>")
        bucket = by_cat.setdefault(cat, {"total": 0, "calibrated": 0})
        bucket["total"] += 1
        if s.get("calibration") == "calibrated":
            bucket["calibrated"] += 1

    return {
        "overall": {"total": overall_total, "calibrated": overall_calibrated,
                    "percent": round(overall_calibrated / overall_total * 100, 1) if overall_total else 0.0},
        "by_category": {cat: {**b,
                              "percent": round(b["calibrated"] / b["total"] * 100, 1) if b["total"] else 0.0}
                        for cat, b in by_cat.items()},
    }


def print_report(cov: dict) -> None:
    o = cov["overall"]
    print("Data Sizing catalogue calibration coverage")
    print("=" * 42)
    print(f"  calibrated: {o['calibrated']:>3} / {o['total']:<3} ({o['percent']}%)")
    print(f"  pending:    {o['total'] - o['calibrated']:>3} / {o['total']:<3} "
          f"({round(100 - o['percent'], 1)}%)")
    print("")
    print("By category:")
    for cat, b in cov["by_category"].items():
        print(f"  {cat:<42}{b['calibrated']:>3} / {b['total']:<3} ({b['percent']}%)")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--check", type=float, default=None,
                   help="(future) fail when overall coverage < N percent")
    p.add_argument("--json", action="store_true",
                   help="emit JSON only (no human-readable report)")
    args = p.parse_args()

    sources = extract_catalogue()
    cov = coverage(sources)

    COVERAGE_OUT.parent.mkdir(parents=True, exist_ok=True)
    COVERAGE_OUT.write_text(json.dumps(cov, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(cov, indent=2))
    else:
        print_report(cov)
        print("")
        print(f"Wrote machine-readable report: {COVERAGE_OUT.relative_to(REPO)}")

    if args.check is not None and cov["overall"]["percent"] < args.check:
        print(f"FAIL: coverage {cov['overall']['percent']}% < required {args.check}%")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### Step 2: Run it against the migrated catalogue

Run:

```bash
python3 tools/data-sizing/scripts/calibration-coverage.py
```

Expected output starts with `calibrated:   0 / 206 (0.0%)` and ends with `Wrote machine-readable report: dist/data-sizing-coverage.json`.

### Step 3: Commit

```bash
git add tools/data-sizing/scripts/calibration-coverage.py
git commit -m "feat(data-sizing): advisory calibration-coverage report (per-category)"
```

---

## Task 5: Wire validation + node-test + coverage into CI

**Files:**
- Modify: `.github/workflows/validate.yml`

### Step 1: Locate the right place to add the new job

Run:

```bash
grep -n '^  [a-z-]*:$' .github/workflows/validate.yml | head -20
```

Pick a sibling job that already uses Python + a small setup; the new job adds Python + Node.

### Step 2: Append the new job

Add this YAML block to `.github/workflows/validate.yml` at the end of the `jobs:` map (preserving existing job order; only appending):

```yaml
  data-sizing-catalogue:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install jsonschema
      - name: Validate v2 catalogue against schema
        run: python3 tools/data-sizing/scripts/validate-catalogue.py
      - name: Compute function unit tests
        run: node --test tools/data-sizing/__tests__/
      - name: Calibration coverage (advisory)
        run: python3 tools/data-sizing/scripts/calibration-coverage.py
```

### Step 3: Lint the YAML locally

Run:

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/validate.yml'))"
```

Expected: no output (parses cleanly).

### Step 4: Commit

```bash
git add .github/workflows/validate.yml
git commit -m "ci(data-sizing): wire v2 catalogue validation + unit tests"
```

---

## Task 6: Engine rewrite — driver pipeline + two-component compression + cluster math

**Files:**
- Modify: `tools/data-sizing/app.js` (engine block; UI rendering stays untouched until Task 7+)

The engine is the heart of v2. Replace `getInstanceEps`, `getInstanceBytes`, `getInstanceGBDay`, `computeTotals`, and `renderSummary`'s number-crunching with the spec §7 pipeline. UI rendering remains the v1 table for one more commit (no visual change yet) so the engine can be unit-tested via the browser console / a temporary `node` smoke-test before the UI churns.

### Step 1: Define `runComputeForInstance(entry, profile)` as the new core

Replace the `getInstanceEps`, `getInstanceBytes`, `getInstanceGBDay` helpers (currently around `app.js:140-180`) with the v2 pipeline. Insert this code block into `app.js` immediately after the `BYTES_PER_GB` constant:

```javascript
  // ── v2 engine pipeline (spec §7) ──────────────────────────────────────
  const PROFILE = "typical";  // global profile knob (Task 8 wires the UI control)

  function runComputeForInstance(entry, profile) {
    profile = profile || PROFILE;
    const src = entry.source;
    const fn  = (window.COMPUTE_FUNCTIONS || {})[src.compute];
    if (typeof fn !== "function") {
      console.error("Unknown compute function: " + src.compute + " on source " + src.id);
      return { eps: 0, bytesPerEvent: 0 };
    }
    // Merge driver defaults <- profile presets <- user overrides
    const driverValues = {};
    src.drivers.forEach(d => {
      const presets = d.profilePresets || {};
      const v = (entry.driverValues && entry.driverValues[d.id] !== undefined)
                  ? entry.driverValues[d.id]
                  : (presets[profile] !== undefined ? presets[profile] : d.default);
      driverValues[d.id] = v;
    });
    // Legacy compute functions read v1 tables stashed in source._v1_tables
    if (src._v1_tables) driverValues._v1_tables = src._v1_tables;
    const out = fn(driverValues, profile);
    // Apply uncertainty multiplier (spec §7.1 step 3)
    const u = (src.uncertainty || {})[profile] || 1.0;
    return { eps: out.eps * u, bytesPerEvent: out.bytesPerEvent };
  }

  function getInstanceEps(entry)     { return runComputeForInstance(entry).eps; }
  function getInstanceBytes(entry)   { return runComputeForInstance(entry).bytesPerEvent; }
  function getInstanceEffectiveEps(entry) {
    const { eps } = runComputeForInstance(entry);
    const f = (entry.source.realism || {}).filterable_fraction_typical || 0;
    return eps * (1 - f);  // spec §7.1 step 4
  }
  function getInstanceGBDay(entry) {
    const eps = getInstanceEffectiveEps(entry);
    const bpe = getInstanceBytes(entry);
    return (eps * SECONDS_PER_DAY * bpe) / BYTES_PER_GB;
  }
```

### Step 2: Replace `computeTotals` with cluster-aware math

Replace the existing `computeTotals` function (currently around `app.js:275-292`) with:

```javascript
  // ── v2 cluster math (spec §7.3) ───────────────────────────────────────
  const CLUSTER = {
    rf: 2, sf: 2, smartstore: false, indexerCount: 3,
    burst: 1.5, headroom: 1.25, retentionDays: 30
  };

  function computeTotals() {
    let totalRawEps = 0;      // pre-filter, pre-uncertainty already applied via runComputeForInstance
    let totalEffectiveEps = 0;
    let totalDailyRawGB = 0;
    let totalClusterRawGB = 0;
    let totalClusterTsidxGB = 0;
    const byCat = {}, byIngest = {};

    instances.forEach(entry => {
      const s = entry.source;
      const { eps: rawEps, bytesPerEvent } = runComputeForInstance(entry);
      const filt = (s.realism || {}).filterable_fraction_typical || 0;
      const effEps = rawEps * (1 - filt);
      const gbDay  = (effEps * SECONDS_PER_DAY * bytesPerEvent) / BYTES_PER_GB;

      const rawdataC = (s.realism || {}).rawdata_compression_typical || 0.15;
      const tsidxC   = (s.realism || {}).tsidx_overhead_typical      || 0.35;
      const rfMul    = CLUSTER.smartstore ? 1 : CLUSTER.rf;
      const clusterRaw   = gbDay * rawdataC * rfMul;
      const clusterTsidx = gbDay * tsidxC   * CLUSTER.sf;

      totalRawEps        += rawEps;
      totalEffectiveEps  += effEps;
      totalDailyRawGB    += gbDay;
      totalClusterRawGB  += clusterRaw;
      totalClusterTsidxGB+= clusterTsidx;

      byCat[s.category] = (byCat[s.category] || 0) + gbDay;
      const method = (s.ingest_method || "Unknown").split(",")[0].split("/")[0].trim();
      byIngest[method] = (byIngest[method] || 0) + gbDay;
    });

    const diurnalPeakEps = totalEffectiveEps * CLUSTER.burst;
    const headroomPeakEps = diurnalPeakEps   * CLUSTER.headroom;

    return {
      totalRawEps, totalEffectiveEps, totalDailyRawGB,
      diurnalPeakEps, headroomPeakEps,
      totalClusterRawGB, totalClusterTsidxGB,
      totalClusterGB: totalClusterRawGB + totalClusterTsidxGB,
      perIndexerGB:   (totalClusterRawGB + totalClusterTsidxGB) / Math.max(1, CLUSTER.indexerCount),
      byCat, byIngest
    };
  }
```

### Step 3: Update `renderSummary` to read the new totals shape

Replace `renderSummary` (currently around `app.js:294-333`) so the existing KPI DOM nodes still render — even before the UI redesign:

```javascript
  function renderSummary() {
    const t = computeTotals();

    // Existing KPI cards (we keep wiring them in this task so the engine
    // change ships in isolation; Task 7 restructures the panel.)
    $kpiTotalGB.textContent        = t.totalDailyRawGB.toFixed(2);
    $kpiTotalEPS.textContent       = formatNumber(t.totalEffectiveEps, 1);
    $kpiTotalEventsDay.textContent = formatCompact(t.totalEffectiveEps * SECONDS_PER_DAY);
    $kpiLicense.textContent        = recommendLicenseTier(t.totalDailyRawGB).label;
    $kpiLicenseTier.textContent    = recommendLicenseTier(t.totalDailyRawGB).tier
                                     + " \u2014 "
                                     + recommendLicenseTier(t.totalDailyRawGB).typical_use;
    $kpiRawStorage.textContent     = formatCompact(t.totalDailyRawGB * CLUSTER.retentionDays);
    $kpiDiskStorage.textContent    = formatCompact(t.totalClusterGB * CLUSTER.retentionDays);
    $kpiPeakGB.textContent         = (t.totalDailyRawGB * CLUSTER.burst).toFixed(2);

    $catBreakdown.innerHTML = "";
    Object.entries(t.byCat).sort((a, b) => b[1] - a[1]).forEach(([cat, gb]) => {
      const dotClass = CATEGORY_DOT_CLASS[cat] || "";
      const pct = t.totalDailyRawGB > 0 ? (gb / t.totalDailyRawGB * 100).toFixed(1) : 0;
      $catBreakdown.innerHTML += `
        <div class="breakdown-item">
          <span class="bd-label"><span class="cat-dot ${dotClass}"></span>${cat}</span>
          <span class="bd-value">${gb.toFixed(2)} GB (${pct}%)</span>
        </div>`;
    });

    $ingestBreakdown.innerHTML = "";
    Object.entries(t.byIngest).sort((a, b) => b[1] - a[1]).forEach(([method, gb]) => {
      const pct = t.totalDailyRawGB > 0 ? (gb / t.totalDailyRawGB * 100).toFixed(1) : 0;
      $ingestBreakdown.innerHTML += `
        <div class="breakdown-item">
          <span class="bd-label">${method}</span>
          <span class="bd-value">${gb.toFixed(2)} GB (${pct}%)</span>
        </div>`;
    });
  }
```

### Step 4: Replace the `SPLUNK_LICENSE_TIERS` table

Find the existing `SPLUNK_LICENSE_TIERS` (currently around `app.js:113-130`) and replace with the spec §7.5 table:

```javascript
  const SPLUNK_LICENSE_TIERS = [
    { gb_per_day: 0.5,  label: "0.5 GB/day", tier: "Entry",       typical_use: "Pilot, lab, or single small service" },
    { gb_per_day: 1,    label: "1 GB/day",   tier: "Entry",       typical_use: "Single-site pilot or proof-of-concept" },
    { gb_per_day: 2,    label: "2 GB/day",   tier: "Entry",       typical_use: "Small team / single department" },
    { gb_per_day: 5,    label: "5 GB/day",   tier: "Small",       typical_use: "Single site, limited sources" },
    { gb_per_day: 10,   label: "10 GB/day",  tier: "Small",       typical_use: "Single site with moderate visibility" },
    { gb_per_day: 25,   label: "25 GB/day",  tier: "Medium",      typical_use: "Multi-site or full single-site deployment" },
    { gb_per_day: 50,   label: "50 GB/day",  tier: "Medium",      typical_use: "Multi-site with full security + ops telemetry" },
    { gb_per_day: 100,  label: "100 GB/day", tier: "Large",       typical_use: "Enterprise with firewalls + flow data" },
    { gb_per_day: 200,  label: "200 GB/day", tier: "Large",       typical_use: "Enterprise multi-site with full IT/OT/security" },
    { gb_per_day: 500,  label: "500 GB/day", tier: "Enterprise",  typical_use: "Large enterprise with full telemetry" },
    { gb_per_day: 1000, label: "1 TB/day",   tier: "Enterprise+", typical_use: "Major enterprise with NetFlow + full logging" },
    { gb_per_day: 2000, label: "2 TB/day",   tier: "Enterprise+", typical_use: "Global enterprise, maximum visibility" }
  ];
```

### Step 5: Update `instances[]` shape — driver values bag

The legacy `entry` was `{ instanceId, source, endpoints, epsProfile, customEps, customBytes, tags, pollSec }`. Replace with `{ instanceId, source, driverValues: {} }`. Find the `addSource(id)` function (currently around `app.js:152-185`) and replace its body so new instances start with empty `driverValues`:

```javascript
  function addSource(id) {
    const src = (window.OT_DATA_SOURCES || []).find(s => s.id === id);
    if (!src) return;
    instances.push({
      instanceId: nextInstanceId++,
      source: src,
      driverValues: {}  // empty = use defaults (or profile presets)
    });
    refreshAll();
  }
```

Update `applyFieldToState(el)` (currently around `app.js:531-561`) so it writes into `entry.driverValues[fieldName]` instead of the v1 named properties:

```javascript
  function applyFieldToState(el) {
    const iid = parseInt(el.dataset.iid);
    const field = el.dataset.field;
    if (!iid || !field) return null;
    const entry = findInstance(iid);
    if (!entry) return null;
    const raw = el.value;
    const driver = (entry.source.drivers || []).find(d => d.id === field);
    if (!driver) return null;
    let v;
    if (driver.type === "number") {
      v = parseFloat(raw);
      if (Number.isNaN(v)) v = driver.default;
      if (driver.min !== undefined && v < driver.min) v = driver.min;
      if (driver.max !== undefined && v > driver.max) v = driver.max;
    } else {
      // enum — try coercing to number first so numeric option values stay numeric
      v = (raw !== "" && !isNaN(Number(raw))) ? Number(raw) : raw;
    }
    if (!entry.driverValues) entry.driverValues = {};
    entry.driverValues[field] = v;
    return entry;
  }
```

(The v1 `renderConfigTable` will break in this commit because its inputs still write into the old field names. That's OK — Task 7 rewrites the table to read from drivers. We accept the temporary regression in the v1 UI to keep this commit's diff focused on the engine.)

### Step 6: Smoke-test the engine in the browser console

After saving `app.js`, open `tools/data-sizing/index.html` directly in a browser. In the JS console run:

```javascript
window.OT_DATA_SOURCES.length          // expect: 206
window.OT_DATA_SOURCES.find(s => s.id === 'sec_ngfw_paloalto').drivers
// expect: array with `endpoints` + `eps_profile` drivers (pending shape)
```

The existing UI table will mis-render because Task 7 hasn't rewritten the row HTML yet — that's expected. Verify the engine code didn't throw.

### Step 7: Run the node tests

Run:

```bash
node --test tools/data-sizing/__tests__/
```

Expected: still 7 tests pass. (No new tests in this task; the compute functions are unchanged.)

### Step 8: Commit

```bash
git add tools/data-sizing/app.js
git commit -m "feat(data-sizing): v2 engine pipeline (drivers, RF/SF, two-component compression)"
```

---

## Task 7: UI shell — per-source cards replace the table

**Files:**
- Modify: `tools/data-sizing/index.html` (replace `<table class="config-table">` with a `<div id="cardList">`)
- Modify: `tools/data-sizing/app.js` (`renderConfigTable` → `renderCardList`)
- Modify: `tools/data-sizing/styles.css` (add `.source-card` styles + calibration badge styles)

### Step 1: Edit `index.html` — replace the table with a card container

Replace lines 61-78 of `index.html` (the `<div id="configTableWrap">` block) with:

```html
      <div id="configTableWrap" class="config-table-wrap" style="display:none;">
        <div id="cardList" class="card-list"></div>
      </div>
```

### Step 2: Add the per-source card renderer to `app.js`

Find the `renderConfigTable` function (currently around `app.js:204-269`) and replace it with `renderCardList`:

```javascript
  function renderCardList() {
    const count = instances.length;
    $selectedCount.textContent = count + " source" + (count !== 1 ? "s" : "");
    $emptyState.style.display = count === 0 ? "" : "none";
    $configWrap.style.display = count === 0 ? "none" : "";

    const $cards = document.getElementById("cardList");
    $cards.innerHTML = "";

    instances.forEach(entry => {
      const s = entry.source;
      const profile = PROFILE;
      const { eps, bytesPerEvent } = runComputeForInstance(entry, profile);
      const effEps = eps * (1 - ((s.realism || {}).filterable_fraction_typical || 0));
      const gbDay = (effEps * SECONDS_PER_DAY * bytesPerEvent) / BYTES_PER_GB;
      const iid = entry.instanceId;
      const dotClass = CATEGORY_DOT_CLASS[s.category] || "";
      const calBadge = s.calibration === "calibrated"
          ? `<span class="cal-badge cal-ok">Calibrated \u00B7 ${(s.citations || []).length} src</span>`
          : `<span class="cal-badge cal-pending">\u26A0 Calibration pending</span>`;

      const card = document.createElement("div");
      card.className = "source-card";
      card.innerHTML = `
        <div class="card-header">
          <div class="card-title">
            <span class="cat-dot ${dotClass}"></span>${s.name} ${calBadge}
            <button class="btn-card-remove" data-iid="${iid}" title="Remove">&times;</button>
          </div>
          <div class="card-sub">${s.category} \u203A ${s.subcategory}</div>
        </div>
        <div class="card-drivers">${renderDriverInputs(entry)}</div>
        <div class="card-estimate">
          \u2192 Estimate:
          <span class="est-num">${formatNumber(effEps, 0)}</span> EPS \u00B7
          <span class="est-num">${formatBytes(bytesPerEvent)}</span>/event \u00B7
          <span class="est-num">${gbDay.toFixed(2)}</span> GB/day
        </div>
        <details class="card-disclosure">
          <summary>\u25B8 Why these numbers? <span class="ds-meta">${
              s.calibration === "calibrated"
                ? `${(s.citations || []).length} citations \u00B7 formula \u00B7 realism`
                : `no citations yet \u00B7 formula \u00B7 realism`
            }</span></summary>
          <div class="ds-body">${renderDisclosure(entry)}</div>
        </details>`;
      $cards.appendChild(card);
    });
  }

  function renderDriverInputs(entry) {
    return (entry.source.drivers || []).map(d => {
      const presets = d.profilePresets || {};
      const cur = entry.driverValues && entry.driverValues[d.id] !== undefined
                    ? entry.driverValues[d.id]
                    : (presets[PROFILE] !== undefined ? presets[PROFILE] : d.default);
      const labelExtra = d.unit ? ` <span class="driver-unit">${d.unit}</span>` : "";
      const help = d.help ? ` <span class="driver-help" title="${d.help.replace(/"/g, "&quot;")}">\u24D8</span>` : "";

      if (d.type === "number") {
        const min = d.min !== undefined ? ` min="${d.min}"` : "";
        const max = d.max !== undefined ? ` max="${d.max}"` : "";
        const preset = presets[PROFILE];
        const hint = preset !== undefined ? `<span class="driver-hint">(typical: ${preset})</span>` : "";
        return `<label class="driver-row">
                  <span class="driver-label">${d.label}${labelExtra}${help}</span>
                  <input type="number"${min}${max} step="any" value="${cur}"
                         data-iid="${entry.instanceId}" data-field="${d.id}">
                  ${hint}
                </label>`;
      }
      // enum
      const opts = (d.options || []).map(o =>
        `<option value="${o.value}" ${String(o.value) === String(cur) ? "selected" : ""}>${o.label}</option>`
      ).join("");
      return `<label class="driver-row">
                <span class="driver-label">${d.label}${labelExtra}${help}</span>
                <select data-iid="${entry.instanceId}" data-field="${d.id}">${opts}</select>
              </label>`;
    }).join("");
  }

  function renderDisclosure(entry) {
    const s = entry.source;
    let html = `<div class="ds-formula">Formula (<code>${s.compute}</code>): see <code>compute-functions.js</code></div>`;
    if (s.calibration === "calibrated" && (s.citations || []).length > 0) {
      html += `<div class="ds-section-title">Citations</div><ol class="ds-citations">`;
      s.citations.forEach(c => {
        html += `<li><strong>${c.type}</strong> \u2014 <a href="${c.url}" target="_blank" rel="noopener">${c.url}</a> <span class="ds-accessed">(accessed ${c.accessed})</span>${c.note ? `<div class="ds-note">${c.note}</div>` : ""}</li>`;
      });
      html += `</ol>`;
    } else {
      html += `<div class="ds-warning">\u26A0 Calibration pending \u2014 these numbers are a best-effort port from the v1 catalogue. No vendor citations have been gathered yet.</div>`;
    }
    const r = s.realism || {};
    html += `<div class="ds-section-title">Realism factors</div>
             <div>Compression on-disk: rawdata ${Math.round((r.rawdata_compression_typical||0)*100)}% + tsidx ${Math.round((r.tsidx_overhead_typical||0)*100)}% = ${Math.round(((r.rawdata_compression_typical||0)+(r.tsidx_overhead_typical||0))*100)}% of raw</div>
             <div>Filtering at ingest: ~${Math.round((r.filterable_fraction_typical||0)*100)}% of events droppable at SC4S / Edge Processor</div>`;
    return html;
  }
```

### Step 3: Wire the new event handlers (card remove + driver input)

Find the existing `$configBody.addEventListener("input"...)`, `$configBody.addEventListener("change"...)`, and `$configBody.addEventListener("click"...)` (currently around `app.js:574-599`) and replace `$configBody` with the card container (the existing var is still bound to the now-removed `<tbody>`). Add this above the existing block:

```javascript
  const $cards = document.getElementById("cardList");
  $cards.addEventListener("input", (e) => {
    const el = e.target;
    if (el.tagName === "SELECT") return;
    const entry = applyFieldToState(el);
    if (entry) {
      // re-render only the affected card's estimate + summary
      renderCardList();   // simplest correct option; optimise later if needed
      renderSummary();
    }
  });
  $cards.addEventListener("change", (e) => {
    const entry = applyFieldToState(e.target);
    if (!entry) return;
    renderCardList();
    renderSummary();
  });
  $cards.addEventListener("click", (e) => {
    const btn = e.target.closest(".btn-card-remove");
    if (btn) removeInstance(parseInt(btn.dataset.iid));
  });
```

Delete the now-orphaned `$configBody.addEventListener(...)` calls and the `$configBody` reference (still keep `$configWrap` and `$emptyState`).

Update `refreshAll()` (currently `app.js:339-343`) to call `renderCardList` instead of `renderConfigTable`:

```javascript
  function refreshAll() {
    renderCardList();
    renderSummary();
    buildCatalog($searchInput.value);
  }
```

Same for the initial bootstrapping call near the bottom of the file: replace any `renderConfigTable()` with `renderCardList()`.

### Step 4: Add the card CSS

Append to `tools/data-sizing/styles.css`:

```css
/* ── v2 source cards ─────────────────────────────────────────── */
.card-list { display: flex; flex-direction: column; gap: 12px; }

.source-card {
  background: var(--surface-1);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 14px 16px;
  display: flex; flex-direction: column; gap: 10px;
}

.card-header { display: flex; flex-direction: column; gap: 2px; }
.card-title  { display: flex; align-items: center; gap: 8px; font-weight: 600; }
.card-title .btn-card-remove {
  margin-left: auto;
  background: transparent; border: 0; cursor: pointer;
  color: var(--text-secondary); font-size: 18px; padding: 0 6px;
}
.card-title .btn-card-remove:hover { color: var(--cisco-red, #c92e2e); }
.card-sub    { font-size: 12px; color: var(--text-secondary); }

.cal-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
}
.cal-badge.cal-ok      { background: rgba(46, 160, 67, 0.12); color: #2ea043; }
.cal-badge.cal-pending { background: rgba(212, 153, 0, 0.15); color: #d49900; }

.card-drivers { display: flex; flex-direction: column; gap: 8px; }
.driver-row {
  display: grid;
  grid-template-columns: minmax(160px, 1fr) auto auto;
  align-items: center;
  gap: 10px;
}
.driver-label { font-size: 12px; color: var(--text-secondary); }
.driver-unit  { font-size: 11px; color: var(--text-tertiary); }
.driver-help  { cursor: help; color: var(--text-tertiary); }
.driver-hint  { font-size: 11px; color: var(--text-tertiary); }
.driver-row input[type="number"],
.driver-row select { padding: 4px 8px; border-radius: 4px; border: 1px solid var(--border-subtle); }

.card-estimate {
  font-size: 13px; color: var(--text-primary); padding-top: 6px;
  border-top: 1px dashed var(--border-subtle);
}
.card-estimate .est-num { font-weight: 600; color: var(--cisco-blue); }

.card-disclosure summary { cursor: pointer; font-size: 12px; color: var(--text-secondary); }
.card-disclosure summary .ds-meta { font-size: 11px; color: var(--text-tertiary); margin-left: 6px; }
.card-disclosure .ds-body  { padding: 8px 0 0 14px; font-size: 12px; color: var(--text-secondary); }
.card-disclosure .ds-section-title { margin-top: 8px; font-weight: 600; color: var(--text-primary); }
.card-disclosure .ds-citations { padding-left: 18px; }
.card-disclosure .ds-citations li { margin: 4px 0; }
.card-disclosure .ds-accessed { font-size: 10px; color: var(--text-tertiary); }
.card-disclosure .ds-note     { font-size: 11px; color: var(--text-tertiary); padding-left: 8px; }
.card-disclosure .ds-warning  {
  background: rgba(212, 153, 0, 0.08);
  border-left: 3px solid #d49900;
  padding: 6px 10px;
  margin: 6px 0;
  font-size: 12px;
}
```

### Step 5: Smoke-test in browser

Open `tools/data-sizing/index.html`. Add a few sources (e.g. Palo Alto, Modbus, Linux). Verify:

- Each appears as a card (not a row).
- Pending badge shows "⚠ Calibration pending".
- Driver inputs render (number + enum).
- Editing a driver updates the estimate and the summary.
- The "Why these numbers?" disclosure expands and shows formula + realism + warning.

### Step 6: Commit

```bash
git add tools/data-sizing/index.html tools/data-sizing/app.js tools/data-sizing/styles.css
git commit -m "feat(data-sizing): per-source cards with driver inputs + calibration badge"
```

---

## Task 8: Sizing-assumptions panel — burst/headroom/RF/SF/SmartStore/indexer-count

**Files:**
- Modify: `tools/data-sizing/index.html` (replace the "Storage Estimate" + "Peak Headroom" sub-panels with one consolidated panel per spec §8.4)
- Modify: `tools/data-sizing/app.js` (wire the new controls into `CLUSTER` and re-render)
- Modify: `tools/data-sizing/styles.css` (panel layout)

### Step 1: Edit `index.html` — restructure the summary panel

In `<aside class="summary-panel">`, find the existing Storage Estimate + Peak Headroom blocks (lines 118-162) and replace them with one panel:

```html
      <div class="summary-section assumptions">
        <h3>Sizing Assumptions</h3>
        <div class="assumptions-grid">
          <label>Profile
            <select id="globalProfile">
              <option value="low">Low</option>
              <option value="typical" selected>Typical</option>
              <option value="high">High</option>
            </select>
          </label>
          <label>Burst factor
            <select id="burstFactor">
              <option value="1.0">\u00D71.0 (no burst)</option>
              <option value="1.3">\u00D71.3 (steady OT/IoT)</option>
              <option value="1.5" selected>\u00D71.5 (typical IT)</option>
              <option value="2.0">\u00D72.0 (business hours)</option>
              <option value="3.0">\u00D73.0 (incident security)</option>
              <option value="5.0">\u00D75.0 (extreme)</option>
            </select>
          </label>
          <label>Headroom
            <select id="headroomFactor">
              <option value="1.0">\u00D71.0 (none)</option>
              <option value="1.25" selected>\u00D71.25 (capacity-safe)</option>
              <option value="1.5">\u00D71.5 (generous)</option>
            </select>
          </label>
          <label>Retention
            <select id="retentionDays">
              <option value="30" selected>30 days</option>
              <option value="90">90 days</option>
              <option value="180">180 days</option>
              <option value="365">1 year</option>
              <option value="730">2 years</option>
            </select>
          </label>
        </div>
        <div class="assumptions-subhead">Cluster</div>
        <div class="assumptions-grid">
          <label>Replication F
            <select id="rfFactor">
              <option value="1">1</option>
              <option value="2" selected>2</option>
              <option value="3">3</option>
              <option value="4">4</option>
              <option value="5">5</option>
            </select>
          </label>
          <label>Search F
            <select id="sfFactor">
              <option value="1">1</option>
              <option value="2" selected>2</option>
              <option value="3">3</option>
              <option value="4">4</option>
              <option value="5">5</option>
            </select>
          </label>
          <label class="checkbox">
            <input type="checkbox" id="smartStore"> SmartStore
            <span class="driver-help" title="Cloud-style: single S3 copy of compressed raw (RF=1 effective); tsidx still replicated per SF.">\u24D8</span>
          </label>
          <label>Indexers
            <input type="number" id="indexerCount" min="1" max="100" value="3">
          </label>
        </div>
      </div>

      <div class="summary-section results">
        <h3>Results</h3>
        <div class="results-block" id="resultsBlock"></div>
      </div>
```

(The old `$kpiTotalGB`, `$kpiRawStorage`, `$kpiDiskStorage`, `$kpiPeakGB` etc. nodes are no longer used after Task 9 — leave them in place for this task and just stop reading them; Task 9 deletes them.)

### Step 2: Wire the new controls in `app.js`

Add to the DOM refs block at top of `app.js`:

```javascript
  const $globalProfile = document.getElementById("globalProfile");
  const $headroom      = document.getElementById("headroomFactor");
  const $rf            = document.getElementById("rfFactor");
  const $sf            = document.getElementById("sfFactor");
  const $smartStore    = document.getElementById("smartStore");
  const $indexerCount  = document.getElementById("indexerCount");
  const $resultsBlock  = document.getElementById("resultsBlock");
```

Add change handlers at the bottom (before the `INIT` section):

```javascript
  function syncClusterFromUI() {
    CLUSTER.rf            = parseInt($rf.value, 10) || 2;
    CLUSTER.sf            = Math.min(CLUSTER.rf, parseInt($sf.value, 10) || 2);
    CLUSTER.smartstore    = $smartStore.checked;
    CLUSTER.indexerCount  = Math.max(1, parseInt($indexerCount.value, 10) || 1);
    CLUSTER.burst         = parseFloat($burstFactor.value);
    CLUSTER.headroom      = parseFloat($headroom.value);
    CLUSTER.retentionDays = parseInt($retentionDays.value, 10);
  }

  [$rf, $sf, $smartStore, $indexerCount, $burstFactor, $headroom, $retentionDays]
    .forEach(el => el && el.addEventListener("change", () => { syncClusterFromUI(); refreshAll(); }));

  // SF must not exceed RF — clamp the dropdown after RF change
  $rf.addEventListener("change", () => {
    const rf = parseInt($rf.value, 10) || 2;
    Array.from($sf.options).forEach(o => { o.disabled = parseInt(o.value, 10) > rf; });
    if (parseInt($sf.value, 10) > rf) $sf.value = String(rf);
  });

  // Profile change re-renders all instances (seeds new defaults via runCompute)
  $globalProfile.addEventListener("change", () => {
    // Update the module-level PROFILE constant indirectly — promote to a let.
    PROFILE_REF.value = $globalProfile.value;
    refreshAll();
  });
```

Promote the `PROFILE` constant to a holder so the change handler can mutate it. Change the original line `const PROFILE = "typical";` to:

```javascript
  const PROFILE_REF = { value: "typical" };
  function PROFILE() { return PROFILE_REF.value; }
```

Then update every read of `PROFILE` in the file to `PROFILE()` (occurs in `runComputeForInstance`, `renderCardList`, `renderDriverInputs`).

### Step 3: CSS for the assumptions panel

Append to `styles.css`:

```css
.summary-section.assumptions { padding-bottom: 8px; }
.assumptions-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px 12px;
  margin-bottom: 8px;
}
.assumptions-grid label {
  display: flex;
  flex-direction: column;
  font-size: 11px;
  color: var(--text-secondary);
  gap: 3px;
}
.assumptions-grid label.checkbox {
  flex-direction: row;
  align-items: center;
  gap: 6px;
}
.assumptions-grid select,
.assumptions-grid input[type="number"] {
  padding: 4px 8px; border-radius: 4px; border: 1px solid var(--border-subtle);
  font-size: 12px;
}
.assumptions-subhead {
  font-size: 11px; font-weight: 600; color: var(--text-tertiary);
  text-transform: uppercase; letter-spacing: 0.05em;
  margin: 6px 0 4px;
}
```

### Step 4: Smoke-test in browser

Open `index.html`. Confirm the new sizing-assumptions panel renders with all controls. Toggling SmartStore should change the storage results (Task 9 wires the results display; for now the existing v1 KPI cards reflect changes via `renderSummary`).

### Step 5: Commit

```bash
git add tools/data-sizing/index.html tools/data-sizing/app.js tools/data-sizing/styles.css
git commit -m "feat(data-sizing): sizing-assumptions panel (burst/headroom/RF/SF/SmartStore/indexers)"
```

---

## Task 9: Structured Results block + Methodology pane + Catalogue browser badges

**Files:**
- Modify: `tools/data-sizing/index.html` (delete the legacy KPI cards; add Methodology details)
- Modify: `tools/data-sizing/app.js` (add `renderResultsBlock` + `renderMethodology` + extend `buildCatalog` for badges)
- Modify: `tools/data-sizing/styles.css` (results block + methodology pane styles)

### Step 1: Delete the legacy KPI cards from `index.html`

Remove the existing `.kpi-card`, `.kpi-row`, and `.summary-section` blocks for "Breakdown by Category" / "Ingest Method Summary" (these are now driven by `renderResultsBlock`). After Step 1 the `<aside class="summary-panel">` should contain only the new `Sizing Assumptions` and `Results` sections from Task 8, plus the Methodology details added in Step 4 below.

### Step 2: Replace `renderSummary` with `renderResultsBlock`

Replace the body of `renderSummary` from Task 6 with a single call:

```javascript
  function renderSummary() { renderResultsBlock(); }

  function renderResultsBlock() {
    const t = computeTotals();
    const lic = recommendLicenseTier(t.totalDailyRawGB);
    const nextTier = SPLUNK_LICENSE_TIERS[SPLUNK_LICENSE_TIERS.indexOf(lic) + 1];
    const utilPct = lic.gb_per_day > 0 ? Math.round(t.totalDailyRawGB / lic.gb_per_day * 100) : 0;
    const headroomToNext = nextTier ? (nextTier.gb_per_day - t.totalDailyRawGB).toFixed(1) : "\u2014";

    const eff = formatCompact(t.totalEffectiveEps);
    const raw = formatCompact(t.totalRawEps);
    const dailyEv = formatCompact(t.totalEffectiveEps * SECONDS_PER_DAY);

    const peak = (t.totalEffectiveEps * CLUSTER.burst);
    const peakHr = peak * CLUSTER.headroom;

    const rawDay = (t.totalDailyRawGB * (averageRawdata())).toFixed(1);   // per-day compressed raw across cluster
    const tsidxDay = (t.totalClusterTsidxGB).toFixed(1);
    const totDay = t.totalClusterGB.toFixed(1);
    const totRet = (t.totalClusterGB * CLUSTER.retentionDays).toFixed(0);
    const perIdxDay = t.perIndexerGB.toFixed(1);
    const perIdxRet = (t.perIndexerGB * CLUSTER.retentionDays).toFixed(0);

    $resultsBlock.innerHTML = `
      <div class="rb-section">
        <div class="rb-title">Ingest</div>
        <div class="rb-row"><span>Sources selected</span><span>${instances.length}</span></div>
        <div class="rb-row"><span>Effective EPS (post-filter)</span><span>${eff} <em>raw pre-filter ${raw}</em></span></div>
        <div class="rb-row"><span>Daily events</span><span>${dailyEv}</span></div>
        <div class="rb-row"><span>Daily raw ingest</span><span>${t.totalDailyRawGB.toFixed(2)} GB/day</span></div>
        <div class="rb-row"><span>Diurnal peak EPS</span><span>${formatCompact(peak)} <em>(burst \u00D7${CLUSTER.burst})</em></span></div>
        <div class="rb-row"><span>Peak EPS w/ headroom</span><span>${formatCompact(peakHr)} <em>(\u00D7${CLUSTER.headroom})</em></span></div>
      </div>
      <div class="rb-section">
        <div class="rb-title">License</div>
        <div class="rb-row"><span>Recommended tier</span><span>${lic.label} (${lic.tier})</span></div>
        <div class="rb-row"><span>Utilization</span><span>${utilPct}% of recommended tier</span></div>
        <div class="rb-row"><span>Headroom to next tier</span><span>${headroomToNext === "\u2014" ? "\u2014" : headroomToNext + " GB/day"}</span></div>
      </div>
      <div class="rb-section">
        <div class="rb-title">Storage (cluster-wide \u00B7 RF=${CLUSTER.rf} \u00B7 SF=${CLUSTER.sf}${CLUSTER.smartstore ? " \u00B7 SmartStore" : ""})</div>
        <div class="rb-row"><span>Compressed raw</span><span>${(t.totalClusterRawGB).toFixed(1)} GB/day \u2192 ${(t.totalClusterRawGB * CLUSTER.retentionDays).toFixed(0)} GB / ${CLUSTER.retentionDays} d</span></div>
        <div class="rb-row"><span>TSIDX</span><span>${tsidxDay} GB/day \u2192 ${(t.totalClusterTsidxGB * CLUSTER.retentionDays).toFixed(0)} GB / ${CLUSTER.retentionDays} d</span></div>
        <div class="rb-row rb-total"><span>Total cluster-wide</span><span>${totDay} GB/day \u2192 ${totRet} GB / ${CLUSTER.retentionDays} d</span></div>
        <div class="rb-row"><span>Per indexer (${CLUSTER.indexerCount} idx)</span><span>${perIdxDay} GB/day \u2192 ${perIdxRet} GB / ${CLUSTER.retentionDays} d</span></div>
      </div>
      <div class="rb-section">
        <div class="rb-title">Breakdown by Category</div>
        ${Object.entries(t.byCat).sort((a,b)=>b[1]-a[1]).map(([cat, gb]) => {
          const dot = CATEGORY_DOT_CLASS[cat] || "";
          const pct = t.totalDailyRawGB > 0 ? (gb / t.totalDailyRawGB * 100).toFixed(1) : 0;
          return `<div class="rb-row"><span><span class="cat-dot ${dot}"></span>${cat}</span><span>${gb.toFixed(2)} GB (${pct}%)</span></div>`;
        }).join("")}
      </div>
      <div class="rb-section">
        <div class="rb-title">Ingest Method Summary</div>
        ${Object.entries(t.byIngest).sort((a,b)=>b[1]-a[1]).map(([m, gb]) => {
          const pct = t.totalDailyRawGB > 0 ? (gb / t.totalDailyRawGB * 100).toFixed(1) : 0;
          return `<div class="rb-row"><span>${m}</span><span>${gb.toFixed(2)} GB (${pct}%)</span></div>`;
        }).join("")}
      </div>`;
  }

  function averageRawdata() {
    // Weighted by GB/day across selected instances; falls back to 0.15 default.
    if (instances.length === 0) return 0.15;
    let tot = 0, w = 0;
    instances.forEach(e => {
      const gb = getInstanceGBDay(e);
      tot += gb * ((e.source.realism || {}).rawdata_compression_typical || 0.15);
      w   += gb;
    });
    return w > 0 ? tot / w : 0.15;
  }
```

Delete the old DOM refs that no longer exist (`$kpiTotalGB`, `$kpiTotalEPS`, etc.). Strip them from the top-of-file block.

### Step 3: Methodology pane

Append to `index.html` summary panel:

```html
      <details class="methodology-pane">
        <summary>\u25B8 Methodology</summary>
        <div class="meth-body">
          <div class="meth-section"><strong>Compression model</strong><br>Two-component per source (rawdata + tsidx). Defaults: 15% + 35% = 50% on-disk. Calibrated sources override per data type.</div>
          <div class="meth-section"><strong>Cluster math</strong><br><code>cluster_raw = ingest \u00D7 rawdata \u00D7 RF</code><br><code>cluster_tsidx = ingest \u00D7 tsidx \u00D7 SF</code><br>(SmartStore \u2192 RF=1 for raw, tsidx unchanged.)</div>
          <div class="meth-section"><strong>License pricing</strong><br>Ingest-based (Splunk Cloud / Enterprise). Recommendation rounds UP to next standard tier.</div>
          <div class="meth-section"><strong>Realism inputs</strong><br>Per-source <code>filterable_fraction</code> accounts for SC4S / Edge Processor / props.conf nullQueue. Protocol sources include deadband (value-change filtering) as a user-editable driver.</div>
          <div class="meth-section meth-out"><strong>Not included</strong><br>Workload Pricing / SVC translation. Search-tier sizing (SHs, KV store, scheduler). Replicated DM-acceleration overhead. Indexer hardware sizing (CPU / IOPS). Forwarder fan-out CPU cost.</div>
        </div>
      </details>
```

### Step 4: Catalogue browser — calibration filter + coverage stat

Find `buildCatalog` (around `app.js:67-126`). Add a header block above the accordion that shows coverage + filter checkboxes:

```javascript
  let CATALOGUE_FILTER = { calibrated: true, pending: true };

  function renderCatalogueHeader() {
    const all = window.OT_DATA_SOURCES || [];
    const cal = all.filter(s => s.calibration === "calibrated").length;
    const pct = all.length ? Math.round(cal / all.length * 100) : 0;
    const $h = document.querySelector(".catalog-header");
    let $stat = document.getElementById("calStat");
    if (!$stat) {
      $stat = document.createElement("div");
      $stat.id = "calStat";
      $stat.className = "cal-stat";
      $h.appendChild($stat);
    }
    $stat.innerHTML = `
      <div class="cal-stat-bar">Calibration ${cal} / ${all.length} (${pct}%)</div>
      <div class="cal-filter">
        <label><input type="checkbox" id="filtCal" ${CATALOGUE_FILTER.calibrated ? "checked":""}> Calibrated</label>
        <label><input type="checkbox" id="filtPend" ${CATALOGUE_FILTER.pending ? "checked":""}> Pending</label>
      </div>`;
    document.getElementById("filtCal").addEventListener("change", e => {
      CATALOGUE_FILTER.calibrated = e.target.checked; buildCatalog($searchInput.value);
    });
    document.getElementById("filtPend").addEventListener("change", e => {
      CATALOGUE_FILTER.pending = e.target.checked; buildCatalog($searchInput.value);
    });
  }
```

Inside `buildCatalog`, after the `if (lowerFilter)` filter block, add the calibration filter:

```javascript
      sources = sources.filter(s => {
        if (s.calibration === "calibrated" && !CATALOGUE_FILTER.calibrated) return false;
        if (s.calibration === "pending"    && !CATALOGUE_FILTER.pending)    return false;
        return true;
      });
```

And inside the per-source `<button>` HTML in `buildCatalog`, add a calibration badge:

```javascript
        const sBadge = src.calibration === "calibrated" ? "Calib" : "Pend";
        const sBadgeCls = src.calibration === "calibrated" ? "cal-ok" : "cal-pending";
```

…then include `<span class="cal-badge cal-mini ${sBadgeCls}">${sBadge}</span>` in the source row's HTML.

Call `renderCatalogueHeader()` at the end of `buildCatalog`.

### Step 5: Append CSS for results + methodology + catalogue header

```css
.rb-section { margin-bottom: 14px; }
.rb-title   { font-weight: 700; font-size: 12px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }
.rb-row     { display: flex; justify-content: space-between; font-size: 12px; padding: 3px 0; }
.rb-row em  { color: var(--text-tertiary); font-style: normal; font-size: 11px; }
.rb-row.rb-total { border-top: 1px solid var(--border-subtle); padding-top: 6px; margin-top: 4px; font-weight: 600; }

.methodology-pane { margin-top: 14px; }
.methodology-pane summary { cursor: pointer; font-weight: 600; font-size: 12px; color: var(--text-secondary); }
.meth-body { padding-top: 8px; display: flex; flex-direction: column; gap: 10px; font-size: 11px; color: var(--text-secondary); }
.meth-section { line-height: 1.5; }
.meth-out  { color: var(--text-tertiary); }

.cal-stat       { margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--border-subtle); }
.cal-stat-bar   { font-size: 11px; color: var(--text-secondary); margin-bottom: 4px; }
.cal-filter     { display: flex; gap: 12px; font-size: 11px; color: var(--text-secondary); }
.cal-badge.cal-mini { font-size: 10px; padding: 1px 5px; margin-left: 4px; }
```

### Step 6: Smoke-test

Open the page. Verify: cards render, results block populates, methodology details expand, calibration filter toggles, coverage bar shows `0 / 206 (0%)`.

### Step 7: Commit

```bash
git add tools/data-sizing/index.html tools/data-sizing/app.js tools/data-sizing/styles.css
git commit -m "feat(data-sizing): structured Results block + Methodology pane + catalogue badges"
```

---

## Task 10: Share-URL extension + CSV export extension

**Files:**
- Modify: `tools/data-sizing/app.js` (share URL encode/decode, CSV column extension)

### Step 1: Extend share-URL parsing on init

Find the existing URL-param block at the bottom of `app.js` (around `app.js:651-673`). Replace the `sourcesParam` handling with the v2 driver-aware format:

```javascript
  var sourcesParam = params.get('sources');
  if (sourcesParam) {
    sourcesParam.split('|').filter(Boolean).forEach(function (entry) {
      // Format: src_id  OR  src_id:k1=v1,k2=v2
      var parts = entry.split(':');
      var sid = parts[0].trim();
      addSource(sid);
      if (parts[1]) {
        var added = instances[instances.length - 1];
        if (added) {
          parts[1].split(',').forEach(function (kv) {
            var eq = kv.indexOf('=');
            if (eq <= 0) return;
            var k = kv.slice(0, eq).trim();
            var v = kv.slice(eq + 1).trim();
            // Coerce numeric driver values
            var driver = (added.source.drivers || []).find(function (d) { return d.id === k; });
            var coerced = (driver && driver.type === "number") ? parseFloat(v) : v;
            if (!added.driverValues) added.driverValues = {};
            added.driverValues[k] = coerced;
          });
        }
      }
    });
    refreshAll();
  }
```

### Step 2: Add a "Copy share link" button

Add an export-row button beside the existing `btnExport` button in `index.html`:

```html
        <button id="btnShare" class="btn btn-ghost" title="Copy a shareable URL with current scenario">Share link</button>
```

Bind it in `app.js`:

```javascript
  document.getElementById("btnShare").addEventListener("click", function () {
    var encoded = instances.map(function (e) {
      var kv = Object.entries(e.driverValues || {})
                     .map(function ([k, v]) { return k + "=" + v; })
                     .join(",");
      return e.source.id + (kv ? ":" + kv : "");
    }).join("|");
    var url = window.location.origin + window.location.pathname
            + "?sources=" + encodeURIComponent(encoded);
    navigator.clipboard.writeText(url).then(function () {
      alert("Share link copied to clipboard.");
    }, function () {
      window.prompt("Copy this link:", url);
    });
  });
```

### Step 3: Extend the CSV export with driver values + computed numbers

Find `exportReport` (around `app.js:423-486`). Replace the per-source row block with:

```javascript
    csv += csvRow(['Source','Category','Subcategory','Calibration','Compute','Drivers (k=v)','Effective EPS','Bytes/Event','GB/Day','Sourcetype']);
    instances.forEach(function (entry) {
      var s = entry.source;
      var profile = PROFILE();
      var out = runComputeForInstance(entry, profile);
      var f = (s.realism || {}).filterable_fraction_typical || 0;
      var effEps = out.eps * (1 - f);
      var gbDay  = (effEps * SECONDS_PER_DAY * out.bytesPerEvent) / BYTES_PER_GB;
      var kv = (s.drivers || []).map(function (d) {
        var v = entry.driverValues && entry.driverValues[d.id] !== undefined
                  ? entry.driverValues[d.id]
                  : ((d.profilePresets && d.profilePresets[profile] !== undefined)
                      ? d.profilePresets[profile] : d.default);
        return d.id + "=" + v;
      }).join("; ");
      csv += csvRow([s.name, s.category, s.subcategory, s.calibration, s.compute,
                     kv, effEps.toFixed(1), out.bytesPerEvent, gbDay.toFixed(2),
                     s.splunk_sourcetype || ""]);
    });
```

### Step 4: Smoke-test

Add 2 sources, edit a driver, click "Share link" → confirm clipboard contains `?sources=fw_x:throughput_gbps=2|sec_y:endpoints=10`. Paste into a new tab → confirm the scenario reloads identically. Click "Export Report" → confirm the CSV has a `Drivers (k=v)` column with current values.

### Step 5: Commit

```bash
git add tools/data-sizing/index.html tools/data-sizing/app.js
git commit -m "feat(data-sizing): driver-aware share URLs + CSV export with driver values"
```

---

## Task 11: Calibration template — Palo Alto NGFW as worked example

**Files:**
- Modify: `tools/data-sizing/compute-functions.js` (add `fw_palo_alto_ngfw_v1`)
- Modify: `tools/data-sizing/ot-data-sources.js` (swap `sec_ngfw_paloalto` from pending to calibrated)
- Modify: `tools/data-sizing/__tests__/compute-functions.test.js` (add tests for the new function)

This task is the TEMPLATE the next 24 calibration tasks repeat. The worked example is fully specified in spec §5.1 (catalogue entry), §6 (compute function body), and §8.3 (citation panel).

### Step 1: Research the citation set

Open the three citation targets listed in spec §9.2 row 1 (Palo Alto):

1. Vendor sizing: PAN-OS Log Storage Sizing — `https://docs.paloaltonetworks.com/pan-os/11-0/pan-os-admin/monitoring/log-storage-sizing`
2. Splunkbase TA: `https://splunkbase.splunk.com/app/491` (Splunk_TA_paloalto — default `props.conf` for per-sourcetype rates)
3. Splunk Lantern: Firewall sizing — `https://lantern.splunk.com/Splunk_Platform/Use_Cases/Architectures/Splunk_Validated_Architectures`

Capture for each: accessed date (today), one-line note describing what the citation supports.

### Step 2: Add the compute function

Append to `compute-functions.js` inside the IIFE, before the `return { ... }` block:

```javascript
  function fw_palo_alto_ngfw_v1(d, profile) {
    // Spec §6. Source: PAN-OS 11 log-storage sizing PDF.
    // EPS per Gbps and bytes-per-event are derived from PAN's published
    // log-storage table cross-referenced against Splunk_TA_paloalto v9.x
    // default props.conf rates.
    var baseEpsPerGbps = 4500;
    var profileMultipliers = {
      "traffic-only":                    { eps: 0.70, bytesPerEvent: 1200 },
      "traffic+threat":                  { eps: 1.00, bytesPerEvent: 1800 },
      "traffic+threat+url":              { eps: 1.45, bytesPerEvent: 2100 },
      "traffic+threat+url+dns+wildfire": { eps: 2.10, bytesPerEvent: 2400 }
    };
    var m = profileMultipliers[d.log_profile] || profileMultipliers["traffic+threat"];
    return {
      eps:           (d.throughput_gbps || 1.0) * baseEpsPerGbps * m.eps,
      bytesPerEvent: m.bytesPerEvent
    };
  }
```

Add it to the `return { ... }` block:

```javascript
  return {
    endpoint_legacy_v1: endpoint_legacy_v1,
    protocol_legacy_v1: protocol_legacy_v1,
    fw_palo_alto_ngfw_v1: fw_palo_alto_ngfw_v1
  };
```

### Step 3: Add unit tests

Append to `__tests__/compute-functions.test.js`:

```javascript
test('fw_palo_alto_ngfw_v1 typical (1 Gbps, traffic+threat)', () => {
  const out = COMPUTE.fw_palo_alto_ngfw_v1(
    { throughput_gbps: 1.0, log_profile: 'traffic+threat' }, 'typical');
  assert.equal(out.eps, 4500);
  assert.equal(out.bytesPerEvent, 1800);
});

test('fw_palo_alto_ngfw_v1 edge-low (0.1 Gbps, traffic-only)', () => {
  const out = COMPUTE.fw_palo_alto_ngfw_v1(
    { throughput_gbps: 0.1, log_profile: 'traffic-only' }, 'low');
  assert.equal(Math.round(out.eps), 315);  // 0.1 * 4500 * 0.70
  assert.equal(out.bytesPerEvent, 1200);
});

test('fw_palo_alto_ngfw_v1 edge-high (10 Gbps, full sub)', () => {
  const out = COMPUTE.fw_palo_alto_ngfw_v1(
    { throughput_gbps: 10, log_profile: 'traffic+threat+url+dns+wildfire' }, 'high');
  assert.equal(Math.round(out.eps), 94500);  // 10 * 4500 * 2.10
  assert.equal(out.bytesPerEvent, 2400);
});

test('fw_palo_alto_ngfw_v1 unknown log_profile defaults to traffic+threat', () => {
  const out = COMPUTE.fw_palo_alto_ngfw_v1(
    { throughput_gbps: 1.0, log_profile: 'invalid' }, 'typical');
  assert.equal(out.eps, 4500);
});
```

Run tests:

```bash
node --test tools/data-sizing/__tests__/
```

Expected: `# pass 11` (4 new + 7 existing).

### Step 4: Replace the pending catalogue entry with the calibrated version

Find `sec_ngfw_paloalto` in `ot-data-sources.js` (search for `"id": "sec_ngfw_paloalto"`). Replace the entire entry with the calibrated version from spec §5.1 (but with the actual id `sec_ngfw_paloalto`, not the spec example's `fw_palo_alto_ngfw`):

```javascript
  {
    "id": "sec_ngfw_paloalto",
    "name": "Palo Alto NGFW",
    "category": "Security Sources",
    "subcategory": "Firewalls",
    "description": "Next-Gen Firewall traffic, threat, URL, DNS-Security, WildFire logs",
    "vendor_examples": "PA-5450, PA-3200, PA-VM",
    "protocol": "Syslog / Splunk_TA_paloalto API",
    "ingest_method": "Splunk_TA_paloalto",
    "splunk_sourcetype": "pan:traffic, pan:threat, pan:url, pan:system, pan:config",
    "calibration": "calibrated",
    "drivers": [
      { "id": "throughput_gbps", "label": "Sustained throughput",
        "unit": "Gbps", "type": "number",
        "default": 1.0, "min": 0.01, "max": 100,
        "profilePresets": { "low": 0.3, "typical": 1.0, "high": 4.0 } },
      { "id": "log_profile", "label": "Log subscriptions enabled",
        "type": "enum",
        "default": "traffic+threat",
        "options": [
          { "value": "traffic-only",                    "label": "Traffic only" },
          { "value": "traffic+threat",                  "label": "Traffic + Threat" },
          { "value": "traffic+threat+url",              "label": "Traffic + Threat + URL" },
          { "value": "traffic+threat+url+dns+wildfire", "label": "Traffic + Threat + URL + DNS-Security + WildFire" }
        ] }
    ],
    "compute": "fw_palo_alto_ngfw_v1",
    "uncertainty": { "low": 0.6, "typical": 1.0, "high": 1.8 },
    "realism": {
      "rawdata_compression_typical": 0.18,
      "tsidx_overhead_typical":      0.40,
      "filterable_fraction_typical": 0.20
    },
    "citations": [
      { "type": "vendor-sizing", "url": "https://docs.paloaltonetworks.com/pan-os/11-0/pan-os-admin/monitoring/log-storage-sizing",
        "accessed": "<TODAY>", "note": "PAN-OS 11 log-storage sizing" },
      { "type": "splunkbase-ta", "url": "https://splunkbase.splunk.com/app/491",
        "accessed": "<TODAY>", "note": "Splunk_TA_paloalto default props.conf" },
      { "type": "lantern", "url": "https://lantern.splunk.com/Splunk_Platform/Use_Cases/Architectures/Splunk_Validated_Architectures",
        "accessed": "<TODAY>", "note": "SVA firewall sizing guidance" }
    ],
    "related_uc_ids": ["5.2.1", "5.2.2", "5.2.3", "17.2.9", "17.3.23"]
  },
```

Replace `<TODAY>` with the current ISO date (e.g. `2026-05-27`). Remove the `_v1_tables` field — calibrated sources don't need it.

### Step 5: Validate the catalogue

Run:

```bash
python3 tools/data-sizing/scripts/validate-catalogue.py
python3 tools/data-sizing/scripts/calibration-coverage.py
node --test tools/data-sizing/__tests__/
```

Expected: validator PASSes; coverage shows `1 / 206 (0.5%)`; tests still all pass.

### Step 6: Browser smoke-test

Open `index.html`, search "Palo Alto", click + Add. Verify:

- Card shows green "Calibrated · 3 src" badge.
- Drivers are "Sustained throughput" (number, default 1.0 Gbps) and "Log subscriptions enabled" (enum, default "Traffic + Threat").
- Estimate shows `4500 EPS · 1.8 KB/event · 0.70 GB/day` (matches spec §8.1 mock).
- "Why these numbers?" expansion shows 3 clickable citation links.

### Step 7: Commit

```bash
git add tools/data-sizing/compute-functions.js \
        tools/data-sizing/__tests__/compute-functions.test.js \
        tools/data-sizing/ot-data-sources.js
git commit -m "feat(data-sizing): calibrate sec_ngfw_paloalto (3 citations: PAN docs + TA + Lantern)"
```

---

## Tasks 12–35: Remaining 24 Tier-1+2 calibrations

**Workflow per source:** repeat Task 11, Steps 1-7 with the specific source ID, drivers, compute function, citation targets, and expected estimate. Each task is its own commit using the message pattern:

```
feat(data-sizing): calibrate <source_id> (N citations: <one-line summary>)
```

The 24 sources to calibrate, with citation targets from spec §9.2:

### Task 12: `sec_ngfw_fortinet` — Fortinet FortiGate

Citation targets: Fortinet "FortiAnalyzer Sizing Guide" (vendor-sizing) + Splunkbase Fortinet FortiGate Add-on `splunkbase.splunk.com/app/2846` (splunkbase-ta).
Compute name: `sec_ngfw_fortinet_v1`. Drivers: `throughput_gbps` (number), `utm_features` (enum: `base`, `+ips`, `+ips+webfilter`, `+ips+webfilter+av`). Realism: `rawdata=0.15, tsidx=0.35, filterable=0.20`.

### Task 13: `sec_fw_cisco` — Cisco Secure Firewall (FTD / ASA)

Citation targets: Cisco "Firewall Logging Sizing" (vendor-sizing) + Splunk Add-on for Cisco ASA `splunkbase.splunk.com/app/1620` (splunkbase-ta) + Splunk_TA_cisco_firepower (splunkbase-ta).
Compute name: `sec_fw_cisco_v1`. Drivers: `throughput_gbps` (number), `mode` (enum: `asa-syslog`, `ftd-syslog`, `ftd-estreamer`). ASA syslog is compact (~200B); FTD security events are larger (1–3 KB).

### Task 14: `sec_edr` — Endpoint Detection & Response (generic)

Citation targets: CrowdStrike sizing (vendor-sizing) + SentinelOne sizing (vendor-sizing) + Microsoft Defender E5 audit-log sizing (vendor-sizing). Cross-vendor average — note explicitly in the `note` field of the first citation. Splunkbase TAs for the three vendors as secondary refs.
Compute name: `sec_edr_v1`. Drivers: `endpoints` (number), `telemetry_profile` (enum: `summary`, `behavioural`, `full-process`). bytes/event ranges from ~500 (summary) to ~4 KB (full process telemetry).

### Task 15: `sec_ids_cybervision` — Cisco Cyber Vision

Citation targets: Cyber Vision Sensor Performance Guide (vendor-sizing) + Splunkbase Cisco Cyber Vision Add-on (splunkbase-ta).
Compute name: `sec_ids_cybervision_v1`. Drivers: `monitored_devices` (number), `dpi_mode` (enum: `summary`, `full`). Cyber Vision emits a steady "components" + "flows" stream — model EPS per monitored device.

### Task 16: `sec_ise` — Cisco ISE

Citation targets: Cisco ISE Performance Guide (vendor-sizing) + Splunkbase Cisco ISE Add-on (splunkbase-ta) + Splunk Lantern ISE sizing post.
Compute name: `sec_ise_v1`. Drivers: `authentications_per_hour` (number), `accounting_enabled` (enum yes/no). Auth events are dense at scale; accounting is the volume driver.

### Task 17: `dsa_sec_waf` — WAF (generic — F5 ASM / ModSec / AWS WAF / Cloudflare)

Citation targets: F5 ASM Sizing (vendor-sizing) + ModSecurity logging defaults (rfc / vendor-blog) + Cloudflare logs (vendor-sizing). Bundled source — note in citation.
Compute name: `dsa_sec_waf_v1`. Drivers: `requests_per_sec` (number), `log_mode` (enum: `denied-only`, `denied+sampled-allowed`, `full`).

### Task 18: `dsa_sec_ips_ids` — IPS/IDS (Network)

Citation targets: Suricata default config + perf benchmarks (vendor-blog) + Snort default config (vendor-blog) + Cisco FTD IPS docs (vendor-sizing).
Compute name: `dsa_sec_ips_ids_v1`. Drivers: `inspected_throughput_gbps` (number), `ruleset` (enum: `balanced`, `connectivity`, `security`). Alert rate scales with throughput × tuned-rule density.

### Task 19: `dsa_it_cloud_iaas` — Cloud IaaS

Citation targets: AWS CloudTrail pricing & sizing (vendor-sizing) + Azure Monitor Activity logs (vendor-sizing) + GCP Cloud Audit Logs (vendor-sizing). Cross-cloud average — note in citation.
Compute name: `dsa_it_cloud_iaas_v1`. Drivers: `monthly_api_calls` (number), `data_event_pct` (number 0–100). Management events are small; data events are the volume driver.

### Task 20: `dsa_it_office365` — Office 365 / Microsoft 365

Citation targets: Microsoft "Unified Audit Log volumes" docs (vendor-sizing) + Splunkbase Microsoft 365 Add-on (splunkbase-ta).
Compute name: `dsa_it_office365_v1`. Drivers: `seats` (number), `tier` (enum: `e3`, `e5`). E5 includes Defender + ATP audit streams; volume per seat differs sharply.

### Task 21: `dsa_it_sso` — SSO / IAM

Citation targets: Okta System Log volumes (vendor-sizing) + PingFederate audit (vendor-sizing) + Azure AD sign-in logs (vendor-sizing). Cross-vendor average — note in citation.
Compute name: `dsa_it_sso_v1`. Drivers: `daily_active_users` (number), `mfa_enabled` (enum yes/no). MFA roughly doubles per-login event count.

### Task 22: `it_windows` — Windows Server (Security / System logs)

Citation targets: Splunkbase Splunk Add-on for Microsoft Windows (splunkbase-ta) `splunkbase.splunk.com/app/742` + Lantern Windows logging sizing.
Compute name: `it_windows_v1`. Drivers: `endpoints` (number), `audit_policy` (enum: `default`, `advanced`, `advanced+ps-transcript`). Advanced + PowerShell transcript can 10x volume.

### Task 23: `it_windows_dc` — Windows Domain Controller

Citation targets: Same Windows TA as Task 22 + Splunk Lantern DC monitoring sizing post.
Compute name: `it_windows_dc_v1`. Drivers: `users_authenticated_per_hour` (number), `audit_logon_level` (enum: `success-only`, `success+failure`). 4624/4625 dominate volume.

### Task 24: `it_linux` — Linux Server (syslog / auth / auditd)

Citation targets: Splunkbase Splunk Add-on for Unix and Linux `splunkbase.splunk.com/app/833` (splunkbase-ta) + Lantern Linux sizing + SC4S reference configs `github.com/splunk/splunk-connect-for-syslog` (vendor-blog).
Compute name: `it_linux_v1`. Drivers: `endpoints` (number), `auditd_enabled` (enum yes/no), `auditd_ruleset_size` (enum: `minimal`, `cis`, `full`). auditd dominates when enabled.

### Task 25: `dsa_it_database` — Database Instances (generic)

Citation targets: Oracle Unified Audit volumes (vendor-sizing) + MS-SQL Extended Events (vendor-sizing) + PostgreSQL pgAudit (vendor-blog).
Compute name: `dsa_it_database_v1`. Drivers: `transactions_per_sec` (number), `audit_level` (enum: `dml-only`, `dml+ddl`, `full+select`).

### Task 26: `dsa_it_webserver` — Web Servers (Apache + Nginx + IIS)

Citation targets: Apache combined-log spec (rfc) + nginx default access-log format (vendor-blog) + IIS W3C extended log format (vendor-blog).
Compute name: `dsa_it_webserver_v1`. Drivers: `requests_per_sec` (number), `log_format` (enum: `combined`, `combined+vhost`, `json-rich`). bytes/event 350-1100.

### Task 27: `net_netflow` — NetFlow / IPFIX / sFlow

Citation targets: Splunkbase NetFlow Logic / Splunk_TA_netflow (splunkbase-ta) + vendor sizing PDFs (Cisco Catalyst NetFlow defaults).
Compute name: `net_netflow_v1`. Drivers: `aggregated_flows_per_sec` (number), `format` (enum: `netflow-v5`, `netflow-v9`, `ipfix`, `sflow`). bytes/event 100-200 after collector aggregation.

### Task 28: `net_meraki` — Cisco Meraki

Citation targets: Meraki Dashboard API sizing (vendor-sizing) + Splunk_TA_meraki `splunkbase.splunk.com/app/3018` (splunkbase-ta).
Compute name: `net_meraki_v1`. Drivers: `devices` (number), `syslog_features` (enum: `events-only`, `events+flows`, `events+flows+url`).

### Task 29: `dsa_net_loadbalancer` — Load Balancers / ADC (F5 + Citrix + AVI)

Citation targets: F5 logging best practices (vendor-blog) + Citrix NetScaler log config (vendor-blog) + AVI Networks logging (vendor-blog).
Compute name: `dsa_net_loadbalancer_v1`. Drivers: `requests_per_sec` (number), `log_level` (enum: `denied-only`, `summary`, `full-detail`).

### Task 30: `dsa_net_vpn` — VPN Concentrators / Remote Access

Citation targets: Cisco AnyConnect logging (vendor-sizing) + OpenVPN log defaults (vendor-blog) + Ivanti/Pulse Connect Secure docs (vendor-sizing).
Compute name: `dsa_net_vpn_v1`. Drivers: `concurrent_sessions` (number), `disconnect_alerts_enabled` (enum yes/no).

### Task 31: `proto_opcua` — OPC UA

Citation targets: OPC UA spec (rfc) + Unified Automation OPC UA Server perf (vendor-blog) + Splunk Edge Hub OPC UA add-on (splunkbase-ta).
Compute name: `proto_opcua_v1`. Drivers: `tag_count` (number), `publish_interval_ms` (enum: `100`, `500`, `1000`, `5000`), `deadband_ratio` (number 0-0.95). bytes/event ~350.

### Task 32: `proto_modbus` — Modbus TCP / RTU

This is the second worked example fully specified in spec §5.2 and §6 — implement exactly as the spec shows. Citations: Modbus.org spec (rfc) + Splunk Edge Hub Modbus add-on (splunkbase-ta). Compute: `proto_modbus_v1` (spec §6).

### Task 33: `proto_mqtt` — MQTT

Citation targets: MQTT 5.0 spec (rfc) + HiveMQ broker default config (vendor-blog) + Splunk Edge Hub MQTT add-on (splunkbase-ta).
Compute name: `proto_mqtt_v1`. Drivers: `topic_count` (number), `messages_per_topic_per_sec` (number), `qos` (enum: `0`, `1`, `2`). bytes/event ~280 (JSON payload).

### Task 34: `proto_bacnet` — BACnet/IP

Citation targets: BACnet/IP spec (rfc) + ASHRAE BACnet object-property guide (vendor-blog) + Splunk Edge Hub BACnet add-on (splunkbase-ta).
Compute name: `proto_bacnet_v1`. Drivers: `device_count` (number), `polled_objects_per_device` (number), `poll_interval_sec` (enum), `deadband_ratio` (number). bytes/event ~320.

### Task 35: `proto_snmp` — SNMP (v2c / v3)

Citation targets: SNMP RFC 3411-3418 (rfc) + Splunk Connect for SNMP `splunkbase.splunk.com/app/5347` (splunkbase-ta).
Compute name: `proto_snmp_v1`. Drivers: `oid_count` (number), `poll_interval_sec` (enum), `version` (enum: `v2c`, `v3`). bytes/event ~150 (compact varbinds).

---

**For each of Tasks 12-35:** follow Task 11's seven-step recipe exactly. Each task ships as one commit. After Task 35, the calibration count should read `25 / 206 (12.1%)` matching spec §9.1.

Verify by running after Task 35:

```bash
python3 tools/data-sizing/scripts/calibration-coverage.py | head -3
```

Expected:

```
Data Sizing catalogue calibration coverage
==========================================
  calibrated:  25 / 206 (12.1%)
```

---

## Task 36: Catalogue snapshot regression test

**Files:**
- Create: `tools/data-sizing/__tests__/catalogue-snapshot.json`
- Create: `tools/data-sizing/__tests__/catalogue-snapshot.test.js`
- Create: `tools/data-sizing/scripts/generate-snapshot.js`

### Step 1: Write the snapshot generator

Create `tools/data-sizing/scripts/generate-snapshot.js`:

```javascript
#!/usr/bin/env node
/**
 * Generate __tests__/catalogue-snapshot.json — for each source, given
 * default driver values + "typical" profile, the {eps, bytesPerEvent}
 * tuple produced by its compute function. The CI test compares actual
 * vs frozen; intentional updates re-run this script.
 */
const fs   = require('fs');
const path = require('path');

global.window = {};
require(path.join(__dirname, '..', 'compute-functions.js'));
require(path.join(__dirname, '..', 'ot-data-sources.js'));
const SOURCES = global.window.OT_DATA_SOURCES;
const COMPUTE = global.window.COMPUTE_FUNCTIONS;

const PROFILE = 'typical';

function defaultDriverValues(src) {
  const out = {};
  (src.drivers || []).forEach(d => {
    const preset = (d.profilePresets || {})[PROFILE];
    out[d.id] = preset !== undefined ? preset : d.default;
  });
  if (src._v1_tables) out._v1_tables = src._v1_tables;
  return out;
}

const snapshot = {};
SOURCES.forEach(src => {
  const fn = COMPUTE[src.compute];
  if (typeof fn !== 'function') {
    snapshot[src.id] = { error: 'missing compute: ' + src.compute };
    return;
  }
  const result = fn(defaultDriverValues(src), PROFILE);
  const u = (src.uncertainty || {})[PROFILE] || 1.0;
  snapshot[src.id] = {
    eps:           +(result.eps * u).toFixed(6),
    bytesPerEvent: +result.bytesPerEvent.toFixed(6)
  };
});

const outPath = path.join(__dirname, '..', '__tests__', 'catalogue-snapshot.json');
fs.writeFileSync(outPath, JSON.stringify(snapshot, null, 2) + '\n');
console.log('Wrote snapshot for ' + Object.keys(snapshot).length + ' sources.');
```

### Step 2: Generate the snapshot

Run:

```bash
node tools/data-sizing/scripts/generate-snapshot.js
```

Expected: `Wrote snapshot for 206 sources.`

### Step 3: Write the snapshot comparator test

Create `tools/data-sizing/__tests__/catalogue-snapshot.test.js`:

```javascript
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

global.window = {};
require(path.join(__dirname, '..', 'compute-functions.js'));
require(path.join(__dirname, '..', 'ot-data-sources.js'));
const SOURCES = global.window.OT_DATA_SOURCES;
const COMPUTE = global.window.COMPUTE_FUNCTIONS;

const SNAPSHOT = JSON.parse(fs.readFileSync(
  path.join(__dirname, 'catalogue-snapshot.json'), 'utf8'));

const PROFILE = 'typical';

function defaultDriverValues(src) {
  const out = {};
  (src.drivers || []).forEach(d => {
    const preset = (d.profilePresets || {})[PROFILE];
    out[d.id] = preset !== undefined ? preset : d.default;
  });
  if (src._v1_tables) out._v1_tables = src._v1_tables;
  return out;
}

test('catalogue snapshot — every source produces frozen {eps, bytesPerEvent}', () => {
  const drift = [];
  SOURCES.forEach(src => {
    const fn = COMPUTE[src.compute];
    if (typeof fn !== 'function') { drift.push(`${src.id}: missing compute ${src.compute}`); return; }
    const u = (src.uncertainty || {})[PROFILE] || 1.0;
    const out = fn(defaultDriverValues(src), PROFILE);
    const actual = { eps: +(out.eps * u).toFixed(6), bytesPerEvent: +out.bytesPerEvent.toFixed(6) };
    const expected = SNAPSHOT[src.id];
    if (!expected) { drift.push(`${src.id}: not in snapshot (run generate-snapshot.js)`); return; }
    if (actual.eps !== expected.eps || actual.bytesPerEvent !== expected.bytesPerEvent) {
      drift.push(`${src.id}: expected ${JSON.stringify(expected)} got ${JSON.stringify(actual)}`);
    }
  });
  // Reverse: catch deletions
  Object.keys(SNAPSHOT).forEach(id => {
    if (!SOURCES.find(s => s.id === id)) drift.push(`${id}: in snapshot but not in catalogue`);
  });
  assert.deepEqual(drift, [],
    'Catalogue drift detected — review changes, then regenerate the snapshot:\n' +
    'node tools/data-sizing/scripts/generate-snapshot.js');
});
```

### Step 4: Run tests

```bash
node --test tools/data-sizing/__tests__/
```

Expected: all tests pass (the new snapshot test plus all the compute-function tests).

### Step 5: Commit

```bash
git add tools/data-sizing/__tests__/catalogue-snapshot.json \
        tools/data-sizing/__tests__/catalogue-snapshot.test.js \
        tools/data-sizing/scripts/generate-snapshot.js
git commit -m "test(data-sizing): catalogue snapshot regression guard (206 sources)"
```

---

## Task 37: README + inventory-and-sizing.md updates

**Files:**
- Modify: `tools/data-sizing/README.md`
- Modify: `docs/inventory-and-sizing.md`

### Step 1: Rewrite `tools/data-sizing/README.md`

Replace the current contents with:

```markdown
# Data Sizing Assessment Tool (v2)

A browser-only sizing assistant for Splunk SE conversations: pick the data
sources in scope, set the real-world drivers (throughput, endpoints, polling
rate, log profile, …), and read back an EPS / GB-per-day / license-tier /
cluster-storage estimate built on vendor-cited math.

Open `index.html` directly in a browser. No build step, no server.

## v2 vs v1

The v2 catalogue (206 sources) replaces v1's flat `eps_per_endpoint × bytes_per_event`
heuristic with:

- **Driver-based inputs** — each source declares its real-world parameters
  (throughput, log profile, polled tag count, poll interval, deadband, …).
- **Pure compute functions** — `compute-functions.js` is a named registry of
  side-effect-free `(driverValues, profile) -> {eps, bytesPerEvent}` functions.
- **Two-component compression** — separate `rawdata_compression` and
  `tsidx_overhead` per source instead of a single `0.5` constant.
- **Cluster-aware storage** — RF, SF, SmartStore toggle, indexer count.
- **Burst vs headroom** — diurnal peak (sizes indexer pipeline) is separated
  from capacity-planning safety margin (sizes the cluster).
- **Calibration tiers** — every source is either `calibrated` (≥ 1 vendor
  citation, dedicated compute function) or `pending` (mechanically ported
  from v1, generic legacy compute, no citations yet). The UI surfaces the
  status with a green/yellow badge and a click-to-expand citation list.

The catalogue spans IT, security, network, OT/IoT and protocols — the
legacy filename (`ot-data-sources.js`) is preserved to avoid breaking
existing external links and bookmarks.

## Architecture

```
tools/data-sizing/
├── index.html                       browser UI (no toolchain)
├── styles.css                       dark + light theme
├── app.js                           driver-aware engine + UI
├── compute-functions.js             named pure-function registry
├── ot-data-sources.js               v2 catalogue (206 sources)
├── mapping.js                       UC ↔ source ↔ equipment cross-refs
├── schemas/
│   └── data-source.schema.json      JSON Schema 2020-12 (CI gate)
├── scripts/
│   ├── validate-catalogue.py        CI: schema + compute-ref + UC-ID checks
│   ├── calibration-coverage.py      CI: per-category coverage report
│   └── generate-snapshot.js         regenerate the catalogue snapshot
└── __tests__/
    ├── compute-functions.test.js    `node --test` unit suite
    ├── catalogue-snapshot.json      frozen {eps, bytesPerEvent} per source
    └── catalogue-snapshot.test.js   drift detector
```

## Citation policy

A source is `calibrated` only when it carries at least one citation drawn
from the approved mix:

- Vendor sizing docs (`vendor-sizing`) — primary source.
- Splunkbase TA defaults (`splunkbase-ta`) — primary source for ingest shape.
- Splunk Lantern (`lantern`) — published best-practice guidance.
- Industry / analyst reports (`industry-report`).
- Vendor blogs (`vendor-blog`) — used cautiously, dated.
- RFCs / protocol specs (`rfc`).

Self-reported field-SE experience and AI guesses are explicitly **not** accepted.

## Calibration coverage

Run:

```
python3 tools/data-sizing/scripts/calibration-coverage.py
```

CI emits the same report as an advisory step. Calibration coverage is
**observational**, not gated — the bar is raised in follow-up PRs as more
sources gain citations.

## Browser smoke checklist

1. Open `index.html` directly in a browser.
2. Add "Palo Alto NGFW" → throughput `1.0` Gbps, profile `Traffic + Threat`
   → confirm ~4,500 EPS and ~0.7 GB/day in the per-source card.
3. Toggle SmartStore in Sizing Assumptions → confirm compressed-raw line in
   the Storage block drops by the RF multiplier.
4. Click "Why these numbers?" on a calibrated source → 3 citations render
   with clickable URLs and accessed dates.
5. Click "Why these numbers?" on a pending source → "no citations yet"
   warning renders.
6. Click "Share link" → paste the URL in a new tab → scenario reloads
   identically (sources + driver values).
7. Click "Export Report" → confirm CSV contains a `Drivers (k=v)` column.

## Adding a new calibrated source

1. Decide the source's drivers (≥ 1 with `type: number` or `type: enum`).
2. Write the compute function in `compute-functions.js`, named
   `<source_id>_v1`. Pure — no DOM, no network, no `Date.now()`, no
   `Math.random()`.
3. Add unit tests in `__tests__/compute-functions.test.js` covering at
   minimum: typical case, edge-low driver values, edge-high driver values.
4. Add the source to `ot-data-sources.js` with `calibration: "calibrated"`
   and a `citations` array of ≥ 1 entries from the approved mix.
5. Regenerate the snapshot: `node tools/data-sizing/scripts/generate-snapshot.js`.
6. Run the local validators:
   ```
   python3 tools/data-sizing/scripts/validate-catalogue.py
   node --test tools/data-sizing/__tests__/
   ```
7. Commit.

## CI

`.github/workflows/validate.yml` runs:

- `validate-catalogue.py` (gating) — schema + compute references + UC IDs + unique IDs.
- `node --test` (gating) — compute-function unit tests + snapshot drift guard.
- `calibration-coverage.py` (advisory) — coverage report.
```

### Step 2: Update `docs/inventory-and-sizing.md`

Read the current file (skim the structure) and update the data-sizing section to mention:

- The v2 driver-based UI (cards replace the table).
- Two-component compression (rawdata + tsidx).
- Cluster math (RF / SF / SmartStore / indexer count).
- Burst vs headroom separation.
- Calibration tiers (`calibrated` vs `pending`) with the green/yellow badge.
- The "Why these numbers?" disclosure and the Methodology pane.

Keep the existing structure of the doc; the data-sizing section is one of several. Make targeted edits — no wholesale rewrite of unrelated sections.

### Step 3: Run any doc-lint / link-check that the repo enforces

Check `Makefile` for a `make docs` or similar target; run it if present. If absent, manually verify the new code blocks render in a markdown preview.

### Step 4: Commit

```bash
git add tools/data-sizing/README.md docs/inventory-and-sizing.md
git commit -m "docs(data-sizing): document v2 architecture, drivers, calibration, cluster math"
```

---

## Task 38: Release coordination — VERSION, CHANGELOG, in-app release notes

**Files:**
- Modify: `VERSION`
- Modify: `CHANGELOG.md`
- Modify: `index.html` (release-notes overlay)

### Step 1: Ask the user what version number to use

Per workspace rule `versioning.mdc`: **always ask the user before bumping VERSION**. Recommend `8.7.0` (minor — significant new feature; no breaking change because the URL `?sources=ID` format still works). State recommendation, wait for confirmation before proceeding.

### Step 2: Bump `VERSION`

After user approval, replace the content of `VERSION`:

```
8.7.0
```

(Or whatever the user picks.)

### Step 3: Add a top entry to `CHANGELOG.md`

Insert a new section at the top of `CHANGELOG.md` (after the `# Changelog` header and any `## [Unreleased]` block, before the previous version's section):

```markdown
## [8.7.0] - 2026-MM-DD

### Added
- **Data Sizing tool v2 (`tools/data-sizing/`)** — Replaces v1's flat
  `eps_per_endpoint × bytes_per_event` heuristic with a driver-based model:
  each source declares its real-world parameters (throughput, log profile,
  polled tag count, poll interval, deadband, …), routed through a registry
  of pure `compute()` functions in `compute-functions.js`. Adds a
  two-component compression model (rawdata + tsidx), cluster-aware storage
  math (RF / SF / SmartStore / indexer count), a burst-vs-headroom split,
  per-source "Why these numbers?" citation disclosures, and a Methodology
  pane that surfaces all assumptions. Ships with 25 of 206 sources hand-
  calibrated against vendor sizing docs, Splunkbase TA defaults, and
  Splunk Lantern guidance (12.1% coverage). Pending sources stay
  numerically close to v1 via legacy compute functions, so unmigrated
  entries don't silently shift estimates. v1 `?sources=ID` share URLs
  continue to work; new `?sources=ID:k=v,…` format encodes driver values.
  CI gates the catalogue against a JSON Schema 2020-12 (`schemas/data-source.schema.json`)
  and runs `node --test` unit tests on every compute function plus a
  catalogue-snapshot regression guard.
```

Replace `MM-DD` with the actual ship month and day.

### Step 4: Add a release-notes overlay entry in `index.html`

Insert a new `<div class="rn-version">…</div>` block as the new top entry of the `rn-overlay` in `index.html`. Find the existing top entry (currently `8.6.4` on line 1608) and add immediately above it:

```html
        <div class="rn-version"><span class="rn-version-tag minor">8.7.0</span><span class="rn-version-date">Month DD, YYYY</span></div>
        <div class="rn-section">
          <h3 class="rn-section-title">Data Sizing tool v2</h3>
          <ul class="rn-list">
            <li><strong>Driver-based sizing</strong> &mdash; Each data source now declares its real-world parameters (throughput, log subscriptions, polled tags, deadband, …) and routes through a registry of pure <code>compute()</code> functions. Replaces the flat per-endpoint heuristic with vendor-cited math.</li>
            <li><strong>Two-component compression + cluster math</strong> &mdash; Storage estimates now split <code>rawdata_compression</code> and <code>tsidx_overhead</code> per source, multiplied by Replication Factor / Search Factor / SmartStore toggle / indexer count. The old single &times;0.5 constant is gone.</li>
            <li><strong>Calibration badges &amp; "Why these numbers?"</strong> &mdash; Every source carries a green &laquo;Calibrated&raquo; or yellow &laquo;Pending&raquo; badge. Expand any card to see the formula, the citations (vendor sizing docs, Splunkbase TA defaults, Splunk Lantern posts) and the realism factors that produced the estimate.</li>
            <li><strong>25 Tier-1 sources calibrated at launch</strong> &mdash; Palo Alto NGFW, Fortinet, Cisco Secure Firewall, EDR (CrowdStrike/SentinelOne/Defender avg), Cisco Cyber Vision, Cisco ISE, WAF, IPS/IDS, Cloud IaaS, M365, SSO, Windows/Linux server families, databases, web servers, NetFlow, Meraki, load balancers, VPN, OPC UA, Modbus, MQTT, BACnet, SNMP.</li>
            <li><strong>Share links encode driver values</strong> &mdash; <code>?sources=fw_pan:throughput_gbps=2,log_profile=traffic+threat+url</code>. v1 source-ID-only URLs still work and seed defaults.</li>
            <li><strong>Methodology pane</strong> &mdash; A collapsible bottom-of-summary panel documents the compression model, cluster math, license logic, realism inputs and the things explicitly NOT in scope (Workload Pricing / SVC, search-tier sizing, indexer hardware).</li>
          </ul>
        </div>
```

Replace `Month DD, YYYY` with the actual ship date in the same format as the existing top entry.

### Step 5: Verify the workspace `versioning.mdc` CI guard passes

Run any local equivalent of the CI version-triple check; usually:

```bash
test "$(cat VERSION)" = "$(grep -oE '^\## \[[0-9.]+\]' CHANGELOG.md | head -1 | tr -d '#[] ')"
echo "version triple sync: $?"
```

Expected: prints `0`. Also confirm the version inside `index.html`'s top `rn-version-tag` matches `VERSION` exactly.

### Step 6: Commit

```bash
git add VERSION CHANGELOG.md index.html
git commit -m "release: bump to v8.7.0 (data sizing realism v2)"
```

---

## Task 39: Browser smoke checklist run-through (manual gate)

**Files:** none (purely verification)

### Steps

Run through the spec §13.4 / README smoke checklist in a real browser. Each pass is a checkbox; any failure becomes a follow-up commit before the cleanup task.

- [ ] Open `tools/data-sizing/index.html` directly in a browser (no HTTP server).
- [ ] Add "Palo Alto NGFW" → set throughput to `1.0` → confirm ~4,500 EPS and ~0.7 GB/day in the per-source card.
- [ ] Add "Modbus TCP / RTU" → tag_count `500` / poll `30 s` / deadband `0.40` → confirm ~10 EPS and the disclosure shows the deadband multiplier.
- [ ] Add "Cisco Secure Firewall" (pending) → confirm yellow "Pending" badge and that the disclosure shows "no citations yet".
- [ ] In Sizing Assumptions, toggle SmartStore on → confirm the "Storage (cluster-wide …)" line drops the RF multiplier on the compressed-raw line.
- [ ] Set RF=3 and confirm the storage line scales accordingly.
- [ ] Set indexer count=5 and confirm the "Per indexer" line updates.
- [ ] Click "Why these numbers?" on Palo Alto → 3 citations render with clickable URLs.
- [ ] Toggle the catalogue's "Pending" checkbox off → only the 25 calibrated sources show in the catalogue.
- [ ] Search for "modbus" in the catalogue → confirm the result list filters correctly.
- [ ] Click "Share link" → paste the URL in a new tab → confirm sources + driver values reload.
- [ ] Click "Export Report" → open the CSV → confirm the per-source rows include a "Drivers (k=v)" column.
- [ ] Open `index.html` from the repo root → click "Release notes" → confirm the new v8.7.0 entry shows at the top with the data-sizing list.

If any item fails, file a fix commit and re-run the checklist.

---

## Task 40: Cleanup — delete the one-shot migrator

**Files:**
- Delete: `tools/data-sizing/scripts/migrate-v1-to-v2.js`

### Step 1: Verify the migrator is unreferenced

Run:

```bash
grep -rn "migrate-v1-to-v2" --include='*.md' --include='*.yml' --include='*.py' --include='*.js' .
```

Expected: zero hits (the only reference should be the file itself, which is being deleted).

### Step 2: Delete the file

```bash
git rm tools/data-sizing/scripts/migrate-v1-to-v2.js
```

### Step 3: Verify nothing is broken

Run:

```bash
python3 tools/data-sizing/scripts/validate-catalogue.py
node --test tools/data-sizing/__tests__/
python3 tools/data-sizing/scripts/calibration-coverage.py
```

Expected: validator PASS; tests pass; coverage shows `25 / 206 (12.1%)`.

### Step 4: Commit

```bash
git commit -m "chore(data-sizing): remove one-shot v1->v2 migrator after merge"
```

---

## Task 41: Final cross-tool compatibility check

**Files:** none (purely verification)

### Step 1: Confirm `mapping.js` still resolves source IDs

The `tools/data-sizing/mapping.js` file uses the source IDs from `ot-data-sources.js` indirectly via `DSA_EQUIPMENT_MAP` and `DSA_UC_MAP`. Since v2 preserves every v1 source ID, mapping should remain compatible. Verify:

```bash
node -e "
global.window = {};
require('./tools/data-sizing/ot-data-sources.js');
require('./tools/data-sizing/mapping.js');
const v2ids = new Set(global.window.OT_DATA_SOURCES.map(s => s.id));
let missing = 0;
Object.values(global.window.DSA_EQUIPMENT_MAP || {}).forEach(arr =>
  arr.forEach(id => { if (!v2ids.has(id)) { console.error('missing in v2:', id); missing++; } })
);
Object.values(global.window.DSA_UC_MAP || {}).forEach(arr =>
  arr.forEach(id => { if (!v2ids.has(id)) { console.error('missing in v2:', id); missing++; } })
);
console.log(missing === 0 ? 'mapping.js intact (all IDs resolve)' : missing + ' broken refs');
process.exit(missing === 0 ? 0 : 1);
"
```

Expected: `mapping.js intact (all IDs resolve)`.

If any IDs are missing, the v2 catalogue accidentally dropped or renamed a v1 source — fix in a follow-up commit before merging. The migrator in Task 2 preserves every v1 ID, so this is a regression check.

### Step 2: Confirm the inventory page's hand-off still works

Open `inventory.html` (repo root or the path the project uses). Add equipment → click "Size in Data Sizing tool" (or however the hand-off button is named). Confirm the destination URL loads the right sources and that they render as cards with driver inputs.

### Step 3: Confirm the use-case page's hand-off still works

Open `index.html` (repo root). Pick any UC referenced by a calibrated source. Use the "Size related data sources" affordance (if present). Confirm the destination loads.

(If either hand-off is silently broken, file a follow-up fix commit, then re-run the smoke checklist.)

### Step 4: No commit needed if everything passes

If all three checks pass, this task is done with no diff. If any fails, fix in a follow-up commit before merging the branch.

---

## Self-Review

Before opening the PR, run through this checklist.

### 1. Spec coverage

Walk every section of [`docs/superpowers/specs/2026-05-22-data-sizing-realism-design.md`](../specs/2026-05-22-data-sizing-realism-design.md) and confirm:

| Spec § | Task(s) | Covered? |
|---|---|---|
| §4 Architecture | Task 2 (compute-functions.js, ot-data-sources.js shape), Task 6 (app.js engine), Task 7 (index.html structure), Task 1 (schema dir) | yes |
| §5 Source schema (v2) | Task 1 (JSON Schema), Task 2 (migrator emits v2 shape), Tasks 11-35 (calibrated shape) | yes |
| §6 Compute function contract | Task 2 (legacy functions + Node-shim pattern), Task 11 (Palo Alto worked example), Tasks 12-35 (24 more) | yes |
| §7 Calculation engine | Task 6 (pipeline + two-component compression + cluster math + license tiers), Task 8 (burst/headroom UI), Task 9 (results panel layout) | yes |
| §8 UI & UX | Task 7 (cards + drivers + disclosure), Task 8 (sizing-assumptions panel), Task 9 (structured results + methodology + catalogue browser), Task 10 (share URL + CSV) | yes |
| §9 Calibration tiers | Task 7 (badge UI), Tasks 11-35 (25 calibrated), Task 4 (coverage script) | yes |
| §10 JSON Schema | Task 1 | yes |
| §11 CI integration | Task 5 (validate.yml job), Task 3 (validator), Task 4 (coverage), Task 36 (snapshot) | yes |
| §12 Migration plan | Task 2 (Phase A — mechanical port), Tasks 11-35 (Phase B — Tier-1+2 calibration), Tasks 37-40 (Phase C — cleanup, docs, version) | yes |
| §13 Testing strategy | Task 2 (compute-functions tests), Task 36 (snapshot), Task 3 (schema validation in CI), Task 39 (browser smoke) | yes |
| §14 Release coordination | Task 38 (VERSION + CHANGELOG + release-notes overlay) | yes |
| §15 Rollback plan | Inherent in `git revert <merge-commit>`; documented in spec, no action needed in plan | yes |
| §16 Known catalogue-shape issues | Out of scope per spec; deferred to follow-up PRs | n/a |
| §17/18 Open questions / future work | Out of scope per spec | n/a |

### 2. Placeholder scan

- No "TBD", "FIXME", "fill in later", "similar to Task N" patterns in this plan.
- Tasks 12-35 are NOT placeholders — each has a concrete source ID, citation targets (referenced from spec §9.2), compute function name, and the workflow recipe in Task 11.
- Where I show example code (cluster math, card renderer, snapshot generator), the code is complete and runnable as-shown.

### 3. Type / name consistency

- `COMPUTE_FUNCTIONS` registry: lowercase function names ending `_vN`. Used in `ot-data-sources.js` `compute` field, validated by schema `pattern: ^[a-z0-9_]+_v[0-9]+$` and by `validate-catalogue.py` resolving every reference.
- `CLUSTER` object: fields `rf`, `sf`, `smartstore`, `indexerCount`, `burst`, `headroom`, `retentionDays` consistent across Tasks 6, 7, 8, 9.
- `entry.driverValues[<id>]`: write path (Task 6 Step 5 — `applyFieldToState`), read path (Task 6 Step 1 — `runComputeForInstance`), share-URL encode/decode (Task 10), CSV export (Task 10). All four use the same `driverValues[<driver.id>]` shape.
- DOM IDs: `cardList`, `resultsBlock`, `globalProfile`, `burstFactor`, `headroomFactor`, `rfFactor`, `sfFactor`, `smartStore`, `indexerCount`, `retentionDays`, `btnShare` consistent across `index.html` and `app.js`.
- File paths consistent: `tools/data-sizing/{compute-functions,ot-data-sources,app}.js`, `schemas/data-source.schema.json`, `scripts/{validate-catalogue,calibration-coverage,migrate-v1-to-v2,generate-snapshot}.{py,js}`, `__tests__/{compute-functions,catalogue-snapshot}.{test.js,json}`.

### 4. Task ordering (dependency-aware)

1-2: Schema + migrator must come before any catalogue manipulation. ✓
3-5: Validators ship before CI hookup so the failing-then-passing TDD loop runs locally. ✓
6: Engine before UI (Task 7) so the engine math is shippable in isolation. ✓
7-10: UI builds bottom-up (cards → assumptions panel → results block → share URL). ✓
11-35: Calibration tasks come after the engine + UI are stable so each calibration can smoke-test end-to-end. ✓
36: Snapshot test comes AFTER all calibrations so the frozen values reflect calibrated math, not legacy math. ✓
37-40: Docs / release / cleanup last. ✓

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-27-data-sizing-realism.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task (one per commit), review between tasks, fast iteration. Best for the 25-source calibration block (Tasks 11-35) because each subagent can independently research one source's vendor docs without context bleed.

**2. Inline Execution** — Execute tasks in this session using `executing-plans`, batch execution with checkpoints for review. Best for the engine + UI block (Tasks 1-10) where state needs to be held in working memory across tasks.

**Which approach?**

**If Subagent-Driven chosen:**
- REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
- Fresh subagent per task + two-stage review

**If Inline Execution chosen:**
- REQUIRED SUB-SKILL: Use superpowers:executing-plans
- Batch execution with checkpoints for review
