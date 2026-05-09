# `coverage-baseline.schema.json` changelog

Per-schema lifecycle log. Contract: see [`docs/schema-versioning.md`](../../docs/schema-versioning.md).

| Version | Released | Stability | Notes                                                                                                                                                                              |
|---------|----------|-----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1.0.0   | 2026-Q2  | preview   | Initial release. Locks the per-file test-coverage snapshot consumed by `audit_coverage_budget.py` as a no-regression contract. One baseline per minor release at `data/baselines/coverage-vX.Y.Z.json`. Marked `preview` until the tier-1/tier-2/tier-3 module taxonomy stabilises across releases. |

## Stability commitment

`x-stability: preview` — internal CI contract; shape may evolve as the
coverage-tier policy is refined. Treat as locked once promoted to
`stable`.
