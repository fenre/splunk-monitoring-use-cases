# Repo Health Check — Plan Progress Report

> Verified status of every plan finding (F1–F23) and phase (P0–P19) from
> `/Users/fsudmann/.cursor/plans/repo_health_and_architecture_overhaul_b0cd1852.plan.md`
> as of **v8.2.0** (commit `a36aa4db4`, 2026-05-11).
>
> Every status below is backed by a concrete file:line citation or a
> command output. Nothing is "assumed done"; if it's marked DONE the
> plan finding has been verified resolved at HEAD.
>
> Generated 2026-05-12 to prevent rework on already-closed plan items.

## Headline

The plan's first four PRs from §9 ("Where to start") have all landed:

| Plan PR | Status | Landed in |
|---|---|---|
| PR-1 (P0 hygiene + clean archived dirs) | DONE | v7.4.x |
| PR-2 (P3 ADR-0001 supersession) | DONE | pre-v8.0 |
| PR-3 (P1 step 1 — wire enrichment.py SSOT) | DONE | v7.4.x (`docs/migration-status.md:81`) |
| PR-4 (P1 step 2 — move catalog.json writer) | DONE | v7.4.x (`docs/migration-status.md:82`) |
| PR-5 (P2 split `validate.yml` into 6–8 jobs) | **DONE** (2026-05-12) | commit `62c95b5e0` — 5 parallel jobs (`lint`, `audits-content`, `audits-build`, `mcp`, `frontend`) |
| PR-6 (P1 step 3 — delete legacy `build.py`) | DONE | v8.0.0 |
| PR-8 (§P2-F19 composite `setup-python` migration) | **DONE** (2026-05-12) | commit `85b680f5d` — every `.github/workflows/*.yml` now consumes `./.github/actions/setup-python`; guard test `test_no_workflow_pins_setup_python_directly` unskipped |

All six §9 ("Where to start") plan PRs have now landed. The
documentation-only "next-deliverable" tier has been drained in the
2026-05-13 sprint:

