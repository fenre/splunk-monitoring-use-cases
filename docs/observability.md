# Catalogue observability metrics

Lane L (P8 observability) adds **orthogonal** metrics under
`dist/observability/` that complement the existing build-time snapshot at
`dist/metrics.json` (schema: `schemas/v2/metrics.schema.json`).

`metrics.json` already carries top-line counts, global quality-tier rollups,
coverage percentages for a fixed axis set, depth percentiles, and leaderboards.
The observability family goes deeper on three axes CI and maintainers asked for
but `metrics.json` deliberately does not duplicate:

| Artefact | Path | What it measures |
|----------|------|------------------|
| Freshness | `dist/observability/freshness.json` | Per-UC git (or mtime) last-modified age, quantiles, age buckets, oldest/newest 25 |
| Quality cube | `dist/observability/quality.json` | Gold-profile tier counts per **category × criticality**, bronze-heavy categories |
| Coverage cube | `dist/observability/coverage.json` | Optional-field population (compliance, MITRE, KFP, prerequisites, …) with a per-category matrix |
| Prometheus | `dist/observability/catalogue.prom` | Text exposition of the same rollups for scrape-friendly monitoring |

All four files are **build outputs** (gitignored under `dist/`) and are
regenerated on demand or in CI.

## Generate

```bash
# Full corpus (local maintainer run)
python -m splunk_uc generate-observability-metrics

# Fast PR-style sample (200 sidecars per category cap on git calls)
python -m splunk_uc generate-observability-metrics --limit 200

# Drift gate (exit 1 when on-disk bytes differ)
python -m splunk_uc generate-observability-metrics --check

# Single family
python -m splunk_uc generate-observability-metrics --family freshness
```

Makefile targets:

```bash
make generate-observability-metrics
make audit-observability-drift
```

## Validate

```bash
python -m splunk_uc audit-observability-drift --check
```

The drift audit checks JSON shape invariants (monotone freshness quantiles,
exclusive age buckets summing to total UCs, quality tier/distribution math,
coverage percentages in `[0, 100]`) and that `catalogue.prom` lines match the
[Prometheus text exposition format](https://prometheus.io/docs/instrumenting/exposition_formats/).

## Scrape `catalogue.prom`

Point a Prometheus `file_sd` or node_exporter `textfile collector` at
`dist/observability/catalogue.prom` after generation. Example metric families:

- `splunk_uc_total` — UC count in the snapshot
- `splunk_uc_freshness_age_days{quantile="0.5"}` — median sidecar age in days
- `splunk_uc_freshness_age_bucket{bucket="720plus"}` — exclusive age bucket counts
- `splunk_uc_quality_tier{category="01",criticality="high",tier="gold"}` — tier cube
- `splunk_uc_coverage_percentage{dimension="compliance"}` — optional-field coverage

Each family includes `# HELP` and `# TYPE` comments as required by the format.

## Trend across releases

Release snapshots of `dist/metrics.json` are archived under
`data/metrics-history/<VERSION>.json` (see `docs/metrics-history.md` and
`make snapshot-metrics`). Observability JSON is **not** committed, but you can
archive it the same way after each release:

```bash
python -m splunk_uc generate-observability-metrics
cp dist/observability/freshness.json data/metrics-history/observability-freshness-$(cat VERSION).json
cp dist/observability/quality.json    data/metrics-history/observability-quality-$(cat VERSION).json
cp dist/observability/coverage.json   data/metrics-history/observability-coverage-$(cat VERSION).json
```

Plot ideas:

- **Freshness** — track `quantiles.p50` and `cumulativeOlderThan.olderThan180Days` release-over-release; rising median age signals stale review debt.
- **Quality** — compare `bronzeHeavyCategories` length and per-category bronze `%` from `quality.json`; pairs with `dist/stewardship-digest.{json,md}` stale-UC tables.
- **Coverage** — graph `perDimension.*.percentage` for compliance, MITRE, and prerequisites; use the `matrixPercentages` block to find categories lagging on a single dimension.

The stewardship digest (`make stewardship-digest`) already diffs `metrics.json`
against the previous `data/metrics-history/` entry; observability files extend
that story with git-derived freshness and the category × criticality quality cube
that `metrics.json` only rolls up globally.

## CI

`.github/workflows/validate.yml` (audits-content job) runs:

```bash
python -m splunk_uc generate-observability-metrics --limit 200
python -m splunk_uc audit-observability-drift --check
```

The nightly `build-reproducibility` workflow can run the generator without
`--limit` for a full-corpus observability snapshot alongside reproducible builds.

## Related commands

| Command | Role |
|---------|------|
| `make build` | Emits `dist/metrics.json` (do not duplicate here) |
| `make snapshot-metrics` | Archives `metrics.json` into `data/metrics-history/` |
| `make stewardship-digest` | Release-over-release delta digest |
| `python -m splunk_uc audit-gold-profile` | Source rubric for tier classification |
