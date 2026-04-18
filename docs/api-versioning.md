# API Versioning Policy

This document governs the public, read-only HTTP/JSON API exposed under
[`/api/v1/`](../api/v1/). The goal is simple: let downstream tools (dashboards,
Splunk apps, MCP servers, audit consumers, the project's own scorecard
page) depend on the API without their pipelines breaking every time we
improve the catalogue.

> Scope: this document applies only to the API surface under `api/v{N}/`.
> The **authoring schema** (`schemas/uc.schema.json`) and the
> **regulation catalogue** (`data/regulations.json`) have their own
> `schemaVersion` fields with a separate lifecycle — they may change more
> frequently and are documented in [`docs/coverage-methodology.md`](coverage-methodology.md)
> and the schema itself.

## Guiding principles

1. **Stable URLs.** Once a path under `/api/vN/` is published, its URL does
   not change for the lifetime of version N.
2. **Additive-only within a major version.** Inside `/api/v1/` we may add
   new fields, new endpoints, or new enum values. We never remove,
   rename, restrict the type of, or otherwise narrow the meaning of an
   existing field.
3. **Deterministic output.** `scripts/generate_api_surface.py` emits
   byte-identical output for the same inputs. CI enforces this via
   `python3 scripts/generate_api_surface.py --check`, so every response
   body is reviewable in `git diff`.
4. **No surprises.** Breaking changes ship at a new major version. We
   announce them at least one minor release in advance and keep the old
   version live for a documented deprecation window.

## Versioning scheme

### API version (this document)

The API uses **major-only** versioning in the URL: `/api/v1/`, `/api/v2/`,
etc. No `v1.1` in the URL. Within a major version the implementation may
improve continuously — existing fields stay, new fields can appear — and
those changes are communicated via the `generatedAt` timestamp and the
`apiVersion` field in every response.

### Catalogue version (shipped alongside the API)

The `catalogueVersion` field in
[`/api/v1/manifest.json`](../api/v1/manifest.json) mirrors the repository's
`VERSION` file (`MAJOR.MINOR.PATCH`), so consumers can detect content
changes without hitting every endpoint. The catalogue version bumps
independently from the API version — e.g. `catalogueVersion: 6.0` running
over `apiVersion: v1`.

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
| Change sort order of a deterministic list | flip alpha → freq sort | Yes (observational break) |
| Add a new field | add `lastVerifiedAt` to UC detail | No |
| Add a new endpoint | `/api/v1/compliance/roadmaps.json` | No |
| Add a new enum value | add `"mobile"` to a MITRE domain | No, but see below |
| Add a new optional request parameter | (n/a: API is static JSON) | No |

### Additive enum values: the "tolerant consumer" rule

A new enum value is technically a breaking change for consumers that
exhaust-match on the current set. We add new values freely, but:

* We document each new value in the [release notes](../CHANGELOG.md) and
  the `index.html` release-notes popup.
* We never add values that invalidate a documented invariant (for example,
  we never add a new `assurance` value between `full` and `partial`
  without also updating `docs/coverage-methodology.md`).
* Consumers are expected to parse enum values with a default branch.
  Implementations that throw on unknown enum values are considered
  incorrect under this policy.

## Deprecation policy

When a field or endpoint is slated for removal in the next major version
we do four things in parallel:

1. **Mark it** in the response body with a sibling `deprecated` key
   (boolean or object with `{"sinceCatalogueVersion", "removeAt"}`):
   ```jsonc
   {
     "status": "draft",
     "status_deprecated": {
       "sinceCatalogueVersion": "6.4",
       "removeAt": "v2",
       "replacement": "lifecycleStatus"
     }
   }
   ```
2. **Document it** in `CHANGELOG.md` under a "Deprecations" heading.
3. **Surface it** in the release-notes popup on the project site.
4. **Expose it** via the `deprecations` array in
   `/api/v1/manifest.json` so automated consumers can audit their
   own usage:
   ```jsonc
   {
     "deprecations": [
       {
         "field": "status",
         "endpoint": "/api/v1/compliance/ucs/{id}.json",
         "sinceCatalogueVersion": "6.4",
         "removeAt": "v2",
         "replacement": "lifecycleStatus"
       }
     ]
   }
   ```

Deprecation windows:

* **Minor deprecation** (field replaced, old still works): one minor
  release.
* **Major deprecation** (field removed or type changed): minimum **two
  minor releases** or 90 days from the first release that marks it
  deprecated, whichever is later.

## Lifecycle of a major version

| Stage | Meaning | Support |
|---|---|---|
| Active | The version most consumers depend on. Fully maintained. | Full |
| Deprecated | Successor has shipped. Still receives fixes. | Bug-fix only |
| Sunset | Frozen. No further updates. | Read-only archive |
| Retired | URL returns 410 Gone (or, for static hosting, a sunset manifest). | None |

A major version stays **Active** for at least 180 days after the next
major version ships. It then enters **Deprecated** for a minimum of 180
more days before sunset.

## v1 → v2 transition plan

When v2 ships we will:

1. Publish `/api/v2/` alongside `/api/v1/`. Both are generated by the
   same script from the same sources; `v1` is shimmed to preserve its
   field set.
2. Add a `successor` pointer to `/api/v1/manifest.json`:
   ```json
   { "successor": "/api/v2/manifest.json" }
   ```
3. Keep `v1` at the **Active → Deprecated → Sunset** cadence above.
4. Provide a migration guide (`docs/api-v1-to-v2.md`) listing every
   field and endpoint change, with copy-paste consumer migrations.

## How the API is generated

The entire tree under `api/v1/` is generated by
[`scripts/generate_api_surface.py`](../scripts/generate_api_surface.py)
from:

* `schemas/uc.schema.json`
* `data/regulations.json`
* `use-cases/cat-*/uc-*.json` (1 200+ sidecars)
* `data/crosswalks/oscal/*.json`
* `data/crosswalks/attack/*.json`
* `data/crosswalks/d3fend/*.json`
* `reports/compliance-coverage.json`

The script is **offline**: it makes no network calls. Running it on the
same commit yields byte-identical output, which lets CI block merges
that forget to regenerate the tree:

```bash
python3 scripts/generate_api_surface.py            # regenerate
python3 scripts/generate_api_surface.py --check    # fail if out of date
```

## How to use a specific version

### From the browser / `curl` / `fetch`

```bash
curl https://fenre.github.io/splunk-monitoring-use-cases/api/v1/manifest.json
```

### From Splunk (fetching the artefact package)

```splunk
| rest /services/apps/local/splunk_monitoring_use_cases count=0
| eval api_version="v1"
```

### From an MCP server

Point your MCP server's `resources` array at
`/api/v1/manifest.json` and fetch endpoints lazily. The manifest
includes a `deprecations` list so your tool can warn users on unsafe
usage.

## Versioning this document

When this policy changes, bump its own top-level heading with the
catalogue version where the change took effect, and note the diff in
`CHANGELOG.md`.

Current policy effective from `VERSION = 6.0` (catalogue) and
`apiVersion = v1`.