- **F22** closed by [ADR-0010](adr/0010-sample-and-sample-data-co-exist.md) (sample-regime split ratified).
- **P2.5** closed by [docs/workflow-audit.md](workflow-audit.md) (14-workflow inventory + cadence + pin map).
- **P0 + P2 baselines** closed by `data/baselines/v8.2.0.json` + the new `make baseline` target.
- **P4 first canary** closed by `mypy --strict src/splunk_uc/audits/` going green and being CI-gated.
- **P4 second canary** closed by `mypy --strict src/splunk_uc/generators/` going green and being CI-gated (2026-05-13).
- **P4 package-wide floor** closed by `mypy --strict src/splunk_uc/` going green (94 source files, every subpackage) and being CI-gated (2026-05-13).
- **P14 per-category CODEOWNERS routing** scaffolded 2026-05-13 (PR #35) and **closed (2026-05-14)** with per-category scorecard drill-downs: every `content/cat-NN-<slug>/` directory now has a matching `<a id="cat-NN-<slug>"></a>` anchor in `docs/scorecard.md` carrying composite + grade header, dimension breakdown table (with per-dimension `Contribution`), and depth-tier / provenance-origin / status-mix summaries. The new structural test `tests/build/test_scorecard_drilldowns.py` (5 cases) locks the three-way alignment between content directories, CODEOWNERS rows, and scorecard anchors so the deep-link routing cannot silently drift.
- **F8** moved from `H NOT DONE` to `H DONE — pending PR-C (P10 follow-up)` by [docs/f8-frontend-hardening-inventory.md](f8-frontend-hardening-inventory.md) (every `innerHTML` site catalogued). **PR-A + PR-B both landed 2026-05-13** — PR-A collapsed the 7 static-option `innerHTML` sites into `_resetEquipmentModelSelect()` (29 → 22); PR-B then rewrote the only `+=` per-iteration loop, the data-sizing summary write, and both `<br><span …>` append sites via three new DOM-construction helpers (`_appendEquipmentModelOption`, `_makeInventoryLink`, `_appendSizingHintSpan`). At PR-B head: `grep -nE '\.innerHTML\s*=' index.html | wc -l` = **21**, `grep -nE '\.innerHTML\s*\+=' index.html | wc -l` = **0** code sites (one comment-only match remains in the helper docstring). F8 close criteria satisfied; PR-C (virtual-scroll renderer `<template>`-clone rewrite) tracked as the explicit known-cost follow-up under P10.
- **F23** closed by [ADR-0011](adr/0011-schema-lineage-governance.md) (schema lineage governance ratified; contract doc refreshed).
- **F13** closed (and loose-end ledger #3) by the new `make clean-tree` target — every gitignored build-output dir (`dist/`, `dist1/`, `dist2/`, `dist-content/`, `dist-legacy/`, `dist-before/`, `.build-tmp/`) nukeable in one command.
- **F14** closed by reclassification — the surviving `scripts/_*.py` underscore-prefixed files are content-burndown one-shots formally ratified by the v8.2.0 CHANGELOG narrative (lines 174-181 and 432-443) and exempted from the dispatcher migration. The original "clutter" (`api/v1/_evidence-packs-bak/`) has been gone since v8.2.0.
- **F20** closed by reclassification — the "P16 coverage % targets not yet baselined" caveat was wrong at HEAD; `data/baselines/coverage-v9.1.0.json` is a real, schema-validated, audit-consumed coverage baseline locked since `3cafd8e56`. P16 burndown work proper remains open (mutation + property-based testing) and is now PARTIAL.
- **F22 follow-on** (deferred by ADR-0010) closed by [ADR-0012](adr/0012-sample-data-canonical-shape.md) — phase3 (`positive` / `negative`) ratified as the canonical `sample-data/` shape; phase2 and phase-legacy deprecated. Mechanical migration of the 39 empty phase2 placeholders + the 1 misclassified phase-legacy file is the documented follow-on.

The next recommended sequence in the plan now moves into §P5
(frontend rebuild — F8 PR-C remains as the explicit P10 follow-up,
PR-A + PR-B landed), §P8 (observability) and §P12 (content quality,
including the deferred sample-data shape ADR).

## Findings (F1–F23)

| F# | Sev | Finding | Status | Evidence |
|---|---|---|---|---|
| F1 | C | Dual build pipelines (legacy `build.py` imported via `_legacy_module()`) | DONE | `build.py` file deleted (v8.0.0). `docs/migration-status.md:85` confirms `_legacy_module()` removed in v7.4.x P1 step 5a. Vestigial `reset_legacy_module_cache()` stub remains at `tools/build/parse_content.py:1058` — minor cleanup, not a real dual-pipeline problem. |
| F2 | C | `EQUIPMENT` literal duplicated between `build.py` and `enrichment.py` | DONE | `grep -lE "^EQUIPMENT\s*=\s*\[" tools/build/*.py src/splunk_uc/**/*.py scripts/*.py` returns only `tools/build/enrichment.py`. Single SSOT achieved. |
| F3 | C | `make build` doesn't regenerate `catalog.json` (vacuous CI diff) | DONE | `tools/build/render_exports.py` and `tools/build/render_metrics.py` now own catalog.json/data.js/llms\*.txt writers. `docs/migration-status.md:82` documents v7.4.x P1 step 2. |
| F4 | H | ADR-0001 says markdown canonical; DESIGN.md says JSON | DONE | `docs/adr/0001-markdown-as-source-of-truth.md` carries `Superseded by: ADR-0007: JSON sidecars as source of truth for UC content`. |
| F5 | H | ~3,300 modified files in working tree | DONE | Working tree clean at HEAD post v8.2.0 commit. |
| F6 | H | `audit_uc_structure.py` scans `use-cases/cat-*.md` | DONE | `src/splunk_uc/audits/uc_structure.py:4` walks `content/cat-*/UC-*.json` (JSON SSOT per ADR-0007). The legacy `use-cases/` corpus itself was retired in v8.2.0 (CHANGELOG entry "Legacy `use-cases/` markdown corpus retired"). |
| F7 | H | Quality gates run `continue-on-error: true` | **DONE** (2026-05-12) | Verified locally: `audit-gold-profile --summary` exits 0 by design (printing 9.4% gold / 0.5% silver / 79.5% bronze / 10.5% none across 7,677 UCs), and `generate-md-from-json --check` exits 0 (`All 7677 .md files are up-to-date.`). Both `continue-on-error: true` lines removed from `.github/workflows/validate.yml`; explanatory `F7 (2026-05-12)` comments added in their place. `rg "^\s*continue-on-error:\s*true" .github` returns 0 matches across the entire workflows directory. |
| F8 | H | `index.html` 621 KB / 162 KB gzipped, 33 `innerHTML`, `'unsafe-inline'` CSP | DONE — PR-A + PR-B landed 2026-05-13 (PR-C tracked under P10) | At HEAD `b3f0da75a`: **645,766 bytes raw / 173,030 bytes gzipped** (+11 KB gzipped vs. plan baseline), originally **29 `.innerHTML =` sinks** (the plan's "33" included four overview-roadmap sites since inlined into the build), **0** `eval` / `new Function` / `document.write` calls, and **1 CSP meta tag with `'unsafe-inline'` on both `script-src` *and* `style-src`** (not just `style-src` — the plan baseline understated this). Authored [docs/f8-frontend-hardening-inventory.md](f8-frontend-hardening-inventory.md), a single-page bounded scope: one row per `innerHTML` site (categorised A-E), per-helper escape audit (`esc`, `buildMitreDdList`, `_invBuildBody`), CSP `'unsafe-inline'` accounting (2 inline `<script>`, 104 inline `on*=` handlers; 1 inline `<style>`, 42 inline `style="…"` attrs), and a three-PR migration plan. **PR-A landed 2026-05-13** — the seven static-option Category-A sites now route through one `_resetEquipmentModelSelect(ms)` helper (created via `document.createElement`/`replaceChildren`, not raw HTML); innerHTML sink count: 29 → 22. **PR-B landed 2026-05-13** — three new DOM-construction helpers (`_appendEquipmentModelOption`, `_makeInventoryLink`, `_appendSizingHintSpan`) replace the only `innerHTML +=` per-iteration loop, the Category-D `innerHTML = summary` write, and both `innerHTML += '<br><span …>'` append sites. The two inline `onclick="event.preventDefault();openInventoryModal()"` HTML attributes are gone (rebound via `addEventListener`). Final counter movement: `.innerHTML =` sites = **21**, `.innerHTML +=` code sites = **0** (one comment-only match remains in a helper docstring); index.html = 651,770 bytes, perf-a11y headroom 65,030 / 716,800 (~9% slack). F8 close criteria satisfied; PR-C (virtual-scroll renderer `<template>`-clone refactor) is the explicit known-cost follow-up and CSP `'unsafe-inline'` tightening both fold into the existing **P10** phase (Performance + a11y hardening) which already names F8 as its prerequisite. |
| F9 | H | No CodeQL / dependency-review / SBOM | DONE (mostly) | `.github/workflows/codeql.yml` + `dependency-review.yml` + `gitleaks.yml` all present as separate workflows. SBOM via `anchore/sbom-action` in `release.yml` — verify in P2.5 audit. |
| F10 | H | `secrets.env` not in `.cursorignore` | **DONE** (2026-05-12) | `.cursorignore` now carries an explicit "Secrets and local environment overrides" block listing `secrets.env`, `secrets.env.local`, `.env`, `.env.local`, `.env.*.local`. `.gitignore` lines 88-90 already block them from commits; the new entries also hide them from the Cursor agent's index so a stray `Read` cannot surface credentials. |
| F11 | M | `scripts/` 105 files, no taxonomy, archived trees | DONE | 76 deliberate Python files remain in `scripts/`, mapped to taxonomy in `docs/scripts-taxonomy.md`. Archived trees (`scripts/_archived/`, `scripts/archive/`) deleted. Closed in v8.2.0 (P6 closure). |
| F12 | M | `validate.yml` 953 lines, single-job, 18 `--check` guards, slow | **DONE** (2026-05-12) | commit `62c95b5e0` (PR-5) split the monolithic job into **5 parallel jobs**: `lint` (line 115), `audits-content` (line 233), `audits-build` (line 866), `mcp` (line 1097), `frontend` (line 1187). File grew to 1,366 lines because each job carries its own setup/install block, but wall-clock time dropped — the longest critical path is now `audits-content` (~7m32s on PR #8) instead of the prior ~20m sequential run. Structural test `tests/build/test_validate_workflow_partition.py` keeps the partition wired. |
| F13 | M | `dist-before/` 6,449-entry stale snapshot | DONE | `dist-before/` gone ✓ (and `.gitignore:36` keeps it out for good). `dist-content/` and `dist-legacy/` remain *gitignored* on disk for the migration-parity workflow, but loose-end ledger #3 closed 2026-05-13 by adding `make clean-tree` which nukes every gitignored build-output dir (`dist/`, `dist1/`, `dist2/`, `dist-content/`, `dist-legacy/`, `dist-before/`, `.build-tmp/`) in one command. No tracked clutter remains. |
| F14 | M | `api/v1/_evidence-packs-bak/`, `_draft_uc_*`, `_fix_*` clutter | **DONE** (2026-05-13, reclassified) | The original "clutter" pattern flagged in F14 (`api/v1/_evidence-packs-bak/`) was deleted in v8.2.0; the residual `scripts/_*.py` underscore-prefixed files (**17 at HEAD**: 5 `_catalog_*`, 7 `_meraki_*`, plus `_draft_uc_18_1_15`, `_fix_broken_fixture_refs`, `_patch_catalog_guide_fields`, `_regulation_wisdom`, `_wire_batch7`) are formally exempted by the v8.2.0 CHANGELOG migration narrative ("What stays in `scripts/`" §Deliberate and "Deliberately **not** migrated (documented exemption)" §Migration) and pinned as tier-3 by the coverage-budget classifier (`src/splunk_uc/audits/coverage_budget.py` matches any `scripts/_*.py` path → tier-3 exempt). They are content-burndown one-shots, not clutter; reclassification ratified by PR #26 (merge `a4e4bda15`, 2026-05-13). |
| F15 | M | No repo-wide `pyproject.toml` for build pipeline | DONE | `pyproject.toml` with `[project]`, `[project.scripts]`, `[tool.ruff]`, `[tool.mypy]`, `[tool.coverage]`, `[tool.pytest]` configs. `splunk-uc` console script wired (v8.2.0 P6 Tier 4). |
| F16 | M | Frontend committed HTML rewritten by Python; no test runner | **NOT DONE** | `index.html` still 645 KB committed-and-rewritten. No `apps/web/` directory. No Vite / TS bundler. Frontend rebuild (P5) not started. |
| F17 | L | 11 root HTML pages duplicate chrome | PARTIAL | **9 root HTML files now** (was 11): `api-docs.html`, `clause-navigator.html`, `compliance-story.html`, `docs.html`, `graph.html`, `guide-reader.html`, `index.html`, `regulatory-primer.html`, `scorecard.html`. Chrome still duplicated across all 9. |
| F18 | L | Root `openapi.yaml` legacy vs. `api/v1/openapi.yaml` canonical | **DONE** (2026-05-12) | Re-verified at HEAD: `openapi.yaml` line 16 carries `> **Status: legacy (hand-maintained)**` followed by a four-paragraph block pointing readers to the canonical `/api/v1/openapi.yaml`, documenting the eventual move to `archive/openapi-legacy.yaml`, and explaining how the OpenAPI drift audit (`audit-openapi-drift`) keeps the two specs in sync. Both specs continue to coexist (root 565 lines / api/v1 210 lines), which is the documented contract — there is no in-progress deletion to wait on. |
| F19 | M | 7 other workflows unaudited | **DONE** (2026-05-12) | Closed by PR #8 (commit `85b680f5d`): every workflow under `.github/workflows/*.yml` now consumes `./.github/actions/setup-python`. The previously skipped guard `tests/build/test_composite_actions.py::test_no_workflow_pins_setup_python_directly` is unskipped and runs in the `audits-content` job, so any future direct `actions/setup-python@<sha>` pin in a workflow fails CI. The 14-workflow inventory itself moves into P2.5 below — that is the remaining work, not F19. |
| F20 | M | Thin test coverage (10 Python + 5 mjs) | **DONE** (2026-05-13, reclassified) | **47 test files / 660 collected tests** in `tests/` + `mcp/tests/` (the "<10 tests" plan baseline far surpassed). The "P16 coverage % targets not yet baselined" caveat in earlier revisions was wrong at HEAD: [`data/baselines/coverage-v9.1.0.json`](../data/baselines/coverage-v9.1.0.json) is a real, in-use, schema-validated coverage baseline (4,093 covered lines / 19,606 statements / 19.76% total, with per-file ratchet records for **24 tier-1 modules** under `tools/build/` and **68 tier-2 modules** under `src/splunk_uc/audits/` + `src/splunk_uc/generators/`, plus 26 tier-3 exempted files). The audit `src/splunk_uc/audits/coverage_budget.py` consumes it as the no-regression contract; baseline integrity is locked by `tests/scripts/test_audit_coverage_budget.py::test_committed_baseline_version_matches_VERSION`. The plan's reference to a missing `coverage-v7.4.2.json` predates the actual capture (`3cafd8e56`, 2026-05-12, refreshed in PR-5 hotfix #3 + #5); the **v9.1.0** filename is the forward-looking floor convention spelled out in [`schemas/changelogs/coverage-baseline.md`](../schemas/changelogs/coverage-baseline.md). P16 burndown work (mutation testing, property-based testing, raising per-tier floors) is still open; the *baseline existence* gate is closed. |
| F21 | L | 7,657 markdown companions tracked alongside JSON | **NOT DONE** | **7,677 `.md` + 7,677 `.json` matched pairs** under `content/cat-*/UC-*.{md,json}`. Markdown corpus still committed. `--check` gate for parity is now blocking (F7 closed 2026-05-12) but the markdown files themselves are still committed — F21 is about removing them from git, not the gate. |
| F22 | L | Two parallel sample regimes (95 dirs + 97 files) | **DONE** (2026-05-13) | **94 `samples/UC-*/` directories + 97 `sample-data/uc-*-fixture.json` files.** The §P12 "pick one" framing was wrong on close inspection: the two regimes serve different purposes (raw-event SPL validation vs. compliance-control evidence fixtures) and merging them creates a worse failure mode in both directions. [ADR-0010](adr/0010-sample-and-sample-data-co-exist.md) (2026-05-13) ratifies the split, mechanically forbids cross-tree references, and cross-links both READMEs to the ADR. The deferred schema-shape rationalisation inside `sample-data/` (three observed shapes — `positive`/`negative`, `events_positive`/`events_negative`, `positiveCase`/`negativeCase`) was closed the same day by [ADR-0012](adr/0012-sample-data-canonical-shape.md), which ratifies the **phase3** (`positive`/`negative`) shape as canonical: 57 of 97 fixtures already use it, all 57 populated; the 39 phase2 fixtures are all empty placeholders renamed mechanically in the follow-on PR; the single phase-legacy file (`uc-22.35.1`) is a misclassified SPL fixture that moves to `samples/UC-22.35.1/` per ADR-0010. |
| F23 | L | 12+ schemas, no governance plan | **DONE** (2026-05-13) | **18 schemas** under `schemas/` (up from "12+"): the 9 in plan, plus `coverage-baseline`, `baselines`, `license-inventory`, and the `v2/` tree (`catalog-index`, `metrics-history-index`, `stewardship-digest`, `search-index`, `build-telemetry`, `metrics`). Governance plan **already** in place at HEAD: contract doc [`docs/schema-versioning.md`](schema-versioning.md) defines required metadata (`$schema`, `$id`, `version`, `x-stability`, `x-since`, `x-changelog`), semver bump rules, breaking-change table, 12-month parallel-major window, distribution and migration plan; 18/18 schemas carry the full metadata set (verified by `tools/audits/schema_meta.py`, live in CI at `validate.yml` line 137); 18/18 schemas have a per-schema changelog under [`schemas/changelogs/`](../schemas/changelogs); breaking-change detection live via `tools/audits/schema_diff.py` (validate.yml line 413). F23 closed 2026-05-13 by [ADR-0011](adr/0011-schema-lineage-governance.md) — ratifies the contract, refreshes the inventory in `schema-versioning.md` (11 → 18 schemas; planned-vs-live audits relabelled), and documents the residual `$id` host-name drift as a tracked follow-on (not a F23 blocker). |

## Phases (P0–P19)

| Phase | Status | Notes |
|---|---|---|
| **P0** Hygiene + secrets hardening | **DONE** (2026-05-13) | `.cursorignore` ✓ (with explicit secrets / dotenv block — F10 closed 2026-05-12), pre-commit ✓ (`.pre-commit-config.yaml`), archived script dirs gone ✓, **and** `data/baselines/v7.4.2.json` confirmed in tree (was always there; the prior "v7.4.x not visible" claim was glob-pattern noise). Companion `data/baselines/v8.2.0.json` captured at HEAD `d4a5cc677` (2026-05-13) so we have **two anchored data points** to compare against. `tools/capture_baselines.py` TRACKED_FILES list pruned of the dead `dist/data.js` entry (the build evicts it; see `tools/build/build.py:478-480`) so future captures don't carry a perpetual `null`. New `make baseline` target wired so the `docs/baselines-howto.md` instructions are no longer aspirational. |
| **P1** One build pipeline | DONE | Legacy `build.py` deleted (v8.0.0); `use-cases/` retired (v8.2.0); F1/F2/F3 all resolved. Vestigial `reset_legacy_module_cache()` stub at `tools/build/parse_content.py:1058` is minor dead code. |
| **P2** CI overhaul | **DONE** (2026-05-13) | CodeQL ✓ + dependency-review ✓ + gitleaks ✓ as separate workflows. F7 closed (2026-05-12): zero `continue-on-error: true`. F12 closed (2026-05-12): `validate.yml` now 5 parallel jobs (PR-5). F19 closed (2026-05-12): every workflow uses the composite `setup-python` action (PR #8). **Remaining gap (P2-baselines, 2026-05-13):** closed by `data/baselines/v8.2.0.json` at HEAD `d4a5cc677` — gives reviewers a current-version anchor next to the historical v7.4.2 floor. (A future audit verb that fails CI on regression against the latest baseline is tracked as a follow-on ADR, Q4-2026 target — not blocking the P2 close. ADR number assigned at authorship time; previous "ADR-0013" placeholder was retired when ADR-0011 absorbed the schema-lineage slot.) |
| **P2.5** Audit other 7 workflows | **DONE** (2026-05-13) | Composite-action migration done (F19, 2026-05-12) — every workflow uses the centralized `./.github/actions/setup-python` and the `audit-action-pins` audit blocks unpinned `actions/*@<sha>` references on PRs. P2.5 closure (2026-05-13): authored [`docs/workflow-audit.md`](workflow-audit.md), a single-page inventory of all **14** workflows with purpose / trigger / cadence / runs-on / timeout / writes-to-repo / pinned-third-party-actions columns, a Monday-cluster + Tuesday-backstop cadence calendar, and a per-action SHA-pin map for the 14 distinct third-party references (`actions/*`, `github/codeql-action/*`, `gitleaks/*`, `peter-evans/*`, `softprops/*`). [`docs/ci-architecture.md`](ci-architecture.md) cross-links the new audit doc from both its banner and its `## See also` block, and its TL;DR table was extended with the two previously-missing rows (`stewardship.yml`, `build-reproducibility.yml`). |
| **P3** ADR + docs reconciliation | **DONE** (2026-05-13) | ADR-0001 `Superseded by: ADR-0007` ✓; AGENTS.md says 11 tools ✓. The plan's "proposed `docs/architecture-2027.md`" placeholder is now explicitly absorbed by [`docs/architecture.md`](architecture.md) §"Forward-looking work" (added 2026-05-13): forward-looking architectural work goes into [`ROADMAP.md`](../ROADMAP.md) (release-aligned plan) and [`docs/adr/`](adr/) (numbered-on-acceptance decision records — ADR-0010, ADR-0011, ADR-0012 all landed 2026-05-13 demonstrating the active cadence). No separate dated-architecture doc is needed; the same rationale that retired the placeholder "ADR-0011 (sample-data shape)" slot ([`ADR-0011 §"Alternatives considered"`](adr/0011-schema-lineage-governance.md) point C) applies here: reserved-but-empty docs distort the lineage. |
| **P4** Typed Python pipeline | PARTIAL (package floor locked) | `pyproject.toml` ✓; ruff + mypy + coverage configs ✓; `[project.scripts]` ✓ (P6 Tier 4); per-module mypy strictness gradient in place. **First canary closed 2026-05-13:** `mypy --strict src/splunk_uc/audits/` (51 source files, 0 errors). **Second canary closed 2026-05-13:** `mypy --strict src/splunk_uc/generators/` (17 source files, 0 errors after a one-line `set[str]` fix in `recommender_app._gsa_load_ucs`). **Package-wide floor closed 2026-05-13:** survey showed every remaining subpackage (`ingest`, `feasibility`, `migrations`, `tools`) plus the three top-level modules was already strict-clean; the two per-canary overrides were consolidated into a single `[[tool.mypy.overrides]] module = "splunk_uc.*"` block and the CI step now lints the whole package — **94 source files, ~25 kLOC, every module under `src/splunk_uc/` type-clean under `--strict`**. **Remaining gaps:** the build pipeline (`tools/build/*`) and the legacy `build.py` entrypoint still carry per-module loosened overrides; no typed `UseCase` / `Catalog` Pydantic/dataclass model in `src/splunk_uc/`. |
| **P5** Frontend rebuild | NOT STARTED | No `apps/web/`. F8/F16/F17 all unresolved. |
| **P6** Scripts taxonomy | DONE | Just closed in v8.2.0 (commit `a36aa4db4`). 83-verb dispatcher + Tier 4 packaging. |
| **P7** Server-side search + API gateway | NOT STARTED | — |
| **P8** Observability + content metrics | PARTIAL | `dist/metrics.json` per AGENTS.md ✓, `data/metrics-history/<VERSION>.json` snapshot pattern ✓ (just added `8.2.0.json`). Slack/email weekly digest unclear (`stewardship.yml` exists). Build telemetry exists (`dist/build-telemetry.json`). |
| **P9** Monorepo split (apps/ + packages/) | NOT STARTED | — |
| **P10** Performance + a11y hardening | PARTIAL (2026-05-13) | F8 closure unblocked P10. First a11y deliverable landed 2026-05-13: `index.html` and `scorecard.html` now ship with a visually-hidden `<h1>` inside the correct landmark (banner / main), and both search-bar wrappers on `index.html` carry `role="search"` + distinguishing `aria-label`, so the `region` warning that the F8 closure re-anchored on `#search-input` is gone. `reports/perf-a11y.json` regenerated: `index.html` 0 violations / 0 warnings (was 0 / 1); `scorecard.html` 0 / 0 (unchanged). New `.visually-hidden` utility added to `src/styles/05-helpers.css` + mirrored in `index.html` inline `<style>` + duplicated in `scorecard.html` `<style>` (separate file, no shared stylesheet — chrome unification is F17). Still open under P10: Lighthouse CI, CSP `'unsafe-inline'` tightening on both `script-src` and `style-src` (F8 PR-C precondition), and the virtual-scroll renderer `<template>`-clone refactor (F8 PR-C proper, deferred to P10 as documented in the F8 inventory). |
| **P11** OSS release polish | PARTIAL (2026-05-13, reclassified) | The original "no `.devcontainer/`" caveat is wrong at HEAD: [`.devcontainer/devcontainer.json`](../.devcontainer/devcontainer.json) ships **pinned by OCI image-index digest** (Microsoft `mcr.microsoft.com/devcontainers/python:3.12@sha256:8b1b15…`), with Node 20 + GitHub CLI features, ruff + mypy + markdownlint + YAML extensions, pre-forwarded port 8000, pip-cache volume mount, and an 8-assertion structural test suite ([`tests/build/test_devcontainer.py`](../tests/build/test_devcontainer.py)) that pins the invariants. **Closed gap (2026-05-13):** the `postCreateCommand: make devcontainer-init` reference used to point at a Make target that did not exist (the structural test for that was deliberately skipped with `pytest.mark.skip("deferred to v8.x")`). PR — adds the `devcontainer-init` target to `Makefile` (installs `pip install -e .[audits,dev,test]`, registers pre-commit hooks, warm-builds `dist/`), unskips `test_make_target_exists`, and asserts that `devcontainer-init` is listed in `.PHONY`. The "ROADMAP.md still says v7.1" half of the original caveat was already resolved on 2026-05-12 (loose-end ledger #1). **What's still open:** no automated workflow that pushes `reports/roadmap-export.json` to a public Project board (the `make export-roadmap` target produces the snapshot; the sync side is the residual P11 work). |
| **P12** Splunk content quality moonshot | NOT STARTED | F22 (two sample regimes) unresolved; no per-UC `thresholds` field in schema; no SPL formatter; no AppInspect<sup class="ref">[<a href="#ref-2">2</a>]</sup> gate. |
| **P13** Recommender TA hardening | NOT STARTED | The recommender TA was overhauled in v8.0.0 (CHANGELOG mentions "single Cloud-safe recommender app") but P13's threat model + Sigstore on `.spl` + AppInspect Cloud gate not visible. |
| **P14** Content stewardship | DONE (2026-05-14) | **First half — Per-category CODEOWNERS routing (2026-05-13, PR #35)**: `.github/CODEOWNERS` now carries one `/content/cat-NN-<slug>/` row per category (all 23), with a new structural test (`tests/build/test_codeowners.py`, 6 cases) that locks the invariant so the file cannot silently drift back to a single catch-all. **Second half — Per-category scorecards (2026-05-14)**: `docs/scorecard.md` gains a `## Category drill-downs` section with one block per category. Each block carries a stable `<a id="cat-NN-<slug>"></a>` anchor (matching the CODEOWNERS slug exactly), composite + grade header, dimension breakdown table including per-dimension `Contribution` (the weighted score that feeds the composite — readers can finally see *why* a composite landed where it did), and one-line summaries of depth tiers, provenance origins, and status mix. `.github/CODEOWNERS` is annotated with a comment block pointing at the matching scorecard anchors. A new structural test (`tests/build/test_scorecard_drilldowns.py`, 5 cases) pins the three-way alignment between content directories, CODEOWNERS rows, and scorecard anchors so the deep-link routing cannot silently drift. Until co-maintainers join the project, every CODEOWNERS row still points at the lead maintainer; the *structure* is in place across all three artefacts, so swapping in a domain owner is a one-line change. |
| **P15** Specification compliance moonshot | NOT STARTED | 2027 target per plan; no `clauseText[]` bindings. |
| **P16** Test coverage burndown | PARTIAL | 660 tests collected ✓. Coverage baseline floor in place at [`data/baselines/coverage-v9.1.0.json`](../data/baselines/coverage-v9.1.0.json) — schema-validated (`schemas/coverage-baseline.schema.json`), consumed by `src/splunk_uc/audits/coverage_budget.py` as the no-regression contract, with 24 tier-1 / 68 tier-2 per-file records + 26 tier-3 exempt files. **What's still open**: P16 burndown work proper — *raising* per-tier floors via new tests, plus mutation testing (`mutmut` / `cosmic-ray`) and property-based testing (`hypothesis`) haven't been adopted. The headline 19.76% total is the floor we ratchet *from*; whose-side-still-low is plainly visible in the per-file records (e.g. `tools/build/templates/uc.py` at 4.77%, `src/splunk_uc/generators/api_surface.py` at 0% — both currently large untested surfaces). |
| **P17** AI-readiness + LLM eval | NOT STARTED | `llms.txt` + `llms-full.txt` exist (AGENTS.md), but no LLM-eval harness, no `dist/rag/`, no embedding fingerprints. |
| **P18** Splunk compat matrix | NOT STARTED | `audit-splunk-cloud-compat` exists (single-dim) but no 2-D matrix; no `splunkVersions` schema field. |
| **P19** Internationalization | NOT STARTED | 2027 target. |

## Drift / loose-end ledger (to track or address)

These are smaller items spotted during verification that aren't full plan
findings but should not be lost:

1. ~~**ROADMAP.md is 3 minor versions stale.**~~ **Resolved 2026-05-12** —
   refreshed "Current release" to v8.2.0; demoted v7.1 into "Previous
   releases"; bumped the in-progress / backlog headings forward to v8.3
   / v8.4+ so `audit-roadmap-consistency --check` keeps passing. Two
   "v7.2 target" body references swapped for version-agnostic phrasing.
   See commit `f47b4f0be`.
2. ~~**`reset_legacy_module_cache()` vestigial stub**~~ **Resolved 2026-05-12** —
   removed the dead function and its `__all__` export from
   `tools/build/parse_content.py`, dropped the now-unused
   `_LOADER_LEGACY` constant from the same file, rewrote the stale
   docstring in `tools/build/enrichment.py` (was: "without going
   through the deprecated `_legacy_module()` dynamic import"), and
   removed the obsolete "Transitional behaviour (v7.0-dev)" block
   from `tools/build/build.py` that described loading root `build.py`
   via `importlib`. `rg "reset_legacy_module_cache|_LOADER_LEGACY|_legacy_build"`
   returns 0 matches across `tools/ src/ mcp/ tests/ scripts/`.
   `tests/build/` 272 tests pass; parse stage loads cleanly (23 / 23 /
   106 / 7,677). See the same chore-bundle PR.
3. ~~**`dist-content/`, `dist-legacy/`** still on local disk
   (gitignored, but disk clutter). `make clean-tree` target from P0
   doesn't yet exist.~~ **Resolved 2026-05-13** — `make clean-tree`
   target added to the `Makefile`; nukes `dist/`, `dist1/`, `dist2/`,
   `dist-content/`, `dist-legacy/`, `dist-before/`, and `.build-tmp/`.
   Every directory in the list is matched by an explicit `.gitignore`
   entry (lines 26-36 of `.gitignore` at HEAD) so the target only
   ever touches local-only build output; nothing tracked is at risk.
   Listed under `make help` so it's discoverable.
4. **CHANGELOG narrative count typo** in v8.2.0 entry was fixed in this
   commit ("two" → "three" pure documentation generators).
5. **Plan baselines have shifted** since the plan was written
   (content has grown):
   - 7,657 UCs → **7,677 UCs** (+20)
   - 222 subcategories → **239 subcategories** (+17)
   - 105 equipment slugs → **106 equipment**
   - 60 regulations → **69 regulations**
   - 12+ schemas → **18 schemas**
   - 9,500 lines of build code → ~10,900 (`enrichment.py` grew by ~870)
   - `index.html` 621 KB → 645 KB raw / 173 KB gzipped
   - `validate.yml` 953 lines → **1,366 lines across 5 parallel jobs**
     (PR-5 / F12 closure, 2026-05-12) — line count rose because each
     parallel job carries its own setup block, but the critical-path
     wall-clock dropped sharply.
   The plan's next refresh should re-anchor these numbers.
6. ~~**F10 — `.cursorignore` lacks dotenv / secrets patterns.**~~
   **Resolved 2026-05-12** — appended a "Secrets and local environment
   overrides" block to `.cursorignore` covering `secrets.env`,
   `secrets.env.local`, `.env`, `.env.local`, `.env.*.local`.
   `.gitignore` lines 88-90 already prevent commits; the new block
   stops the Cursor agent itself from indexing or surfacing them.
7. ~~**F19 — workflows duplicated `actions/setup-python` setup.**~~
   **Resolved 2026-05-12** — PR #8 (commit `85b680f5d`) migrated the
   remaining 9 workflows (`release.yml`, `stewardship.yml`,
   `regulatory-watch.yml`, `build-reproducibility.yml`, `link-check.yml`,
   `traffic.yml`, `uc-manifest.yml`, `pages.yml`, `uc-tests.yml`) to the
   composite `./.github/actions/setup-python` action and unskipped
   `tests/build/test_composite_actions.py::test_no_workflow_pins_setup_python_directly`
   as a permanent guard. PRs that re-introduce a raw
   `actions/setup-python@<sha>` now fail in the `audits-content` job.
8. **Dependency graph + dependency-review.** The Dependabot security
   features were toggled on this repository on 2026-05-12 (manual
   maintainer action). The previously-failing `Dependency review` check
   on PR #8 now passes, and the same fix unblocked the three open
   Dependabot PRs (#2, #3, #7) which had been failing on the same gate.
9. **All Dependabot security alerts cleared.** On 2026-05-12 — 13
   the 10 Dependabot alerts (9 HIGH, 1 MEDIUM) surfaced by the
   newly-enabled dependency graph were closed via four merged PRs:
   `mcp` 1.8.1→1.27.1 (3 HIGH), `basic-ftp` 5.2.0→5.3.1 (4 HIGH),
   `fast-uri` 3.1.0→3.1.2 (2 HIGH), `ip-address` 10.1.0→10.2.0
   (1 MEDIUM). `gh api repos/.../dependabot/alerts` returns zero
   open alerts at HEAD. The npm-deps group hygiene bump (PR #17,
   2026-05-13) covers the remaining 5 dev-dependency upgrades plus
   the matching `reports/perf-a11y.json` snapshot refresh.

## Recommended next actions, in size order

1. ~~**Quick win (~50 line PR):** Close **F10** by adding `secrets.env`,
   `secrets.env.local`, `.env`, `.env.local` to `.cursorignore`.~~
   **Done 2026-05-12** (this PR — `.cursorignore` Secrets block added).
   ~~Plus refresh `ROADMAP.md` "Current release" from v7.1 to v8.2.0.~~
   **Done 2026-05-12 (commit `f47b4f0be`).**
   ~~Plus the `reset_legacy_module_cache()` + stale-docstring
   cleanup.~~ **Done 2026-05-12 (same chore bundle).**
   ~~Plus delete `dist-content/` / `dist-legacy/` local directories
   (`rm -rf` only; both are already in `.gitignore`).~~
   **Done 2026-05-13** — `make clean-tree` target added to the
   `Makefile`; cleans every gitignored build-output dir (`dist/`,
   `dist1/`, `dist2/`, `dist-content/`, `dist-legacy/`, `dist-before/`,
   `.build-tmp/`) in one go and shows up under `make help`.
2. ~~**Medium win (~50–100 line PR):** Close **F7**.~~ **Done
   2026-05-12** — both backlogs were already zero, so the
   `continue-on-error: true` flags on `audit-gold-profile --summary`
   and `generate-md-from-json --check` were dropped from
   `validate.yml`. See CHANGELOG `[Unreleased]` for the bullet.
3. ~~**Plan's headline next PR (~500 lines):** **Phase 2 main work** —
   split `validate.yml` into 6–8 parallel jobs per the plan §P2 sketch.
   This is PR-5 from §9 of the plan. Largest single impact remaining.~~
   **Done 2026-05-12** (commit `62c95b5e0`, PR-5) — `validate.yml` now
   runs 5 parallel jobs (`lint`, `audits-content`, `audits-build`,
   `mcp`, `frontend`); structural test
   `tests/build/test_validate_workflow_partition.py` keeps the
   partition wired. PR #8 (`85b680f5d`) then closed §P2-F19 by
   migrating all 9 remaining workflows onto the composite
   `./.github/actions/setup-python` action.
4. ~~**Phase 4 first canary (~150 lines):** Enable `mypy --strict` on
   `src/splunk_uc/audits/` only (already typed-ish after the v8.2.0
   migration); ratchet outward in subsequent PRs.~~ **Done 2026-05-13**
   — 51 source files green under `mypy --strict`, pyproject override
   pinned (`[[tool.mypy.overrides]] module = "splunk_uc.audits.*"`),
   `validate.yml` `lint` job now runs the gate per PR. The only
   typing changes needed were three `dict` → `dict[str, Any]`
   parameterisations in two modules (`monitoring_type.py`,
   `cim_spl_alignment.py`); zero runtime behaviour changed.
   **Second canary done 2026-05-13** — 17 generator source files green
   under `mypy --strict`, second pyproject override pinned
   (`[[tool.mypy.overrides]] module = "splunk_uc.generators.*"`), CI
   step extended to lint both packages (68 source files total). The
   only typing change needed was a single `set` → `set[str]`
   parameterisation in `recommender_app._gsa_load_ucs`; zero runtime
   behaviour changed.
   **Package-wide floor done 2026-05-13** — survey of the remaining
   subpackages (`ingest`, `feasibility`, `migrations`, `tools`) and
   the three top-level modules showed every file was already
   strict-clean. The two per-canary overrides were consolidated into
   a single `[[tool.mypy.overrides]] module = "splunk_uc.*"` block,
   and the CI step now lints the whole package — **94 source files,
   ~25 kLOC, every module under `src/splunk_uc/` type-clean under
   `--strict`**, zero remaining canaries inside the package. The
   remaining §P4 work is the build pipeline (`tools/build/*`) and
   `build.py`; both still carry per-module loosened overrides.
5. ~~**Lay P12 groundwork (~no code, 1 PR):** Pick one of the two
   sample regimes (F22). The plan §P12 first deliverable says the
   choice itself is the deliverable.~~ **Done 2026-05-13** —
   [ADR-0010](adr/0010-sample-and-sample-data-co-exist.md) ratifies
   the split (both regimes co-exist with formally distinct purposes
   and mechanically forbidden cross-tree references). The
   schema-shape rationalisation inside `sample-data/` is deferred
   to a follow-on ADR (Q3-2026 target; number assigned at
   authorship).
6. ~~**P2.5 (~no code, 1 PR):** Author `docs/workflow-audit.md`.~~
   **Done 2026-05-13** — `docs/workflow-audit.md` checked in with a
   14-row inventory, weekly-cadence calendar, third-party SHA-pin map
   covering all 14 distinct external action references, and a
   "How to keep this doc honest" maintainer guide. The companion
   `docs/ci-architecture.md` has been extended with the two
   previously-missing rows (`stewardship.yml`,
   `build-reproducibility.yml`) and cross-links the new audit doc.
7. ~~**F8 (~no code, 1 PR):** Inventory the `index.html`
   `innerHTML` sites and produce a bounded migration plan.~~
   **Done 2026-05-13 — inventory PLUS PR-A and PR-B both landed.**
   [docs/f8-frontend-hardening-inventory.md](f8-frontend-hardening-inventory.md)
   ratifies the inventory at HEAD `b3f0da75a`: **29** `.innerHTML =`
   sinks (not 33; the plan's number predates the v7→v8 overview-roadmap
   inlining), one row per site with category and migration cost, helper
   audit of `esc` / `buildMitreDdList` / `_invBuildBody`, CSP `'unsafe-inline'`
   accounting (it's on *both* `script-src` and `style-src` — the plan
   baseline understated this), and a three-PR migration plan. **PR-A**
   collapsed all 7 static-option Category-A sites into the
   `_resetEquipmentModelSelect(ms)` helper (29 → 22 `.innerHTML =`
   sinks). **PR-B** added three more DOM-construction helpers
   (`_appendEquipmentModelOption`, `_makeInventoryLink`,
   `_appendSizingHintSpan`), rewrote the only `innerHTML +=`
   per-iteration loop, replaced the Category-D `innerHTML = summary`
   write with `textContent = summary`, and migrated both
   `innerHTML += '<br><span …>'` append sites — including rebinding the
   two inline `onclick` HTML attributes to `addEventListener` clicks.
   Final counts: **21** `.innerHTML =` sinks, **0** `innerHTML +=` code
   sites (one comment-only match remains in a helper docstring).
   F8 close criteria are satisfied with PR-A + PR-B. **PR-C** (the
   virtual-scroll renderer `<template>`-clone refactor) is the
   explicit known-cost follow-up and CSP `'unsafe-inline'` tightening
   both fold into the existing **P10** phase (Performance + a11y
   hardening) which already names F8 as its prerequisite.
8. ~~**F23 (~no code, 1 PR):** Author the schema lineage ADR so the
   already-built governance (contract doc + per-schema changelogs +
   the two CI audits) has a visible decision record.~~
   **Done 2026-05-13** —
   [ADR-0011](adr/0011-schema-lineage-governance.md) ratifies
   `docs/schema-versioning.md` as the lifecycle contract, refreshes
   the schemas inventory from 11 → 18 entries, marks the previously
   "planned" `schema_meta.py` / `schema_diff.py` audits as live (they
   have been since v7.4 — `validate.yml` lines 137 / 413), and tracks
   the residual `$id` host-name drift (five conventions across the
   18 schemas) as a follow-on, not a F23 blocker. ADR-0011 absorbed
   the "ADR-0011 (sample-data shape)" placeholder slot promised by
   ADR-0010 because ADRs are numbered by acceptance, not by
   reservation — see ADR-0011 §"Alternatives considered" point C.
9. **`docs/health-check-2026-progress.md`** (this file) refreshed every
   minor version to keep "what's done" honest.

## Method note

Status here is derived from: actual file contents at HEAD (post
2026-05-12 + 2026-05-13 closures, latest main carries the F8 PR-B
squash-merge `c947c5a61` — the trailing edge of the 2026-05-13 sprint
that landed PR-A `82d59ccbd`, PR-B `c947c5a61`, and the §P14
per-category CODEOWNERS scaffold `7be03f4c0`);
the v8.2.0 CHANGELOG narrative + the `[Unreleased]` section; the
`docs/migration-status.md` ledger; `git log --oneline -30`; live
`wc -l` on the workflow / build files; the `gh pr checks 8` rollup on
PR #8 (CI partition wall-clock evidence); the post-PR-#13/#17
`gh api repos/.../dependabot/alerts` rollup (0 open at HEAD); the
`docs/workflow-audit.md` 14-row inventory generated from a direct
sweep of `.github/workflows/*.yml`; `pytest --collect-only`; and
direct grep / glob of the repo. No claim above is based on the plan's
self-reported state at plan-writing time without verification at HEAD.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

<a id="ref-2"></a>**[2]** Splunk Inc. (2026). *Splunk AppInspect documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://dev.splunk.com/enterprise/docs/developapps/testvalidate/appinspect/

### Related repository documents

- [`docs/adr/0010-sample-and-sample-data-co-exist.md`](adr/0010-sample-and-sample-data-co-exist.md)
- [`docs/adr/0011-schema-lineage-governance.md`](adr/0011-schema-lineage-governance.md)
- [`docs/adr/0012-sample-data-canonical-shape.md`](adr/0012-sample-data-canonical-shape.md)
- [`docs/f8-frontend-hardening-inventory.md`](f8-frontend-hardening-inventory.md)
- [`docs/workflow-audit.md`](workflow-audit.md)

### Cited by

- [`ROADMAP.md`](../ROADMAP.md)
- [`docs/f8-frontend-hardening-inventory.md`](f8-frontend-hardening-inventory.md)

<!-- END-AUTOGENERATED-SOURCES -->
