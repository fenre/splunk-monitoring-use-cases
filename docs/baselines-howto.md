# How to capture and use baselines

The repo-overhaul plan repeatedly says "X% smaller" or "Y× faster". Without numbers
on disk those targets are unverifiable. This file documents how `data/baselines/v*.json`
gets captured, what it covers, and how reviewers should use it during PR review.

## tl;dr

```bash
# Capture a fresh baseline at the current VERSION
make baseline

# Capture a baseline AND time `make build`
python3 tools/capture_baselines.py --build

# Capture a baseline at a custom version label
python3 tools/capture_baselines.py --version 7.5.0
```

The output is `data/baselines/v<VERSION>.json` and it must validate against
`schemas/baselines.schema.json`.

## What's measured

| Block                       | What's in it                                                                 | Source         |
|-----------------------------|------------------------------------------------------------------------------|----------------|
| `tracked_file_sizes_bytes`  | Per-file raw + gzipped byte counts for every file the plan refers to.       | `os.stat` + `gzip.compress` |
| `counts.uc_json_sidecars`   | Total UC JSON sidecars under `content/cat-*/UC-*.json`.                     | rglob          |
| `counts.uc_md_companions`   | Total `.md` companions under `content/cat-*/UC-*.md`.                       | rglob          |
| `counts.use_cases_md_headings` | Total `### UC-*` headings in legacy `use-cases/cat-*.md`.                | grep           |
| `counts.scripts_total`      | Files in `scripts/` (folders count as 1).                                   | iterdir        |
| `counts.categories`         | Files matching `_category.json` under `content/`.                           | rglob          |
| `counts.schemas`            | Files matching `*.schema.json` under `schemas/`.                            | rglob          |
| `counts.tests_python`       | `test_*.py` + `*_test.py` under `tests/`.                                   | rglob          |
| `counts.tests_mjs`          | `*.test.mjs` under `tests/`.                                                | rglob          |
| `counts.workflows`          | `.yml` files under `.github/workflows/`.                                    | rglob          |
| `counts.validate_yml_steps` | Number of `- name:` entries in `.github/workflows/validate.yml`.            | line scan      |
| `counts.samples_dirs`       | Subdirectories of `samples/` (one per UC fixture).                          | iterdir        |
| `counts.sample_data_files`  | `*.json` files under `sample-data/`.                                        | rglob          |
| `tree_sizes_kb`             | Recursive disk usage of top-level directories.                              | os.walk + stat |
| `timing.make_build_*`       | Wall-clock seconds + dist file count + dist MiB. Filled when `--build`.    | subprocess     |
| `timing.lighthouse_*`       | Captured manually (Phase 10/16). `null` until done.                         | manual         |
| `timing.mcp_search_*`       | Captured manually with `mcp/bench/`. `null` until Phase 17 lands.           | manual         |

## When to capture

1. **Once per minor version**, before tagging the release. Commit alongside
   the version bump in the same PR.
2. **Whenever a phase target is met** (e.g. P5 reduces `index.html` size).
   Capture a new baseline and reference it from the success-metrics
   section of the PR.
3. **Never speculatively** — baselines are facts, not aspirations. Don't
   commit a `v8.0.0.json` until v8.0.0 actually ships.

## How reviewers use the file

When an architecture PR claims a quantitative improvement, the architecture
PR template expects this table:

| Metric (from `data/baselines/v7.4.2.json`) | Before | After | Δ |
|---|---|---|---|

The "Before" number must be a value from the most recent committed
baseline. The "After" must be measurable on the PR branch with the same
tool that captured "Before". Anything else is hand-waving.

## Manual numbers

A few numbers can't be captured by `tools/capture_baselines.py` because
they need a browser, a network, or a live Splunk instance:

* **Lighthouse scores** — run `npx lighthouse https://<page>` against the
  GitHub Pages preview deployment. Record the Performance / Accessibility /
  Best-Practices / SEO scores in `timing.lighthouse_<page>`.
* **MCP latency** — `python3 mcp/bench/run_bench.py --tool search_use_cases`
  (Phase 17 deliverable). Record p50/p99 in `timing.mcp_search_*`.
* **CI wall-clock** — read it off a recent green `validate.yml` run on
  `main`; record in `timing.validate_yml_wall_seconds`.
* **Coverage %** — `coverage run -m pytest && coverage json -o /tmp/cov.json`
  (Phase 16 deliverable). Record per-module under `coverage.<path>`.

Edits to a captured baseline are allowed only for these manual numbers,
and only with a short commit message explaining the source of the
measurement.

## See also

* `tools/capture_baselines.py` — the generator.
* `schemas/baselines.schema.json` — the contract.
* Repo-overhaul plan §7 (success metrics) — every reduction target keys
  back to the latest baseline.
