# Data Sizing Tool — Realism Refresh Design Spec

> **Status.** Proposed (2026-05-22).
> **Author.** Claude (Cursor) in collaboration with `@fenre`.
> **Supersedes.** —
> **Scope.** [`tools/data-sizing/`](../../../tools/data-sizing/) (single-page static web app).
> **Tracks against.** [`docs/inventory-and-sizing.md`](../../inventory-and-sizing.md) (user-facing documentation will need to be updated when this ships).

## 1. Problem

The [Data Sizing Assessment](../../../tools/data-sizing/) tool is a single-page,
no-build-step static web app that gives Splunk SEs and customer architects a
back-of-the-envelope ingest-and-storage estimate. Its current catalogue
([`tools/data-sizing/ot-data-sources.js`](../../../tools/data-sizing/ot-data-sources.js))
covers **206 data sources** across 9 categories (178 endpoint-style + 28
protocol-style) and feeds a simple per-source calculation engine in
[`app.js`](../../../tools/data-sizing/app.js).

The numbers it produces today are **not realistic enough to use in a customer
sizing call without disclaimers**. Three classes of inaccuracy are present:

1. **Per-source ingest rates are stale or toy.** Palo Alto's
   `eps_per_endpoint: {typical: 200}` is reasonable for a small-to-mid
   deployment but is much too quiet for a modern PA-5450-class firewall
   with URL filtering and DNS-Security enabled — those routinely add 5–10× to
   the event rate at the same throughput. OT defaults are toys
   (`proto_modbus: default_tags: 50` vs ~20–50 K registers in a real
   refinery; `proto_opcua: default_tags: 100` vs ~5 K in a real plant
   historian). Protocol poll intervals are aggressive defaults
   (Modbus 10 s, OPC-UA 5 s — production sites usually run 30–60 s for
   register-rich devices). And there is no deduplication knob: real
   gateways drop 30–70 % of unchanged polls via deadband, which the
   current catalogue ignores entirely.

2. **The math model collapses several distinct concepts.** A flat `0.5`
   compression constant stands in for what is actually a two-component
   on-disk overhead (compressed raw + tsidx). There is no replication-factor
   or search-factor multiplier — i.e. the tool reports single-indexer storage
   regardless of cluster size. There is no SmartStore awareness, no
   filtering allowance (SC4S / Edge Processor / `nullQueue` drops), and the
   single `burstFactor` conflates the diurnal peak ratio with capacity-plan
   headroom.

3. **There is no provenance.** None of the numbers carry a citation. Numbers
   can drift over years of edits without any signal in the source file
   that says "this was last verified against the PAN-OS sizing PDF in 2026".
   An SE in front of a customer cannot show their work.

The user's instruction is direct: *"make the expected data volume for each
source more realistic compared to what can be expected in production."* This
spec proposes a one-PR greenfield rewrite of the schema, engine, and UI to
make that realism structurally enforceable — every calibrated number is
vendor-cited, every formula is unit-tested, and the on-disk math reflects how
Splunk actually stores data in clustered deployments.

## 2. Goal

Replace the current ad-hoc per-source schema and single-constant math model
with a **driver-based schema** (each source declares the real-world inputs
that drive its ingest volume), a **named compute-function registry** (each
formula is a pure, unit-tested function), and a **two-component cluster-aware
storage model** (separates rawdata compression from tsidx overhead and
multiplies by RF / SF / SmartStore appropriately).

### Success metric

When v2 ships:

- The tool's per-source ingest numbers for the **25 Tier-1+Tier-2 calibrated
  sources** match within ±25 % of the documented vendor sizing guides /
  Splunkbase TA defaults / Splunk Lantern guidance they cite. Drift outside
  that band requires a citation update or a formula version bump.
- Every `calibration: "calibrated"` source carries ≥ 1 entry in `citations[]`.
  CI fails the PR if this invariant breaks.
- Every compute function is a pure function with at least three unit tests
  (known-good, edge-low, edge-high) under `__tests__/`.
- The on-disk storage breakout displays compressed-raw and tsidx separately,
  multiplied by RF and SF, with a SmartStore toggle that collapses raw RF to 1.
- A calibration-coverage report (per-category) emits in CI and surfaces in
  the tool's `README.md`.

### Non-goals

- Not a Workload Pricing / SVC translator. License recommendation stays
  ingest-pricing (Splunk Cloud / Enterprise). SVC sizing is a separate PR.
- Not a search-tier sizer. SH count, KV-store sizing, scheduler concurrency,
  forwarder CPU fan-out — all out of scope.
- Not an indexer hardware sizer. The storage math feeds an "indexer count"
  divisor, but CPU / IOPS / RAM sizing per indexer is out of scope.
- Not a JSON-import tool. CSV export stays (and is extended with driver
  values); JSON import is a separate PR.
- Not a mobile-responsive redesign. Tool remains desktop-first.
- Not a Splunkbase auto-discovery. The catalogue is hand-curated; CI does not
  reach out to Splunkbase to refresh add-on metadata.
- Not a rename of `ot-data-sources.js`. The historical filename stays to avoid
  external-link breakage; the README notes the catalogue is broader than OT.

## 3. Source-of-truth policy

Every `calibration: "calibrated"` source's numbers must be backed by ≥ 1
citation drawn from this approved source mix (recorded in `citations[].type`):

| Type | What counts | Examples |
|---|---|---|
| `vendor-sizing` | Official vendor sizing guide, datasheet, log-storage PDF, or admin guide | PAN-OS log storage guide; Fortinet FortiGate VM datasheet; Cisco Secure Firewall logging best-practices |
| `splunkbase-ta` | Splunkbase add-on documentation, default `props.conf`, or release notes | `Splunk_TA_paloalto` v9.x `default/props.conf`; `Splunk_TA_cisco_ise` README |
| `lantern` | A Splunk Lantern article on sizing, onboarding, or data-source best practices | Lantern "firewall sizing" guidance |
| `industry-report` | Published analyst report or community-curated benchmark (`.conf` talks, vendor benchmarks) | Gartner sizing notes; `.conf` "Sizing Splunk" presentations |
| `vendor-blog` | A primary-source vendor engineering blog with concrete numbers | CrowdStrike blog "How much data does Falcon ship?" |
| `rfc` | Protocol RFC (when the protocol fundamentally bounds frame size) | RFC 1157 (SNMP), Modbus TCP spec, BACnet/IP spec |

**Explicitly excluded** as primary citations:

- "Field SE experience" — not reproducible / auditable. Useful for cross-check
  but cannot stand alone.
- Vendor marketing pages — not concrete enough.
- Reddit / Stack Overflow threads without primary-source corroboration.

