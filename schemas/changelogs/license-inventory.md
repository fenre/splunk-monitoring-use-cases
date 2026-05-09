# `license-inventory.schema.json` changelog

Per-schema lifecycle log. Contract: see [`docs/schema-versioning.md`](../../docs/schema-versioning.md).

| Version | Released | Stability | Notes                                                                                                                                                                                            |
|---------|----------|-----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1.0.0   | 2026-Q2  | preview   | Initial release. Validates the committed snapshot of every third-party Python dependency and every vendored `LICENSE` file with its SPDX identifier. Maintained by `audit_license_inventory.py`; CI fails on drift. Marked `preview` until the SPDX allow-list policy is finalised. |

## Stability commitment

`x-stability: preview` — internal compliance / supply-chain artefact;
shape may evolve as we tighten the SPDX allow-list and add subgrouping.
Treat as locked once promoted to `stable`.
