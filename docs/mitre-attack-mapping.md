# MITRE ATT&CK Mapping

Central reference for how the catalogue encodes MITRE ATT&CK coverage.

Audience: detection engineers building SOC coverage matrices, threat
hunters scoping campaigns, security architects pitching ATT&CK-aligned
roadmaps, anyone integrating the catalogue into a coverage dashboard.

For the visual coverage map, use the **MITRE Coverage Map** modal in
the [Site User Guide](site-user-guide.md). For the API endpoints, use
the [API Docs page](api-docs-guide.md).

## Coverage at a glance

The catalogue tags use cases with **MITRE ATT&CK techniques** in the
`mitreAttack` field. Tactics are derived through the
technique-to-tactic mapping in [`mitre_techniques.json`](../mitre_techniques.json).

| Metric | Value (representative; live numbers in `dist/metrics.json`) |
|---|---|
| Total UCs in catalogue | ~7,300 |
| UCs with at least one MITRE technique | ~2,600 |
| Unique techniques mapped | ~428 |
| Unique tactics derived | All 14 enterprise + 12 ICS where applicable |
| MITRE coverage matrix | [`api/v1/mitre/coverage.json`](api-docs-guide.md#mitre--d3fend) |

The catalogue's MITRE coverage skews to detection-engineering domains
(cat-9 Identity & Access, cat-10 Endpoint, cat-17 Network Security,
cat-7 Cloud Workloads). It also covers **ICS ATT&CK** (T0800-series)
in cat-11 (OT/Industrial Monitoring).

## How MITRE is encoded on a UC

In the per-UC sidecar (`content/cat-NN-*/UC-X.Y.Z.json`):

```json
{
  "id": "9.6.4",
  "title": "Brute force against AD over RDP",
  "mitreAttack": [
    "T1110.003",
    "T1078"
  ]
}
```

Rules:

- The field is an **array of technique strings**.
- Strings are **MITRE technique IDs**: `T1110`, `T1110.003`, `T0800`
  (ICS), or `S0001` (software, rare).
- Sub-techniques are written as `T<parent>.<NNN>` (e.g. `T1078.004`).
- Tactics are **never** authored directly — they're derived at build
  time from the technique → tactic mapping.
- A UC can carry multiple techniques. There is no minimum or maximum.

The schema reference is in
[`schemas/uc.schema.json`](../schemas/uc.schema.json) and the field
contract is in [Use Case Field Reference](use-case-fields.md).

## How tactics are derived

[`mitre_techniques.json`](../mitre_techniques.json) is the canonical
technique → tactic mapping. Each entry:

```json
"T0800": {
  "name": "Activate Firmware Update Mode",
  "tactics": ["inhibit-response-function"]
}
```

The build (`tools/build/enrichment.py`) joins each UC's `mitreAttack`
list against this map and emits the derived tactics into:

- `catalog.json` → per-UC `mitre` block.
- `api/v1/mitre/techniques.json` → flattened technique → UCs.
- `api/v1/mitre/coverage.json` → tactic × technique matrix with counts.

## API surface

Four endpoints under `/api/v1/mitre/`:

| Endpoint | Shape | Use |
|---|---|---|
| `mitre/index.json` | `{ totals, links }` | Discovery |
| `mitre/techniques.json` | `[ { id, name, tactics, ucs[] } ]` | Per-technique reverse index |
| `mitre/coverage.json` | `{ tactics: { <tactic>: { techniques: { <id>: { count, ucs[] } } } } }` | Coverage matrix for dashboards |
| `mitre/d3fend.json` | D3FEND defensive-technique mapping (where MITRE D3FEND data is available) | Defensive coverage |

Use these to build:

- ATT&CK Navigator JSON files (export coverage to `attack-navigator.json`
  format).
- SOC coverage dashboards (tactic-by-tactic UC count heat maps).
- Detection-engineering work-trackers (find under-covered techniques).
- D3FEND-aligned defensive coverage maps.

## Filtering the catalogue by MITRE

Three ways:

1. **MITRE filter dropdown** in the catalogue's advanced filter strip
   — searchable, multi-select.
2. **MITRE Coverage Map modal** (button next to the dropdown) — visual
   tactic × technique grid with click-to-filter on any tile.
3. **URL hash** — `index.html#mitre=T1110.003` opens the catalogue
   pre-filtered. Combine with other filters via `&` (e.g.
   `#mitre=T1110.003&cat=9`).

## Coverage methodology

A UC counts as covering a technique when:

- The technique ID appears in the UC's `mitreAttack` list, **or**
- A sub-technique of the technique appears (e.g. `T1110.003` covers `T1110`).

We do **not** count partial coverage (e.g. one of three preconditions).
The mapping is binary at the technique level.

For richer assurance — *how well* a UC covers a technique — see the
per-UC quality-tier system in the [scorecard](scorecard.md) and the
[Gold Standard Template](gold-standard-template.md).

## Data sources

The catalogue's MITRE data comes from:

| Source | Path | Refreshed |
|---|---|---|
| MITRE ATT&CK Enterprise STIX bundle | `data/crosswalks/attack/` | On schedule via [Regulatory Change Watch](regulatory-change-watch.md) |
| MITRE ATT&CK ICS STIX bundle | `data/crosswalks/attack/` | Same |
| D3FEND mappings | `data/crosswalks/d3fend/` | Same |
| Per-UC tagging | `content/cat-NN-*/UC-X.Y.Z.json` `mitreAttack[]` | Per UC commit |

The `mitre_techniques.json` file in the repo root is regenerated from
the STIX bundles by the build pipeline.

## Atomic Red Team cross-reference

Where Atomic Red Team has a test for a technique, the catalogue carries
a cross-reference under `data/crosswalks/atomic-red-team/`. This is
*not* exposed in the catalogue UI today, but is consumed by the
[Knowledge Graph](knowledge-graph-guide.md) and is available for
agents fetching the underlying crosswalk JSON.

## Anti-patterns to avoid

- **Tagging without coverage** — don't add a technique just because
  the UC name mentions an attacker behaviour. The SPL must actually
  detect the technique. See [UC Quality Mandate](uc-quality-mandate.md).
- **Sub-technique mismatch** — if your detection only covers the parent
  technique, tag the parent (`T1110`), not a sub-technique (`T1110.003`).
- **Stale technique IDs** — when MITRE retires or renames a technique,
  the change-watch flow updates `mitre_techniques.json` and the per-UC
  fields need to be migrated. The audit `python -m splunk_uc audit-mitre`
  catches drift.

## Where to go next

- [Knowledge Graph](knowledge-graph-guide.md) — visualises MITRE
  techniques as nodes and lets you see clusters with shared coverage.
- [Site User Guide](site-user-guide.md) — for the in-catalogue MITRE
  filter and coverage map.
- [API Docs page](api-docs-guide.md) — for endpoint detail and
  request examples.
- [CIM Models Inventory](cim-models-inventory.md) — for the data-model
  side of the SOC coverage equation.
- [Gold Standard Template](gold-standard-template.md) — for the
  authoring contract that governs MITRE tagging.
- [Regulatory Change Watch](regulatory-change-watch.md) — for how
  MITRE updates flow into the catalogue.
