# `search-index.schema.json` changelog

Per-schema lifecycle log. Contract: see [`docs/schema-versioning.md`](../../docs/schema-versioning.md).

| Version | Released | Stability | Notes                                                                                                                                                                                                                                                                                                                                                                                                          |
|---------|----------|-----------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 2.0.0   | v7.0     | preview   | Initial release. Defines `dist/assets/search-vocab.json` (vocabulary + per-shard fingerprinted filenames + integer UC-id table) and `dist/assets/search-shard-NN.<hash>.json` (per-shard inverted index — token → array of compact UC ids). Routing uses FNV-1a 32-bit (`shard = fnv1a32(utf8(token)) % shardCount`) so the JS implementation stays under 10 lines and avoids any dependence on Web Crypto. Replaces the in-memory linear scan over the legacy 39 MB `data.js` blob. |

## Stability commitment

`x-stability: preview` — the on-disk shape is settled but the build pipeline
reserves the right to tweak document-frequency cutoffs, shard count, or the
vocabulary normalisation rules without a deprecation cycle while the search
shards bed in. Any such change re-fingerprints every shard, so caches stay
coherent automatically.

Renaming or removing fields requires a major bump and a 12-month
parallel-release window per
[`docs/api-versioning.md`](../../docs/api-versioning.md). Switching the
hash algorithm in `vocab.hash` is a breaking change because it invalidates
every cached shard route.

Promotion to `stable` is scheduled for v7.1, after the search shards have
served real-user traffic for at least one minor release without regressions
and the budget tooling has confirmed gz-shard sizes stay within
`tools/build/budgets.json`.

## Migration plan

A v3 major will be branched only when a breaking change to the search-index
shape is unavoidable. When that happens:

1. The new schema lives at `/schemas/v3/search-index.schema.json`.
2. v2 stays online for ≥12 months at `/schemas/v2/search-index.schema.json`
   and the corresponding `/assets/search-shard-*.v2.json` artifacts.
3. A migration tool ships under `tools/build/migrate_search_index_v2_to_v3.py`
   if any consumer outside this repo has cached the postings.
4. A migration guide ships at `docs/migrations/search-index-v2-to-v3.md`.
