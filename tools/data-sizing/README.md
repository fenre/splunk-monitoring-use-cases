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
   node --test tools/data-sizing/__tests__/*.test.js
   ```
7. Commit.

## CI

`.github/workflows/validate.yml` runs:

- `validate-catalogue.py` (gating) — schema + compute references + UC IDs + unique IDs.
- `node --test` (gating) — compute-function unit tests + snapshot drift guard.
- `calibration-coverage.py` (advisory) — coverage report.

## Branding

The page header shows "Data Sizing Assessment — Community Reference"
and is styled with the same design tokens as the main catalogue. There
is no claim of an official Cisco product.
