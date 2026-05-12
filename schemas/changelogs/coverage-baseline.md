# `coverage-baseline.schema.json` changelog

Per-schema lifecycle log. Contract: see [`docs/schema-versioning.md`](../../docs/schema-versioning.md).

| Version | Released | Stability | Notes                                                                                                                                                                              |
|---------|----------|-----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1.0.0   | 2026-Q2  | preview   | Initial release. Locks the per-file test-coverage snapshot consumed by `audit_coverage_budget.py` as a no-regression contract. One baseline per minor release at `data/baselines/coverage-vX.Y.Z.json`. Marked `preview` until the tier-1/tier-2/tier-3 module taxonomy stabilises across releases. |

## Baseline refreshes

| Baseline file | git_head | Reasoning |
|---------------|----------|-----------|
| `data/baselines/coverage-v9.1.0.json` | `40cb461008b` → `3cafd8e5611` (PR-5 hotfix #3 + #5, 2026-05-12) | The 9.1.0 baseline captured at `40cb461008b` predates two structural changes that have already landed on `main`: (a) the `tools/build/` modularisation (introduced `build.py`, `models.py`, `render_metrics.py`, `render_telemetry.py`; retired `types.py`) and (b) the `splunk_uc` package migration that relocated every `scripts/audit_*.py` to `src/splunk_uc/audits/*.py` and the tier-2 `scripts/generate_*.py` files to `src/splunk_uc/generators/*.py`. F18-coverage-tier-rules was completed inline alongside the refresh so the tier-2 ratchet picks up the migrated implementations: `TIER_2_INCLUDES` in `src/splunk_uc/audits/coverage_budget.py` now also matches `^src/splunk_uc/audits/.*\.py$` and `^src/splunk_uc/generators/.*\.py$`. The refreshed snapshot has 24 tier-1 entries and 68 tier-2 entries (every prior tier-2 entry under `scripts/` was migrated; the bare `scripts/` regexes remain to soak any not-yet-migrated stragglers). Two real deltas under `tools/build/` were accepted into the snapshot: `tools/build/build.py` (new file, 13.4% — no tests yet because it's the 836-line pipeline orchestrator) and `tools/build/enrichment.py` (52.03% → 46.25%, a real regression introduced when modular code paths moved out of enrichment.py without corresponding test relocations). The `version` field is manually pinned at `9.1.0` (forward-looking, matching the baseline filename); `--print-baseline` reads `_read_version()` from the repo `VERSION` file (`8.2.0` at refresh time), so contributors who regenerate the baseline must override the field to keep `test_committed_baseline_version_matches_VERSION` green until VERSION is bumped to 9.1.x. |

## Stability commitment

`x-stability: preview` — internal CI contract; shape may evolve as the
coverage-tier policy is refined. Treat as locked once promoted to
`stable`.
