# Migration build parity

This document explains why the new `content/`-tree loader (`SPLUNK_UC_LOADER=content`)
does **not** produce a byte-identical build to the legacy
monolithic-markdown loader (`SPLUNK_UC_LOADER=legacy`), and why every
remaining diff is an *intentional content improvement*, not a regression.

It is the closing artifact for the `migrate-step-4-build-parity`
sub-task of the `migrate-to-per-uc-files` migration.

---

## Reproducing the parity diff

```bash
# Re-emit content/ from use-cases/ + sidecars (idempotent)
python3 tools/build/migrate_to_per_uc.py

# Validate the regenerated tree against schemas/uc.schema.json (1.3.0)
python3 tools/validate/validate_md.py

# Build twice — once via the legacy v6 markdown parser, once via the
# new canonical-JSON loader. Both runs are reproducible.
SPLUNK_UC_LOADER=legacy   python3 tools/build/build.py --out dist-legacy   --reproducible
SPLUNK_UC_LOADER=content  python3 tools/build/build.py --out dist-content  --reproducible

diff -rq dist-legacy dist-content | grep -v 'BUILD-INFO\|integrity\.json\|search-shard\|search-vocab'
```

Files **expected to differ** between the two builds:

* `BUILD-INFO.json` — embeds the loader name + git SHA
* `integrity.json` — SHA-256s every emitted artifact, so its content
  changes whenever any other artifact changes
* `assets/search-shard-*.json` and `assets/search-vocab.json` — the
  search shard/vocab contents differ because the indexed UC field
  values differ (titles, regs, value); the *shard layout, hash
  algorithm, and shard count* are identical

Files that **also differ today** because of accepted content
enrichment:

* `api/catalog-index.json` — `regs` lists are richer for 667 UCs
* `api/manifest.json` — paths unchanged; embedded title/regs strings
  follow `catalog-index.json`
* Every `category/<slug>/index.json` — embedded UC title/regs/value
  follow `catalog-index.json`
* `category/regulatory-compliance/index.html` — the only HTML diff,
  driven by 1 079 cleaner cat-22 titles (see below)
* Every `regulation/<slug>/index.{html,json}` — UC counts grow when
  new sidecar `regs` add UCs to a regulation
* `exports/catalog.csv` — same UC rows, richer regs columns
* `index.html` — embeds a `data-build-version` attribute that hashes
  `catalog-index.json`

Files that are **byte-identical**: every UC-detail page
(`uc/UC-X.Y.Z/index.{html,json}`), every static asset other than the
search shards, every fingerprinted JS/CSS bundle, every per-UC machine
export.

## Why the diffs are accepted

The `migrate-to-per-uc-files` task moved the source-of-truth for use
case data from a single 35 000-line markdown file per category to a
per-UC canonical JSON file plus a free-form prose markdown file.
During that move, **every existing JSON sidecar in
`use-cases/cat-NN/uc-*.json` was merged into the canonical JSON** —
sidecar keys winning on conflict, since sidecars are the
SME-curated source of truth. The legacy markdown parser had been
silently dropping most of that sidecar metadata.

Concretely, the field-level diffs aggregate (across the entire build)
to:

| Field            | UCs differing | Lost in content | Gained in content | Notes                                                                                                                              |
|------------------|---------------|-----------------|-------------------|------------------------------------------------------------------------------------------------------------------------------------|
| `title`          | 1 079         | 0               | 0                 | All in cat-22. Sidecars drop the inline parenthetical clause refs (e.g. `(Art. 33(3))`); the clause now lives structured in `compliance[].clause` instead of being duplicated in the title. |
| `regulations`    | 667           | 0               | 5 + 57 globally    | Sidecar regs add real coverage (e.g. UC-1.1.108 → CJIS / Cyber Essentials / HITRUST) and normalise legacy aliases (`HIPAA` → `HIPAA Security` to match the slug in `data/regulations.json`). |
| `value`          | 85            | 0               | 0                 | Sidecar `value` strings expand the legacy one-liners.                                                                              |
| `dataModels`     | 42            | 0               | 0                 | Sidecar `cimModels` carries cleaner CIM model names (e.g. `Network_Traffic` instead of `network_traffic.network_traffic`).         |
| `monitoringTypes`| 10            | 0               | 0                 | Sidecar `monitoringType` refines a handful of cat-22 classifications.                                                              |
| `regs` (catalog) | (incl. above) | 0               | 57                | Same as `regulations`; this is the short-key view in `catalog-index.json`.                                                         |

