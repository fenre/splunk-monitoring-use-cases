# Knowledge Graph — User Guide

The [Knowledge Graph](../graph.html) is an interactive visualisation of
the catalogue: 7,300+ use cases as nodes, with edges connecting them to
their categories, equipment, CIM models, MITRE techniques, regulations,
and pillars.

Audience: architects orienting themselves to the catalogue, security
engineers spotting clusters of related detections, anyone curious about
how the data fits together.

If you prefer tables to graphs, look at the
[Site User Guide](site-user-guide.md) — every relationship in the graph
is also accessible through the catalogue's filter strip.

## Quick start

1. Open [`graph.html`](../graph.html).
2. Wait for the layout to settle (a few seconds for the first
   interaction).
3. Hover any node to see its label and degree.
4. Click a node to focus the neighbourhood.
5. Use the **filter input** to find a node by name.

## What you see

### Canvas

A force-directed graph rendered with `d3-force` (or equivalent). Nodes
are coloured by **type**:

| Node type | Colour | Examples |
|---|---|---|
| **Use case** | One per `splunkPillar` (security/observability/platform/itops) | UC-9.6.4 *Brute force against AD over RDP* |
| **Category** | Domain group palette | cat-9 *Identity & Access* |
| **Subcategory** | Same as parent category, lighter | 9.6 *Wireless authentication* |
| **Equipment** | Vendor palette | `cisco-catalyst`, `paloalto-pa`, `microsoft-active-directory` |
| **CIM model** | CIM palette | `Authentication`, `Network_Traffic`, `Endpoint` |
| **MITRE technique** | MITRE palette | `T1110.003 Password Spraying` |
| **Regulation** | Compliance palette | `NIS2`, `PCI-DSS`, `HIPAA Security` |

Edges represent the relationships authored in the per-UC sidecars:

- UC ↔ Category / Subcategory.
- UC ↔ Equipment / Equipment models.
- UC ↔ CIM models.
- UC ↔ MITRE techniques.
- UC ↔ Regulation clauses.
- UC ↔ UC for prerequisites (`prerequisiteUseCases`).

The graph is *not* a Bayesian network or a control-flow diagram — every
edge is a static relationship from the authored sidecars.

### Toolbar (top-right)

| Button | What it does |
|---|---|
| 🔍 **Filter input** | Type to highlight nodes whose label matches. Other nodes fade. |
| ↻ **Re-run layout** | Re-shuffle the physics simulation (useful after filtering). |
| **Reset view** | Zoom and pan back to fit-to-window. |
| ➕ **Zoom in** / ➖ **Zoom out** | Manual zoom. |
| 🌙 **Toggle dark mode** | Light / dark theme. |

### Layers panel (when present)

Toggle visibility of each node type to declutter the view. Common
patterns:

- Hide MITRE + Regulation to see the **operational graph** only
  (UC ↔ Equipment ↔ CIM).
- Hide Equipment + CIM to see the **security graph** only
  (UC ↔ MITRE ↔ Regulation).
- Hide everything but Categories + UCs to see the **structural graph**
  (where the catalogue is dense vs sparse).

## Interacting with the graph

- **Hover** a node — pops a tooltip with the label, type, degree, and
  the first few neighbours.
- **Click** a node — focuses the neighbourhood (1-hop). Other nodes
  fade.
- **Double-click** a UC node — opens that UC in a new tab in the
  catalogue (`/uc/UC-X.Y.Z/`).
- **Drag** a node — pin it. The simulation respects pinned nodes.
- **Drag the canvas** — pan.
- **Scroll** — zoom.
- **Esc** — clear focus.

## Where the data comes from

| Surface | Source |
|---|---|
| Graph data | `graph-data.json` (built from `catalog.json` + crosswalks) |
| Layout | Client-side, with stored positions for stability across reloads |
| Colours and styling | `graph.html` inline CSS using the same design tokens as the catalogue |

The build emits `graph-data.json` alongside `catalog.json` so the page
loads in one fetch.

## When the graph is useful

- **Spotting clusters** — UCs that share equipment + CIM are often
  candidates for a single deployment wave.
- **Finding orphan equipment** — equipment nodes with low degree are
  either niche or under-covered.
- **MITRE coverage gaps** — MITRE technique nodes with low degree are
  techniques the catalogue doesn't cover well. Cross-reference with
  the [MITRE ATT&CK Mapping](mitre-attack-mapping.md) doc.
- **Regulation cross-cutting** — clicking a regulation node and seeing
  its UCs across categories tells you which domains contribute most to
  compliance posture.

## When the graph is *not* useful

- For exhaustive lists — use the catalogue's tabs or the API.
- For SPL or implementation detail — drill into a UC instead.
- For performance — the graph renders 7,300+ nodes; older laptops will
  feel it. Use the layer toggles to declutter.
- For mobile — the canvas works on a phone but the dragging and
  hovering UX is laptop-class.

## Limitations

- Layout is **non-deterministic**. The same catalogue can render
  visually different from one reload to the next. Pinned positions
  (when present) are stored in `localStorage`.
- Node labels are **truncated** at small zoom. Zoom in to read the
  full text.
- The graph **does not** represent prerequisite cycles or wave
  ordering — those are concepts in the per-UC sidecar, not in the
  graph data. Use the [Implementation Ordering](implementation-ordering.md)
  doc for that view.

## Where to go next

- [Site User Guide](site-user-guide.md) — for the table-driven view of
  the same data.
- [MITRE ATT&CK Mapping](mitre-attack-mapping.md) — for MITRE coverage
  in tabular form.
- [CIM Models Inventory](cim-models-inventory.md) — for the CIM model
  list with UC counts.
- [Equipment Table](equipment-table.md) — for the equipment registry.
- [Catalog Schema](catalog-schema.md) — for the underlying data shape.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** MITRE Corporation. (2026). *MITRE ATT&CK Knowledge Base*. MITRE Engenuity. https://attack.mitre.org/

<a id="ref-2"></a>**[2]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

<a id="ref-3"></a>**[3]** Splunk Inc. (2026). *Splunk Common Information Model Add-on Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/CIM

<a id="ref-4"></a>**[4]** Splunk Inc. (2026). *Splunk Enterprise Security Administration Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ES

### Related repository documents

- [`docs/catalog-schema.md`](catalog-schema.md)
- [`docs/cim-models-inventory.md`](cim-models-inventory.md)
- [`docs/equipment-table.md`](equipment-table.md)
- [`docs/implementation-ordering.md`](implementation-ordering.md)
- [`docs/mitre-attack-mapping.md`](mitre-attack-mapping.md)
- [`docs/site-user-guide.md`](site-user-guide.md)

### Cited by

- [`docs/build-artefacts-reference.md`](build-artefacts-reference.md)
- [`docs/clause-navigator-guide.md`](clause-navigator-guide.md)
- [`docs/mitre-attack-mapping.md`](mitre-attack-mapping.md)
- [`docs/site-user-guide.md`](site-user-guide.md)

<!-- END-AUTOGENERATED-SOURCES -->
