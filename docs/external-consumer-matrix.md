# External-consumer impact matrix

> **Audience.** External consumers (Splunk admins pinning to specific
> URLs, MCP clients calling our tool surface, CI pipelines fetching
> `catalog.json`, dashboards embedding our search shards) **and** the
> maintainers of those consumers reading the roadmap to predict what
> might break and when.
>
> Treat this document as the **public release contract**. Anything
> listed here as "locked" is load-bearing for downstream products;
> changing it requires the deprecation process in
> [`docs/api-versioning.md`](api-versioning.md) or
> [`docs/url-scheme.md`](url-scheme.md).

## TL;DR

The catalogue exposes seven categories of consumer surface. Each is
classified by stability tier and labelled with the repo-overhaul plan
phases that could put it at risk. The two foundational rules:

1. **Locked surfaces never change without a major-version cycle**
   (12-month parallel-support window per
   [`docs/api-versioning.md`](api-versioning.md)).
2. **Additive-only surfaces accept new fields/endpoints freely; the
   deprecation contract still applies** to renames, removals, type
   narrowings, and enum shrinkages.

If you depend on any of the surfaces below, scan the **Locked-by**
column to know which document you can pin to, and the
**At-risk phases** column to know which roadmap items might prompt a
migration request.

## Stability tiers

| Tier | Meaning | Example | Change discipline |
|---|---|---|---|
| **🔒 Locked (URL or shape)** | URL path or top-level field set is permanent for the lifetime of the major version. | `/api/v1/compliance/regulations/<slug>.json`, the abbreviated `i`/`n`/`c`/`f`/`q` keys in `catalog.json`. | Removals/renames require a major bump; deprecation period is 12 months. |
| **➕ Additive-only** | URL exists, but the response body may grow with new fields. Existing fields keep their semantics. | Per-UC JSON sidecar (`/uc/UC-X.Y.Z/index.json`) gaining `lastVerifiedAt`. | New fields ship freely; removals follow the locked rules. |
| **📦 Versioned bundle** | Distributed as a tagged artefact; consumers pin to a specific release tag. | `.spl` packages on GitHub Releases. | Each tag is immutable. New tags supersede old ones; old tags stay reachable. |
| **🧪 Advisory / experimental** | Documented but explicitly not promised stable. | `dist/api/manifest.json`, `/llms.txt`. | Best-effort stability; breaking changes announced in `CHANGELOG.md` only. |
| **⚙️ Internal helper** | Exists for the in-repo SPA or build pipeline. Downstream products should build on `/api/v1/` instead. | `/api/cat-N.json`, MiniSearch shard files. | May change between minor versions without deprecation. |

## The matrix

