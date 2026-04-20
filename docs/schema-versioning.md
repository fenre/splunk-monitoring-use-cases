# Schema Versioning Policy

> **Status:** Locked at v7.0.0. This document governs every JSON Schema in
> `schemas/` and every schema-validated artefact emitted to `dist/`. The HTTP/JSON
> API surface that consumes these schemas is governed separately by
> [`api-versioning.md`](api-versioning.md); URL stability is governed by
> [`url-scheme.md`](url-scheme.md).

## Mission

Let downstream consumers (Splunk apps, MCP servers, OSCAL validators, third-party
SIEM vendors, the project's own build) generate code, run validators, and persist
data against our schemas — and trust that those schemas evolve predictably.

## Where schemas live

```
schemas/
  uc.schema.json                       Use case (the central authoring schema)
  category.schema.json                 Per-category metadata (_category.json)
  regulation.schema.json
  crosswalk.schema.json
  evidence-pack.schema.json
  manifest.schema.json                 Schema for /api/v1/manifest.json
  catalog-index.schema.json            Schema for /api/catalog-index.json
  oscal/                               OSCAL component-definition fragments
  stix/                                STIX 2.1 fragments
  changelogs/                          Per-schema CHANGELOG.md (one per schema)
```

Every schema in `schemas/` MUST include the four headers listed below. The CI
audit (`tools/audits/schema_meta.py`) blocks merges that omit them.

## Required schema metadata

Every schema declares its lifecycle in its top-level keywords. Example:

```jsonc
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://splunk-monitoring.io/schemas/v2/uc.schema.json",
  "title": "Splunk Monitoring Use Case",
  "version": "2.0.0",
  "x-stability": "stable",
  "x-since": "v7.0",
  "x-deprecated": null,
  "x-replaces": "https://splunk-monitoring.io/schemas/v1/uc.schema.json",
  "x-replacedBy": null,
  "x-changelog": "/schemas/changelogs/uc.md",
  "type": "object",
  "properties": { /* … */ }
}
```

| Keyword | Required | Meaning |
|---|---|---|
| `$schema` | Yes | JSON Schema draft. Pinned to **2020-12** for v7.0.0. |
| `$id` | Yes | Permanent absolute URL. MUST embed the schema major version (`/schemas/v2/`). |
| `version` | Yes | semver of the schema (`MAJOR.MINOR.PATCH`). |
| `x-stability` | Yes | `stable`, `preview`, or `deprecated`. See "Stability levels" below. |
| `x-since` | Yes | First catalogue version this schema shipped in. |
| `x-deprecated` | No | Catalogue version when this schema was marked deprecated, or `null`. |
| `x-replaces` | No | `$id` of the previous major this schema supersedes, or `null`. |
| `x-replacedBy` | No | `$id` of the next major that supersedes this one, or `null`. |
| `x-changelog` | Yes | Path under `/schemas/changelogs/` documenting every change. |

`x-` keywords are JSON Schema's officially supported extension namespace; they're
ignored by validators that don't understand them and surfaced by tooling that does.

## Stability levels

| Level | Promise | Allowed changes within a major |
|---|---|---|
| **stable** | Permanent contract. Validates production data. | Additive only (new optional properties, new enum values, new `oneOf` branches). |
| **preview** | May change during the current major. Useful for early adopters. | Anything that isn't a major bump (additions, restructuring of optional properties, enum changes). |
| **deprecated** | Frozen. Use the schema in `x-replacedBy`. | None. |

A `stable` schema can never silently relax to `preview`. Going `stable → preview`
requires a major version bump and an RFC under
[`GOVERNANCE.md`](../GOVERNANCE.md). Going `preview → stable` is a free
operation: it only happens when the maintainers commit to the additive-only
constraint.

## Versioning

semver, applied per schema:

| Bump | Trigger |
|---|---|
| **Patch** (`x.y.Z`) | Description text, examples, or `title` clarifications. No structural change. |
| **Minor** (`x.Y.z`) | Additive: new optional property, new enum value, new optional `$defs` entry, new optional `oneOf`/`anyOf` branch. |
| **Major** (`X.y.z`) | Breaking: remove/rename a property, narrow a type, shrink an enum, tighten validation in a way that rejects previously valid input, change `$id`. |

Every major bump moves the schema to a new `$id` path (`/schemas/v3/...`) and is
shipped alongside the previous major for the entire 12-month parallel-support
window required by [`api-versioning.md`](api-versioning.md).

## What is a breaking change?

| Change | Breaking? |
|---|---|
| Add an optional property | No |
| Remove a property (any required-ness) | Yes |
| Change a property's `type` | Yes |
| Make an optional property required | Yes |
| Make a required property optional | Yes (consumers may rely on its presence) |
| Add a value to an open enum | No (tolerant-consumer rule) |
| Remove a value from an enum | Yes |
| Tighten `pattern`, `minLength`, `maxLength`, `minimum`, `maximum` | Yes |
| Loosen `pattern`, `minLength`, `maxLength`, `minimum`, `maximum` | No |
| Add `$defs` | No |
| Remove `$defs` referenced from elsewhere | Yes |
| Replace `oneOf` with `anyOf` (or vice versa) | Yes |
| Add a new `oneOf` / `anyOf` branch | No (existing data still validates) |
| Reorder `properties` keys | No (semantically identical) |

CI blocks any of the "Yes" rows on a `stable` schema unless the change ships with
a major bump and a fresh `$id`.

## Per-schema CHANGELOG

Each schema has its own CHANGELOG at `schemas/changelogs/<name>.md`. Format:

```markdown
# uc.schema CHANGELOG

## 2.0.0 — 2026-04-18
- BREAKING: removed `legacyOwner` (deprecated in 1.4.0, sunset 2026-04-18).
- Added `lifecycleStatus` (oneOf: draft|review|published|archived).
- Migrated `status` to `lifecycleStatus` (see migration guide).

## 1.4.0 — 2025-04-10
- DEPRECATED: `legacyOwner` (use `owner`). Removal in 2.0.0.
- Added optional `lastVerifiedAt` (RFC 3339).

## 1.3.0 — …
```

The build's `tools/audits/schema_diff.py` cross-checks every release: if the
schema body changed but the changelog didn't, CI fails.

## Automated breaking-change detection

`tools/audits/schema_diff.py` runs in CI on every PR:

```bash
python3 tools/audits/schema_diff.py \
  --baseline-tag v7.0.0 \
  --head HEAD \
  --schemas schemas/
```

The audit:

1. Walks every `schemas/**/*.schema.json`.
2. Loads the baseline copy from `git show v7.0.0:schemas/...`.
3. Computes a structural diff (property add/remove, type change, enum change,
   constraint tighten/loosen, `$ref` chain change, `$id` change).
4. Classifies each change as additive, breaking, or metadata-only per the table
   above.
5. Cross-checks the change class against the schema's `version` bump:
   * Additive change with a patch bump → fail (must be minor).
   * Any change without a `version` bump → fail.
   * Breaking change without a major bump → fail.
   * Breaking change on a `stable` schema without a fresh `$id` → fail.
   * Breaking change on a `stable` schema without a deprecation marker in the
     baseline → fail (the previous major must have flagged it deprecated for at
     least 12 months — see [`api-versioning.md`](api-versioning.md)).
6. Cross-checks the schema's `x-changelog` for an entry covering the new version.

`tools/audits/schema_meta.py` runs alongside it and asserts every schema in
`schemas/` declares the full required-metadata set above.

Both audits are blocking gates in `.github/workflows/validate.yml`.

## Validation in the build

Every JSON file emitted to `dist/` is validated by `tools/build/render_*` against
its declaring schema before the file is written. The validation set:

| Artefact | Schema |
|---|---|
| `dist/uc/UC-X.Y.Z/index.json` | `schemas/uc.schema.json` |
| `dist/uc/UC-X.Y.Z/oscal.json` | `schemas/oscal/component-definition.schema.json` |
| `dist/uc/UC-X.Y.Z/stix.json` | `schemas/stix/bundle.schema.json` |
| `dist/category/<slug>/index.json` | `schemas/category.schema.json` |
| `dist/regulation/<slug>/index.json` | `schemas/regulation.schema.json` |
| `dist/api/catalog-index.json` | `schemas/catalog-index.schema.json` |
| `dist/api/v1/manifest.json` | `schemas/manifest.schema.json` |

Source-of-truth files in `content/cat-NN-slug/UC-X.Y.Z.json` are validated by
`tools/validate/validate_md.py` (the v7 successor to the root-level
`validate_md.py`) before any build runs. Validation failure blocks the PR.

## Distribution

Schemas are published independently of the catalogue, on every tag:

* **GitHub Pages**: served at `https://splunk-monitoring.io/schemas/v{N}/...`.
  These URLs are the canonical `$id` values.
* **jsDelivr**: served automatically at `https://cdn.jsdelivr.net/gh/<owner>/<repo>@v<tag>/schemas/...`
  for fixed-tag pinning.
* **npm**: `@splunk-uc/schemas` ships every schema plus auto-generated TypeScript
  type definitions. Package version mirrors the highest schema major.
* **PyPI**: `splunk-uc-schemas` ships every schema plus auto-generated Pydantic
  models. Package version mirrors the highest schema major.

Both the npm and PyPI packages export a `STABILITY` constant per schema so static
analysis can flag use of `preview` schemas.

## Migration guides

Every schema major ships with a migration guide at
`docs/schemas/<name>-v{N}-to-v{N+1}.md`. Format:

```markdown
# uc.schema migration: v1 → v2

## Removed
- `legacyOwner` → use `owner` (string, identical semantics)

## Added
- `lifecycleStatus` (replaces `status`; values are draft|review|published|archived)

## Renamed
- (none)

## Type-narrowed
- `tier`: was `int | string`, is now `int`

## Code samples
- Python: …
- Go: …
- TypeScript: …
```

The guide is linked from the deprecated schema's `x-replacedBy` chain and from
`/api/v1/manifest.json`'s `deprecations` array, so a consumer running an automated
audit can find the migration with two HTTP requests.

## Lifecycle of a schema major

| Stage | `x-stability` | Support |
|---|---|---|
| **Active** | `stable` | New minor/patch versions. New consumers should adopt. |
| **Deprecated** | `deprecated` | Frozen. Bug fixes only via patch. `x-replacedBy` set. |
| **Sunset** | `deprecated` | Frozen. URL still resolves; no further changes. |

A `stable` schema major stays **Active** for at least 12 months after its
successor ships, then **Deprecated** for a minimum of 12 more months before sunset
(matching the API's 24-month total window in [`api-versioning.md`](api-versioning.md)).

## Tooling-friendly outputs

To make the schemas useful to as many ecosystems as possible, the build emits, on
every release:

| Artefact | Source | Consumer |
|---|---|---|
| `dist/schemas/v{N}/*.schema.json` | `schemas/` | Any JSON Schema validator |
| `dist/schemas/v{N}/index.json` | generated | Tooling discovery |
| `dist/schemas/v{N}/types.d.ts` | json-schema-to-typescript | TypeScript consumers (also published to npm) |
| `dist/schemas/v{N}/types.py` | datamodel-code-generator | Python/Pydantic consumers (also published to PyPI) |
| `dist/schemas/v{N}/types.go` | go-jsonschema | Go consumers |
| `dist/schemas/v{N}/openapi-snippets.yaml` | extracted | Stitched into `/api/v1/openapi.yaml` |

Type generators run only in CI and are not required for the core build (which
remains stdlib-only).

## Versioning this document

When this policy changes, note the diff in `CHANGELOG.md` under "Policy" and link
the originating RFC under [`GOVERNANCE.md`](../GOVERNANCE.md). The current policy
is effective from **catalogue 7.0.0**.
