# `product-fit-rules.schema.json` changelog

Per-schema lifecycle log. Contract: see [`docs/schema-versioning.md`](../../docs/schema-versioning.md).

| Version | Released | Stability | Notes |
|---------|----------|-----------|-------|
| 1.0.0   | Unreleased | preview | Initial release. Validates `data/product-fit-rules.json`: per Splunk product, the prose aliases, the index/sourcetype markers that identify its data in SPL, the documented ingest path into the Splunk platform, and the evidence for it. Read by `audit-uc-product-fit`. See [ADR-0017](../../docs/adr/0017-splunk-product-per-use-case.md). |

## Stability commitment

`x-stability: preview` — the rule shape may change while the ADR-0017
migration runs.
