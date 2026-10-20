# Fabric registry schema changelog

Per-schema lifecycle log for the use-case fabric registries. Contract: see [`docs/schema-versioning.md`](../../docs/schema-versioning.md).

These files share one changelog because they shipped together:

- `schemas/fabric/sourcetypes.schema.json`
- `schemas/fabric/vendor-products.schema.json`
- `schemas/fabric/addons.schema.json`
- `schemas/fabric/cim.schema.json`
- `schemas/fabric/industries.schema.json`
- `schemas/fabric/business-outcomes.schema.json`
- `schemas/fabric/business-areas.schema.json`
- `schemas/fabric/personas.schema.json`
- `schemas/fabric/ambiguous.schema.json`

| Version | Released | Stability | Notes |
|---------|----------|-----------|-------|
| 1.0.0 | 2026-10-16 | preview | Initial fabric registry schemas. Each file validates one registry document (`sourcetypes`, `vendor-products`, `addons`, `cim`, `industries`, `business-outcomes`, `business-areas`, `personas`, `ambiguous`). Preview while enrichment grading is still open. |

## Stability commitment

`x-stability: preview` — registry fields may still be renamed or tightened while the fabric is graded. Promotion to `stable` waits until the enrichment precision bars are accepted.
