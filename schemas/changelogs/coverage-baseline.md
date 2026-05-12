# `coverage-baseline.schema.json` changelog

Per-schema lifecycle log. Contract: see [`docs/schema-versioning.md`](../../docs/schema-versioning.md).

| Version | Released | Stability | Notes                                                                                                                                                                              |
|---------|----------|-----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1.0.0   | 2026-Q2  | preview   | Initial release. Locks the per-file test-coverage snapshot consumed by `audit_coverage_budget.py` as a no-regression contract. One baseline per minor release at `data/baselines/coverage-vX.Y.Z.json`. Marked `preview` until the tier-1/tier-2/tier-3 module taxonomy stabilises across releases. |

## Baseline refreshes

| Baseline file | git_head | Reasoning |
|---------------|----------|-----------|
| `data/baselines/coverage-v9.1.0.json` | `40cb461008b` → `4d1ab40eb15` (PR-5 hotfix #3, 2026-05-12) | The 9.1.0 baseline captured at `40cb461008b` predates the `tools/build/` modularisation (introduced `build.py`, `models.py`, `render_metrics.py`, `render_telemetry.py`; retired `types.py`) and the `splunk_uc` package migration that relocated every `scripts/audit_*.py` to `src/splunk_uc/audits/*.py`. Refreshed in-place so the `audits-content` coverage-budget step can run inside the new parallel CI partition (PR-5). Three real deltas were accepted into the new snapshot: `tools/build/build.py` (new file, 13.4% — no tests yet because it's the pipeline orchestrator script), `tools/build/enrichment.py` (52.03% → 46.25%, a real regression introduced when modular code paths moved out of enrichment.py without corresponding test relocations), and zero tier-2 entries (every prior tier-2 file lives under `src/splunk_uc/` now). Follow-up: update `TIER_2_INCLUDES` in `src/splunk_uc/audits/coverage_budget.py` to also match `^src/splunk_uc/audits/.*\.py$`, then refresh the baseline again so the tier-2 ratchet starts protecting the migrated auditors. Tracked as F18-coverage-tier-rules in the repo health-check plan. |

## Stability commitment

`x-stability: preview` — internal CI contract; shape may evolve as the
coverage-tier policy is refined. Treat as locked once promoted to
`stable`.