| # | Consumer surface | Locked-by | Tier | At-risk phases | What could break | Migration path |
|---|---|---|---|---|---|---|
| 1 | **MCP tool names + arg shapes** (10 tools: `search_use_cases`, `get_use_case`, `get_use_case_markdown`, `list_categories`, `list_regulations`, `get_regulation`, `list_equipment`, `get_equipment`, `find_compliance_gap`, `get_clause_coverage`, `list_uncovered_clauses`) | [`docs/mcp-server.md`](mcp-server.md), JSON Schemas under `mcp/src/splunk_uc_mcp/tools/` | 🔒 Locked at v7.0 | P9 (monorepo) — tools could move package; P17 (AI-readiness) — adding latency-instrumented variants; P19 (i18n) — adding `lang` parameter | Tool rename, argument removal, return-shape narrowing, package import path change | 12-month deprecation: shipped tool gets `deprecated: true` flag in its JSON Schema; replacement tool ships alongside; CHANGELOG.md entry; MCP `resources/list` continues serving the old name until next major. |
| 2 | **Per-UC SSG URLs** (`/uc/UC-X.Y.Z/`, `/uc/UC-X.Y.Z/index.json`, `/uc/UC-X.Y.Z/jsonld.json`, `/uc/UC-X.Y.Z/oscal.json`, `/uc/UC-X.Y.Z/stix.json`, `/uc/UC-X.Y.Z/csv-row.json`, `/uc/UC-X.Y.Z/uc.md`, `/uc/UC-X.Y.Z/og.png`) | [`docs/url-scheme.md`](url-scheme.md) §"Use cases" | 🔒 Locked at v7.0 | P5 (frontend bundler) — output paths must remain stable while the SPA is rewritten; P6 (scripts taxonomy) — generators must keep emitting these paths; P9 (monorepo) — `apps/web/` must not change publicly-visible URLs | URL path change, `index.json` shape change, removal of any sibling format | URL change requires a major bump. Field-level changes within `index.json` follow the additive-only rule. The `tools/audits/url_freeze.py` audit blocks regressions on every PR. |
| 3 | **`/api/v1/` versioned endpoints** (compliance/, mitre/, equipment/, oscal/, recommender/, evidence-packs/) | [`docs/api-versioning.md`](api-versioning.md) | 🔒 Locked + ➕ additive-only within v1 | P5 (frontend bundler) — `apps/web/` must consume the same endpoints; P7 (search-API edge) — adding new search endpoints on top; P9 (monorepo) — endpoint generators move package; P17 (AI-readiness) — adding RAG endpoints | Removing/renaming any endpoint, narrowing a type, shrinking an enum, changing deterministic sort order | Additive changes ship in any minor; breaking changes ship in `/api/v2/` with 12-month parallel-support window per `api-versioning.md` §"Deprecation policy". |
| 4 | **MiniSearch shards** (`/assets/search-shard-NN.<hash>.json`, bootstrap via `/api/catalog-index.json`) | [`docs/url-scheme.md`](url-scheme.md) §"Discovery" + `dist/manifest.json` | ⚙️ Internal helper | P5 (frontend bundler + virtualization) — bundler may change shard layout; P7 (search-API edge) — server-side search would obsolete the shards; P10 (perf budgets) — shard count or size could change for budget reasons | Shard naming scheme change, shard format change, `catalog-index.json` shape change | These are explicitly internal helpers per `url-scheme.md`. Consumers building on `/api/v1/` are insulated; consumers reading shards directly should pin to a tagged release `dist/manifest.json` and migrate within one minor version of any change. |
| 5 | **`catalog.json` shape** (abbreviated keys: `i`, `n`, `c`, `f`, `v`, `ge`, `q`, `qs`, `t`, `d`, `s`, `u`, `e`, `em`, `wv`, `pre`, etc. — full mapping in [`docs/catalog-schema.md`](catalog-schema.md)) | [`docs/catalog-schema.md`](catalog-schema.md) + [ADR-0007](adr/0007-json-as-source-of-truth.md) | 🔒 Locked + ➕ additive-only | P1 step 5c (legacy artefact deletion) — file may move to `dist/`-only authoritative location; P4 step 3 (TypedDict consumer migration) — shape becomes more rigorously enforced; P8 (observability) — new audit fields like `_qg`, `_qs`, `_qt` emit | Renaming an abbreviated key, narrowing a value type, dropping a key | Abbreviated key rename = major bump. New keys ship freely (the `_qg`/`_qs`/`_qt` series in 2026 was an example). The TypedDict in `tools/build/types.py` pins the shape; CI fails if it drifts from the JSON Schema. |
| 6 | **`.spl` package filenames + app IDs** (`TA-splunk-use-cases-vX.Y.Z.spl`, `DA-ITSI-monitoring-use-cases-vX.Y.Z.spl`, `DA-ESS-monitoring-use-cases-vX.Y.Z.spl`, `splunk-uc-recommender-vX.Y.Z.spl`) | `release.yml` packaging steps + each app's `app.manifest`/`default/app.conf` | 📦 Versioned bundle | P9 (monorepo) — packaging scripts move; P11 (release polish) — release artefact bundle reorganisation; P18 (Splunk version compat) — could split per Splunk-version target | Filename rename, app-id rename inside `default/app.conf`, breaking changes to package layout | App-id rename = major bump (Splunk treats app-id as identity). Filename change without app-id change = minor bump with `CHANGELOG.md` callout. The Sigstore attestation chain in `release.yml` makes the lineage verifiable across renames. |
| 7 | **Schema files** (`schemas/uc.schema.json`, `schemas/regulations.schema.json`) | [`docs/schema-versioning.md`](schema-versioning.md) | 🔒 Locked (the `$id` URL is the contract) | P1 (SSOT migration) — adding fields like `cimSpl`, `wave`; P4 (TypedDict) — schema drift becomes a CI failure; P17 (AI-readiness) — RAG-related fields; P18 (Splunk version compat) — `splunkVersions` field; P19 (i18n) — `n_lang`, `v_lang` siblings | Renaming fields, narrowing types, shrinking enums | Schema `$id` URL never changes for the lifetime of major version `v1`. New fields are additive (`v1.6.1` → `v1.7.0`). Breaking changes land in `schemas/v2/` with the 12-month parallel-support window. |

