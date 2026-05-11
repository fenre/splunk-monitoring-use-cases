# Build Artefacts Reference

Every file emitted into `dist/` by `make build`, what it is, and who
consumes it.

Audience: developers extending the build pipeline, integrators
deciding which artefact to fetch, anyone debugging a build or auditing
what gets deployed to GitHub Pages.

For the build *pipeline* (stages, dependencies, perf budgets), see
[Architecture](architecture.md). For the *contract* governing each
artefact, see [API Versioning](api-versioning.md) and
[Schema Versioning](schema-versioning.md).

## Build pipeline overview

```
make build
└── tools/build/build.py --out dist
    ├── parse        — load and validate every UC sidecar
    ├── assets       — fingerprint CSS, JS, images
    ├── pages        — render per-UC, per-category, per-regulation pages
    ├── api          — emit /api/v1/* JSON tree
    ├── search       — build sharded inverted index
    ├── exports      — CSV / future formats
    ├── meta         — sitemap, RSS, robots, AI policy, manifests
    ├── public       — copy static project files (HTML tools, AGENTS.md, etc.)
    ├── html_rewrite — apply integrity hashes and theme tokens to HTML
    ├── integrity    — emit SHA-256 manifest + Merkle root
    ├── build_info   — write BUILD-INFO.json
    └── metrics      — write metrics.json
```

A reproducible build (`--reproducible` / `make audit-reproducibility`)
suppresses non-deterministic output (build telemetry, timestamps in
HTML comments) and asserts byte-identical results across two runs.

## SPA shell and assets

| Path | Description |
|---|---|
| `dist/index.html` | Catalogue SPA shell (rewritten to reference fingerprinted assets). |
| `dist/data.js` | Inlined catalogue payload + globals consumed by the SPA. |
| `dist/assets/styles.<hash>.css` | Fingerprinted catalogue CSS. |
| `dist/assets/app.<hash>.js` | Fingerprinted SPA JavaScript. |
| `dist/assets/<image|font>` | Fingerprinted media. |
| `dist/assets/search-vocab.json` | Search index vocabulary (MiniSearch tokens). |
| `dist/assets/search-shard-NN.json` | Sharded inverted index. |
| `dist/browse/index.html` | Mirror of the SPA at `/browse/`. |

## Per-UC twins

For every `UC-X.Y.Z`:

| Path | Format | Purpose |
|---|---|---|
| `dist/uc/UC-X.Y.Z/index.html` | HTML | Static SSG page (humans + crawlers). |
| `dist/uc/UC-X.Y.Z/index.json` | JSON | Machine-readable twin (~2 KB). |
| `dist/uc/UC-X.Y.Z/uc.md` | Markdown | LLM-friendly twin, stamped with `Last-modified` + `Catalogue-version`. |
| `dist/uc/UC-X.Y.Z/index.jsonld` | JSON-LD | Linked-data twin. |
| `dist/uc/UC-X.Y.Z/component-definition.json` | OSCAL | OSCAL Component Definition. |
| `dist/uc/UC-X.Y.Z/stix.json` | STIX 2.1 | Cyber-threat-intelligence twin (when MITRE present). |

For embedding patterns, see [Embedding](embedding.md).

## Per-category and per-regulation pages

| Path | Description |
|---|---|
| `dist/category/<slug>/index.html` | Static category page. |
| `dist/category/<slug>/index.json` | Per-category JSON. |
| `dist/regulation/<slug>/index.html` | Static regulation page. |
| `dist/regulation/<slug>/index.json` | Per-regulation JSON. |
| `dist/equipment/<slug>/index.html` | Static equipment page (lazy — emitted only if ≥1 UC references it). |
| `dist/equipment/<slug>/index.json` | Per-equipment JSON. |

## Catalogue payload

| Path | Description |
|---|---|
| `dist/catalog.json` | Full machine-readable catalogue with abbreviated keys. See [Catalog Schema](catalog-schema.md). |
| `dist/cat-N.json` | Legacy per-category mirror (kept for v6 consumers). |
| `dist/manifest.json` | Top-level paths to every artefact. Differs from `dist/api/v1/manifest.json` in scope. |

## API tree (`/api/v1/`)

