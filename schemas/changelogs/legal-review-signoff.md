# `legal-review-signoff.schema.json` changelog

Per-schema lifecycle log. Contract: see [`docs/schema-versioning.md`](../../docs/schema-versioning.md).

| Version | Released  | Stability | Notes                                                                                                  |
|---------|-----------|-----------|--------------------------------------------------------------------------------------------------------|
| 1.0.0   | 2025-Q4   | stable    | Initial release for Phase 4.5b. Records that qualified legal counsel reviewed a compliance-claim PR. Required fields: `generated_at`, `baseline_commit`, `signoffs`. |

## Stability commitment

`x-stability: stable` — no breaking changes within v1 major. Additive
(minor) changes allowed.

## Migration plan

If/when a v2 ships, the `signoffs[]` shape will be the breaking surface;
v1 instances will be auto-migrated by `tools/build/migrate_v1_to_v2.py`.
