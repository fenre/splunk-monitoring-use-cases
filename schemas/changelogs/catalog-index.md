# `catalog-index.schema.json` changelog

Per-schema lifecycle log. Contract: see [`docs/schema-versioning.md`](../../docs/schema-versioning.md).

| Version | Released | Stability | Notes                                                                                                                                                                                                                                            |
|---------|----------|-----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 2.0.0   | v7.0     | preview   | Initial release. Lightweight bootstrap payload served at `/api/catalog-index.json`; ships per-UC stubs (`i`, `n`, `c`, `d`, `cat`, `sub`, `mtype`, `regs`, `searchBlob`) plus the small dictionaries (categories, subcategories, regulations, sources, apps) the SPA needs before opening a category. Replaces the legacy `data.js` blob and unblocks lazy fetches against `/api/cat-N.json`. |

## Stability commitment

`x-stability: preview` — the field set is settled but reserves the right to
add or remove fields without a deprecation cycle while the lazy-bootstrap
hardens in production. Adding new optional fields is allowed at any time and
is non-breaking; renaming or removing fields requires a major bump and a
12-month parallel-release window per
[`docs/api-versioning.md`](../../docs/api-versioning.md).

Promotion to `stable` is scheduled for v7.1, after the SSG per-UC and
per-category pages have shipped and the SPA has lived on the lazy bootstrap
for at least one minor release without regressions.

## Migration plan

A v3 major will be branched only when a breaking change to the bootstrap
payload is unavoidable. When that happens:

1. The new schema lives at `/schemas/v3/catalog-index.schema.json`.
2. v2 stays online for ≥12 months at `/schemas/v2/catalog-index.schema.json`
   and `/api/v2/catalog-index.json`.
3. A migration tool ships under `tools/build/migrate_catalog_index_v2_to_v3.py`.
4. A migration guide ships at `docs/migrations/catalog-index-v2-to-v3.md`.
