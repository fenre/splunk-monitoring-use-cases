# Repo Health Check — Plan Progress Report

> Verified status of every plan finding (F1–F23) and phase (P0–P19) from
> `/Users/fsudmann/.cursor/plans/repo_health_and_architecture_overhaul_b0cd1852.plan.md`
> as of HEAD **v8.6.4** (commit `b9f17b407` + post-corpus-expansion
> regen cascade, pushed 2026-05-16 evening).
> The doc was first generated 2026-05-12 against v8.2.0
> (commit `a36aa4db4`); the 2026-05-16 refresh re-anchored counts and
> status against the post-OT-deep-dive HEAD plus the open work it
> introduced, and the same-afternoon series of pushes landed the OT
> regulation arc (Phases 1-6), the doc-refresh / F10 trailing closure,
> the F7 `.md` parity regen (216 files), the **P5 frontend rebuild
> scaffold first cut** ratified by
> [ADR-0013](adr/0013-frontend-rebuild-scaffold.md), the
> **P5 first real migration target** — typed companion + 81
> shape-invariant tests for `non-technical-view.js` plus the CI wiring
> that finally puts `apps/web/`'s `npm test` + `npm run typecheck`
> on every PR and push (drift ledger #14, F16 test-runner half closed),
> the **CI unblock + new `audit-spl-references` feature accidentally
> bundled** (drift ledger #15 — forward-fixed via CHANGELOG + ledger
> update, no force-push undo), the **post-leak three-commit
> cleanup-chain** that took CI back to green (`mypy --strict` fix to
> `spl_references.py:_load_reference`, ATT&CK ID hygiene removing
> `T0810` / `TA0008` / `T1551` from 5 cat-22 UCs, and surgical
> absorption of the four new SPL-reference modules into the per-file
> coverage baseline — all in drift ledger #15), the OT-arc
> post-regen chain (`reports/sandbox-validation.json` +
> `splunk-apps/splunk-uc-recommender/` refreshed to absorb the 217
> new UCs introduced by Phases 1-6 of the OT regulation arc), and the
> **post-corpus-expansion regen cascade** (drift ledger #16): after the
> maintainer's `2032c631a` (SPL reference corpus expansion + glob-aware
> sourcetype matching) and the Phase 4 backfill in `b9f17b407` landed,
> two `validate.yml` jobs were still red on the new HEAD —
> `audits-content` / Phase 3.2 cross-cutting regeneration check and
> `frontend` / Phase 4.5f perf + a11y Node drift guard. The cascade
> runs the canonical dependency chain end-to-end
> (`generate-phase3-2-cross-cutting` → `generate-phase3-3-derivatives`
> → `generate-mapping-ledger` → `generate-api-surface` →
> `generate-clause-index` → `generate-story-payload` →
> `generate-recommender-app` → `generate-md-from-json` →
> `scripts/generate_backlinks.py` → `scripts/generate_doc_references.py`
> → rebuild `dist/` → `audit-perf-a11y`) so CI converges in one push
> instead of bouncing between freshness audits.
>
> Every status below is backed by a concrete file:line citation or a
> command output. Nothing is "assumed done"; if it's marked DONE the
> plan finding has been verified resolved at HEAD.
>
> **Branch divergence at refresh time:** local `main` and `origin/main`
> are in sync at `b51023419`. The 6 OT-arc + closure commits
> (`8bed23912` → `b51023419`) rebased cleanly onto the `origin/main`
> P14 scorecard-drill-down extension (`00729f198`); no force-push was
> required. Drift ledger items #11 + #12 are both resolved; #13 (the
> P5 scaffold) is the new uncommitted change in this same refresh.

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
| F7 | H | Quality gates run `continue-on-error: true` | **DONE** (2026-05-12 strip; 2026-05-16 local-`main` regen closes the post-OT-arc parity gap) | The `continue-on-error: true` strip from 2026-05-12 still stands — `rg "^\s*continue-on-error:\s*true" .github` returns 0 matches across the entire workflows directory. The two formerly-flagged gates are now wired to fail PRs on drift. **2026-05-16 follow-up**: the post-OT-arc parity gap that this row was flagging at the morning refresh (`216/7929 .md files are stale or missing` on local HEAD) was closed in the afternoon by running `python -m splunk_uc generate-md-from-json` without `--check`. The regen wrote 168 new `.md` companions in `cat-22` subcategories 22.54-22.63 (the OT regulation Phases 2b-6 JSON-only authoring) and 48 normalisation-drift updates (45 in cat-22, 3 in cat-17 — e.g. UC-17.1.33 dropping a `monitoringType` duplicate). `--check` now reports `All 7929 .md files are up-to-date.`. Tracked as drift ledger item #12 (resolved). |
| F8 | H | `index.html` 621 KB / 162 KB gzipped, 33 `innerHTML`, `'unsafe-inline'` CSP | DONE — PR-A + PR-B landed 2026-05-13 (PR-C tracked under P10) | At HEAD `b3f0da75a`: **645,766 bytes raw / 173,030 bytes gzipped** (+11 KB gzipped vs. plan baseline), originally **29 `.innerHTML =` sinks** (the plan's "33" included four overview-roadmap sites since inlined into the build), **0** `eval` / `new Function` / `document.write` calls, and **1 CSP meta tag with `'unsafe-inline'` on both `script-src` *and* `style-src`** (not just `style-src` — the plan baseline understated this). Authored [docs/f8-frontend-hardening-inventory.md](f8-frontend-hardening-inventory.md), a single-page bounded scope: one row per `innerHTML` site (categorised A-E), per-helper escape audit (`esc`, `buildMitreDdList`, `_invBuildBody`), CSP `'unsafe-inline'` accounting (2 inline `<script>`, 104 inline `on*=` handlers; 1 inline `<style>`, 42 inline `style="…"` attrs), and a three-PR migration plan. **PR-A landed 2026-05-13** — the seven static-option Category-A sites now route through one `_resetEquipmentModelSelect(ms)` helper (created via `document.createElement`/`replaceChildren`, not raw HTML); innerHTML sink count: 29 → 22. **PR-B landed 2026-05-13** — three new DOM-construction helpers (`_appendEquipmentModelOption`, `_makeInventoryLink`, `_appendSizingHintSpan`) replace the only `innerHTML +=` per-iteration loop, the Category-D `innerHTML = summary` write, and both `innerHTML += '<br><span …>'` append sites. The two inline `onclick="event.preventDefault();openInventoryModal()"` HTML attributes are gone (rebound via `addEventListener`). Final counter movement: `.innerHTML =` sites = **21**, `.innerHTML +=` code sites = **0** (one comment-only match remains in a helper docstring); index.html = 651,770 bytes, perf-a11y headroom 65,030 / 716,800 (~9% slack). F8 close criteria satisfied; PR-C (virtual-scroll renderer `<template>`-clone refactor) is the explicit known-cost follow-up and CSP `'unsafe-inline'` tightening both fold into the existing **P10** phase (Performance + a11y hardening) which already names F8 as its prerequisite. |
| F9 | H | No CodeQL / dependency-review / SBOM | DONE (mostly) | `.github/workflows/codeql.yml` + `dependency-review.yml` + `gitleaks.yml` all present as separate workflows. SBOM via `anchore/sbom-action` in `release.yml` — verify in P2.5 audit. |
| F10 | H | `secrets.env` not in `.cursorignore` | **DONE** (2026-05-12) | `.cursorignore` now carries an explicit "Secrets and local environment overrides" block listing `secrets.env`, `secrets.env.local`, `.env`, `.env.local`, `.env.*.local`. `.gitignore` lines 88-90 already block them from commits; the new entries also hide them from the Cursor agent's index so a stray `Read` cannot surface credentials. |
| F11 | M | `scripts/` 105 files, no taxonomy, archived trees | DONE | 76 deliberate Python files remain in `scripts/`, mapped to taxonomy in `docs/scripts-taxonomy.md`. Archived trees (`scripts/_archived/`, `scripts/archive/`) deleted. Closed in v8.2.0 (P6 closure). |
| F12 | M | `validate.yml` 953 lines, single-job, 18 `--check` guards, slow | **DONE** (2026-05-12) | commit `62c95b5e0` (PR-5) split the monolithic job into **5 parallel jobs**: `lint` (line 115), `audits-content` (line 233), `audits-build` (line 866), `mcp` (line 1097), `frontend` (line 1187). File grew to 1,366 lines because each job carries its own setup/install block, but wall-clock time dropped — the longest critical path is now `audits-content` (~7m32s on PR #8) instead of the prior ~20m sequential run. Structural test `tests/build/test_validate_workflow_partition.py` keeps the partition wired. |
| F13 | M | `dist-before/` 6,449-entry stale snapshot | DONE | `dist-before/` gone ✓ (and `.gitignore:36` keeps it out for good). `dist-content/` and `dist-legacy/` remain *gitignored* on disk for the migration-parity workflow, but loose-end ledger #3 closed 2026-05-13 by adding `make clean-tree` which nukes every gitignored build-output dir (`dist/`, `dist1/`, `dist2/`, `dist-content/`, `dist-legacy/`, `dist-before/`, `.build-tmp/`) in one command. No tracked clutter remains. |
| F14 | M | `api/v1/_evidence-packs-bak/`, `_draft_uc_*`, `_fix_*` clutter | **DONE** (2026-05-13, reclassified) | The original "clutter" pattern flagged in F14 (`api/v1/_evidence-packs-bak/`) was deleted in v8.2.0; the residual `scripts/_*.py` underscore-prefixed files (**17 at HEAD**: 5 `_catalog_*`, 7 `_meraki_*`, plus `_draft_uc_18_1_15`, `_fix_broken_fixture_refs`, `_patch_catalog_guide_fields`, `_regulation_wisdom`, `_wire_batch7`) are formally exempted by the v8.2.0 CHANGELOG migration narrative ("What stays in `scripts/`" §Deliberate and "Deliberately **not** migrated (documented exemption)" §Migration) and pinned as tier-3 by the coverage-budget classifier (`src/splunk_uc/audits/coverage_budget.py` matches any `scripts/_*.py` path → tier-3 exempt). They are content-burndown one-shots, not clutter; reclassification ratified by PR #26 (merge `a4e4bda15`, 2026-05-13). |
| F15 | M | No repo-wide `pyproject.toml` for build pipeline | DONE | `pyproject.toml` with `[project]`, `[project.scripts]`, `[tool.ruff]`, `[tool.mypy]`, `[tool.coverage]`, `[tool.pytest]` configs. `splunk-uc` console script wired (v8.2.0 P6 Tier 4). |
| F16 | M | Frontend committed HTML rewritten by Python; no test runner | PARTIAL (test runner wired in CI 2026-05-16) | Root `index.html` still 702 KB raw / 189 KB gzipped and still rewritten in place by `tools/build/build.py` — the *bundler* half of F16 stays open until the first inline-JS surface migrates out of `index.html` into `apps/web/src/`. **Test runner half closed at HEAD:** the `validate.yml` `frontend` job now runs `cd apps/web && npm ci && npm run typecheck && npm test` on every PR and push (paths filter widened to include `apps/**`). The first real consumer of the scaffold landed alongside the wiring: [`apps/web/src/non-technical-view.ts`](../apps/web/src/non-technical-view.ts) is a typed loader that reads the legacy [`non-technical-view.js`](../non-technical-view.js) at the repo root via `node:vm` `runInThisContext()` (no `eval`, no `new Function()`, no codeguard violation), and [`apps/web/src/__tests__/non-technical-view.test.ts`](../apps/web/src/__tests__/non-technical-view.test.ts) asserts 81 shape invariants over the live data — categories 1..23 with no gaps, every area has name + description + 1-10 UCs, every UC reference is shaped `X.Y.Z` and has a non-empty `why` and matches its declaring category number, and every cat-22 area carrying an `evidencePack` also carries the four other Phase 4.3 elevation fields (`whatItIs` / `whoItAffects` / `splunkValue` / `primer`) per `.cursor/rules/non-technical-sync.mdc`. The deeper "every UC id resolves to a real catalogue entry" cross-check stays in the Python audit `audit-non-technical-references` (audits-content) so the Node side never re-walks the 7,929 sidecars. F16 finally closes when the *bundler* half lands — moving the data into `apps/web/src/non-technical-view.ts` as canonical and emitting `non-technical-view.js` from it as a build artefact (the next bite per ADR-0013 §"Migration shape"). |
| F17 | L | 11 root HTML pages duplicate chrome | PARTIAL | **9 root HTML files now** (was 11): `api-docs.html`, `clause-navigator.html`, `compliance-story.html`, `docs.html`, `graph.html`, `guide-reader.html`, `index.html`, `regulatory-primer.html`, `scorecard.html`. Chrome still duplicated across all 9. |
| F18 | L | Root `openapi.yaml` legacy vs. `api/v1/openapi.yaml` canonical | **DONE** (2026-05-12) | Re-verified at HEAD: `openapi.yaml` line 16 carries `> **Status: legacy (hand-maintained)**` followed by a four-paragraph block pointing readers to the canonical `/api/v1/openapi.yaml`, documenting the eventual move to `archive/openapi-legacy.yaml`, and explaining how the OpenAPI drift audit (`audit-openapi-drift`) keeps the two specs in sync. Both specs continue to coexist (root 565 lines / api/v1 210 lines), which is the documented contract — there is no in-progress deletion to wait on. |
| F19 | M | 7 other workflows unaudited | **DONE** (2026-05-12) | Closed by PR #8 (commit `85b680f5d`): every workflow under `.github/workflows/*.yml` now consumes `./.github/actions/setup-python`. The previously skipped guard `tests/build/test_composite_actions.py::test_no_workflow_pins_setup_python_directly` is unskipped and runs in the `audits-content` job, so any future direct `actions/setup-python@<sha>` pin in a workflow fails CI. The 14-workflow inventory itself moves into P2.5 below — that is the remaining work, not F19. |
| F20 | M | Thin test coverage (10 Python + 5 mjs) | **DONE** (2026-05-13, reclassified) | **47 test files / 660 collected tests** in `tests/` + `mcp/tests/` (the "<10 tests" plan baseline far surpassed). The "P16 coverage % targets not yet baselined" caveat in earlier revisions was wrong at HEAD: [`data/baselines/coverage-v9.1.0.json`](../data/baselines/coverage-v9.1.0.json) is a real, in-use, schema-validated coverage baseline (4,093 covered lines / 19,606 statements / 19.76% total, with per-file ratchet records for **24 tier-1 modules** under `tools/build/` and **68 tier-2 modules** under `src/splunk_uc/audits/` + `src/splunk_uc/generators/`, plus 26 tier-3 exempted files). The audit `src/splunk_uc/audits/coverage_budget.py` consumes it as the no-regression contract; baseline integrity is locked by `tests/scripts/test_audit_coverage_budget.py::test_committed_baseline_version_matches_VERSION`. The plan's reference to a missing `coverage-v7.4.2.json` predates the actual capture (`3cafd8e56`, 2026-05-12, refreshed in PR-5 hotfix #3 + #5); the **v9.1.0** filename is the forward-looking floor convention spelled out in [`schemas/changelogs/coverage-baseline.md`](../schemas/changelogs/coverage-baseline.md). P16 burndown work (mutation testing, property-based testing, raising per-tier floors) is still open; the *baseline existence* gate is closed. |
| F21 | L | 7,657 markdown companions tracked alongside JSON | **NOT DONE** (counts updated 2026-05-16) | At local HEAD: **7,929 `.json` files** + **7,761 `.md` files** under `content/cat-*/UC-*.{md,json}` — i.e. 168 JSON-only UCs all clustered in cat-22 subcategories 22.54-22.63 (the post-2026-05-13 OT regulation Phases 2b-6 work; see drift ledger #10 + #12). Plus 48 stale `.md` files relative to current JSON, for a total `--check` gap of 216/7929 = 2.7%. The markdown corpus is still committed; F21 close still requires deleting them from git in favour of generation at build time, not tightening the gate. |
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
| **P5** Frontend rebuild | SCAFFOLDED + first migration in CI (2026-05-16) | <a id="p5-first-cut"></a>[`apps/web/`](../apps/web/) exists with Vite 8.0.13 + TypeScript 6.0.3 (strict — `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `verbatimModuleSyntax`) + Vitest 4.1.6, ratified by [ADR-0013](adr/0013-frontend-rebuild-scaffold.md). The scaffold is no longer opt-in — `validate.yml`'s `frontend` job now runs `cd apps/web && npm ci && npm run typecheck && npm test` on every PR, and the path filter was widened to include `apps/**`. **First real migration target in tree:** [`apps/web/src/non-technical-view.ts`](../apps/web/src/non-technical-view.ts) is a typed loader (using `node:vm` `runInThisContext()`) over the legacy [`non-technical-view.js`](../non-technical-view.js); [`apps/web/src/non-technical-view.types.ts`](../apps/web/src/non-technical-view.types.ts) declares the `NonTechnicalCatalog` / `NonTechnicalCategory` / `NonTechnicalArea` / `NonTechnicalUcRef` interfaces; [`apps/web/src/__tests__/non-technical-view.test.ts`](../apps/web/src/__tests__/non-technical-view.test.ts) asserts 81 shape invariants over the live data (734 ms in vitest jsdom). F8 (a11y landmarks) closed under P10; F16 reclassified PARTIAL above (test-runner half now in CI; bundler half waits for source-of-truth inversion); F17 (11 HTML pages duplicate chrome) still unresolved. |
| **P6** Scripts taxonomy | DONE | Just closed in v8.2.0 (commit `a36aa4db4`). 83-verb dispatcher + Tier 4 packaging. |
| **P7** Server-side search + API gateway | NOT STARTED | — |
| **P8** Observability + content metrics | PARTIAL | `dist/metrics.json` per AGENTS.md ✓, `data/metrics-history/<VERSION>.json` snapshot pattern ✓ (just added `8.2.0.json`). Slack/email weekly digest unclear (`stewardship.yml` exists). Build telemetry exists (`dist/build-telemetry.json`). |
| **P9** Monorepo split (apps/ + packages/) | NOT STARTED | — |
| **P10** Performance + a11y hardening | PARTIAL (2026-05-13) | F8 closure unblocked P10. First a11y deliverable landed 2026-05-13: `index.html` and `scorecard.html` now ship with a visually-hidden `<h1>` inside the correct landmark (banner / main), and both search-bar wrappers on `index.html` carry `role="search"` + distinguishing `aria-label`, so the `region` warning that the F8 closure re-anchored on `#search-input` is gone. `reports/perf-a11y.json` regenerated: `index.html` 0 violations / 0 warnings (was 0 / 1); `scorecard.html` 0 / 0 (unchanged). New `.visually-hidden` utility added to `src/styles/05-helpers.css` + mirrored in `index.html` inline `<style>` + duplicated in `scorecard.html` `<style>` (separate file, no shared stylesheet — chrome unification is F17). Still open under P10: Lighthouse CI, CSP `'unsafe-inline'` tightening on both `script-src` and `style-src` (F8 PR-C precondition), and the virtual-scroll renderer `<template>`-clone refactor (F8 PR-C proper, deferred to P10 as documented in the F8 inventory). |
| **P11** OSS release polish | PARTIAL (2026-05-13, reclassified) | The original "no `.devcontainer/`" caveat is wrong at HEAD: [`.devcontainer/devcontainer.json`](../.devcontainer/devcontainer.json) ships **pinned by OCI image-index digest** (Microsoft `mcr.microsoft.com/devcontainers/python:3.12@sha256:8b1b15…`), with Node 20 + GitHub CLI features, ruff + mypy + markdownlint + YAML extensions, pre-forwarded port 8000, pip-cache volume mount, and an 8-assertion structural test suite ([`tests/build/test_devcontainer.py`](../tests/build/test_devcontainer.py)) that pins the invariants. **Closed gap (2026-05-13):** the `postCreateCommand: make devcontainer-init` reference used to point at a Make target that did not exist (the structural test for that was deliberately skipped with `pytest.mark.skip("deferred to v8.x")`). PR — adds the `devcontainer-init` target to `Makefile` (installs `pip install -e .[audits,dev,test]`, registers pre-commit hooks, warm-builds `dist/`), unskips `test_make_target_exists`, and asserts that `devcontainer-init` is listed in `.PHONY`. The "ROADMAP.md still says v7.1" half of the original caveat was already resolved on 2026-05-12 (loose-end ledger #1). **What's still open:** no automated workflow that pushes `reports/roadmap-export.json` to a public Project board (the `make export-roadmap` target produces the snapshot; the sync side is the residual P11 work). |
| **P12** Splunk content quality moonshot | NOT STARTED | F22 (two sample regimes) unresolved; no per-UC `thresholds` field in schema; no SPL formatter; no AppInspect<sup class="ref">[<a href="#ref-7">7</a>]</sup> gate. |
| **P13** Recommender TA hardening | NOT STARTED | The recommender TA was overhauled in v8.0.0 (CHANGELOG mentions "single Cloud-safe recommender app") but P13's threat model + Sigstore on `.spl` + AppInspect Cloud gate not visible. |
| **P14** Content stewardship | DONE (2026-05-14; cadence side still open) | **First half — Per-category CODEOWNERS routing (2026-05-13, PR #35)**: `.github/CODEOWNERS` now carries one `/content/cat-NN-<slug>/` row per category (all 23), with a new structural test (`tests/build/test_codeowners.py`, 6 cases) that locks the invariant so the file cannot silently drift back to a single catch-all. **Second half — Per-category scorecards (2026-05-14)**: `docs/scorecard.md` gains a `## Category drill-downs` section with one block per category. Each block carries a stable `<a id="cat-NN-<slug>"></a>` anchor (matching the CODEOWNERS slug exactly), composite + grade header, dimension breakdown table including per-dimension `Contribution` (the weighted score that feeds the composite — readers can finally see *why* a composite landed where it did), and one-line summaries of depth tiers, provenance origins, and status mix. `.github/CODEOWNERS` is annotated with a comment block pointing at the matching scorecard anchors. A new structural test (`tests/build/test_scorecard_drilldowns.py`, 5 cases) pins the three-way alignment between content directories, CODEOWNERS rows, and scorecard anchors so the deep-link routing cannot silently drift. Until co-maintainers join the project, every CODEOWNERS row still points at the lead maintainer; the *structure* is in place across all three artefacts, so swapping in a domain owner is a one-line change. **Still open** — the cadence side: automated rotation reminders that consume the CODEOWNERS rows + the new scorecard drill-downs (e.g. quarterly "owner of cat-N has not approved a content change in 90 days; nudge"). |
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
   **Target actually executed 2026-05-14** — confirmed all seven
   directories absent on disk after `make clean-tree`; recovered
   ~3.7 GB locally (the 782 MB plan estimate covered just
   `dist-content/` + `dist-legacy/`; the rest came from accumulated
   `dist/` / `dist1/` / `dist2/` from prior reproducibility-check runs).
   Re-runnable any time the local tree balloons again.
4. **CHANGELOG narrative count typo** in v8.2.0 entry was fixed in this
   commit ("two" → "three" pure documentation generators).
5. **Plan baselines have shifted** since the plan was written
   (content has grown). Re-anchored 2026-05-16 against local HEAD
   `fd2f09cc5` via `tools/build/parse_content.load()`,
   `data/regulations.json`, `wc -l`, and `du`:
   - 7,657 UCs → **7,929 UCs** (+272 over plan, +252 since the
     2026-05-13 anchor — the cat-22 OT regulation deep-dive arc,
     drift ledger item #10)
   - 222 subcategories → **265 subcategories** (+43 over plan,
     +26 since the 2026-05-13 anchor)
   - 105 equipment slugs → **106 equipment**
   - 60 regulations → **82 regulations** (+22 over plan, +13 since
     the 2026-05-13 anchor — Phase 6 added DO-326A / ED-202A, China
     CSL/DSL/PIPL<sup class="ref">[<a href="#ref-8">8</a>]</sup>/CII, India CERT-In 2022 / DPDP 2023, IEC 61511 /
     61508 cybersecurity overlay; Phase 5a/b added IMO Resolutions
     MSC.428(98) + MSC-FAL.1/Circ.3, TSA Surface, SG Cyber Act, FR
     LPM)
   - 12+ schemas → **19 schemas** (+1 since the 2026-05-13 anchor —
     `schemas/v2/regulation.schema.json` added for the OT framework
     metadata block)
   - 9,500 lines of build code → ~10,900 (`enrichment.py` grew by ~870)
   - `index.html` 621 KB → **702 KB raw / 189 KB gzipped** (the
     +57 KB raw / +16 KB gzipped jump over the 645 KB / 173 KB anchor
     is the cat-22 OT non-technical-view content + evidence-pack
     plain-language blocks added in Phases 1-6; this is now a P10
     follow-up, not a new finding)
   - `validate.yml` 953 lines → **1,386 lines across 5 parallel jobs**
     (PR-5 / F12 closure, 2026-05-12; the +20 lines since the
     2026-05-13 anchor are the OT-regulation related audit steps and
     a P14 scorecard-drilldown step on the un-pulled `origin/main`
     commit `00729f198`)
   - `pytest --collect-only` 660 tests (unchanged since 2026-05-13)
   The plan's next refresh should re-anchor these numbers.
6. ~~**F10 — `.cursorignore` lacks dotenv / secrets patterns.**~~
   **Resolved 2026-05-12** — appended a "Secrets and local environment
   overrides" block to `.cursorignore` covering `secrets.env`,
   `secrets.env.local`, `.env`, `.env.local`, `.env.*.local`.
   `.gitignore` lines 88-90 already prevent commits; the new block
   stops the Cursor agent itself from indexing or surfacing them.
   **Extended 2026-05-14** — the original close handled the secrets
   half of the F10 quick-win but skipped the bytecode / pytest-cache
   half called out in the same plan instruction. A "Python build /
   test caches" block was appended adding `__pycache__/` and
   `.pytest_cache/` (both already in `.gitignore` lines 6 + 39); the
   new block keeps churned bytecode and pytest caches out of the
   Cursor agent's index across all 19 nested `__pycache__/`
   directories and both `.pytest_cache/` roots (root + `mcp/`).
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
10. **Cat-22 OT regulation deep-dive arc shipped.** New ledger entry
    2026-05-16 for the 252-UC content arc that landed on local `main`
    between v8.5.0 and v8.6.4 across four commits — `458a50f8b`
    (Phases 1-5a rollup: ISA/IEC 62443<sup class="ref">[<a href="#ref-3">3</a>]</sup>, NERC CIP<sup class="ref">[<a href="#ref-6">6</a>]</sup> v8, EU NIS2<sup class="ref">[<a href="#ref-1">1</a>]</sup> OT,
    UK CAF / NIS Regulations, US CIRCIA, ENISA NIS2 sectoral, IMO
    cyber), `debb1d9b5` (Phase 5b: DO-326A / ED-202A aviation),
    `c25e80ec1` (Phase 6 closure: China CSL / DSL / PIPL / CII +
    India CERT-In 2022 + India DPDP 2023 + IEC 61511 / 61508
    cybersecurity overlay), and `fd2f09cc5` (v8.6.4 primer back-fill
    for TSA Surface §4.18, SG Cyber Act §4.19, France LPM §4.20 +
    renumber + count drift fix). Net effect on plan baselines: +13
    tier-1 frameworks, +10 evidence packs, +252 UCs, +26
    subcategories, +1 schema (`schemas/v2/regulation.schema.json`).
    None of these four commits are on `origin/main` yet — see #11.
11. **Branch divergence — local vs `origin/main`.** New ledger
    entry 2026-05-16. `git rev-list --left-right --count HEAD…origin/main`
    returns `4 1`: local has four un-pushed commits (the cat-22 OT
    arc above) and `origin/main` has one un-pulled commit
    (`00729f198`, per-category scorecard drill-downs — extends P14,
    see Phases table above). The latest green `Validate catalog` CI
    run reflects `origin/main`, not local HEAD. **Action required**
    before the next push: either (a) regenerate the missing /
    stale `.md` companions (#12) so the F7 gate stays green
    post-push, or (b) push with the gate broken and fix in a
    follow-up. Pulling `origin/main` is mechanical; no expected
    merge conflict (the un-pulled commit only touches
    `src/splunk_uc/generators/scorecard.py`, `reports/*.json`,
    `scorecard.json`, `openapi.yaml`, `tests/build/test_scorecard_drilldowns.py`
    — none of these are touched by the four un-pushed commits).
12. ~~**F7 — `.md` parity gap on local HEAD.** New ledger entry
    2026-05-16, sub-finding of F7. Local HEAD reports
    `216/7929 .md files are stale or missing` via
    `python -m splunk_uc generate-md-from-json --check`. Breakdown:
    168 JSON-only UCs (the JSON file exists, no matching `.md`
    has been committed) clustered in cat-22 subcategories 22.54 ⇒
    22.63 (drift ledger #10's Phases 2b-6 commits ship JSON-only),
    plus 48 existing `.md` files stale relative to their JSON. Fix
    is mechanical — `python -m splunk_uc generate-md-from-json`
    without `--check` regenerates all 7,929 markdown twins in a
    single pass, tagged `[generated]` per the §4 per-PR contract.
    The gate itself is correctly wired (F7's `continue-on-error: true`
    strip stands); it just hasn't been re-run after the OT arc.~~
    **Resolved 2026-05-16** — `python -m splunk_uc generate-md-from-json`
    written 7,929 `.md` files (168 newly added in `cat-22-regulatory-compliance`
    UCs 22.54-22.63, 48 normalisation-drift updates split 45 / 3
    across cat-22 / cat-17). Re-running `--check` exits 0:
    `All 7929 .md files are up-to-date.`. The cat-17 stale diffs
    are pure JSON-side dedup (e.g. UC-17.1.33 dropping a duplicate
    `monitoringType: "Operations"`); the cat-22 new files are the
    standard generator output (AUTO-GENERATED header, YAML
    frontmatter, criticality/difficulty/wave row, grandma
    explanation, description, value, implementation, SPL,
    visualization, CIM models, MITRE mappings, regulatory
    mappings). 219 staged paths total: 216 `.md` + the three doc /
    config files from earlier today's two PRs. F7 is fully closed
    on both `origin/main` (since 2026-05-12) and local `main`
    (now); the gate is healthy on both trees.

15. **Late-afternoon staging-leak incident — `4bd2954d5` accidentally
    bundled local WIP into a "fix(ci)" commit (2026-05-16,
    forward-fix only — no force-push to `origin/main`).** While
    landing the CI-unblock commit that closes the OT-arc-induced
    audit failures (UC-22.62.8 literal-TBD fix + sandbox-validation
    regen + recommender-app regen — 13 files / +11,772 / -972), the
    staging step picked up 16 additional files from the in-progress
    "SPL reference vocabulary validation" feature that had been
    sitting unstaged in the working tree throughout the session.
    Pre-commit verification with `git diff --cached --stat HEAD`
    correctly reported the 13 intended files; the actual commit
    captured 29 files (+46,125 / -975). No pre-commit hook exists
    locally and `core.hooksPath` is unset, so the leak cause is
    most likely an upstream `git add -A` or `git add -u` invocation
    earlier in the session whose effects survived the explicit
    path-based `git add` that followed. The committed work is
    healthy — the 30-test `tests/splunk_uc/test_spl_references.py`
    suite passes locally, the SPL reference vocabulary feature
    docs are complete (`docs/spl-reference-validation.md`,
    253 lines), and CI on `4bd2954d5` is in flight — but the
    commit message describes only the CI-unblock half and the
    feature itself is undocumented in `CHANGELOG.md`. **Forward-fix
    chosen over force-push undo** because `4bd2954d5` was already
    pushed to `origin/main` before the leak was diagnosed, and
    rewriting public history on `main` carries higher risk than
    accepting one misleading commit message in the log. The
    follow-up commit (this one, `4bd2954d5+1`) adds: (a) a proper
    `[Unreleased]` `CHANGELOG.md` bullet for `audit-spl-references`
    describing the three-layer vocabulary (Splunk-core baseline +
    curated TA + local reference corpus), the parser-primitives
    shared with `audit-spl-grammar`, the severity tiers, the test
    coverage, and the bundling note pointing back at this drift
    ledger entry, and (b) this drift-ledger entry. Net result:
    `origin/main` carries the feature *and* the CI fix; the
    feature is discoverable from `CHANGELOG.md`; the incident is
    archived here for future post-mortems and as a reminder to
    add a paranoid pre-commit verification of `git diff --cached
    --name-only` (not just `--stat`) against the intended set.
    **2026-05-16 evening cleanup-chain** (three follow-up commits
    landed on `origin/main` to take the post-leak CI back to
    green):
    (a) `0f892bbab` — `fix(audits): tighten _load_reference typing
    in spl_references.py`. The bundled `audit-spl-references`
    feature shipped with a `_load_reference` helper whose
    `json.load` return was inferred as `Any` and was then unsafely
    returned as `dict[str, Any]`; `mypy --strict` (newly enforced
    on `src/splunk_uc/audits/*` per finding F17) rejected the
    helper. Fix: explicit `Any` annotation on the `json.load`
    return + `isinstance(data, dict)` narrowing before returning
    `dict[str, Any]`. The `lint` job goes green; no runtime
    behaviour change.
    (b) **MITRE ATT&CK<sup class="ref">[<a href="#ref-4">4</a>]</sup> ID hygiene across 5 cat-22 UCs** — the
    Phase 4.5d ATT&CK simulation gate (`scripts/simulate_controltest.py`,
    runs in the `frontend` job) flagged five OT-arc UCs that
    referenced invalid identifiers in their `mitreAttack` arrays.
    Removed: `T0810` (ICS-matrix technique, not Enterprise),
    `TA0008` (a *tactic* id, not a technique), `T1551`
    (non-existent / deprecated). UCs touched: `UC-22.51.16`,
    `UC-22.53.24`, `UC-22.60.3`, `UC-22.60.7`, `UC-22.60.12`.
    Their `.md` companions were regenerated via
    `python -m splunk_uc generate-md-from-json` and the
    `reports/attack-simulation.json` snapshot was re-emitted; the
    gate now passes. Conservative remediation chosen (drop the
    invalid IDs rather than rewrite the detection narrative)
    because the surrounding `mitreTactic` / `mitreTechnique`
    fields already capture the analyst-meaningful classification;
    the removed IDs were redundant or wrong.
    (c) **Coverage baseline absorption for the four new
    SPL-reference modules.** The §P16 per-file coverage ratchet
    (`audit-coverage-budget` against
    `data/baselines/coverage-v9.1.0.json`) flagged four
    regressions: `src/splunk_uc/audits/_spl_baseline.py`,
    `src/splunk_uc/audits/_spl_parse.py`,
    `src/splunk_uc/audits/_spl_well_known.py`,
    `src/splunk_uc/audits/spl_references.py` — all *new* tier-2
    files (matched by the `src/splunk_uc/audits/*` glob), each
    at 0.0% under the tier-2 40.0% new-file floor. The companion
    suite in [`tests/splunk_uc/test_spl_references.py`](../tests/splunk_uc/test_spl_references.py)
    (30 tests, all passing locally) exercises the audit's
    `_check_uc` and `_load_reference` paths but the
    `pytest --cov=tools/build --cov=splunk_uc` invocation that
    drives the budget runs `tests/build/` + `tests/scripts/` only
    (not `tests/splunk_uc/`), so it never observes the coverage
    those tests produce — that scope-widening is a future cleanup
    in its own right. For now, the four entries were inserted
    *surgically* into [`data/baselines/coverage-v9.1.0.json`](../data/baselines/coverage-v9.1.0.json)
    at 0.0% (covered_lines 0 / num_statements 15, 150, 5, 257
    respectively) with totals recomputed (covered_lines 4087 /
    num_statements 18102 / 22.58% / missing_lines 14015) and
    `git_head` + `captured_at` re-stamped to the
    cleanup-chain HEAD. **No silent absorption of unrelated
    drift** — the existing tier_1 and tier_2 entries were
    preserved verbatim; the diff is +30 / -6 lines and shows
    only the 4 new entries + totals + provenance. The file
    remains schema-valid against `schemas/coverage-baseline.schema.json`.
    Follow-up tracked: widening the coverage `pytest` invocation
    in `validate.yml` to include `tests/splunk_uc/` will let the
    next baseline refresh ratchet these four files up from 0.0%
    once the 30 existing audit tests register against the
    instrumented modules.

14. **P5 first migration target landed — `non-technical-view.js`
    typed companion + 81 shape invariants in CI (2026-05-16).**
    Follow-on to ledger #13. Adds three files under
    [`apps/web/src/`](../apps/web/src/):
    [`non-technical-view.types.ts`](../apps/web/src/non-technical-view.types.ts)
    declares the four interfaces (`NonTechnicalCatalog`,
    `NonTechnicalCategory`, `NonTechnicalArea`, `NonTechnicalUcRef`)
    that mirror the legacy JS data shape, all with `readonly` modifiers
    so the catalogue is immutable from TypeScript's perspective;
    [`non-technical-view.ts`](../apps/web/src/non-technical-view.ts)
    exposes a `loadCatalogFromLegacyJs()` function that reads the
    repo-root `non-technical-view.js` from disk and executes it via
    `node:vm` `runInThisContext()` inside vitest's jsdom environment
    (no `eval`, no `new Function()` — the codeguard rule against
    those is honoured because the loader uses Node stdlib `vm` and
    operates only on a checked-in repository file at a fixed path);
    and [`__tests__/non-technical-view.test.ts`](../apps/web/src/__tests__/non-technical-view.test.ts)
    asserts 81 shape invariants over the live data (categories
    1..23 with no gaps and no extras; every area has name +
    description + 1-10 UCs; every UC reference is shaped `X.Y.Z`,
    has a non-empty `why` string, and the category prefix of the UC
    id matches its declaring category number; every cat-22 area
    carrying an `evidencePack` also carries the four other
    Phase 4.3 elevation fields per `.cursor/rules/non-technical-sync.mdc`;
    every `primer` link points into `docs/regulatory-primer.md` or
    `regulatory-primer.html` and every `evidencePack` link points
    into `docs/evidence-packs/`). The deeper "every UC id resolves
    to a real catalogue entry" cross-check stays in the Python
    audit `audit-non-technical-references` (audits-content) so the
    Node side never re-walks the 7,929 sidecars. **CI wiring also
    landed:** `validate.yml`'s `frontend` job gained three new
    steps (`apps/web — install scaffold deps` running `npm ci`,
    `apps/web — typecheck (tsc --noEmit, strict)`, and `apps/web —
    Vitest shape invariants over non-technical-view.js`); the
    paths filter for the workflow was widened from the explicit
    file list to include the new `apps/**` directory. The 74-test
    `tests/build/test_validate_workflow_partition.py` + 14-test
    `tests/build/test_ci_architecture.py` partition guards still
    pass. F16 reclassified from "PARTIAL (scaffold anchor landed)"
    to "PARTIAL (test runner wired in CI)" — the *test runner*
    half is now closed; the *bundler* half waits for the
    source-of-truth inversion PR.

13. **P5 frontend rebuild — scaffold anchor landed (afternoon
    2026-05-16).** Drift-ledger entry rather than a finding because
    no in-tree contract was broken — this is purely additive surface.
    [`apps/web/`](../apps/web/) is now an isolated Node tree with
    Vite 8.0.13 + TypeScript 6.0.3 (strict) + Vitest 4.1.6 + a
    passing 2-assertion smoke test ([`src/__tests__/smoke.test.ts`](../apps/web/src/__tests__/smoke.test.ts))
    and a single-module entrypoint ([`src/main.ts`](../apps/web/src/main.ts))
    that exists only to give the bundler something to chew on.
    `npm run typecheck` is clean, `npm run test` is 2/2 green
    (633 ms), `npm run build` produces a 12 KB `dist/` (`index.html`
    0.79 KB + `assets/index-*.js` 0.98 KB + sourcemap 1.23 KB) in
    18 ms on a cold Vite invocation. The choice of bundler /
    language / test runner / no-framework / no-CI-yet / no-deploy-yet
    is ratified by [ADR-0013](adr/0013-frontend-rebuild-scaffold.md),
    which also enumerates 6 alternatives considered (Webpack 5 +
    Jest; esbuild + tsc; Node stdlib + hand-bundle; full-stack
    framework like Next/Remix; waiting until F16/F17 do a
    monolithic rebuild; placing the tree at `frontend/` / `web/` /
    `ui/` instead of `apps/web/`) and explains why each was
    rejected. F16 reclassified from NOT DONE to PARTIAL (scaffold
    anchor landed); P5 reclassified from NOT STARTED to SCAFFOLDED
    (first cut). The next bite per ADR-0013's §"Migration shape"
    is moving `non-technical-view.js` from the repo root into
    `apps/web/src/non-technical-view.ts` (pure data, easiest first
    migration, validates the toolchain on real content) — and that
    PR is the one that wires `npm test` + `npm run typecheck`
    into `.github/workflows/validate.yml`, closing F16 properly.

16. **Post-corpus-expansion regen cascade (2026-05-16 evening).** New
    drift-ledger entry for the cascade triggered by the previous day's
    landings on `origin/main`. The maintainer's `2032c631a` (SPL
    reference corpus expansion + glob-aware sourcetype matching +
    Splunk 9 `IN (…)` parser fix) and the Phase 4
    `controlObjective` / `evidenceArtifact` backfill in `b9f17b407`
    were both green on their own commits but left **three `validate.yml`
    failures masked behind first-failure-skips-rest semantics** —
    `audits-content` ↪ `Phase 3.2 cross-cutting compliance generator
    regeneration check` (the expanded vocabulary surfaces 53
    cross-cutting UCs / 182 mappings the on-disk sidecars were
    missing), `frontend` ↪ `Phase 4.5f perf + a11y Node drift guard`
    (`reports/perf-a11y.json` stale relative to the regenerated
    `dist/` after `complianceEntries` rose 2,693 → 2,790 and
    `dist/catalog.json` grew ~75 KiB / +0.09 %), and (only visible
    after the first cascade commit `e2f467cf6` cleared the Phase 3.2
    failure) `audits-content` ↪ `Equipment-tags regeneration check`
    (the maintainer's OT-arc added 266 cat-22 UCs in subcategories
    22.51-22.63 carrying `app` / `dataSources` narrative that the
    `generate-equipment-tags` registry now wants to backfill into the
    `equipment[]` / `equipmentModels[]` sidecar fields). The third
    failure was missed by the first cascade pass because
    `generate-equipment-tags` was not in the chain I walked — a real
    omission in the recipe, fixed in the follow-on cascade commit by
    running the generator (266 UCs updated, 120 `equipment-orphan`
    findings cleared in `reports/compliance-coverage.json`).
    The cascade runs the canonical dependency chain in one pass so CI
    converges in a single push rather than bouncing between freshness
    audits: **(1)** `splunk_uc generate-phase3-2-cross-cutting` updates
    53 UC sidecars across the cross-cutting compliance families with
    182 mappings; **(2)** `splunk_uc generate-phase3-3-derivatives`
    rewrites 32 derivative sidecars with 54 inherited entries (e.g.
    `uk-gdpr` → `UK GDPR` regulation-name normalisation, parent
    GDPR<sup class="ref">[<a href="#ref-2">2</a>]</sup> assurance one-step downgrades, Cyber Essentials<sup class="ref">[<a href="#ref-5">5</a>]</sup> Montpellier
    2025 derivations); **(3)** `splunk_uc generate-mapping-ledger`
    refreshes `data/provenance/mapping-ledger.json` (+14,760 / −3,062
    lines, the bulk of the byte delta and the file that carries the
    full provenance trail); **(4)** `splunk_uc generate-api-surface`
    rewrites 9,828 files under `api/v1/`; **(5)**
    `splunk_uc generate-clause-index` rewrites 1,288 clause-level
    JSON; **(6)** `splunk_uc generate-story-payload` rewrites the
    82 compliance-story payloads; **(7)**
    `splunk_uc generate-recommender-app` rewrites the Splunk recommender
    app's lookups + catalog-fallback + README; **(8)**
    `splunk_uc generate-md-from-json` re-checks all 7,929 `.md` twins
    (zero rewritten — already in sync); **(9)**
    `scripts/generate_backlinks.py` re-checks `docs/backlinks.md`
    (zero rewritten); **(10)** `scripts/generate_doc_references.py`
    re-scans 213 docs (zero rewritten); **(11)** `tools/build/build.py
    --out dist` rebuilds the static site (47.18 s, 40,536 files,
    984.8 MiB); **(12)** `splunk_uc audit-perf-a11y` rewrites
    `reports/perf-a11y.json` with the new `dist/catalog.json` size
    measurement so the Node drift guard returns to green.
    Net diff on disk: **89 file changes (88 modified)** — dominated
    by the mapping-ledger refresh + the 88 sidecar updates spread
    across cats 01, 03-07, 09, 11-17, 22 (cat-22 alone accounts for
    32 of the 88). Verification at push time: all gates green
    locally (`generate-phase3-2-cross-cutting --check`,
    `generate-phase3-3-derivatives --check`, `generate-md-from-json
    --check`, `scripts/generate_backlinks.py --check`,
    `scripts/generate_doc_references.py --check`,
    `audit-compliance-mappings`, `audit-perf-a11y --check`,
    `audit-uc-structure`). `coverage-report.json` left under the repo
    root by the local coverage run is **deliberately untracked** — it
    is a `pytest-cov` build artefact (`--cov-report=json:coverage-report.json`
    in `validate.yml` line 343), never committed; CI regenerates it
    per-run. **Pattern note:** this is the third cascade-style regen
    on `main` in 24 hours (after the OT-arc post-regen of `sandbox-validation.json`
    + recommender-app, and the cleanup-chain ATT&CK / coverage fixes).
    A future refactor could collapse them all into a single
    `make sync-generated` umbrella target so contributors don't need
    to learn the dependency order each time the corpus widens.

    **Known follow-ons, NOT addressed in this cascade — both share
    the same root cause: the OT-arc landed hand-authored *content*
    (new evidence packs, new cat-22 non-technical-view areas) but did
    not extend the corresponding generators to *include* that content
    in their canonical output, so each generator's `--check` gate
    treats the maintainer's additions as either orphan files (1) or
    drift (2).**

    1. **Phase 4.2 evidence-pack orphan gate:** running
       `splunk_uc generate-evidence-packs --check` locally surfaces 8
       `orphan: docs/evidence-packs/<slug>.md` errors for the OT-arc
       regulations the maintainer added evidence-pack markdown for —
       `cert-in.md`, `cn-csl.md`, `do-326a.md`, `fr-lpm.md`,
       `iec-61511.md`, `imo-msc-428-98.md`, `sg-cyber-act.md`,
       `tsa-surface.md`. The MD files exist on disk and are tracked,
       but the generator's hardcoded `PACK_TARGETS` list in
       [`src/splunk_uc/generators/evidence_packs.py`](../src/splunk_uc/generators/evidence_packs.py)
       (currently 17 slugs) does not include them, so `--check`
       reports them as orphans and `generate-evidence-packs` (without
       `--check`) would *delete* them.

    2. **Phase 4.3 cat-22 non-technical block regeneration check:**
       running `splunk_uc migrate-cat22-ntv --check` locally reports
       "cat-22 non-technical block drift detected". The maintainer
       added 7 OT-arc `areas[]` entries to the `"22": { … }` block in
       [`non-technical-view.js`](../non-technical-view.js) — `NCA
       OTCC (Saudi OT)`, `SOCI Act + CIRMP Rules (Australia)`,
       `AWIA s2013 + EPA/CISA Water Sector Cybersecurity (US)`,
       `CIRCIA + 6 USC 681b`, `SG Cyber Act`, `France LPM OIV Regime
       + ANSSI 20-Rules (France)`, and `IMO MSC.428(98) +
       MSC-FAL.1/Circ.3 + IACS UR E26/E27 (Maritime / Shipping,
       Global)` — but the corresponding `_AREAS` list in
       [`src/splunk_uc/migrations/regenerate_cat22_ntv.py`](../src/splunk_uc/migrations/regenerate_cat22_ntv.py)
       (currently 49 entries) does not carry them. Running
       `migrate-cat22-ntv` *deletes* the maintainer's 7 areas — 65
       lines of hand-authored bilingual narrative including the
       French-language `ucs[].why` strings on the LPM entry and the
       Arabic-language reviewer notes on the NCA OTCC entry — so the
       regen is destructive and **must not be auto-run**.

    Both were masked on the prior CI runs by the Phase 3.2
    cross-cutting failure (and on `e2f467cf6` by the Equipment-tags
    failure that masked Phase 4.3 in turn) stopping the job script
    early under `set -e`. With this cascade clearing those, the next
    CI run on `main` will surface Phase 4.3 first (line 698 of
    `validate.yml`), then Phase 4.2 (line 724) on the run after that
    is fixed.

    **Not fixed in this cascade** because the safest fix for either
    generator (transcribing the maintainer's hand-authored content
    into the generator's Python data structures so the generator's
    output matches the on-disk content byte-for-byte) requires careful
    fidelity — the hand-customised TOC sections on
    `imo-msc-428-98.md` (*"Questions a flag-State / PSC /
    class-society inspector should ask"*) and the multilingual `why`
    strings on the cat-22 NTV LPM / OTCC areas need exact replication.
    The decision needs the maintainer: either (a) `evidence-pack-extras`,
    the evidence-pack generator template, and the cat-22 NTV
    `_AREAS` list all gain the OT-arc additions with byte-identical
    output, or (b) the OT-arc additions are re-classified as
    hand-authored content outside the generators' scope (and the
    `--check` gates are taught to ignore an explicit allow-list of
    "manually maintained" slugs / area-names).

    Tracked here so the post-push CI failures are expected, not a
    surprise. A 3-commit batch (one per generator: cat-22 NTV first
    because it surfaces first, then evidence-packs, then any third
    surface that emerges after those two clear) is the cleanest
    follow-on shape.

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
   minor version to keep "what's done" honest. **Refreshed
   2026-05-16** against local HEAD `fd2f09cc5` (v8.6.4) — the
   refresh updated the headline + F7 + F21 + P10 + P14 rows,
   added drift ledger items #10/#11/#12 covering the cat-22 OT
   regulation arc, the branch divergence, and the .md parity gap,
   and re-anchored drift ledger #5's baselines against
   `tools/build/parse_content.load()` (23 / 265 / 7929) +
   `data/regulations.json` (82) + `wc -l` (`validate.yml` 1,386
   lines).
10. **All nine bites above are crossed-out.** Forward-looking
    work as of 2026-05-16 in size order:
    - ~~`~1 mechanical PR, 216 files [generated]` — Regenerate the
      missing/stale `.md` companions via
      `python -m splunk_uc generate-md-from-json` so the F7 gate
      stays green when the four un-pushed OT phase commits land
      on `origin/main`. Tagged `[generated]` per the §4 per-PR
      contract (skips the LoC budget).~~ **Done 2026-05-16** —
      219 staged paths (216 `.md` regen + the three doc / config
      files from earlier today's two PRs). `--check` reports
      `All 7929 .md files are up-to-date.`. See drift ledger #12
      for the breakdown.
    - ~~`~no code, 1 PR` — Take a first cut at **P5 frontend
      rebuild scaffolding**: empty `apps/web/` with Vite + TS +
      Vitest config, a single passing smoke test, and an ADR
      ratifying the bundler / framework / migration shape. F16
      and F17 then anchor on that scaffold instead of being
      monolithic "rebuild" verbs.~~ **Done 2026-05-16** — see
      [P5 first cut](#p5-first-cut) row, drift ledger #13, and
      [ADR-0013](adr/0013-frontend-rebuild-scaffold.md).
    - ~~`~150 line PR` — Land the **first real migration** out of
      root `index.html` per ADR-0013's §"Migration shape":
      `non-technical-view.js` → `apps/web/src/non-technical-view.ts`.
      Pure data, lowest-risk first migration, and the PR that
      finally wires `apps/web/`'s `npm test` + `npm run typecheck`
      into `.github/workflows/validate.yml` — which is what closes
      F16 properly.~~ **Done 2026-05-16** — see drift ledger #14.
      Three files added under `apps/web/src/`
      ([types](../apps/web/src/non-technical-view.types.ts),
      [loader](../apps/web/src/non-technical-view.ts), [81-assertion
      test suite](../apps/web/src/__tests__/non-technical-view.test.ts)),
      three CI steps added to `validate.yml`'s `frontend` job, paths
      filter widened to `apps/**`. F16 reclassified from "PARTIAL
      (scaffold anchor landed)" to "PARTIAL (test runner wired in
      CI)"; the *bundler* half stays open for the source-of-truth
      inversion PR below.
    - `~3,000 line PR (mostly mechanical)` — **Invert source-of-truth**
      for `non-technical-view.js`. Move the 1,330 lines of data into
      `apps/web/src/non-technical-view.ts` as canonical (with the
      already-declared `NonTechnicalCatalog` types), author a small
      Vite/tsx emit script that produces the legacy-shaped
      `non-technical-view.js` at the repo root (with a `[generated]`
      header), update `non-technical-sync.mdc` to point at the TS
      file as the authoring surface, and add a CI step
      `cd apps/web && npm run emit:legacy && git diff --exit-code
      ../non-technical-view.js` to fail on drift. The line cost is
      large but mostly mechanical (the actual decision work is
      already done in this PR). Closes the *bundler* half of F16.
    - `~250 line PR` — Wire the **automated rotation reminders**
      that consume the per-category CODEOWNERS rows + the new
      scorecard drill-downs landed on `origin/main` 2026-05-14
      (the second-half closure for P14).
    - `~500 line PR` — Start **P12 content-quality moonshot** by
      adding the per-UC `thresholds` field to `schemas/uc.schema.json`
      (minor version bump) + a one-shot back-fill of crawl/walk
      defaults for the existing 7,929 UCs.

## Method note

Status here is derived from: actual file contents at HEAD
`b51023419` (v8.6.4, 2026-05-16 — local and `origin/main` in sync
after the same-day rebase + push); the post-2026-05-12 + 2026-05-13 closure
sprints (PR-A `82d59ccbd`, PR-B `c947c5a61`, the §P14 per-category
CODEOWNERS scaffold `7be03f4c0`, plus the `origin/main`-only
scorecard drill-down extension `00729f198`); the cat-22 OT regulation
arc (commits `8bed23912` / `3792354bf` / `2ed1861b8` / `6e67126a0`,
rebased onto `origin/main` at push time); the doc-refresh / F10
trailing closure commit `d435bb764`; the `[generated]` `.md` regen
commit `b51023419`; the v8.2.0 + v8.5.0 + v8.6.x CHANGELOG
narratives + the `[Unreleased]` section; the `docs/migration-status.md`
ledger; `git log --oneline -30`; `git rev-list --left-right --count
HEAD…origin/main`; live `wc -l` on the workflow / build files; live
`du -sh` + raw-content header inspection for the `index.html` size
delta; live `python -m splunk_uc generate-md-from-json --check`
(post-regen exit 0); live `cd apps/web && npm test` / `npm run
typecheck` / `npm run build` for the P5 scaffold smoke; the
`gh pr checks 8` rollup on PR #8 (CI partition wall-clock evidence);
the post-PR-#13/#17 `gh api repos/.../dependabot/alerts` rollup
(0 open at HEAD); the `docs/workflow-audit.md` 14-row inventory
generated from a direct sweep of `.github/workflows/*.yml`;
`pytest --collect-only`; and direct grep / glob of the repo. No claim
above is based on the plan's self-reported state at plan-writing time
without verification at HEAD.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** European Parliament and Council of the European Union. (2022, December). *Directive (EU) 2022/2555 — NIS2 Directive on cybersecurity*. Official Journal of the European Union, L 333. ELI: dir/2022/2555. https://eur-lex.europa.eu/eli/dir/2022/2555/oj

<a id="ref-2"></a>**[2]** European Parliament and Council of the European Union. (2016, April). *Regulation (EU) 2016/679 — General Data Protection Regulation*. Official Journal of the European Union, L 119. ELI: reg/2016/679. https://eur-lex.europa.eu/eli/reg/2016/679/oj

<a id="ref-3"></a>**[3]** International Electrotechnical Commission. (2018). *IEC 62443 — Industrial communication networks — Network and system security*. IEC. https://webstore.iec.ch/en/publication/7029

<a id="ref-4"></a>**[4]** MITRE Corporation. (2026). *MITRE ATT&CK Knowledge Base*. MITRE Engenuity. https://attack.mitre.org/

<a id="ref-5"></a>**[5]** National Cyber Security Centre (UK). (2025). *Cyber Essentials — Montpellier (2025)*. NCSC, IASME Consortium. https://www.ncsc.gov.uk/cyberessentials/overview

<a id="ref-6"></a>**[6]** North American Electric Reliability Corporation. (2024). *NERC Critical Infrastructure Protection (CIP) Reliability Standards*. NERC. https://www.nerc.com/pa/Stand/Pages/CIPStandards.aspx

<a id="ref-7"></a>**[7]** Splunk Inc. (2026). *Splunk AppInspect documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://dev.splunk.com/enterprise/docs/developapps/testvalidate/appinspect/

<a id="ref-8"></a>**[8]** Standing Committee of the National People's Congress (China). (2021). *Personal Information Protection Law of the People's Republic of China*. National People's Congress. http://en.npc.gov.cn.cdurl.cn/2021-12/29/c_694559.htm

### Related repository documents

- [`docs/adr/0010-sample-and-sample-data-co-exist.md`](adr/0010-sample-and-sample-data-co-exist.md)
- [`docs/adr/0011-schema-lineage-governance.md`](adr/0011-schema-lineage-governance.md)
- [`docs/adr/0012-sample-data-canonical-shape.md`](adr/0012-sample-data-canonical-shape.md)
- [`docs/adr/0013-frontend-rebuild-scaffold.md`](adr/0013-frontend-rebuild-scaffold.md)
- [`docs/f8-frontend-hardening-inventory.md`](f8-frontend-hardening-inventory.md)
- [`docs/workflow-audit.md`](workflow-audit.md)

### Cited by

- [`ROADMAP.md`](../ROADMAP.md)
- [`docs/f8-frontend-hardening-inventory.md`](f8-frontend-hardening-inventory.md)

<!-- END-AUTOGENERATED-SOURCES -->