## Phase-by-phase risk register

The matrix above maps consumer surfaces to phases. This section
inverts that view: for each phase, which consumer surfaces it
touches, so PR authors can sanity-check their reach before merging.

| Phase | Surfaces touched | Mitigation |
|---|---|---|
| **P0** Hygiene | None — internal cleanup only. | None needed. |
| **P1** SSOT migration | 5 (catalog.json shape — additive: `cimSpl`, `wave`, `_qs`); 7 (schema files — `cimModels` clarification). | Already mitigated. P1 step 5b kept project-root copies for one transition release. P1 step 5c will require a major bump only if external consumers pin to the project-root URL; the migration plan explicitly covers this. |
| **P2** CI parallelisation | None directly — but a long CI break could delay legitimate consumer requests indirectly. | Pin third-party actions per [SECURITY.md](../SECURITY.md). |
| **P2** CI security | None — internal gates only. | None needed. |
| **P2.5** Action pinning | None. | None needed. |
| **P3** Docs / ADR | None. | None needed. |
| **P4** Typed models | 5 (catalog.json shape — TypedDicts make drift CI-detectable); 7 (schema files — TypedDicts mirror them). | Schema-parity test in `tests/build/test_typed_models.py` blocks any drift between the TypedDict and the JSON Schema. |
| **P5** Frontend bundler | 2 (per-UC SSG URLs — apps/web/ must keep them); 3 (api/v1/ — apps/web/ consumes the same surface); 4 (MiniSearch shards — bundler may rewrite). | One page at a time per the plan; first page (api-docs.html) is read-only and produces no new URLs. The url_freeze.py audit blocks per-UC URL drift. |
| **P5** CSP / Trusted Types | None directly — but `index.html` carries the embedded JSON used by older consumers; field structure is unchanged. | The CSP work is HTML-internal. The JSON payload format that downstream consumers parse is unchanged. |
| **P5** Virtualisation + Lighthouse | 4 (MiniSearch shards — virtualisation may change page count and shard size targets). | Shards are internal helpers; consumers should be on `/api/v1/`. |
| **P5** Component library | 2 (per-UC SSG URLs — components shape the embed widgets under `/embed/`). | `/embed/` URLs are themselves locked; component-library work cannot rename them. |
| **P5** `data.js` retire | None directly. `data.js` is itself an internal helper, not a published consumer surface. The retirement is gated on apps/web/ shipping. | None needed; `data.js` is not in this matrix. |
| **P6** Scripts taxonomy | None directly — but `scripts/equipment_lib.py` and friends are imported by external consumers via `pip install splunk-uc`. | P6 will preserve a one-release-cycle redirect shim per the rollback playbook. |
| **P7** Search API edge | 3 (api/v1/ — adding `/api/v1/search` is additive); 4 (MiniSearch shards — could be supplanted but not removed in same release). | Edge layer is opt-in: Pages still serves shards if the edge is disabled. |
| **P8** Observability | 5 (catalog.json — `dist/metrics.json` may inherit shape conventions). | Metrics emission is a new artefact, not a change to existing ones. |
| **P9** Monorepo | 1 (MCP package import path); 2 (per-UC SSG URL generators move); 3 (api/v1/ generators move); 5 (catalog.json generator moves); 6 (.spl packagers move); 7 (schema files move). | This is the highest-risk phase. The plan reserves a one-minor-version soak per the rollback playbook. The url_freeze.py + schema_diff.py audits will catch any path or shape regression before merge. |
| **P10** Perf budgets | 4 (MiniSearch shards — budgets may force shard splits). | Internal helpers; consumers on `/api/v1/` insulated. |
| **P11** Release polish | 6 (.spl packaging may reorganise). | Filename changes signalled in CHANGELOG.md; app-ids preserved. |
| **P16** Coverage burndown | None. | None needed. |
| **P17** AI-readiness | 1 (MCP — adding latency-instrumented variants); 3 (api/v1/ — adding RAG endpoints); 7 (schema — RAG-related additions). | All additions, all additive. |
| **P18** Splunk version compat | 6 (.spl — could split per-version); 7 (schema — `splunkVersions` field added). | Schema additive; .spl changes follow the bundle-versioning rules. |
| **P19** i18n | 1 (MCP — `lang` argument added); 5 (catalog.json — `n_lang`, `v_lang` sibling keys); 7 (schema — same). | Strictly additive; English remains canonical. |

