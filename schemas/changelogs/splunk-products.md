# `splunk-products.schema.json` changelog

Per-schema lifecycle log. Contract: see [`docs/schema-versioning.md`](../../docs/schema-versioning.md).

| Version | Released | Stability | Notes |
|---------|----------|-----------|-------|
| 1.0.0   | Unreleased | preview | Initial release. Validates `data/splunk-products.json`: one row per Splunk product with required UC fields, applicable audits, export flags, ledger fingerprint fields, gold-profile implementation heading, and artifact types. See [ADR-0017](../../docs/adr/0017-splunk-product-per-use-case.md). |

## Stability commitment

`x-stability: preview` — the registry shape may gain attributes while
non-platform products are migrated (ADR-0017 Phase 3). Product `id` values
are public once a UC references them and are not renamed.