For `calibration: "pending"` sources the citation array may be empty; the UI
displays an explicit "calibration pending" badge so SEs know which numbers
are best-effort vs. vendor-cited.

## 4. Architecture overview

The current architecture is a single JS file (`ot-data-sources.js`) plus a
calculation engine inlined into `app.js`. v2 splits this into four files
plus a JSON Schema:

```
tools/data-sizing/
├── ot-data-sources.js            (v2 catalogue — 206 sources, new schema)
├── compute-functions.js          (NEW — named registry of pure compute functions)
├── app.js                        (rewritten — driver-aware engine + UI)
├── schemas/
│   └── data-source.schema.json   (NEW — JSON Schema 2020-12)
├── scripts/
│   ├── validate-catalogue.py     (NEW — CI gate: schema + citation validation)
│   ├── calibration-coverage.py   (NEW — coverage report by category)
│   └── migrate-v1-to-v2.js       (NEW — one-shot migrator; deleted after merge)
└── __tests__/
    ├── compute-functions.test.js (NEW — Node built-in `node --test`)
    └── catalogue-snapshot.json   (NEW — regression guard)
```

Three reasons to keep the JS filename `ot-data-sources.js` despite the
catalogue spanning IT/security/network/OT/protocols:

1. Avoids external-link breakage (existing bookmarks, docs references).
2. No build step needed — the file loads via `<script>` in `index.html`,
   matching the rest of the tool's no-toolchain architecture.
3. The CI validator extracts the array literal via a Node one-liner
   (`node -e "...; console.log(JSON.stringify(OT_DATA_SOURCES))"`) and pipes
   it into Python's `jsonschema` for validation — same approach used
   elsewhere in the repo (e.g. `non-technical-view.js`).

The README is updated to explicitly note that the catalogue is broader than
the legacy filename suggests.

## 5. Source schema (v2)

Each source object replaces the current `{eps_per_endpoint, bytes_per_event}`
or `{bytes_per_tag, default_tags, default_poll_sec}` shapes with a single
uniform schema. The schema is enforced by `schemas/data-source.schema.json`.

### 5.1 Endpoint-style example (Palo Alto NGFW, calibrated)

```javascript
{
  id: "fw_palo_alto_ngfw",
  name: "Palo Alto NGFW",
  category: "Security Sources",
  subcategory: "Firewalls",
  description: "Next-Gen Firewall traffic, threat, URL, DNS-Security, WildFire logs",
  vendor_examples: "PA-5450, PA-3200, PA-VM",
  protocol: "Syslog / Splunk_TA_paloalto API",
  ingest_method: "Splunk_TA_paloalto",
  splunk_sourcetype: "pan:traffic, pan:threat, pan:url, pan:system, pan:config",
  calibration: "calibrated",
  drivers: [
    { id: "throughput_gbps", label: "Sustained throughput",
      unit: "Gbps", type: "number",
      default: 1.0, min: 0.01, max: 100,
      profilePresets: { low: 0.3, typical: 1.0, high: 4.0 } },
    { id: "log_profile", label: "Log subscriptions enabled",
      unit: null, type: "enum",
      default: "traffic+threat",
      options: [
        { value: "traffic-only",                    label: "Traffic only" },
        { value: "traffic+threat",                  label: "Traffic + Threat" },
        { value: "traffic+threat+url",              label: "Traffic + Threat + URL" },
        { value: "traffic+threat+url+dns+wildfire", label: "Traffic + Threat + URL + DNS-Security + WildFire" }
      ] }
  ],
  compute: "fw_palo_alto_ngfw_v1",
  uncertainty: { low: 0.6, typical: 1.0, high: 1.8 },
  realism: {
    rawdata_compression_typical: 0.18,
    tsidx_overhead_typical:      0.40,
    filterable_fraction_typical: 0.20
  },
  citations: [
    { type: "vendor-sizing", url: "https://docs.paloaltonetworks.com/...",
      accessed: "2026-05-22", note: "PAN-OS 11 log-storage sizing" },
    { type: "splunkbase-ta", url: "https://splunkbase.splunk.com/app/491",
      accessed: "2026-05-22", note: "Splunk_TA_paloalto v9.x default props.conf" },
    { type: "lantern",       url: "https://lantern.splunk.com/...firewall-sizing",
      accessed: "2026-05-22" }
  ],
  related_uc_ids: ["1.1.1", "1.2.4", "1.6.7"]
}
```

### 5.2 Protocol-style example (Modbus TCP, calibrated)

```javascript
{
  id: "proto_modbus",
  name: "Modbus TCP / RTU",
  category: "Protocols",
  subcategory: "Industrial Polling",
  description: "Register/coil polling from PLCs, VFDs, meters, RTUs",
  vendor_examples: "Siemens S7, Allen-Bradley, Schneider, ABB, Wago, Beckhoff",
  protocol: "Modbus TCP / Modbus RTU",
  ingest_method: "Edge Hub / Cisco EI → HEC",
  splunk_sourcetype: "modbus:register, edge_hub:modbus",
  calibration: "calibrated",
  drivers: [
    { id: "tag_count", label: "Number of registers polled",
      unit: "tags", type: "number",
      default: 500, min: 1, max: 100000,
      profilePresets: { low: 100, typical: 500, high: 5000 } },
    { id: "poll_interval_sec", label: "Polling interval",
      unit: "seconds", type: "enum",
      default: 30,
      options: [
        { value: 1,   label: "1 s (control-loop)" },
        { value: 5,   label: "5 s (fast metrics)" },
        { value: 10,  label: "10 s" },
        { value: 30,  label: "30 s (typical historian)" },
        { value: 60,  label: "60 s (slow trending)" },
        { value: 300, label: "5 min (batch reporting)" }
      ] },
    { id: "deadband_ratio", label: "Value-change filter (deadband)",
      unit: "fraction", type: "number",
      default: 0.40, min: 0.0, max: 0.95,
      profilePresets: { low: 0.10, typical: 0.40, high: 0.80 },
      help: "Fraction of polls deduplicated at the gateway when register value didn't change." }
  ],
  compute: "proto_modbus_v1",
  uncertainty: { low: 0.7, typical: 1.0, high: 1.6 },
  realism: {
    rawdata_compression_typical: 0.10,
    tsidx_overhead_typical:      0.20,
    filterable_fraction_typical: 0.10
  },
  citations: [
    { type: "rfc",           url: "https://modbus.org/specs.php",
      accessed: "2026-05-22", note: "Modbus TCP frame size + register data format" },
    { type: "splunkbase-ta", url: "https://splunkbase.splunk.com/app/...",
      accessed: "2026-05-22", note: "Splunk Edge Hub Modbus add-on default emission shape" }
  ],
  related_uc_ids: ["14.1.8", "14.2.7", "14.3.32"]
}
```