| Path | Description |
|---|---|
| `dist/api/v1/manifest.json` | API discovery manifest. |
| `dist/api/v1/context.jsonld` | JSON-LD context. |
| `dist/api/v1/openapi.yaml` | OpenAPI 3.1 spec (rendered by [`api-docs.html`](api-docs-guide.md)). |
| `dist/api/v1/README.md` | API overview. |
| `dist/api/v1/compliance/{index,coverage,gaps}.json` | Compliance roll-ups. |
| `dist/api/v1/compliance/regulations/<id>{,@<version>}.json` | Per-regulation drill. |
| `dist/api/v1/compliance/clauses/index.json` | Per-clause reverse index (consumed by [Clause Navigator](clause-navigator-guide.md)). |
| `dist/api/v1/compliance/story/<id>.json` | Per-regulation narrative (consumed by [Compliance Story](compliance-story-guide.md)). |
| `dist/api/v1/compliance/ucs/<id>.json` | Per-UC compliance roll-up. |
| `dist/api/v1/oscal/{index,catalogs/<id>,component-definitions/<uc>}.json` | OSCAL artefacts. |
| `dist/api/v1/mitre/{index,techniques,coverage,d3fend}.json` | MITRE ATT&CK<sup class="ref">[<a href="#ref-1">1</a>]</sup> and D3FEND<sup class="ref">[<a href="#ref-2">2</a>]</sup>. See [MITRE ATT&CK Mapping](mitre-attack-mapping.md). |
| `dist/api/v1/recommender/{sourcetype,cim,app,splunkbase}-index.json` | Reverse indices for the [Recommender App](recommender-app.md). See also [CIM Models Inventory](cim-models-inventory.md). |
| `dist/api/v1/recommender/uc-thin.json` | Minimal UC records for in-Splunk matching. |
| `dist/api/v1/equipment/{index,<id>}.json` | Equipment registry. See [Equipment Table](equipment-table.md). |
| `dist/api/v1/evidence-packs/<regulation>.json` | JSON twins of the [evidence packs](evidence-packs/). |

## Discovery and SEO

| Path | Description |
|---|---|
| `dist/sitemap.xml` | Sitemap index. Auto-shards into `dist/sitemap-pages-NN.xml` when total > 50 K URLs. |
| `dist/sitemap-pages-NN.xml` | Per-shard sitemaps. |
| `dist/feed.xml` | RSS feed of recently added UCs. |
| `dist/robots.txt` | Crawler policy. |
| `dist/manifest.webmanifest` | PWA manifest. |
| `dist/.well-known/security.txt` | Security contact (per RFC 9116). |
| `dist/.well-known/ai.txt` | AI usage policy (mirror of root `ai.txt`). |
| `dist/ai.txt` | AI usage policy (root). |

## LLM discovery files

| Path | Description |
|---|---|
| `dist/llms.txt` | Concise LLM-readable index (per the `llms.txt` convention). |
| `dist/llms-full.txt` | Full LLM-readable index with all UC summaries. |
| `dist/llm.txt` | Alternate location for compatibility with some clients. |
| `dist/AGENTS.md` | Mirror of root [`AGENTS.md`](../AGENTS.md), kept in sync. |
| `dist/AGENTS-EXAMPLES.md` | Mirror of root [`AGENTS-EXAMPLES.md`](../AGENTS-EXAMPLES.md). |

## Tools and companion apps

