# `vendor-changelog.schema.json` changelog

Per-schema lifecycle log. Contract: see [`docs/schema-versioning.md`](../../docs/schema-versioning.md).

| Version | Released | Stability | Notes |
|---------|----------|-----------|-------|
| 1.0.0   | 2026-Q2  | preview   | Initial release. Hand-curated, machine-readable record of upstream vendor product release changes that affect Splunk field names, log formats, or sourcetypes. One file per vendor under `data/vendor-changelog/`. Consumed by `python -m splunk_uc audit-vendor-changelog` (Lane J-5) to flag UCs whose SPL or sourcetypes are impacted by an upstream release. Marked `preview` until the entry-level field-impact shape stabilises across additional vendors beyond the seeded Cisco corpus. |

## Stability commitment

`x-stability: preview` — internal lookup contract; the field-impact entry
shape may evolve as additional vendors are onboarded and we discover
patterns not present in the initial Cisco curation. Treat as locked once
promoted to `stable`.
