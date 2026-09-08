# `equipment-app-map.schema.json` changelog

Per-schema lifecycle log. Contract: see [`docs/schema-versioning.md`](../../docs/schema-versioning.md).

| Version | Released | Stability | Notes |
|---------|----------|-----------|-------|
| 1.0.0   | 2026-Q3  | preview   | Initial release (Phase 2). Phase 5 expansion: generator covers all ~127 `kind=equipment` registry slugs with corroboration-gated `apps[]` or ingest-only `dsaSourceIds[]`. Gated by `audit-equipment-app-map`. |

## Stability commitment

`x-stability: preview` — shape may evolve as the picker UI and corroboration heuristics mature.
Treat as locked once promoted to `stable`.
