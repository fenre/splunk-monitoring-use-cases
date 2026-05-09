# `stewardship-digest.schema.json` changelog

Per-schema lifecycle log. Contract: see [`docs/schema-versioning.md`](../../docs/schema-versioning.md).

| Version | Released | Stability | Notes                                                                                                                                                                                                                                                                  |
|---------|----------|-----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1.0.0   | 2026-Q2  | stable    | Initial release (catalogue v8.1). Defines the weekly stewardship digest emitted by `scripts/generate_stewardship_digest.py` (repo-overhaul plan §P8 step 4). Snapshots release-over-release deltas in catalogue counts, quality-tier mix, coverage, leaderboard movers, audit warnings, and stale-UC review backlog. CI-gated by `tests/scripts/test_generate_stewardship_digest.py`. Adding fields is non-breaking; renaming or removing a field is a major bump. |

## Stability commitment

`x-stability: stable` — no breaking changes will be made within the v1
major. Additive (minor) changes are allowed; consumers must tolerate
unknown fields.
