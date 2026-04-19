# API Versioning Policy

> **Status:** Locked at v7.0.0. This is the permanent contract for the public,
> read-only HTTP/JSON API exposed under `/api/v{N}/` and the unversioned helper
> endpoints under `/api/`. Schema and content URL stability are governed separately
> by [`schema-versioning.md`](schema-versioning.md) and [`url-scheme.md`](url-scheme.md).

## Mission

Let every downstream tool — dashboards, Splunk apps, MCP servers, audit pipelines,
SIEM vendors, AI agents, the project's own `/browse/` SPA — depend on the API for
years without their builds breaking when we improve the catalogue.

## Guiding principles

1. **Stable URLs.** Once a path under `/api/v{N}/` is published, its URL never
   changes for the lifetime of major version `N`. Enforced by
   `tools/audits/url_freeze.py`.
2. **Additive-only within a major version.** New fields, endpoints, and enum values
   are allowed at any time. Removals, renames, type narrowings, and enum shrinkages
   are forbidden. Enforced by `tools/audits/schema_diff.py`.
3. **Reproducible.** `tools/build/render_api.py` emits byte-identical output for the
   same source SHA. CI re-builds and diffs.
4. **No surprises.** Breaking changes ship at a new major version with a 12-month
   parallel-support window. The next major (`/api/v2/`) is announced via an RFC at
   least 90 days before its first ship.
5. **Authenticated provenance.** Every release publishes `dist/integrity.json` and a
   Sigstore attestation so consumers can verify the bytes they fetched match the
   bytes the maintainers produced.

## Surface

### Versioned endpoints (the contract)

```
/api/v1/                              Current major. Active.
/api/v1/manifest.json                 Self-describing manifest with counts, deprecations, successor pointer
/api/v1/openapi.yaml                  OpenAPI 3.1 description of every endpoint below
/api/v1/context.jsonld                JSON-LD @context for the entire surface

/api/v1/compliance/index.json
/api/v1/compliance/coverage.json
/api/v1/compliance/gaps.json
/api/v1/compliance/regulations/index.json
/api/v1/compliance/regulations/<slug>.json
/api/v1/compliance/ucs/index.json
/api/v1/compliance/ucs/UC-X.Y.Z.json

/api/v1/equipment/index.json
/api/v1/equipment/<slug>.json

/api/v1/mitre/index.json
/api/v1/mitre/coverage.json
/api/v1/mitre/d3fend.json
/api/v1/mitre/techniques.json

/api/v1/oscal/index.json
/api/v1/oscal/catalogs/<slug>.json
/api/v1/oscal/component-definitions/index.json
/api/v1/oscal/component-definitions/<slug>.json

/api/v1/recommender/app-index.json
/api/v1/recommender/cim-index.json
/api/v1/recommender/sourcetype-index.json
/api/v1/recommender/uc-thin.json

/api/v1/evidence-packs/index.json
/api/v1/evidence-packs/<regulation>.json

/api/v2/                              Reserved for the next major version.
```

### Unversioned helper endpoints

These exist outside the `/api/v{N}/` namespace because they exist solely to make the
single-page browser cheap to load. They follow the same backwards-compatibility rules
as `/api/v1/` (additive-only within a major) but are **not** intended for downstream
products. Build products on top of `/api/v1/`.

```
/api/catalog-index.json               UC stubs for /browse/ bootstrap (≤1 MB gzip target)
/api/cat-N.json                       Per-category full UC payload, lazy-loaded by /browse/
/api/manifest.json                    Global path index for machine consumers (sitemap-like)
/api/shortlinks.json                  /v/{shortid}/ → /uc/UC-X.Y.Z/ map
```

## What is a breaking change?

A change is breaking if it does any of the following in an already-published
response:

| Kind | Example | Breaking? |
|---|---|---|
| Remove a field | drop `controlFamily` from a UC detail | Yes |
| Rename a field | `regulations` → `regulationList` | Yes |
| Narrow a field type | `tier: int` → `tier: "high" \| "low"` | Yes |
| Shrink an enum | drop `"contributing"` from `assurance` | Yes |
| Change a URL path | `/ucs/{id}.json` → `/use-cases/{id}.json` | Yes |
| Change deterministic sort order | flip alpha → freq sort | Yes (observational break) |
| Tighten validation (reject previously valid input) | reject UC IDs without leading zeros | Yes |
| Add a new field | add `lastVerifiedAt` to UC detail | No |
| Add a new endpoint | `/api/v1/compliance/roadmaps.json` | No |
| Add a new enum value | add `"mobile"` to a MITRE domain | No (see "tolerant consumer" rule) |

### Tolerant-consumer rule