**Zero UCs lose data on either side.** Every diff is a sidecar
enrichment that was authored months or years ago but never reached the
build because the legacy markdown parser never read sidecars for the
fields above (it only consulted them for `compliance`).

The new loader is therefore **the source of truth going forward**, and
the diffs above are the v7 build catching up with a backlog of
SME-authored corrections.

## What was *not* allowed to differ

The migration deliberately preserved every behaviour the renderer
ecosystem relies on. The following were treated as parity bugs and
fixed in the loader (`tools/build/parse_content.py`) before this doc
was written:

1. **`pillar` short-circuit.** The first cut of the loader pre-set
   `uc["pillar"]` from `canonical["splunkPillar"]`, which made the
   legacy `assign_pillar` post-processor return early. The fix
   (`fix-loader-pillar`) lets `assign_pillar` always recompute from
   `cat_id` + `sub_id` + `app` + `dataSources`.

2. **`em` (equipment models) lost when the migration emitted no
   `equipmentModels` array.** The legacy parser kept `em` as `[]` so
   the post-processor could derive it from the TA string; the
   migration was conservatively dropping empty lists, which left `em`
   as `None`, which the post-processor refused to overwrite. Fix
   (`fix-loader-em-default`): re-derive `em` from the TA string when
   `e` is set but `em` is missing.

3. **`premium` parenthetical duplication.** When the canonical
   `premiumApps[].displayName` already contained a note like
   `"Splunk SOAR (replacing Phantom)"` *and* the structured
   `premiumApps[].note` field was also `"replacing Phantom"`, the
   loader stamped both, producing
   `"Splunk SOAR (replacing Phantom) (replacing Phantom)"`. Fix
   (`fix-loader-premium-dup`): suppress the structured note when the
   display name already contains it.

4. **Duplicate-id subcategory bucketing.** A few legacy markdown files
   (notably `cat-22-regulatory-compliance.md`) have two `### N.M`
   sections sharing the same numerical id (e.g. `### 22.3 DORA` and
   `### 22.3 — DORA (extended clauses)`). The first cut of the loader
   collapsed them into a single bucket because it keyed `sub_buckets`
   by `id` alone. Fix (`fix-duplicate-sub-id-bucketing`):

   * Schema 1.3.0's `subcategory` field accepts a `<id>#<n>`
     disambiguator (e.g. `22.3#1`).
   * Migration assigns `bucketKey: "22.3#1"` to every subcategory
     entry beyond the first occurrence of an id, and stamps
     `subcategory: "22.3#1"` on every UC that lives in that bucket.
   * Loader keys `sub_buckets` by `bucketKey` (falls back to `id`),
     and the sub record's public `i` field still carries the bare id
     so downstream renderers and schema validators see the same shape.

5. **Spurious `tuc: ""` field.** An interim version of the loader
   added `tuc` to `_LEGACY_STRING_DEFAULTS`, which initialised every
   UC dict with an empty string. The legacy parser only ever sets
   `tuc` on UCs that carry an explicit `- **Telco Use Case:**`
   markdown line, so the empty-string default was leaking a new
   field into 6 318 UCs. Fix (`fix-loader-tuc-default`): drop `tuc`
   from the defaults; pass it through only when canonical
   `telcoUseCase` is non-empty.

After all five fixes, the only remaining diffs are the content
enrichments documented in the table above.

## When to delete the legacy loader

The `legacy` branch of `_resolve_loader_kind()` will be removed as
part of the `cleanup-and-docs` task, alongside the deletion of the
monolithic `use-cases/cat-NN-*.md` files. Until then, the legacy
loader stays in the tree as an emergency fallback in case a
content-tree-only regression is discovered post-merge.

The legacy branch is opt-in (env-var-gated) and never selected by
default, so the v7 release ships exclusively from the content tree.