### 5.3 Pending source example (mechanical port, no citations yet)

```javascript
{
  id: "ot_proprietary_dnp3_outstation",
  name: "DNP3 Outstation",
  category: "Protocols",
  subcategory: "Utility SCADA",
  calibration: "pending",
  drivers: [
    { id: "tag_count", label: "Number of DNP3 points",
      unit: "tags", type: "number", default: 100, min: 1, max: 100000,
      profilePresets: { low: 50, typical: 100, high: 1000 } },
    { id: "poll_interval_sec", label: "Polling interval",
      unit: "seconds", type: "enum", default: 60,
      options: [
        { value: 10,  label: "10 s" },
        { value: 60,  label: "60 s" },
        { value: 300, label: "5 min" }
      ] }
  ],
  compute: "generic_protocol_v1",
  uncertainty: { low: 0.5, typical: 1.0, high: 2.5 },
  realism: {
    rawdata_compression_typical: 0.15,
    tsidx_overhead_typical:      0.35,
    filterable_fraction_typical: 0.10
  },
  citations: []
}
```

### 5.4 Required vs optional fields

| Field | Required | Constraint |
|---|---|---|
| `id` | yes | `^[a-z0-9_]+$`, unique catalogue-wide |
| `name` | yes | non-empty string |
| `category`, `subcategory` | yes | non-empty strings |
| `description`, `vendor_examples`, `protocol`, `ingest_method`, `splunk_sourcetype` | optional | descriptive metadata |
| `calibration` | yes | `"calibrated"` \| `"pending"` |
| `drivers` | yes | array with ≥ 1 element matching the `driver` sub-schema |
| `compute` | yes | `^[a-z0-9_]+_v[0-9]+$`, must resolve in `compute-functions.js` |
| `uncertainty` | yes | object with `low`, `typical`, `high` (all numbers > 0) |
| `realism` | yes | object with `rawdata_compression_typical`, `tsidx_overhead_typical`, `filterable_fraction_typical` |
| `citations` | yes (array) | empty allowed when `calibration: "pending"`; ≥ 1 entry required when `calibration: "calibrated"` |
| `related_uc_ids` | optional | array of `"X.Y.Z"` UC IDs that must resolve in `catalog.json` |

The conditional citation rule is enforced by the JSON Schema `allOf` clause:

```json
{
  "if":   { "properties": { "calibration": { "const": "calibrated" } } },
  "then": { "properties": { "citations": { "type": "array", "minItems": 1 } } }
}
```

## 6. Compute function contract

Compute functions live in `compute-functions.js` as a named registry. Each
source's `compute` field is a string reference into this registry, suffixed
with a version number (`_v1`, `_v2`, …) so a formula can evolve without
breaking saved share URLs that depend on a specific output shape.

```javascript
const COMPUTE_FUNCTIONS = {
  // (driverValues, profile) -> { eps: Number, bytesPerEvent: Number }
  fw_palo_alto_ngfw_v1: function(d, profile) {
    const baseEpsPerGbps = 4500;
    const profileMultipliers = {
      "traffic-only":                    { eps: 0.70, bytesPerEvent: 1200 },
      "traffic+threat":                  { eps: 1.00, bytesPerEvent: 1800 },
      "traffic+threat+url":              { eps: 1.45, bytesPerEvent: 2100 },
      "traffic+threat+url+dns+wildfire": { eps: 2.10, bytesPerEvent: 2400 }
    };
    const m = profileMultipliers[d.log_profile] || profileMultipliers["traffic+threat"];
    return {
      eps:           d.throughput_gbps * baseEpsPerGbps * m.eps,
      bytesPerEvent: m.bytesPerEvent
    };
  },

  proto_modbus_v1: function(d, profile) {
    const rawEps     = d.tag_count / d.poll_interval_sec;
    const dedupedEps = rawEps * (1 - d.deadband_ratio);
    return { eps: dedupedEps, bytesPerEvent: 280 };
  },

  generic_protocol_v1: function(d, profile) {
    const dedup = d.deadband_ratio !== undefined ? (1 - d.deadband_ratio) : 0.7;
    return {
      eps:           (d.tag_count / d.poll_interval_sec) * dedup,
      bytesPerEvent: 350
    };
  },

  // Legacy fallbacks for sources still marked `calibration: "pending"`,
  // mechanically ported from v1's per-endpoint and per-tag models.
  endpoint_legacy_v1: function(d, profile) { /* ... */ },
  protocol_legacy_v1: function(d, profile) { /* ... */ }
};
```

### Contract rules

- **Pure functions.** Deterministic. No DOM, no network, no `Date.now()`,
  no `Math.random()`. The same `(driverValues, profile)` always produces the
  same `{eps, bytesPerEvent}`.
- **Output shape.** `eps` and `bytesPerEvent` both numeric, both `≥ 0`, both
  finite. Never `NaN` or `Infinity`.
- **Compression / filterable / dedup separation.** `compression`,
  `filterable_fraction`, and (for non-protocol sources) `deduplication` come
  from `source.realism`, **not** from `compute()`. This keeps the engine
  uniform: all post-EPS / post-bytes adjustments happen in one place.
- **Profile forwarding.** `profile` is passed for the rare source whose
  formula changes shape by profile. Most sources rely on
  `source.uncertainty[profile]` as a flat multiplier applied by the engine
  after `compute()` returns.
- **Versioning.** A formula change ships as `_vN+1`; the old `_vN` stays in
  the file (with a deprecation comment) so saved share URLs that explicitly
  pin a version continue to compute. Catalogue sources point at the latest
  `_vN`.

## 7. Calculation engine

### 7.1 Per-source pipeline

For each selected source instance:

```
1. Read driver values from UI (or profile defaults).
2. Call source.compute(driverValues, profile)
       → { eps, bytesPerEvent }
3. Apply uncertainty multiplier:
       eps = compute.eps × source.uncertainty[profile]
4. Apply filtering allowance (SC4S / Edge Processor / nullQueue):
       effectiveEps = eps × (1 - source.realism.filterable_fraction_typical)
5. Per-day volume:
       dailyEvents = effectiveEps × 86 400
       dailyRawGB  = (dailyEvents × bytesPerEvent) / 1e9
```

Two distinct "less data than naïve poll math would suggest" reductions live
in different places:

