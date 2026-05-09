# `metrics.schema.json` changelog

Per-schema lifecycle log. Contract: see [`docs/schema-versioning.md`](../../docs/schema-versioning.md).

| Version | Released | Stability | Notes                                                                                                                                                                                                                                |
|---------|----------|-----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1.0.0   | 2026-Q2  | stable    | Initial release. Defines `dist/metrics.json` — top-line catalogue health snapshot emitted once per build. Carries trend-friendly rollups (counts, percentile blocks, top-N leaderboards) so a stewardship dashboard or CI step can plot drift over releases. Distinct from `scorecard.json` (per-category quality) and `BUILD-INFO.json` (build environment / git provenance). Adding fields is non-breaking; renaming or removing a field is a major bump. |

## Stability commitment

`x-stability: stable` — no breaking changes will be made within the v1
major. Additive (minor) changes are allowed; consumers must tolerate
unknown fields.