Adding an enum value is technically a break for consumers that exhaust-match. We
allow additions because:

* Each new value is documented in `CHANGELOG.md` and the release-notes popup.
* New values never invalidate documented invariants (e.g. we never insert a value
  between `full` and `partial` in the `assurance` ordering without updating
  `docs/coverage-methodology.md`).
* Consumers must parse enum values with a default branch. Throwing on unknown enum
  values is considered incorrect under this policy.

If a category-level invariant change is needed (e.g. reorder an ordered enum), it
ships in a new major version.

## Versioning

### API version (this document)

Major-only versioning in the URL: `/api/v1/`, `/api/v2/`. No `v1.1` in the URL.
Within a major, the implementation improves continuously. The `apiVersion` field is
present in every response envelope and in `manifest.json`.

### Catalogue version (shipped alongside the API)

The `catalogueVersion` field in `/api/v{N}/manifest.json` mirrors the repository's
`VERSION` file (`MAJOR.MINOR.PATCH`). Consumers can detect content changes without
hitting every endpoint. Catalogue version bumps independently from API version, e.g.
`catalogueVersion: 7.3.1` running over `apiVersion: v1`.

### Release cadence

| Release type | Cadence | Bumps | Example |
|---|---|---|---|
| Content patch | Weekly | `catalogueVersion` patch | 7.0.0 → 7.0.1 |
| Content minor | Monthly | `catalogueVersion` minor | 7.0.1 → 7.1.0 |
| Content major (URL break only) | Annual at most, RFC required | `catalogueVersion` major | 7.x → 8.0.0 |
| API major | Aligned with content major when needed; otherwise standalone via RFC | `apiVersion` and URL prefix | `/api/v1/` → `/api/v2/` |

## Deprecation policy

When a field or endpoint is slated for removal in the next major version we do five
things in parallel:

1. **Mark it** in the response body with a sibling `deprecated` key:
   ```jsonc
   {
     "status": "draft",
     "status_deprecated": {
       "sinceCatalogueVersion": "7.4.0",
       "removeAt": "v2",
       "replacement": "lifecycleStatus",
       "rfc": "https://github.com/<owner>/<repo>/discussions/123"
     }
   }
   ```
2. **Announce it** via a `Deprecation` and `Sunset` HTTP-equivalent header surfaced
   in the JSON envelope (since GitHub Pages doesn't allow custom headers, the same
   data ships as `_meta.deprecations[]` in the response body and in
   `manifest.json`):
   ```jsonc
   {
     "_meta": {
       "deprecations": [
         { "field": "status", "removeAt": "v2", "sunsetDate": "2027-04-30" }
       ]
     }
   }
   ```
3. **Document it** in `CHANGELOG.md` under "Deprecations" and link the originating
   RFC.
4. **Surface it** in the release-notes popup on the project site.
5. **Expose it** via the `deprecations` array in `/api/v{N}/manifest.json` so
   automated consumers can audit their own usage:
   ```jsonc
   {
     "deprecations": [
       {
         "field": "status",
         "endpoint": "/api/v1/compliance/ucs/UC-X.Y.Z.json",
         "sinceCatalogueVersion": "7.4.0",
         "removeAt": "v2",
         "sunsetDate": "2027-04-30",
         "replacement": "lifecycleStatus",
         "rfc": "https://github.com/<owner>/<repo>/discussions/123"
       }
     ]
   }
   ```

### Deprecation windows

| Severity | Behaviour | Minimum window |
|---|---|---|
| Field replacement (old still works) | Warn in `_meta.deprecations[]`. Old field continues. | One minor release. |
| Field removal | Removed only at the next major. Marker required throughout. | **12 months** between deprecation marker and removal. |
| Endpoint removal | Removed only at the next major. Marker required throughout. | **12 months** between deprecation marker and removal. |

The 12-month window is **identical** to the parallel-support window for major
versions, so a consumer running against v1 always sees deprecation markers at least
12 months before any breaking change lands in v2.

## Lifecycle of a major version

| Stage | Meaning | Support |
|---|---|---|
| **Active** | The version most consumers depend on. Fully maintained. | Full content + bug fixes |
| **Deprecated** | Successor has shipped. Still receives content updates. | Content updates + bug fixes |
| **Sunset** | Frozen. No further updates. | Read-only archive (URLs still resolve, content snapshot at sunset) |
| **Retired** | URL returns a sunset manifest at the same path. | None |

A major version stays **Active** for at least 12 months after its successor ships.
It then enters **Deprecated** for a minimum of 12 more months before sunset.
**Total minimum support window from successor ship to sunset: 24 months.**

After sunset, the URLs continue to resolve and serve a frozen snapshot of the last
content release for that major; only the active major receives new content.