- **Filtering** (`filterable_fraction`) is applied uniformly in step 4 for
  **every** source type. It represents drops at SC4S / Edge Processor /
  `nullQueue` — a deployment posture, not a per-source tunable.
- **Deduplication** (deadband, value-change filtering) is applied **inside
  `compute()`** for protocol sources only, because it is operator-tunable
  per source (the `deadband_ratio` driver on `proto_modbus`, `proto_opcua`,
  etc.). For endpoint sources there is no equivalent — events are
  intrinsically discrete.

The two reductions stack multiplicatively for protocols. For Modbus with
the example values: `rawEps × (1 − 0.40 deadband) × (1 − 0.10 filterable)`
= `rawEps × 0.54`.

### 7.2 Two-component on-disk model

The single `0.5` constant is replaced with:

```
storage_per_day_per_indexer = dailyRawGB × (rawdata_compression + tsidx_overhead)
```

Default values (used when a `pending` source carries no per-type override):

| Component | Default | Typical range | Notes |
|---|---|---|---|
| `rawdata_compression_typical` | `0.15` | `0.05`–`0.30` | Compressed-raw-bucket fraction of raw. Highly repetitive → 0.05; binary / pre-compressed → 0.30 |
| `tsidx_overhead_typical` | `0.35` | `0.10`–`0.50` | TSIDX fraction of raw. Field-rich JSON / high-cardinality → larger |
| `filterable_fraction_typical` | `0.15` | `0`–`0.80` | Droppable at SC4S / EP / `nullQueue` in typical deployments |

The default `0.15 + 0.35 = 0.50` preserves rough numeric parity with the v1
catalogue, so unmigrated sources don't suddenly halve or double on launch.

### 7.3 Cluster math

Two new user-set knobs on the summary panel:

| Knob | Default | Range | Meaning |
|---|---|---|---|
| Replication Factor (RF) | `2` | `1`–`5` | Indexer copies of each compressed-raw bucket |
| Search Factor (SF) | `2` | `1`–`5` (≤ RF) | Indexer copies of each tsidx |
| SmartStore | off | toggle | When on, RF collapses to `1` for compressed raw (single S3 copy); SF still applies to local tsidx caches |
| Indexer count | `3` | `1`–`100` | Divisor for "per-indexer" storage line |

Cluster-wide storage per day:

```
clusterRawGB_perDay    = totalDailyRawGB × rawdata_compression × (SmartStore ? 1 : RF)
clusterTsidxGB_perDay  = totalDailyRawGB × tsidx_overhead     × SF
clusterStorageGB_perDay = clusterRawGB_perDay + clusterTsidxGB_perDay
clusterStorageGB_total  = clusterStorageGB_perDay × retentionDays
perIndexerGB_perDay     = clusterStorageGB_perDay / indexerCount
```

The summary panel breaks raw, tsidx, total, and per-indexer onto separate
lines (see § 8.4).

### 7.4 Burst vs headroom

The current `burstFactor` multiplies BOTH daily GB and peak EPS — but these
should not move together. v2 splits them:

| Concept | What it is | What it sizes |
|---|---|---|
| Average daily ingest | `totalDailyRawGB` (no multiplier) | License (sustained ingest) |
| Average EPS | `totalEffectiveEps` (no multiplier) | Some plans cap EPS |
| Diurnal peak EPS | `averageEps × burstFactor` | Indexer count, queue depth, pipeline tuning |
| Peak EPS with headroom | `diurnalPeakEps × headroomFactor` | Capacity-plan "what can the cluster sustain at worst case" |

UI knobs:

- **Burst factor (diurnal)** — `1.0 / 1.3 / 1.5 / 2.0 / 3.0 / 5.0`. Default
  `1.5`. Common shapes: 1.3 (steady OT/IoT), 2.0 (typical IT business hours),
  3.0+ (incident-driven security workloads).
- **Headroom factor** — `1.0 / 1.25 / 1.5`. Default `1.25`. Pure safety
  margin on top of diurnal peak for capacity planning.