## What we explicitly do not promise

These are surfaces that look like they ought to be stable but are
not in the public contract. Consumers that depend on them do so at
their own risk, and the project takes no obligation to preserve
them across versions:

- **`dist/manifest.json` field set.** It is `🧪 advisory` — useful
  for build introspection but explicitly not part of the contract.
  Build proof is published via Sigstore attestation in
  [`release.yml`](../.github/workflows/release.yml), not via
  `manifest.json`.
- **`/llms.txt` and `/llms-full.txt` line ordering.** The set of
  UCs is stable; the order can change between minor versions for
  search-relevance reasons. Consumers must parse line-by-line, not
  by line number.
- **`/api/cat-N.json` payload shape.** Internal helper for the SPA
  bootstrap. Build on `/api/v1/` instead.
- **Search shard hash suffixes** (`search-shard-00.<hash>.json`).
  Hashes change every build; the bootstrap point
  (`/api/catalog-index.json`) is what consumers should pin to.
- **CSS class names + DOM IDs in `index.html`**. The HTML is meant
  to be visited by humans; consumers building on the DOM are
  outside the contract.
- **Cursor / Copilot / Claude / Gemini skill files under
  `.cursor/`, `.cursor/skills/`, `.cursor/skills-cursor/`.** These
  are agent ergonomics; not consumer surfaces.

## Signalling channels

When a consumer surface change is upcoming, we use the following
channels in this order so external consumers have multiple chances
to notice before the change ships:

1. **`CHANGELOG.md` "Unreleased"** — every consumer-facing change
   gets a line under "Unreleased" the moment the implementing PR
   merges. This is the canonical source.
2. **`docs/migration-status.md`** — multi-release migrations (like
   the P1 SSOT migration) get a status row with the planned
   removal version.
3. **`docs/north-star-scorecard.md`** — score 4 (reproducible build)
   regressions show up in the trend table even if the surface
   itself didn't change.
4. **GitHub Releases body** — consumer-impacting changes are
   flagged at the top of the release body, above the auto-generated
   change list.
5. **MCP `resources/list` `notification`** — for MCP-specific
   changes, the deprecated tool surfaces a Sigstore-signed
   `deprecated: true` flag for ≥12 months.
6. **`api/v1/manifest.json` `deprecations[]`** — the manifest
   carries machine-readable deprecation entries with `removalIn`
   (target major version) and `successor` (replacement endpoint
   URL).

A consumer who watches CHANGELOG.md + the deprecations array in
`/api/v1/manifest.json` will catch every break with at least one
minor-version cycle of warning.

## How to update this document

Update the matrix when:

1. **A new external surface ships** — add a row, name its locking
   document, classify its tier, and identify which roadmap phases
   could threaten it.
2. **A surface gains a stronger lock** — e.g. moving from
   `🧪 advisory` to `➕ additive-only` because a documented stable
   contract now exists. Cite the document.
3. **A surface is retired** — do **not** delete the row. Strike
   the surface name and add a "Retired in vX.Y" note so historical
   readers can still see what we used to ship.
4. **A roadmap phase scope changes** — re-check the
   "At-risk phases" column for every row. New phases get added to
   any row they touch.

Each update is its own PR with the architecture template. The
"Affected releases" field in the PR description must list every
consumer surface row touched.

## Links

- API stability contract:
  [`docs/api-versioning.md`](api-versioning.md).
- URL stability contract:
  [`docs/url-scheme.md`](url-scheme.md).
- Schema versioning contract:
  [`docs/schema-versioning.md`](schema-versioning.md).
- MCP tool surface:
  [`docs/mcp-server.md`](mcp-server.md).
- Catalog field abbreviations:
  [`docs/catalog-schema.md`](catalog-schema.md).
- Migration tracker:
  [`docs/migration-status.md`](migration-status.md).
- Operational pair:
  [`docs/rollback-playbook.md`](rollback-playbook.md),
  [`docs/capacity-and-staffing.md`](capacity-and-staffing.md),
  [`docs/north-star-scorecard.md`](north-star-scorecard.md).
- ADRs that constrain consumer-facing shape: [ADR-0007](adr/0007-json-as-source-of-truth.md)
  (UC content), [ADR-0008](adr/0008-canonical-constants.md)
  (constants), [ADR-0009](adr/0009-generated-artefact-policy.md)
  (artefacts).
