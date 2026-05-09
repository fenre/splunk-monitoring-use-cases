# `metrics-history-index.schema.json` changelog

Per-schema lifecycle log. Contract: see [`docs/schema-versioning.md`](../../docs/schema-versioning.md).

| Version | Released | Stability | Notes                                                                                                                                                                              |
|---------|----------|-----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1.0.0   | 2026-Q2  | stable    | Initial release. Defines `data/metrics-history/index.json` — sorted (semver-descending) list of release-time `metrics.json` snapshots stored under `data/metrics-history/`. Maintained by `scripts/snapshot_metrics.py`; never hand-edited. The newest release is always first. |

## Stability commitment

`x-stability: stable` — no breaking changes will be made within the v1
major. Additive (minor) changes are allowed.