## Major-version transition plan (the recipe)

When `vN+1` ships:

1. **Publish `/api/v{N+1}/`** alongside `/api/v{N}/`. Both are generated by the same
   `tools/build/render_api.py` from the same sources. `v{N}` is shimmed to preserve
   its field set.
2. **Add a `successor` pointer** to `/api/v{N}/manifest.json`:
   ```json
   { "successor": "/api/v2/manifest.json" }
   ```
3. **Keep `v{N}`** on the **Active → Deprecated → Sunset** cadence above.
4. **Provide a migration guide** at `docs/api-v{N}-to-v{N+1}.md` listing every
   field and endpoint change with copy-paste consumer migrations.
5. **Surface the migration** in `manifest.json`:
   ```json
   { "migrationGuide": "/docs/api-v1-to-v2.md" }
   ```
6. **Run both surfaces side-by-side in CI**, with the same Lighthouse / schema-diff
   / URL-freeze gates applied independently to each.

## How the API is generated

The entire tree under `dist/api/` is emitted by `tools/build/render_api.py` from:

* `schemas/uc.schema.json` and the rest of `schemas/`
* `data/regulations.json` and `data/per-regulation/*.json`
* `content/cat-NN-slug/UC-X.Y.Z.json` (per-UC sidecars)
* `data/crosswalks/oscal/*.json`
* `data/crosswalks/attack/*.json`
* `data/crosswalks/d3fend/*.json`
* `data/crosswalks/olir/*.json`
* `reports/compliance-coverage.json`

The renderer is **offline** (no network calls), **stdlib-only**, and
**reproducible**. Running it twice on the same commit yields byte-identical output:

```bash
python3 tools/build/build.py --out dist --reproducible
python3 tools/build/build.py --out dist2 --reproducible
diff -r dist/api dist2/api    # silent
```

CI runs both passes and asserts the diff is empty.

## How to use a specific version

### Browser / curl / fetch

```bash
curl https://splunk-monitoring.io/api/v1/manifest.json
```

### Pinning to a release (CDN, no GitHub API rate limits)

```bash
# pinned tag, served from jsDelivr
curl https://cdn.jsdelivr.net/gh/<owner>/<repo>@v7.0.0/api/v1/manifest.json

# floating major (Active version automatically)
curl https://cdn.jsdelivr.net/gh/<owner>/<repo>@v7/api/v1/manifest.json
```

### Splunk

Use the existing `splunk-uc-recommender` app (or its TA), or for ad-hoc queries:

```spl
| rest /services/apps/local/splunk_monitoring_use_cases count=0
| eval api_version="v1"
```

### Python (typed client)

```python
from splunk_uc_client import Client

client = Client(base_url="https://splunk-monitoring.io/api/v1/")
manifest = client.manifest()           # typed against /api/v1/manifest.json
ucs = client.compliance.ucs.list()     # typed against /api/v1/compliance/ucs/
```

`splunk-uc-client` ships from CI on every tag, pinned to the matching catalogue
version.

### MCP server

Point your MCP server's `resources` array at `/api/v1/manifest.json` and fetch
endpoints lazily. The manifest includes a `deprecations` list so your tool can warn
users on unsafe usage.

```python
# mcp/src/splunk_uc_mcp/server.py
BASE_URL = os.environ.get("SPLUNK_UC_API", "https://splunk-monitoring.io/api/v1/")
```

### Verifying provenance

```bash
gh attestation verify dist/integrity.json --owner <owner>
```

`integrity.json` lists the SHA-256 of every artefact in `dist/`, including every
`/api/v1/` endpoint. If a CDN returns a body whose SHA-256 doesn't match, treat the
result as untrusted.

## What is **not** versioned by this document

| Surface | Versioning lives in |
|---|---|
| Authoring schemas (`schemas/*.json`) | [`schema-versioning.md`](schema-versioning.md) — per-schema `version` + `x-stability` |
| Public content URLs (`/uc/`, `/category/`, `/regulation/`) | [`url-scheme.md`](url-scheme.md) — locked, never break |
| HTML page structure | Lighthouse + axe in CI; no formal version |
| Search-index shard format | Internal to `/browse/`; not a public API |
| Embeddable widgets (`/embed/`) | [`docs/embedding.md`](embedding.md) — semver via the embed bundle |
| Distribution channels (jsDelivr, npm, PyPI, Splunkbase) | [`docs/distribution.md`](distribution.md) |

## Versioning this document

When this policy changes, note the diff in `CHANGELOG.md` under "Policy" and link
the originating RFC under [`docs/governance.md`](governance.md). The current policy
is effective from **catalogue 7.0.0** and **API v1**.
