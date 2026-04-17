# ADR-0003: Emit both a single `catalog.json` and per-category `api/cat-N.json`

- **Status:** Accepted
- **Date:** 2024-08-20
- **Deciders:** Repository maintainers

## Context

Two classes of consumer need the catalog in JSON form:

1. **Bulk consumers.** LLM training corpora, MCP servers, scheduled jobs that sync the catalog into an internal CMDB, SE laptops running offline analysis. They want the full catalog in one fetch.
2. **Targeted consumers.** A support ticket tool that only needs category 10 (Security Monitoring); a chatbot that answers "show me UCs for VMware" from `api/cat-2.json`; a dashboard panel embedded on a third-party site that only surfaces one category.

A 40 MB single JSON payload is wasteful and slow for targeted consumers; a zoo of per-category files alone is inconvenient for bulk consumers (23 HTTP fetches, no manifest).

We also observed that single-file consumers sometimes hit 5xx on the CDN when fetching `catalog.json` over flaky mobile networks.

## Decision

**Emit both forms on every build.**

- [`catalog.json`](../../catalog.json) — single pretty-printed JSON with the full catalog tree (`DATA`, `CAT_META`, `CAT_GROUPS`, `EQUIPMENT`).
- [`api/index.json`](../../api/index.json) — small manifest: one entry per category with `i`, `n`, `src`, `uc_count`, `sub_count`.
- [`api/cat-N.json`](../../api/) — per-category slice of `DATA`. There is one file per category; the category ID matches the `N` in the filename.

All three are generated from the same parse tree in one `build.py` invocation; they cannot drift.

## Consequences

**Positive:**

- Targeted consumers fetch `api/index.json` (small), discover the category they care about, and fetch `api/cat-N.json` (tens to hundreds of KB).
- Bulk consumers fetch `catalog.json` once (~40 MB, well cached).
- The OpenAPI spec planned for v5.2 can describe both shapes without contradiction.
- A future v5.2 Splunkbase TA generator reads `catalog.json` directly; the ITSI/ES pack generators can use either.

**Negative:**

- Slightly more disk and repo bandwidth per commit. Mitigation: the `api/` shards rebuild deterministically and only change when their category changes, minimising diff noise on unrelated PRs.
- Consumers must choose which shape to consume. Mitigation: documented in [DESIGN.md §9](../DESIGN.md#9-data-exports-and-integrations) and OpenAPI spec in v5.2.

## Alternatives considered

- **Per-UC JSON files (`api/uc/X-Y-Z.json`).** Rejected: ≥6,300 files is wasteful for the vast majority of consumers who want at least a whole category.
- **GraphQL endpoint.** Rejected: requires a back-end, contradicting [ADR-0002](0002-static-single-page-app.md).
- **Only `catalog.json`, no shards.** Rejected: targeted consumers pay too much to fetch.
- **Only shards, no monolith.** Rejected: bulk consumers pay too much to stitch.
- **Gzipped NDJSON.** Rejected: `catalog.json` is already gzipped by the static host; NDJSON loses the tree shape that the dashboard relies on.

## Links

- Generator: [`build.py:main()`](../../build.py)
- Consumer: [`index.html`](../../index.html) (via `data.js`)
- Sharding logic: [`build.py`](../../build.py), search for `OUTPUT_API_DIR`
- Superseded by: —