| Path | Description |
|---|---|
| `dist/tools/data-sizing/` | Standalone [Data Sizing Assessment](inventory-and-sizing.md#data-sizing-assessment-dsa) web app. |
| `dist/clause-navigator.html` | [Clause Navigator](clause-navigator-guide.md). |
| `dist/compliance-story.html` | [Compliance Story](compliance-story-guide.md). |
| `dist/regulatory-primer.html` | Plain-language regulatory primer reader. |
| `dist/scorecard.html` | Catalogue [scorecard](scorecard.md). |
| `dist/scorecard.json` | Scorecard data backing the page. |
| `dist/graph.html` | Interactive [knowledge graph](knowledge-graph-guide.md). |
| `dist/graph-data.json` | Graph nodes and edges. |
| `dist/api-docs.html` | OpenAPI viewer ([API Docs Page](api-docs-guide.md)). |
| `dist/docs.html` | Documentation hub. |
| `dist/guide-reader.html` + `dist/guide-reader.js` | Markdown reader for the docs hub. |

## Static project files

Per `_PROJECT_STATIC_FILES` in `tools/build/build.py`, the build copies
through to `dist/`:

`index.html`, `scorecard.html`, `scorecard.json`, `graph.html`,
`graph-data.json`, `docs.html`, `clause-navigator.html`,
`compliance-story.html`, `regulatory-primer.html`, `api-docs.html`,
`non-technical-view.js`, `docs-uc-map.js`, `provenance.json`,
`provenance.js`, `mitre_techniques.json`, `recently-added.json`,
`AGENTS.md`, `AGENTS-EXAMPLES.md`, `ai.txt`, icons, `catalog.json`
(second path), and a few others.

The `_PROJECT_CONTENT_DIRS` setting copies whole subtrees: `api/`,
`docs/`, `schemas/`, `samples/`, `splunk-apps/`, `reports/`. The
`_COMPANION_TOOLS` setting copies `tools/data-sizing/`.

## Exports

| Path | Description |
|---|---|
| `dist/exports/catalog.csv` | CSV export of the full catalogue. Filtered exports happen client-side from the catalogue's overview tab. |

Future formats are tracked in `tools/build/render_exports.py`
comments — likely candidates: `parquet`, `xlsx`, OSCAL bundles.

## Integrity and provenance

| Path | Description |
|---|---|
| `dist/integrity.json` | SHA-256 of every artefact, plus a Merkle root and the metadata needed for [signed-provenance](signed-provenance.md) verification. |
| `dist/BUILD-INFO.json` | Catalogue version, git SHA, build date, schema-version pins. |

The `audit-reproducibility` workflow re-runs the build and asserts
that `integrity.json` is byte-identical across runs.

## Metrics and telemetry

| Path | Description |
|---|---|
| `dist/metrics.json` | Top-line counts (UCs, categories, regulations, equipment), quality-tier rollups, depth percentiles, coverage, top-N leaderboards. Schema: [`schemas/v2/metrics.schema.json`](../schemas/v2/metrics.schema.json). See [Metrics History](metrics-history.md) for the trend-record runbook. |
| `dist/build-telemetry.json` | Per-stage wall-clock duration. **Only emitted on non-reproducible builds.** Schema: [`schemas/v2/build-telemetry.schema.json`](../schemas/v2/build-telemetry.schema.json). |

## Generated outside `make build`

| Path | Description | How to generate |
|---|---|---|
| `dist/stewardship-digest.json` + `.md` | Release-over-release deltas, top movers, open audit warnings, stale-UC backlog. | `make stewardship-digest` (or weekly via `.github/workflows/stewardship.yml`). See [Stewardship Digest](stewardship-digest.md). |
| `data/metrics-history/<VERSION>.json` | Snapshot of `dist/metrics.json` at release time. | `make snapshot-metrics`. See [Metrics History](metrics-history.md). |
| `data/license-inventory.json` | Dependency-licence rollup baseline. | `make write-license-inventory`. See [License Inventory](license-inventory.md). |

These files live under `data/` (committed to the repo) rather than
`dist/` (deployed to GitHub Pages) because they are point-in-time
records reviewed and approved by maintainers, not automatically
produced on every commit.

## Where to go next

- [Architecture](architecture.md) — the build pipeline contract,
  performance budgets, and v7 stability commitments.
- [API Versioning](api-versioning.md) — stability of the `/api/v1/`
  tree.
- [URL Scheme](url-scheme.md) — frozen URL conventions for every
  artefact above.
- [Catalog Schema](catalog-schema.md) — what's in `catalog.json`.
- [Stewardship Digest](stewardship-digest.md) — the weekly digest of
  catalogue health.
- [Metrics History](metrics-history.md) — how metrics snapshots are
  captured and tested.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** MITRE Corporation. (2026). *MITRE ATT&CK Knowledge Base*. MITRE Engenuity. https://attack.mitre.org/

<a id="ref-2"></a>**[2]** MITRE Corporation. (2026). *MITRE D3FEND Knowledge Graph*. MITRE. https://d3fend.mitre.org/

<a id="ref-3"></a>**[3]** Splunk Inc. (2026). *Splunk Cloud Platform App Vetting requirements*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/SplunkCloud/latest/Service/SplunkCloudservice

<a id="ref-4"></a>**[4]** Splunk Inc. (2026). *Splunk Common Information Model Add-on Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/CIM

<a id="ref-5"></a>**[5]** Splunk Inc. (2026). *Splunk Enterprise Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk

### Related repository documents

- [`docs/api-docs-guide.md`](api-docs-guide.md)
- [`docs/api-versioning.md`](api-versioning.md)
- [`docs/architecture.md`](architecture.md)
- [`docs/catalog-schema.md`](catalog-schema.md)
- [`docs/cim-models-inventory.md`](cim-models-inventory.md)
- [`docs/clause-navigator-guide.md`](clause-navigator-guide.md)
- [`docs/compliance-story-guide.md`](compliance-story-guide.md)
- [`docs/embedding.md`](embedding.md)
- [`docs/equipment-table.md`](equipment-table.md)
- [`docs/inventory-and-sizing.md`](inventory-and-sizing.md)
- [`docs/knowledge-graph-guide.md`](knowledge-graph-guide.md)
- [`docs/license-inventory.md`](license-inventory.md)
- [`docs/metrics-history.md`](metrics-history.md)
- [`docs/mitre-attack-mapping.md`](mitre-attack-mapping.md)
- [`docs/recommender-app.md`](recommender-app.md)
- [`docs/schema-versioning.md`](schema-versioning.md)
- [`docs/scorecard.md`](scorecard.md)
- [`docs/signed-provenance.md`](signed-provenance.md)
- [`docs/stewardship-digest.md`](stewardship-digest.md)
- [`docs/url-scheme.md`](url-scheme.md)

### Cited by

- [`docs/api-docs-guide.md`](api-docs-guide.md)
- [`docs/catalog-schema.md`](catalog-schema.md)
- [`docs/inventory-and-sizing.md`](inventory-and-sizing.md)
- [`docs/regulatory-primer.md`](regulatory-primer.md)

<!-- END-AUTOGENERATED-SOURCES -->