License sizing stays on **average daily ingest** (ingest-pricing is sustained;
burst doesn't move the license meter).

### 7.5 License tier table

The current `SPLUNK_LICENSE_TIERS` table runs 1 GB → 2 TB. v2 makes two edits:

1. Adds 0.5 GB/day and 2 GB/day tiers (small pilots are common; 1 GB is often
   too high a starting point).
2. Updates `typical_use` strings to be platform-neutral (current strings lean
   OT-centric; the catalogue spans IT, security, and OT).

The complete table:

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

## 8. UI & UX

### 8.1 Per-source card (replaces the table-row layout)

Each selected source becomes a **card** with dynamic driver inputs rendered
from `source.drivers`. The card replaces the current per-row controls in the
"Selected Sources" table.

```
┌─────────────────────────────────────────────────────────────────┐
│ Palo Alto NGFW                          [Calibrated · 3 src]  ✕ │
│ Security Sources › Firewalls                                    │
│                                                                 │
│  Sustained throughput  [   1.0  ] Gbps    (typical: 1.0)        │
│  Log subscriptions     [Traffic + Threat                  ▼]    │
│                                                                 │
│  → Estimate: 4,500 EPS  ·  1.8 KB/event  ·  0.7 GB/day          │
│                                                                 │
│  ▸ Why these numbers? (3 citations · formula · realism)         │
└─────────────────────────────────────────────────────────────────┘
```

For a `pending` source the badge changes to a yellow "⚠ Calibration pending"
indicator and the disclosure section calls out the absence of citations.

### 8.2 Driver rendering rules

| `driver.type` | Renders as |
|---|---|
| `number` | numeric input with optional `unit` suffix, `min` / `max` HTML5 validation, profile-preset hint (`"(typical: 1.0)"`) |
| `enum` | dropdown when `options.length > 3`; segmented radio when `options.length <= 3`; optional `unit` suffix |

Per-driver addons:

- `help` → tooltip on the label
- `profilePresets` → drives the hint text **and** re-seeds the value when the
  global profile toggle changes
- A small "modified" indicator (dot adjacent to the field label) appears when
  the user has edited a driver away from its profile preset

### 8.3 "Why these numbers?" disclosure

Collapsible per source. When expanded for a calibrated source:

```
▾ Why these numbers?

  Formula (compute: fw_palo_alto_ngfw_v1):
    eps = throughput_gbps × 4,500 × log_profile_multiplier
    For "Traffic + Threat":  multiplier = 1.0,  bytesPerEvent = 1.8 KB

  Calibration sources:
   1. Vendor sizing — PAN-OS 11 log-storage sizing
      docs.paloaltonetworks.com/.../log-storage      (accessed 2026-05-22)
   2. Splunkbase TA — Splunk_TA_paloalto v9.x default props.conf
      splunkbase.splunk.com/app/491                  (accessed 2026-05-22)
   3. Splunk Lantern — Firewall sizing guidance
      lantern.splunk.com/.../firewall-sizing         (accessed 2026-05-22)

  Realism factors applied:
    Compression on-disk:  rawdata 18% + tsidx 40% = 58% of raw
    Filtering at ingest:  ~20% of events droppable at SC4S / Edge Processor
```

For pending sources the section opens with an explicit "⚠ Calibration
pending — these numbers are best-effort port from the v1 catalogue. No
vendor citations have been gathered yet." block, followed by the formula
and realism defaults.

### 8.4 Sizing-assumptions panel

Replaces the current `Profile / Burst / Retention` controls with a
restructured panel that exposes the new knobs:

```
Sizing Assumptions
─────────────────────────────────────
Profile:           [ Typical              ▼ ]
Burst factor:      [ ×1.5  (typical IT)   ▼ ]  ⓘ diurnal peak / avg
Headroom:          [ ×1.25 (capacity-safe)▼ ]  ⓘ planning margin
Retention:         [ 30 days              ▼ ]

── Cluster ──
Replication F:     [ 2  ▼ ]
Search F:          [ 2  ▼ ]
SmartStore:        [ ☐ ]    ⓘ Splunk Cloud / S3-backed
Indexer count:     [ 3  ]
```

### 8.5 Summary results layout

The current three boxes (raw / compressed / peak) become three structured
sections that surface the math honestly:

```
Ingest
  Sources selected:                12
  Effective EPS (post-filter):     4,250    raw pre-filter: 5,100
  Daily events:                    367 M
  Daily raw ingest:                23.4 GB/day
  Diurnal peak EPS:                6,375    (burst ×1.5)
  Peak EPS w/ headroom:            7,969    (×1.25)

License
  Recommended tier:                25 GB/day  (Medium)
  Utilization:                     94 % of recommended tier
  Headroom to next tier:           50 %  (≈ 12 GB/day growth room)

Storage (cluster-wide · RF=2 · SF=2 · SmartStore=off)
  Compressed raw                   3.5 GB/day   →    105 GB / 30 d
  TSIDX                           16.4 GB/day   →    491 GB / 30 d
  ─────────────────────────────────────────────────────────────────
  Total cluster-wide              19.9 GB/day   →    596 GB / 30 d
  Per indexer (3 idx)              6.6 GB/day   →    199 GB / 30 d
```

The existing breakdown-by-category and breakdown-by-ingest-method tables
remain below this, populated from the new engine.

### 8.6 Catalogue browser

The catalogue panel header gets a coverage stat and a calibration filter:

```
Data Sources Catalogue
──────────────────────────────────────
Calibration:  ██▒▒▒▒▒▒▒▒  25 / 206 (12 %)

Filter:  [ ☑ Calibrated ]  [ ☑ Pending ]
Search:  [______________________________]

Security Sources                              (45)
  Palo Alto NGFW                       [Calib] ＋
  Fortinet FortiGate                   [Calib] ＋
  Cisco Secure FW                      [Calib] ＋
  CrowdStrike Falcon Insight           [Calib] ＋
  ...
  F5 BIG-IP ASM                        [Calib] ＋
  Check Point R81                      [Pend]  ＋
  ...
```

The filter checkboxes let an SE producing a customer-facing report opt out
of using uncalibrated numbers.

### 8.7 Methodology pane

Collapsible at the bottom of the summary panel:

```
▸ Methodology

   Compression model:  Two-component per source (rawdata + tsidx)
                       Defaults: 15 % + 35 % = 50 % on-disk
                       Calibrated sources override per data type

   Cluster math:       cluster_raw   = ingest × rawdata × RF
                       cluster_tsidx = ingest × tsidx   × SF
                       (SmartStore → RF=1 for raw, tsidx unchanged)

   License pricing:    Ingest-based (Splunk Cloud / Enterprise)
                       Recommendation rounds UP to next standard tier

   Realism inputs:     Per-source `filterable_fraction` accounts for
                       SC4S / Edge Processor / props.conf nullQueue
                       Protocol sources include deadband (value-change
                       filtering) as a user-editable driver

   Not included:       Workload Pricing / SVC translation
                       Search-tier sizing (SHs, KV store, scheduler)
                       Replicated DM-acceleration overhead
                       Indexer hardware sizing (CPU / IOPS)
                       Forwarder fan-out CPU cost
```

### 8.8 Other UX details

- **Theme.** Existing dark theme; no visual restyle in this PR.
- **Empty state.** Existing friendly empty state preserved.
- **CSV export.** Extended to include driver values + computed EPS/GB per
  source (currently exports only source name + total).
- **Share URLs.** Extended to encode driver values:
  `?sources=fw_pan:throughput_gbps=2.0,log_profile=traffic+threat+url|proto_modbus:tag_count=2000,poll_interval_sec=10`.
  v1 URLs (source IDs only) continue to work, seeding defaults.
- **Inventory hand-off.** `?sources=...` from the Inventory page continues
  to work; driver inputs render at defaults and the user tunes from there.
- **Mobile layout.** Explicitly deferred (out of scope per § 2).

## 9. Calibration tiers

Two values for `source.calibration`, both surfaced in the UI:

| Value | Meaning | Citation requirement | UI surface |
|---|---|---|---|
| `calibrated` | Vendor-cited drivers and numbers; reviewed against ≥ 2 sources from the approved mix | **Required:** `citations.length >= 1` | Green badge "Calibrated · N sources" with click-to-expand citation list |
| `pending` | Mechanical port from v1; numbers are best-guess | None required (empty array OK) | Yellow badge "⚠ Calibration pending — numbers approximate" |

CI enforces the citation rule via the JSON Schema conditional clause shown
in § 5.4.

### 9.1 Calibration coverage at launch

The v2 PR ships with the following per-category coverage (counts derived
from the actual catalogue and the Tier-1+Tier-2 roster in §9.2):

```
Data Sizing catalogue calibration coverage (at v2 ship)
=======================================================
  calibrated:  25 / 206 (12.1%)
  pending:    181 / 206 (87.9%)

By category:
  Security Sources                         8 / 21   (38.1%)
  IT Systems & Hardware                    8 / 34   (23.5%)
  OT System Sources                        0 / 13    (0.0%)
  Network Sources                          4 / 14   (28.6%)
  OT Hardware & Sensors                    0 / 12    (0.0%)
  Protocols                                5 / 28   (17.9%)
  Business & Compliance                    0 /  7    (0.0%)
  Cisco Products                           0 / 29    (0.0%)   *
  OT Vendor Systems                        0 / 48    (0.0%)
```

`*` Cisco Products is intentionally 0 at v2 launch — the catalogue has
duplicate entries (e.g. `cisco_secure_firewall` overlaps `sec_fw_cisco`,
`cisco_ise` overlaps `sec_ise`, `cisco_meraki_network` overlaps
`net_meraki`). Calibrating both copies would be misleading; the duplicate
resolution is handled as a follow-up catalogue-cleanup PR (see §16).

The coverage % is **observational, not gated** — it appears in CI logs and
in the README, but the PR does not fail when coverage drops. The point is
to make calibration progress visible across follow-up PRs.

### 9.2 Tier-1 + Tier-2 calibration roster (25 sources at v2 launch)

Uses **actual existing catalogue IDs**. Tier-1 vendors not currently
modelled as their own source (CrowdStrike, SentinelOne, Microsoft Defender
for Endpoint, F5 ASM) are calibrated via the generic capability source
(`sec_edr`, `dsa_sec_waf`) for v2; vendor-specific sources can be added in
follow-up PRs once a citation set is gathered.

| # | Catalogue ID | Name | Category | Citation target |
|---|---|---|---|---|
| 1 | `sec_ngfw_paloalto` | Palo Alto NGFW | Security Sources | vendor docs + Splunkbase TA + Lantern |
| 2 | `sec_ngfw_fortinet` | Fortinet FortiGate | Security Sources | vendor docs + Splunkbase TA |
| 3 | `sec_fw_cisco` | Cisco Secure Firewall (FTD / ASA) | Security Sources | vendor docs + Splunkbase TA |
| 4 | `sec_edr` | Endpoint Detection & Response (generic) | Security Sources | CrowdStrike + SentinelOne + Defender vendor docs (cross-vendor average) |
| 5 | `sec_ids_cybervision` | Cisco Cyber Vision | Security Sources | vendor docs + Splunkbase TA |
| 6 | `sec_ise` | Cisco ISE | Security Sources | vendor docs + Splunkbase TA |
| 7 | `dsa_sec_waf` | WAF (generic — F5 ASM / ModSec / AWS WAF / Cloudflare) | Security Sources | F5 + ModSec + Cloudflare vendor docs |
| 8 | `dsa_sec_ips_ids` | IPS/IDS (Network) | Security Sources | Suricata + Snort + Cisco FTD IPS docs |
| 9 | `dsa_it_cloud_iaas` | Cloud IaaS (AWS CloudTrail + Azure Activity + GCP Audit) | IT Systems & Hardware | three vendor sizing PDFs (cross-cloud average) |
| 10 | `dsa_it_office365` | Office 365 / Microsoft 365 | IT Systems & Hardware | Microsoft Unified Audit Log docs + Splunkbase TA |
| 11 | `dsa_it_sso` | SSO / IAM (Okta + Ping + Azure AD) | IT Systems & Hardware | three vendor docs (cross-vendor average) |
| 12 | `it_windows` | Windows Server (Security / System logs) | IT Systems & Hardware | Splunkbase Windows TA + Lantern |
| 13 | `it_windows_dc` | Windows Domain Controller | IT Systems & Hardware | Splunkbase Windows TA + Lantern |
| 14 | `it_linux` | Linux Server (syslog / auth / auditd) | IT Systems & Hardware | Splunkbase nix TA + Lantern + SC4S reference configs |
| 15 | `dsa_it_database` | Database Instances (generic) | IT Systems & Hardware | DB audit vendor docs (cross-DB average) |
| 16 | `dsa_it_webserver` | Web Servers (Apache + Nginx + IIS) | IT Systems & Hardware | Apache combined-log spec + nginx default + IIS default |
| 17 | `net_netflow` | NetFlow / IPFIX / sFlow | Network Sources | vendor docs + Splunkbase TA |
| 18 | `net_meraki` | Cisco Meraki (Cloud Networking) | Network Sources | vendor docs + Splunkbase TA |
| 19 | `dsa_net_loadbalancer` | Load Balancers / ADC (F5 + Citrix + AVI) | Network Sources | three vendor docs |
| 20 | `dsa_net_vpn` | VPN Concentrators / Remote Access | Network Sources | vendor docs (Cisco AnyConnect, OpenVPN, Pulse) |
| 21 | `proto_opcua` | OPC UA | Protocols | vendor docs (Unified Automation) + Edge Hub TA |
| 22 | `proto_modbus` | Modbus TCP / RTU | Protocols | spec + Edge Hub TA |
| 23 | `proto_mqtt` | MQTT | Protocols | spec + Edge Hub TA |
| 24 | `proto_bacnet` | BACnet/IP | Protocols | spec + Edge Hub TA |
| 25 | `proto_snmp` | SNMP (v2c / v3) | Protocols | spec + SC4SNMP TA |

Each gets a dedicated compute function in `compute-functions.js` named
`<source_id>_v1`.

## 10. JSON Schema

The schema lives at `tools/data-sizing/schemas/data-source.schema.json`,
JSON Schema draft 2020-12, mirroring the repo's `schemas/uc.schema.json`
convention (`additionalProperties: false`, conditional rules via `allOf`).

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/.../tools/data-sizing/schemas/data-source.schema.json",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "name", "category", "subcategory", "calibration",
               "drivers", "compute", "uncertainty", "realism"],
  "properties": {
    "id":              { "type": "string", "pattern": "^[a-z0-9_]+$" },
    "name":            { "type": "string", "minLength": 1 },
    "category":        { "type": "string" },
    "subcategory":     { "type": "string" },
    "description":     { "type": "string" },
    "vendor_examples": { "type": "string" },
    "protocol":        { "type": "string" },
    "ingest_method":   { "type": "string" },
    "splunk_sourcetype": { "type": "string" },
    "calibration":     { "enum": ["calibrated", "pending"] },
    "drivers":         { "type": "array", "minItems": 1, "items": { "$ref": "#/$defs/driver" } },
    "compute":         { "type": "string", "pattern": "^[a-z0-9_]+_v[0-9]+$" },
    "uncertainty": {
      "type": "object",
      "required": ["low", "typical", "high"],
      "additionalProperties": false,
      "properties": {
        "low":     { "type": "number", "exclusiveMinimum": 0 },
        "typical": { "type": "number", "exclusiveMinimum": 0 },
        "high":    { "type": "number", "exclusiveMinimum": 0 }
      }
    },
    "realism": {
      "type": "object",
      "required": ["rawdata_compression_typical",
                   "tsidx_overhead_typical",
                   "filterable_fraction_typical"],
      "additionalProperties": false,
      "properties": {
        "rawdata_compression_typical": { "type": "number", "minimum": 0.01, "maximum": 1.0 },
        "tsidx_overhead_typical":      { "type": "number", "minimum": 0.01, "maximum": 1.0 },
        "filterable_fraction_typical": { "type": "number", "minimum": 0.0,  "maximum": 0.99 }
      }
    },
    "citations":      { "type": "array", "items": { "$ref": "#/$defs/citation" } },
    "related_uc_ids": { "type": "array", "items": { "type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$" } }
  },
  "allOf": [
    {
      "if":   { "properties": { "calibration": { "const": "calibrated" } } },
      "then": { "properties": { "citations": { "type": "array", "minItems": 1 } } }
    }
  ],
  "$defs": {
    "driver": {
      "type": "object",
      "required": ["id", "label", "type", "default"],
      "additionalProperties": false,
      "properties": {
        "id":             { "type": "string", "pattern": "^[a-z0-9_]+$" },
        "label":          { "type": "string", "minLength": 1 },
        "unit":           { "type": ["string", "null"] },
        "type":           { "enum": ["number", "enum"] },
        "default":        {},
        "min":            { "type": "number" },
        "max":            { "type": "number" },
        "help":           { "type": "string" },
        "profilePresets": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "low":     {},
            "typical": {},
            "high":    {}
          }
        },
        "options": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["value", "label"],
            "additionalProperties": false,
            "properties": {
              "value": {},
              "label": { "type": "string", "minLength": 1 }
            }
          }
        }
      }
    },
    "citation": {
      "type": "object",
      "required": ["type", "url", "accessed"],
      "additionalProperties": false,
      "properties": {
        "type":     { "enum": ["vendor-sizing", "splunkbase-ta", "lantern",
                                "industry-report", "vendor-blog", "rfc"] },
        "url":      { "type": "string", "format": "uri" },
        "accessed": { "type": "string", "format": "date" },
        "note":     { "type": "string" }
      }
    }
  }
}
```

## 11. CI integration

A new GitHub Actions job is added to `.github/workflows/validate.yml`:

```yaml
data-sizing-catalogue:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with: { node-version: '20' }
    - uses: actions/setup-python@v5
      with: { python-version: '3.12' }
    - run: pip install jsonschema
    - name: Validate catalogue against schema
      run: python3 tools/data-sizing/scripts/validate-catalogue.py
    - name: Calibration coverage report (advisory)
      run: python3 tools/data-sizing/scripts/calibration-coverage.py
    - name: Compute function unit tests
      run: node --test tools/data-sizing/__tests__/
