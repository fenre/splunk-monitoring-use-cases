# `product-fit-review.schema.json` changelog

Per-schema lifecycle log. Contract: see [`docs/schema-versioning.md`](../../docs/schema-versioning.md).

| Version | Released | Stability | Notes |
|---------|----------|-----------|-------|
| 1.0.0   | Unreleased | preview | Initial release. Validates `data/product-fit-review.json`: one reviewed verdict (`migrate`, `keep`, `needs-sme-review`) per `audit-uc-product-fit` candidate, with the real products, whether SPL is kept, and evidence. See [ADR-0017](../../docs/adr/0017-splunk-product-per-use-case.md). |

## Stability commitment

`x-stability: preview` — the review shape may change while the ADR-0017
migration runs.