```

`validate-catalogue.py` extracts the catalogue array via a Node one-liner,
runs `jsonschema.validate(...)` on each source, asserts every `compute`
reference resolves in `compute-functions.js`, asserts all `id` values are
unique, and asserts every `related_uc_ids` entry resolves in `catalog.json`.

`calibration-coverage.py` emits the per-category report shown in § 9.1. It
exits `0` always; `--check N` mode can later enforce a minimum coverage %
once the user wants to raise the bar.

## 12. Migration plan for the 206 v1 sources

Single PR, three phases, all merged together:

### 12.1 Phase A — Mechanical port

`scripts/migrate-v1-to-v2.js` reads the current `ot-data-sources.js` and
emits a new v2-shaped catalogue:

- **Endpoint sources** → drivers `[{id: "endpoints", default: 1, ...}]`,
  `compute: "endpoint_legacy_v1"`, `calibration: "pending"`.
- **Protocol sources** → drivers
  `[{id: "tag_count", ...}, {id: "poll_interval_sec", ...}, {id: "deadband_ratio", default: 0.0, ...}]`,
  `compute: "protocol_legacy_v1"`, `calibration: "pending"`.
- `realism` defaults: `rawdata=0.15, tsidx=0.35, filterable=0.15` (preserves
  rough numeric parity with v1's `0.5` total compression assumption).
- `uncertainty`: `low=0.5, typical=1.0, high=2.0` (intentionally wide for
  uncalibrated sources).
- `citations`: `[]`.

The two `*_legacy_v1` compute functions in `compute-functions.js` re-implement
the existing v1 math so output parity holds for uncalibrated sources.

### 12.2 Phase B — Tier-1 + Tier-2 hand-calibration (25 sources)

Replace the auto-generated entries for the 25 priority sources (§ 9.2) with
hand-crafted calibrated versions, adding:

- Tightened drivers (sometimes more, sometimes more constrained than the
  mechanical port).
- Custom compute function in `compute-functions.js`, named `<source_id>_v1`.
- ≥ 1 citation per source, drawn from the approved source mix (§ 3).
- Tightened uncertainty band (typically `low=0.6–0.7, typical=1.0, high=1.5–1.8`).
- Per-source `realism` overrides where the data type warrants them.

### 12.3 Phase C — Catalogue cleanup

- Remove `scripts/migrate-v1-to-v2.js` (one-shot; not needed after merge).
- Update `tools/data-sizing/README.md` with the v2 architecture overview,
  the citation policy, the calibration coverage report, and a brief
  methodology section.
- Update `docs/inventory-and-sizing.md` to reflect the new UI and the new
  math (storage breakouts, RF/SF knobs, SmartStore toggle).

## 13. Testing strategy

### 13.1 Compute function unit tests

`__tests__/compute-functions.test.js`, runs under `node --test` (no extra
deps; matches the repo's minimal-tooling pattern):

- One `describe()` block per named function in `compute-functions.js`.
- For each: known-good inputs → known-good outputs (the numbers documented
  in the source's citation set). Three tests minimum per function: typical
  case, edge-low (zero / minimum drivers), edge-high (maximum drivers).
- All `enum` driver options exercised at least once.
- Pure-function discipline asserted by importing the function from a module
  that throws on any DOM / network / `Date.now()` / `Math.random()` access.

### 13.2 Catalogue snapshot test

`__tests__/catalogue-snapshot.json` plus a small test file. For each source,
given **default driver values + "typical" profile**, the engine produces an
expected `{eps, bytesPerEvent}` tuple. The snapshot freezes the current
output across all 206 sources. CI catches unintended drift; intentional
updates require explicitly regenerating the snapshot in the same PR as the
calibration change.

### 13.3 Schema validation test

Covered by `validate-catalogue.py` in CI (§ 11). Fails the PR on any
malformed source, missing citation on a calibrated source, unknown
`compute` reference, duplicate `id`, or unresolved `related_uc_ids`.

### 13.4 Browser smoke checklist

Manual, documented in `README.md`:

1. Open `index.html` directly in a browser (no HTTP server needed).
2. Add "Palo Alto NGFW" → set throughput to `1.0` → confirm ~4,500 EPS and
   ~0.7 GB/day in the per-source card.
3. Toggle SmartStore → confirm RF drops to 1 in the storage breakdown.
4. Click "Why these numbers?" on a calibrated source → confirm 3 citations
   render with clickable URLs.
5. Click "Why these numbers?" on a pending source → confirm "no citations
   yet" message renders.
6. Profile dropdown → switch low/typical/high → confirm driver presets
   update and the uncertainty multiplier is applied (estimate scales).
7. Copy share URL → paste in new tab → confirm the same scenario reproduces.

## 14. Release coordination

Per the workspace rules in [`.cursor/rules/`](../../../.cursor/rules/):

- **`versioning.mdc`.** The PR bumps `VERSION` + adds a `CHANGELOG.md` top
  entry + adds an `index.html` release-note entry. The version number itself
  is the user's call (likely a minor bump given the feature scope).
- **`non-technical-sync.mdc`.** No update — the data sizing tool is not a
  UC category, and the catalogue does not feed `non-technical-view.js`.
- **`docs-uc-map-sync.mdc`.** No update — no new docs created that map to
  specific UCs.
- **`docs/inventory-and-sizing.md`.** Updated to document the v2 UI and
  methodology (Phase C of § 12).

## 15. Rollback plan

- Single-commit revert: `git revert <merge-commit>` restores v1 catalogue
  and engine.
- No data migration; no persistent state outside share URLs.
- v2 share URLs gracefully degrade to "source not recognized" if pasted into
  a v1 instance (preferable to silent miscalculation).

## 16. Known catalogue-shape issues (deferred to follow-up PRs)

During spec development, several catalogue-content issues surfaced that are
intentionally **out of scope** for this v2 PR (which is an engine + schema
refactor) but which limit the realism of the tool until they are addressed
in separate catalogue-cleanup PRs.

### 16.1 Duplicate sources across capability vs vendor namespaces

The catalogue carries duplicate entries for several physical things, modelled
once under the capability namespace (`sec_*`, `net_*`) and once under the
vendor namespace (`cisco_*`). Known duplicates:

| Capability source | Vendor source | Same thing? |
|---|---|---|
| `sec_fw_cisco` | `cisco_secure_firewall` | Yes — both model FTD/ASA |
| `sec_ise` | `cisco_ise` | Yes |
| `sec_ids_cybervision` | `cisco_cyber_vision` | Yes |
| `net_meraki` | `cisco_meraki_network` | Yes |
| `proto_modbus` | `ot_plc_modbus` | Yes — protocol vs hardware speaking the protocol |
| `proto_opcua` | `ot_plc_opcua` | Yes |
| `proto_mqtt` | `ot_mqtt` | Yes |
| `proto_bacnet` | `ot_bacnet` | Yes |
| `proto_snmp` | `dsa_net_snmp_mgmt` | Partial overlap |

For v2 the capability source is calibrated; the vendor / hardware duplicate
stays `pending`. The cleanup PR following v2 must decide per duplicate
whether to merge (delete one), differentiate (give them distinct semantics
in the description), or cross-reference (keep both but note in the
description that they overlap).

### 16.2 Bundled sources that conflate distinct products

Several sources bundle multiple distinct vendor products into a single
catalogue entry, defeating any attempt at vendor-specific calibration:

| Source | What it bundles |
|---|---|
| `dsa_it_cloud_iaas` | AWS CloudTrail + Azure Activity + GCP Audit (three completely different data shapes) |
| `dsa_it_sso` | Okta + Ping + Azure AD (three different audit-log shapes) |
| `dsa_sec_waf` | F5 ASM + ModSecurity + AWS WAF + Cloudflare (four shapes) |
| `dsa_net_loadbalancer` | F5 + Citrix + AVI |

For v2 the bundle is calibrated as a cross-vendor average (with explicit
note in the citation set). The cleanup PR following v2 should consider
unbundling — at least the highest-volume IaaS bundle (split AWS, Azure,
GCP into three distinct sources) — since SE sizing calls usually focus on
one cloud, not all three.

### 16.3 Missing vendor-specific sources for major Tier-1 EDR brands

The catalogue has `sec_edr` (generic) but no entries for CrowdStrike
Falcon Insight, SentinelOne Singularity, or Microsoft Defender for
Endpoint as distinct sources. v2 calibrates the generic with a
cross-vendor average; the cleanup PR following v2 should add the three
brand-specific sources because their event volumes diverge significantly
(Falcon emits substantially less per endpoint than Defender's E5 telemetry).

### 16.4 No source for syslog as a transport vs syslog as a sourcetype

Generic syslog appears only implicitly (via `it_linux`). There is no
`infra_syslog_generic` source for "anything talking syslog that isn't a
firewall, Windows DC, or known vendor product". The cleanup PR should add
one, calibrated against SC4S reference configs.

These four issues are **content debt**, not engine debt. The v2 PR can ship
without resolving any of them; the schema and engine are correct, the
catalogue inventory just lags. Each gets a dedicated follow-up PR after v2.

## 17. Open questions

- Should the calibration coverage % be a CI gate at some threshold (say,
  ≥ 50 %) for v3, or stay observational indefinitely? Recommendation: leave
  observational until coverage naturally reaches 50 %, then gate at 40 %
  to prevent regression.
- Should compute function versioning (`_v1`, `_v2`) be exposed in the share
  URL, so a saved customer scenario stays numerically stable when a formula
  is updated? Recommendation: yes, but as an explicit opt-in (`&pin=v1`),
  not by default — most users want the latest math when they re-open a URL.
- For the long-tail recalibration follow-up PRs, should a batch of
  recalibrations ship per category (one PR for all of "Cisco Products"), or
  one per source? Recommendation: per category, to keep review surface
  manageable and to let the calibration-coverage stat move in visible
  increments.

## 18. Future work (out of scope for this spec)

- Workload Pricing / SVC translation (separate PR; the ingest math from this
  PR feeds it directly).
- Search-tier sizing (SHs, KV store, scheduler concurrency).
- Indexer hardware sizing (CPU, IOPS, RAM per indexer).
- Forwarder fan-out CPU cost model.
- JSON import (round-trip from CSV export).
- Side-by-side scenario compare (`?compare=scenario1|scenario2`).
- Mobile-responsive layout.
- Auto-refresh of Splunkbase TA metadata via the Splunkbase API (would
  require server-side scraping; conflicts with the "no toolchain" architecture).
