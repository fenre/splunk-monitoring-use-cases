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
> `generate-recommender-app` →
> `scripts/generate_backlinks.py` → `scripts/generate_doc_references.py`
> → rebuild `dist/` → `audit-perf-a11y`) so CI converges in one push
> instead of bouncing between freshness audits. *(2026-05-18:
> `generate-md-from-json` removed from the chain — F21 close deleted the
> per-UC `.md` companions and the LLM markdown twin is now emitted only
> by the rebuilt `dist/` step.)*
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
- **P2.5** closed by the [Workflow inventory](ci-architecture.md#workflow-inventory) section of `docs/ci-architecture.md` (13-workflow inventory + cadence calendar; pin map enforced by `audit-action-pins`). PR-3 (2026-05-17) folded the former standalone `docs/workflow-audit.md` into ci-architecture and retired the duplicate page.
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
| F16 | M | Frontend committed HTML rewritten by Python; no test runner | PARTIAL (test runner wired 2026-05-16; bundler-half SOT inversion landed for `non-technical-view.js` 2026-05-17) | Root `index.html` still 702 KB raw / 189 KB gzipped and still rewritten in place by `tools/build/build.py` — the *bundler* half of F16 stays open until the first inline-JS surface migrates out of `index.html` into `apps/web/src/`. **Test runner half closed at HEAD:** the `validate.yml` `frontend` job now runs `cd apps/web && npm ci && npm run typecheck && npm test` on every PR and push (paths filter widened to include `apps/**`). The first real consumer of the scaffold landed alongside the wiring: [`apps/web/src/non-technical-view.ts`](../apps/web/src/non-technical-view.ts) is a typed loader that reads the legacy [`non-technical-view.js`](../non-technical-view.js) at the repo root via `node:vm` `runInThisContext()` (no `eval`, no `new Function()`, no codeguard violation), and [`apps/web/src/__tests__/non-technical-view.test.ts`](../apps/web/src/__tests__/non-technical-view.test.ts) asserts 81 shape invariants over the live data — categories 1..23 with no gaps, every area has name + description + 1-10 UCs, every UC reference is shaped `X.Y.Z` and has a non-empty `why` and matches its declaring category number, and every cat-22 area carrying an `evidencePack` also carries the four other Phase 4.3 elevation fields (`whatItIs` / `whoItAffects` / `splunkValue` / `primer`) per `.cursor/rules/non-technical-sync.mdc`. The deeper "every UC id resolves to a real catalogue entry" cross-check stays in the Python audit `audit-non-technical-references` (audits-content) so the Node side never re-walks the 7,929 sidecars. **Bundler half closed 2026-05-17 for the non-technical-view surface (drift ledger #17):** the typed source [`apps/web/src/data/non-technical-view.data.ts`](../apps/web/src/data/non-technical-view.data.ts) is now the canonical SOT, the repo-root `non-technical-view.js` is generated by [`apps/web/scripts/emit-legacy.ts`](../apps/web/scripts/emit-legacy.ts) (`npm run emit:legacy`), and a CI step in the `frontend` job (`apps/web — non-technical-view.js SOT drift guard`) runs the emitter + `git diff --exit-code` to block drift. Three new SOT invariant Vitest tests pin the typed-source ↔ legacy-loaded ↔ on-disk emitted JS parity (test total 82 → 85). The legacy file shape and consumers (`index.html` global-script load, Python audits, the 81-shape suite that loads via `node:vm` for defense-in-depth) are unchanged — the inversion is invisible at the consumer surface. F16 finally closes when the remaining `index.html` inline-JS sinks migrate out into `apps/web/src/` (still open) and F17 (chrome unification across 9 root HTML pages, still open) lands. |
| F17 | L | 11 root HTML pages duplicate chrome | PARTIAL | **9 root HTML files now** (was 11): `api-docs.html`, `clause-navigator.html`, `compliance-story.html`, `docs.html`, `graph.html`, `guide-reader.html`, `index.html`, `regulatory-primer.html`, `scorecard.html`. Chrome still duplicated across all 9. |
| F18 | L | Root `openapi.yaml` legacy vs. `api/v1/openapi.yaml` canonical | **DONE** (2026-05-12) | Re-verified at HEAD: `openapi.yaml` line 16 carries `> **Status: legacy (hand-maintained)**` followed by a four-paragraph block pointing readers to the canonical `/api/v1/openapi.yaml`, documenting the eventual move to `archive/openapi-legacy.yaml`, and explaining how the OpenAPI drift audit (`audit-openapi-drift`) keeps the two specs in sync. Both specs continue to coexist (root 565 lines / api/v1 210 lines), which is the documented contract — there is no in-progress deletion to wait on. |
| F19 | M | 7 other workflows unaudited | **DONE** (2026-05-12) | Closed by PR #8 (commit `85b680f5d`): every workflow under `.github/workflows/*.yml` now consumes `./.github/actions/setup-python`. The previously skipped guard `tests/build/test_composite_actions.py::test_no_workflow_pins_setup_python_directly` is unskipped and runs in the `audits-content` job, so any future direct `actions/setup-python@<sha>` pin in a workflow fails CI. The 14-workflow inventory itself moves into P2.5 below — that is the remaining work, not F19. |
| F20 | M | Thin test coverage (10 Python + 5 mjs) | **DONE** (2026-05-13, reclassified) | **47 test files / 660 collected tests** in `tests/` + `mcp/tests/` (the "<10 tests" plan baseline far surpassed). The "P16 coverage % targets not yet baselined" caveat in earlier revisions was wrong at HEAD: [`data/baselines/coverage-v9.1.0.json`](../data/baselines/coverage-v9.1.0.json) is a real, in-use, schema-validated coverage baseline (4,093 covered lines / 19,606 statements / 19.76% total, with per-file ratchet records for **24 tier-1 modules** under `tools/build/` and **68 tier-2 modules** under `src/splunk_uc/audits/` + `src/splunk_uc/generators/`, plus 26 tier-3 exempted files). The audit `src/splunk_uc/audits/coverage_budget.py` consumes it as the no-regression contract; baseline integrity is locked by `tests/scripts/test_audit_coverage_budget.py::test_committed_baseline_version_matches_VERSION`. The plan's reference to a missing `coverage-v7.4.2.json` predates the actual capture (`3cafd8e56`, 2026-05-12, refreshed in PR-5 hotfix #3 + #5); the **v9.1.0** filename is the forward-looking floor convention spelled out in [`schemas/changelogs/coverage-baseline.md`](../schemas/changelogs/coverage-baseline.md). P16 burndown work (mutation testing, property-based testing, raising per-tier floors) is still open; the *baseline existence* gate is closed. |
| F21 | L | 7,657 markdown companions tracked alongside JSON | **DONE** (2026-05-18) | All 7,929 `content/cat-*/UC-*.md` companions deleted via `git rm` in this PR (the count grew from 7,761 → 7,929 after the 2026-05-16 regen). The `generate-md-from-json` verb was removed from `splunk_uc/_registry.py`; the `src/splunk_uc/generators/md_from_json.py` module is retained as a deprecation stub so existing imports and the coverage baseline still resolve. The `Markdown freshness check` step was deleted from `.github/workflows/validate.yml` (the cascade is now 13 generators, not 14); the same removal happened in `Makefile`'s `GENERATORS` list and the `sync-generated` / `sync-generated-check` targets, with the `[N/14]` step numbering rewritten to `[N/13]` throughout. `content/cat-*/UC-*.md` is now in `.gitignore` to prevent accidental re-introduction. The LLM-friendly markdown twin is emitted only at build time by `tools/build/templates/uc.py::render_markdown_twin` into `dist/uc/UC-X.Y.Z/uc.md`, which is the path advertised in `AGENTS.md` and on every UC HTML page via `<link rel="alternate" type="text/markdown">`. `src/splunk_uc/tools/lift/validate.py::_regen_markdown` was demoted to a no-op (the `--skip-md-regen` flag still parses, but the validator never writes a sibling `.md` next to a sidecar any more — pinned by `tests/splunk_uc/lift/test_validate.py::test_validate_does_not_emit_in_tree_md_companion`). Doc references updated in `CONTRIBUTING.md`, `ROADMAP.md`, `scripts/README.md`, `docs/adr/0007-json-as-source-of-truth.md`, `docs/adr/0009-generated-artefact-policy.md`, `docs/ci-architecture.md`, `docs/migration-status.md`, `docs/implementation-brief-v7.1.md`, `docs/scripts-taxonomy.md`, `docs/gold-standard-authoring-playbook.md`, and `docs/use-cases-burndown.md`. Drift ledger items #10 / #12 (the cat-22 OT-arc parity gap) are obsoleted by this close. |
| F22 | L | Two parallel sample regimes (95 dirs + 97 files) | **DONE** (2026-05-13) | **94 `samples/UC-*/` directories + 97 `sample-data/uc-*-fixture.json` files.** The §P12 "pick one" framing was wrong on close inspection: the two regimes serve different purposes (raw-event SPL validation vs. compliance-control evidence fixtures) and merging them creates a worse failure mode in both directions. [ADR-0010](adr/0010-sample-and-sample-data-co-exist.md) (2026-05-13) ratifies the split, mechanically forbids cross-tree references, and cross-links both READMEs to the ADR. The deferred schema-shape rationalisation inside `sample-data/` (three observed shapes — `positive`/`negative`, `events_positive`/`events_negative`, `positiveCase`/`negativeCase`) was closed the same day by [ADR-0012](adr/0012-sample-data-canonical-shape.md), which ratifies the **phase3** (`positive`/`negative`) shape as canonical: 57 of 97 fixtures already use it, all 57 populated; the 39 phase2 fixtures are all empty placeholders renamed mechanically in the follow-on PR; the single phase-legacy file (`uc-22.35.1`) is a misclassified SPL fixture that moves to `samples/UC-22.35.1/` per ADR-0010. |
| F23 | L | 12+ schemas, no governance plan | **DONE** (2026-05-13) | **18 schemas** under `schemas/` (up from "12+"): the 9 in plan, plus `coverage-baseline`, `baselines`, `license-inventory`, and the `v2/` tree (`catalog-index`, `metrics-history-index`, `stewardship-digest`, `search-index`, `build-telemetry`, `metrics`). Governance plan **already** in place at HEAD: contract doc [`docs/schema-versioning.md`](schema-versioning.md) defines required metadata (`$schema`, `$id`, `version`, `x-stability`, `x-since`, `x-changelog`), semver bump rules, breaking-change table, 12-month parallel-major window, distribution and migration plan; 18/18 schemas carry the full metadata set (verified by `tools/audits/schema_meta.py`, live in CI at `validate.yml` line 137); 18/18 schemas have a per-schema changelog under [`schemas/changelogs/`](../schemas/changelogs); breaking-change detection live via `tools/audits/schema_diff.py` (validate.yml line 413). F23 closed 2026-05-13 by [ADR-0011](adr/0011-schema-lineage-governance.md) — ratifies the contract, refreshes the inventory in `schema-versioning.md` (11 → 18 schemas; planned-vs-live audits relabelled), and documents the residual `$id` host-name drift as a tracked follow-on (not a F23 blocker). |

## Phases (P0–P19)

| Phase | Status | Notes |
|---|---|---|
| **P0** Hygiene + secrets hardening | **DONE** (2026-05-13) | `.cursorignore` ✓ (with explicit secrets / dotenv block — F10 closed 2026-05-12), pre-commit ✓ (`.pre-commit-config.yaml`), archived script dirs gone ✓, **and** `data/baselines/v7.4.2.json` confirmed in tree (was always there; the prior "v7.4.x not visible" claim was glob-pattern noise). Companion `data/baselines/v8.2.0.json` captured at HEAD `d4a5cc677` (2026-05-13) so we have **two anchored data points** to compare against. `tools/capture_baselines.py` TRACKED_FILES list pruned of the dead `dist/data.js` entry (the build evicts it; see `tools/build/build.py:478-480`) so future captures don't carry a perpetual `null`. New `make baseline` target wired so the `docs/baselines-howto.md` instructions are no longer aspirational. |
| **P1** One build pipeline | DONE | Legacy `build.py` deleted (v8.0.0); `use-cases/` retired (v8.2.0); F1/F2/F3 all resolved. Vestigial `reset_legacy_module_cache()` stub at `tools/build/parse_content.py:1058` is minor dead code. |
| **P2** CI overhaul | **DONE** (2026-05-13) | CodeQL ✓ + dependency-review ✓ + gitleaks ✓ as separate workflows. F7 closed (2026-05-12): zero `continue-on-error: true`. F12 closed (2026-05-12): `validate.yml` now 5 parallel jobs (PR-5). F19 closed (2026-05-12): every workflow uses the composite `setup-python` action (PR #8). **Remaining gap (P2-baselines, 2026-05-13):** closed by `data/baselines/v8.2.0.json` at HEAD `d4a5cc677` — gives reviewers a current-version anchor next to the historical v7.4.2 floor. (A future audit verb that fails CI on regression against the latest baseline is tracked as a follow-on ADR, Q4-2026 target — not blocking the P2 close. ADR number assigned at authorship time; previous "ADR-0013" placeholder was retired when ADR-0011 absorbed the schema-lineage slot.) |
| **P2.5** Audit other 7 workflows | **DONE** (2026-05-13, consolidated 2026-05-17) | Composite-action migration done (F19, 2026-05-12) — every workflow uses the centralized `./.github/actions/setup-python` and the `audit-action-pins` audit blocks unpinned `actions/*@<sha>` references on PRs. P2.5 closure (2026-05-13): authored the standalone `docs/workflow-audit.md` single-page inventory. **PR-3 (2026-05-17, drift ledger #21):** folded that inventory into [`docs/ci-architecture.md` § Workflow inventory](ci-architecture.md#workflow-inventory) and retired the duplicate page. The inventory now lists 13 workflows (post-PR-1 stewardship retirement) with purpose / trigger / cadence / writes-to-repo columns plus the Monday-cluster + Tuesday-backstop cadence calendar. The third-party SHA-pin map is no longer duplicated in prose — `python3 -m splunk_uc audit-action-pins` is the single source of truth for pin enforcement. |
| **P3** ADR + docs reconciliation | **DONE** (2026-05-13) | ADR-0001 `Superseded by: ADR-0007` ✓; AGENTS.md says 11 tools ✓. The plan's "proposed `docs/architecture-2027.md`" placeholder is now explicitly absorbed by [`docs/architecture.md`](architecture.md) §"Forward-looking work" (added 2026-05-13): forward-looking architectural work goes into [`ROADMAP.md`](../ROADMAP.md) (release-aligned plan) and [`docs/adr/`](adr/) (numbered-on-acceptance decision records — ADR-0010, ADR-0011, ADR-0012 all landed 2026-05-13 demonstrating the active cadence). No separate dated-architecture doc is needed; the same rationale that retired the placeholder "ADR-0011 (sample-data shape)" slot ([`ADR-0011 §"Alternatives considered"`](adr/0011-schema-lineage-governance.md) point C) applies here: reserved-but-empty docs distort the lineage. |
| **P4** Typed Python pipeline | PARTIAL (package floor locked) | `pyproject.toml` ✓; ruff + mypy + coverage configs ✓; `[project.scripts]` ✓ (P6 Tier 4); per-module mypy strictness gradient in place. **First canary closed 2026-05-13:** `mypy --strict src/splunk_uc/audits/` (51 source files, 0 errors). **Second canary closed 2026-05-13:** `mypy --strict src/splunk_uc/generators/` (17 source files, 0 errors after a one-line `set[str]` fix in `recommender_app._gsa_load_ucs`). **Package-wide floor closed 2026-05-13:** survey showed every remaining subpackage (`ingest`, `feasibility`, `migrations`, `tools`) plus the three top-level modules was already strict-clean; the two per-canary overrides were consolidated into a single `[[tool.mypy.overrides]] module = "splunk_uc.*"` block and the CI step now lints the whole package — **94 source files, ~25 kLOC, every module under `src/splunk_uc/` type-clean under `--strict`**. **Remaining gaps:** the build pipeline (`tools/build/*`) and the legacy `build.py` entrypoint still carry per-module loosened overrides; no typed `UseCase` / `Catalog` Pydantic/dataclass model in `src/splunk_uc/`. |
| **P5** Frontend rebuild | SCAFFOLDED + first migration in CI (2026-05-16) + SOT inversion for `non-technical-view.js` (2026-05-17) | <a id="p5-first-cut"></a>[`apps/web/`](../apps/web/) exists with Vite 8.0.13 + TypeScript 6.0.3 (strict — `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `verbatimModuleSyntax`) + Vitest 4.1.6, ratified by [ADR-0013](adr/0013-frontend-rebuild-scaffold.md). The scaffold is no longer opt-in — `validate.yml`'s `frontend` job now runs `cd apps/web && npm ci && npm run typecheck && npm test` on every PR, and the path filter was widened to include `apps/**`. **First real migration target in tree:** [`apps/web/src/non-technical-view.ts`](../apps/web/src/non-technical-view.ts) is a typed loader (using `node:vm` `runInThisContext()`) over the legacy [`non-technical-view.js`](../non-technical-view.js); [`apps/web/src/non-technical-view.types.ts`](../apps/web/src/non-technical-view.types.ts) declares the `NonTechnicalCatalog` / `NonTechnicalCategory` / `NonTechnicalArea` / `NonTechnicalUcRef` interfaces; [`apps/web/src/__tests__/non-technical-view.test.ts`](../apps/web/src/__tests__/non-technical-view.test.ts) asserts 81 shape invariants over the live data (734 ms in vitest jsdom). F8 (a11y landmarks) closed under P10; F16 reclassified PARTIAL above (test-runner half now in CI; bundler half waits for source-of-truth inversion); F17 (11 HTML pages duplicate chrome) still unresolved. |
| **P6** Scripts taxonomy | DONE | Just closed in v8.2.0 (commit `a36aa4db4`). 83-verb dispatcher + Tier 4 packaging. |
| **P7** Server-side search + API gateway | NOT STARTED | — |
| **P8** Observability + content metrics | **DONE** (2026-05-18, reclassified to align with P14 lean-mode revert) | The three machine-readable surfaces called for in the plan are in place at HEAD: [`dist/metrics.json`](../dist/metrics.json) (validated against [`schemas/v2/metrics.schema.json`](../schemas/v2/metrics.schema.json) on every reproducible build per AGENTS.md), [`data/metrics-history/<VERSION>.json`](../data/metrics-history/) (release-time trend snapshots, gated by `scripts/snapshot_metrics.py --check`), and [`dist/build-telemetry.json`](../schemas/v2/build-telemetry.schema.json) (per-stage wall-clock duration, schema-pinned). The stewardship digest is generated by `make stewardship-digest` from [`src/splunk_uc/generators/stewardship_digest.py`](../src/splunk_uc/generators/stewardship_digest.py) and a PR smoke-test gates its schema against [`schemas/v2/stewardship-digest.schema.json`](../schemas/v2/stewardship-digest.schema.json). **The "Slack/email weekly digest" item from the original plan was obsoleted by P14 lean-mode revert (drift ledger #19, 2026-05-17):** the scheduled `.github/workflows/stewardship.yml` workflow that would have opened a weekly tracking issue was deleted in PR-1 along with the rotation workflow + per-category CODEOWNERS routing, because the co-maintainer team they were scaffolding for doesn't exist. Wiring a notification channel now would resurrect exactly the auto-opened-issue surface the maintainer just deleted. Per [`docs/stewardship-digest.md`](stewardship-digest.md), the digest stays an on-demand artefact: a single maintainer running `make stewardship-digest` ahead of a release captures the relevant trend snapshot, and `release.yml` already ratifies that snapshot via the metrics-history gate. The notification-channel residual is therefore closed by design, not by implementation. |
| **P9** Monorepo split (apps/ + packages/) | NOT STARTED | — |
| **P10** Performance + a11y hardening | PARTIAL (Lighthouse CI scaffold landed 2026-05-18) | F8 closure unblocked P10. First a11y deliverable landed 2026-05-13: `index.html` and `scorecard.html` now ship with a visually-hidden `<h1>` inside the correct landmark (banner / main), and both search-bar wrappers on `index.html` carry `role="search"` + distinguishing `aria-label`, so the `region` warning that the F8 closure re-anchored on `#search-input` is gone. `reports/perf-a11y.json` regenerated: `index.html` 0 violations / 0 warnings (was 0 / 1); `scorecard.html` 0 / 0 (unchanged). New `.visually-hidden` utility added to `src/styles/05-helpers.css` + mirrored in `index.html` inline `<style>` + duplicated in `scorecard.html` `<style>` (separate file, no shared stylesheet — chrome unification is F17). **Lighthouse CI workflow added 2026-05-18:** [`.github/workflows/lighthouse.yml`](../.github/workflows/lighthouse.yml) runs `treosh/lighthouse-ci-action@3e7e23fb74…` (12.6.2, verified by `audit-action-pins`) against `index.html`, `scorecard.html`, `clause-navigator.html`, and `uc/UC-1.1.1/index.html` on every push to `main` that touches the build inputs (HTML / `src/styles/` / `src/scripts/` / `tools/build/`) and on `workflow_dispatch`. The config in [`.lighthouserc.json`](../.lighthouserc.json) uses warn-only thresholds (`performance ≥ 0.6`, `accessibility ≥ 0.9`, `best-practices ≥ 0.85`, `seo ≥ 0.85`) in the desktop preset under headless Chrome — a deliberately permissive first cut. Lighthouse scores fluctuate ±3 points between runs on the same commit, so we soak the baseline before gating; once the warn → error promotion happens (tracked under the closing of this P10 row), the workflow can move to `pull_request` trigger and become a hard PR gate. Results upload to `temporaryPublicStorage` for at-a-glance trend review plus the `lighthouse-results` workflow artifact for archival. Still open under P10: warn → error promotion of the Lighthouse thresholds after a soak period; CSP `'unsafe-inline'` tightening on both `script-src` and `style-src` (F8 PR-C precondition); and the virtual-scroll renderer `<template>`-clone refactor (F8 PR-C proper, deferred to P10 as documented in the F8 inventory). |
| **P11** OSS release polish | **DONE** (2026-05-18) | The original "no `.devcontainer/`" caveat is wrong at HEAD: [`.devcontainer/devcontainer.json`](../.devcontainer/devcontainer.json) ships **pinned by OCI image-index digest** (Microsoft `mcr.microsoft.com/devcontainers/python:3.12@sha256:8b1b15…`), with Node 20 + GitHub CLI features, ruff + mypy + markdownlint + YAML extensions, pre-forwarded port 8000, pip-cache volume mount, and an 8-assertion structural test suite ([`tests/build/test_devcontainer.py`](../tests/build/test_devcontainer.py)) that pins the invariants. The 2026-05-13 close added the `devcontainer-init` Makefile target (installs `pip install -e .[audits,dev,test]`, registers pre-commit hooks, warm-builds `dist/`), unskipped `test_make_target_exists`, and asserted that `devcontainer-init` is listed in `.PHONY`. The "ROADMAP.md still says v7.1" half was already resolved on 2026-05-12 (loose-end ledger #1). **Closed 2026-05-18:** the previously-residual "no automated workflow that pushes `reports/roadmap-export.json`" item is now addressed by the new [`Roadmap snapshot`](../.github/workflows/roadmap-export.yml) workflow — it runs on every push to `ROADMAP.md` on `main`, every Monday 08:30 UTC, and on manual dispatch. It regenerates `reports/roadmap-export.json`, runs an inline eight-key + schema-version + three-required-backlog-buckets shape check from [`docs/roadmap-sync.md`](roadmap-sync.md) §"JSON snapshot contract" (so a regression in the snapshot contract surfaces at publish time rather than downstream at maintainer-sync time), commits the regenerated file back to `main` with a `github-actions[bot]` message if it differs from HEAD (same pattern as `regulatory-watch.yml`), and uploads the file as the `roadmap-export` workflow artifact (`retention-days: 90`, `if-no-files-found: error`) for off-band consumers running `gh run download`. The repo deliberately stops there — the Project v2 sync side stays in the maintainer runbook because project IDs, field IDs, and the Projects v2 schema evolve out-of-band of this repo (rationale ratified in [`docs/roadmap-sync.md`](roadmap-sync.md) §"Why two layers (CI + maintainer runbook)?"). |
| **P12** Splunk content quality moonshot | NOT STARTED | F22 (two sample regimes) unresolved; no per-UC `thresholds` field in schema; no SPL formatter; no AppInspect gate. |
| **P13** Recommender TA hardening | NOT STARTED | The recommender TA was overhauled in v8.0.0 (CHANGELOG mentions "single Cloud-safe recommender app") but P13's threat model + Sigstore on `.spl` + AppInspect Cloud gate not visible. |
| **P14** Content stewardship | REVERTED (2026-05-17, drift ledger #19) | The 2026-05-13 / -14 / -17 P14 work (per-category CODEOWNERS routing, the two structural tests that locked it, the per-category scorecard drill-downs as a routing surface, and the weekly rotation reminder workflow) was scaffolding for a co-maintainer team that doesn't exist. PR-1 of the lean-mode cleanup deletes the rotation workflow + picker + tests + runbook, deletes the global stewardship-digest scheduled workflow (the *generator* is preserved as `make stewardship-digest` for on-demand use), collapses `.github/CODEOWNERS` to a single `* @fenre` catch-all, and removes the two structural pin tests (`test_codeowners.py`, `test_scorecard_drilldowns.py`). The per-category scorecard drill-down *content* stays in `docs/scorecard.md` — it is genuinely useful self-information about which dimensions are dragging which category — but its preamble no longer frames itself as a CODEOWNERS-routing surface. Net effect: −7 files, −2 scheduled workflows, no loss of correctness coverage. See drift ledger #19. |
| **P15** Specification compliance moonshot | NOT STARTED | 2027 target per plan; no `clauseText[]` bindings. |
| **P16** Test coverage burndown | PARTIAL | 660+ tests collected ✓. Coverage baseline floor in place at [`data/baselines/coverage-v9.1.0.json`](../data/baselines/coverage-v9.1.0.json) — schema-validated (`schemas/coverage-baseline.schema.json`), consumed by `src/splunk_uc/audits/coverage_budget.py` as the no-regression contract, with 24 tier-1 / 68 tier-2 per-file records + 26 tier-3 exempt files. **Wave C-2 (2026-05-18)** raised the floor on the two top zero-coverage surfaces explicitly called out in the previous revision: `tools/build/templates/uc.py` from **4.77% → 90.64%** (`tests/build/test_template_uc.py`, 35 tests exercising `render_html` / `render_index_json` / `render_markdown_twin` with a representative-UC fixture) and `src/splunk_uc/generators/api_surface.py` from **0% → 22.4%** (`tests/splunk_uc/generators/test_api_surface_units.py`, 51 tests for the module's pure helpers: `_safe_version`, `_canonicalise_cim`, `_uc_sort_key`, `_uc_compact`, `_regulation_alias_to_id`, `_index_ucs_by_regulation`, `_recommender_sourcetypes`, `_recommender_cim_models`, `_looks_like_app_label`). Both new floors are absorbed into the baseline (totals: 4,619 / 18,102 covered = 25.52%, up from 22.58%) and the CI coverage capture in `.github/workflows/validate.yml` was widened from `tests/build/ tests/scripts/` to also include `tests/splunk_uc/` so the new tests count toward the per-file ratchet. **What's still open**: mutation testing (`mutmut` / `cosmic-ray`) and property-based testing (`hypothesis`) haven't been adopted; the heavier integration paths in `api_surface.py` (`_load_ucs`, `_render`, `_recommender_splunkbase_index`) need a full-repo fixture for further uplift. |
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
    (Phases 1-5a rollup: ISA/IEC 62443<sup class="ref">[<a href="#ref-3">3</a>]</sup>, NERC CIP<sup class="ref">[<a href="#ref-7">7</a>]</sup> v8, EU NIS2<sup class="ref">[<a href="#ref-1">1</a>]</sup> OT,
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

    1. ~~**Phase 4.2 evidence-pack orphan gate:**~~ **RESOLVED** in
       cascade follow-on commit (see below). The maintainer's OT-arc
       added 8 hand-authored evidence packs (`cert-in.md`,
       `cn-csl.md`, `do-326a.md`, `fr-lpm.md`, `iec-61511.md`,
       `imo-msc-428-98.md`, `sg-cyber-act.md`, `tsa-surface.md`) that
       carry sections the generator template cannot reproduce
       (e.g. §6.1/§6.2 inspector-vs-CO testing flows on the SG pack,
       custom §11 "Questions a flag-State / PSC / class-society
       inspector should ask" on the IMO pack, bilingual FR/EN
       auditor questions on the LPM pack, SIS/BPCS/SCS three-layer
       table on the IEC 61511 pack, stage-of-certification
       hierarchy on the DO-326A pack, MeitY / CERT-In dual-track
       reporting on the cert-in pack, five-statute cross-reference
       matrix on the cn-csl pack, SD 1580/1582-2024-01 cross-mode
       comparison on the tsa-surface pack). Resolution chose path
       **(b)** from the originally documented options below:
       `evidence_packs.py` grew an `EXEMPT_ORPHANS` frozenset (the 8
       slugs) and both `_check_drift()`'s orphan loop and
       `_prune_orphans()` learned to skip entries whose stem is in
       that set. The generator now:

       - Owns the 17 packs in `PACK_TARGETS` (generator-owned,
         template-driven).
       - Leaves the 8 packs in `EXEMPT_ORPHANS` alone on both
         `docs/evidence-packs/<slug>.md` and the (gitignored)
         `api/v1/evidence-packs/<slug>.json` surface — they live
         outside generator scope but ship at predictable URLs that
         match the rest of the pack-catalogue naming convention.
       - Reports byte-identical output for both modes (no `changed:`,
         no `orphan:`, no `missing:` in `--check`).

       Future direction (path **(a)**) is still open: extend
       `evidence_packs.py` to consume per-slug hand-customised
       section bodies from `data/evidence-pack-extras.json` so each
       OT-arc pack can be promoted from `EXEMPT_ORPHANS` to
       `PACK_TARGETS` while keeping its hand-authored §6.1/§11
       sections intact and gaining the generator's clause table /
       coverage rollup / citation injection / API JSON twin
       automatically. Tracked as a separate enhancement, not a CI
       blocker.

       Same commit also refreshed 18 in-`PACK_TARGETS` MD files
       (coverage-table refresh after the OT-arc UCs landed
       compliance coverage for SOCI / AWIA / CIRCIA / CLC-TS-50701 /
       NCA OTCC / SOX-ITGC / NIST 800-53<sup class="ref">[<a href="#ref-6">6</a>]</sup> — the maintainer's UCs
       brought the *previously-zero* clause counts on those packs
       from 0.0% to 75-100%). The clause-by-clause tables on
       AWIA / CIRCIA / CLC-TS-50701 / SOCI in particular gained
       ~150-200 lines each as the "_not yet covered_" placeholder
       rows were replaced with real UC-ID lists.

    2. ~~**Phase 4.3 cat-22 non-technical block regeneration check:**~~
       **RESOLVED** in cascade follow-on commit (see below). The
       maintainer's OT-arc added 13 `areas[]` entries to the
       `"22": { … }` block in
       [`non-technical-view.js`](../non-technical-view.js) — `NCA
       OTCC (Saudi OT)`, `SOCI Act + CIRMP Rules (Australia)`,
       `AWIA s2013 + EPA/CISA Water Sector Cybersecurity (US)`,
       `CIRCIA + 6 USC 681b (US CISA Cyber Incident Reporting)`,
       `CLC/TS 50701 (CENELEC Railway Cybersecurity)`, `TSA Surface
       Cybersecurity Security Directives (US Pipeline + Freight Rail
       + Passenger Rail)`, `SG Cyber Act 2018 + CSA CII Regulations
       (Singapore)`, `France LPM OIV Regime + ANSSI 20-Rules
       (France)`, `IMO MSC.428(98) + MSC-FAL.1/Circ.3 + IACS UR
       E26/E27 (Maritime / Shipping, Global)`, `RTCA DO-326A /
       EUROCAE ED-202A + DO-355A + DO-356A + FAA AC 20-186 + EASA
       AMC 20-42 + EASA Part-IS (Aviation / Airworthiness Security,
       Global)`, `China CSL / DSL / PIPL / CII Regulations / MLPS 2.0
       (Cybersecurity, Data, Privacy, CII — PRC)`, `CERT-In Directions
       2022 + DPDP Act 2023 (Cybersecurity Incident Reporting + Data
       Protection, India)`, `IEC 61508 / 61511 + ISA-TR84.00.09 +
       IEC 62443 (Functional Safety + Cybersecurity overlay, Global
       Process Industries)`. These were extracted from the JS file
       via a one-shot Node `node:vm` loader, emitted as Python source
       through a one-shot Python rendering helper, and spliced into
       the `_AREAS` list in
       [`src/splunk_uc/migrations/regenerate_cat22_ntv.py`](../src/splunk_uc/migrations/regenerate_cat22_ntv.py)
       between the `CMMC defence` entry and the `EU AI Act` entry
       (`_AREAS` count 49 → 62). The generator's `render_block()` now
       emits byte-identical output to the on-disk JS block — i.e. the
       generator's deterministic-rendering contract is preserved
       *and* the maintainer's multilingual hand-authored content
       (French `ucs[].why` strings on the LPM entry, the `24×7` U+00D7
       Unicode multiplication sign on the IMO entry, the `règles
       d'hygiène` and `Délégué OIV` accent-letters, the §3.1 section
       sign) survives intact because the splice was done through a
       JSON round-trip rather than hand-transcription. The Node /
       Python one-shot helpers used for the splice were deleted post-
       commit; the resulting `_AREAS` list is now the canonical
       source-of-truth and the cat-22 NTV `--check` gate passes.

    **Cascade closure (2026-05-16/17).** Four gates that the
    cascade surfaced are now resolved through separate follow-on
    commits, in the order the `set -e` job-script unmasked them:
    Phase 3.2 cross-cutting compliance (e2f467cf6), Phase 4.5f
    perf+a11y (e2f467cf6 + cd1f0b65b refresh), Equipment-tags regen
    (3532a352f), Phase 4.3 cat-22 NTV (1740d1321), Phase 2.1
    compliance-gaps timestamp realignment (1c631b33a), Phase 4.2
    evidence-packs (39be6d175), and finally Phase 5.4 signed
    provenance ledger + Phase 4.5c sandbox-validation report (this
    commit). The two CI-load-bearing gates that the original F16
    narrative explicitly flagged as pre-existing OT-arc generator
    gaps — Phase 4.3 cat-22 non-technical block (`migrate-cat22-ntv
    --check`, line 698 of `validate.yml`) and Phase 4.2
    evidence-pack regeneration (`generate-evidence-packs --check`,
    line 724) — are part of that closure. The path chosen for each:

    - **Phase 4.3** — promotion: maintainer's content moved
      *into* the generator (the 13 OT-arc `_AREAS` entries spliced
      into `regenerate_cat22_ntv.py` via a JSON round-trip), so the
      generator becomes the canonical source-of-truth and the
      maintainer's multilingual narrative survives byte-identical.

    - **Phase 4.2** — exemption: the 8 OT-arc evidence packs stay
      hand-authored and the generator gains an `EXEMPT_ORPHANS` set
      that excludes them from both the orphan-check and the
      orphan-prune. Plus a separate refresh of the 18
      in-`PACK_TARGETS` MD files (legitimate coverage update after
      the OT-arc UCs landed).

    - **Phase 2.1 + Phase 5.4 + Phase 4.5c** — regen: three
      deterministic generators (`audit-compliance-gaps`,
      `generate-mapping-ledger`, `audit-sandbox-validation`) emit
      reports whose deterministic per-entry stamps derive from
      `git log` over the regulations / UC sidecars. The OT-arc
      content commits advanced those upstream files' last-commit
      times, so each report needed a fresh regen-and-commit cycle
      to realign — no template-change or maintainer decision
      required, just `python -m splunk_uc <generator>` and commit.
      All three are pure deterministic anchors against git
      provenance, so the diffs are tightly scoped (compliance-gaps
      = 2-line timestamp shift; mapping-ledger = 664 entries with
      `lastModifiedCommit` SHA refresh from `8bed239` to `e2f467c`
      out of 2680 total, no `firstSeenCommit` / `signature` /
      `payloadHash` / `entryHash` drift; sandbox-validation = 18
      lines adding canonical regulation-name aliases alongside the
      pre-existing ids).

    Both choices are defensible:

    - Promotion (path 4.3) is preferred when the generator template
      can re-emit the maintainer's content byte-identical. The
      cat-22 NTV `_AREAS` entries are dict-shaped data with a
      stable schema, so promotion is mechanical.

    - Exemption (path 4.2) is preferred when the maintainer's
      content has *structural* customisations the template cannot
      reproduce without an invasive template extension. The 8
      OT-arc evidence packs each have custom section bodies (§6.1
      inspector-vs-CO testing flows, §11 jurisdiction-specific
      inspector questions, three-layer separation matrices) that
      vary per regulation, so exemption is the low-risk choice.

    Future direction for path 4.2: extend
    `generators/evidence_packs.py` to consume per-slug
    hand-customised section bodies from
    `data/evidence-pack-extras.json` so each OT-arc pack can be
    promoted from `EXEMPT_ORPHANS` to `PACK_TARGETS` while keeping
    its hand-authored sections intact. Tracked as an enhancement
    rather than a CI blocker.

17. **F16 / P5 source-of-truth inversion for `non-technical-view.js`
    (2026-05-17).** New drift-ledger entry for the bundler-half F16
    closure on the non-technical view surface. Pre-inversion the
    repo-root [`non-technical-view.js`](../non-technical-view.js)
    was the hand-edited authoring surface and
    [`apps/web/src/non-technical-view.ts`](../apps/web/src/non-technical-view.ts)
    was a typed `node:vm`-based loader over it (drift ledger #14,
    2026-05-16). That closed the *test runner* half of F16 but the
    data had no type-checking at authoring time, edits could
    silently produce shapes the legacy parser accepted but
    consumers might not, and there was no migration path into the
    apps/web/ build pipeline.

    **Resolution: typed module is canonical, legacy JS is
    generated.** Three new files plus tightly-scoped edits to the
    existing apps/web/ surface and the workflow:

      - [`apps/web/src/data/non-technical-view.data.ts`](../apps/web/src/data/non-technical-view.data.ts)
        (1,332 lines, 214,047 bytes) — the canonical typed source:
        `export const NON_TECHNICAL: NonTechnicalCatalog = { … };`.
        Content body byte-identical to the pre-inversion JS — the
        data was moved by mechanical header swap, no editorial
        changes. The pre-existing `NonTechnicalCatalog` /
        `NonTechnicalCategory` / `NonTechnicalArea` /
        `NonTechnicalUcRef` interfaces (declared in
        [`non-technical-view.types.ts`](../apps/web/src/non-technical-view.types.ts)
        as part of drift ledger #14) now apply at authoring time —
        `tsc --noEmit` catches typos in field names, wrong types
        on optional fields, and category-key mismatches.
      - [`apps/web/scripts/emit-legacy.ts`](../apps/web/scripts/emit-legacy.ts)
        (~173 lines) — pure `renderLegacy(catalog)` function plus a
        guarded `main()` (uses
        `import.meta.url === pathToFileURL(process.argv[1]).href`
        so importing for tests doesn't side-effect on disk). The
        renderer walks the four observed area-shape combinations
        (plain 160 / tier-1 25 / elevation-only 23 /
        elevation+primer 15) verified in advance via grep over the
        pre-inversion file, and emits each area as a single long
        opener line followed by per-line UCs and the `      ]}`
        closer. Byte-identical round-trip verified on the first
        emit run (no iteration needed): `npm run emit:legacy` +
        `git diff --exit-code non-technical-view.js` exits 0.
      - [`apps/web/src/__tests__/emit-legacy.test.ts`](../apps/web/src/__tests__/emit-legacy.test.ts)
        — three new SOT invariant tests: typed `NON_TECHNICAL`
        deep-equals legacy-loaded catalog; `renderLegacy(NON_TECHNICAL)`
        is byte-identical to the on-disk legacy JS; emitter
        prologue / footer / single trailing newline pinned. Test
        total 82 → 85.

    **CI wiring.** New `apps/web — non-technical-view.js SOT drift
    guard` step added to `validate.yml`'s `frontend` job (after the
    existing Vitest invocation). The step runs `npm run emit:legacy`
    then `cd ../.. && git diff --exit-code non-technical-view.js`;
    PRs that edit the typed source without committing the
    regenerated JS (or vice versa) fail the build with a useful
    diff. The step name is added to
    `tests/build/test_validate_workflow_partition.py::CRITICAL_STEP_NAMES`
    so future drift on the step *name* is caught by the partition
    test (75 tests pass locally).

    **Rule update.**
    [`.cursor/rules/non-technical-sync.mdc`](../.cursor/rules/non-technical-sync.mdc)
    now declares `apps/web/src/data/non-technical-view.data.ts`
    the authoring surface, documents the `npm run emit:legacy`
    workflow, replaces the JavaScript example with the equivalent
    TypeScript object literal, rewrites §"Validation" to point at
    the apps/web/ commands, and extends `globs:` to include the new
    TS module.

    **What stays the same.** The repo-root `non-technical-view.js`
    remains at the exact same path with the exact same byte
    content (byte-identical round-trip), so `index.html` and every
    other consumer that loads it as a global script continues to
    work without any change. The `loadCatalogFromLegacyJs()`
    function still exists in `non-technical-view.ts` and the
    81-shape suite still uses it — preserving defense in depth
    against emitter regressions. The Python audit
    `audit-non-technical-references` reads the legacy JS directly
    and is likewise unaffected.

    **What changes.** F16 *bundler* half is now closed for the
    non-technical-view surface (the test runner half closed
    2026-05-16). The next P5 bites per ADR-0013 are: (a) inverting
    `index.html`'s remaining inline JS, (b) chrome unification
    across the 9 root HTML pages (F17). The pattern established
    here (typed SOT + emitter + drift guard + defense-in-depth
    legacy loader retained) is the template for those follow-ups.

    Files touched (10): `apps/web/package.json`,
    `apps/web/package-lock.json`, `apps/web/tsconfig.json`,
    `apps/web/src/data/non-technical-view.data.ts` (new),
    `apps/web/scripts/emit-legacy.ts` (new),
    `apps/web/src/__tests__/emit-legacy.test.ts` (new),
    `apps/web/src/non-technical-view.ts` (re-exports typed
    `NON_TECHNICAL`, docstring rewrite),
    `.cursor/rules/non-technical-sync.mdc`,
    `.github/workflows/validate.yml` (new SOT drift-guard step),
    `tests/build/test_validate_workflow_partition.py`
    (CRITICAL_STEP_NAMES extended). Plus this drift-ledger entry +
    the F16 / P5 row updates above + the cross-out in
    §"Recommended next actions" #10 + the CHANGELOG `[Unreleased]`
    bullet. The repo-root `non-technical-view.js` is unchanged
    byte-for-byte.
18. **§P14 cadence-half closed.** **2026-05-17** — Reverted same
    day by drift ledger #19 below as part of the lean-mode
    cleanup; left in place as a historical anchor.
    [`.github/workflows/stewardship-rotation.yml`](../.github/workflows/stewardship-rotation.yml)
    ran Mondays 08:30 UTC and rotated one of the 23 content
    categories per week into a per-category GitHub issue assigned
    to the CODEOWNERS owner(s). Files added: the workflow,
    `src/splunk_uc/tools/pick_rotation_category.py`,
    `tests/splunk_uc/test_pick_rotation_category.py`,
    `docs/stewardship-rotation.md` — all removed in PR-1.

19. **Lean-mode PR-1: solo-maintainer cleanup of
    team-coordination scaffolding (2026-05-17).** The repository
    is a one-person catalogue. Several CI surfaces were
    scaffolding for a co-maintainer rotation that never
    materialised: weekly stewardship-rotation reminders assigning
    `@fenre` to review `@fenre`'s content, a 23-row CODEOWNERS
    routing scheme whose every row pointed at `@fenre`, two
    structural tests that pinned the 23-row layout against
    silent drift, the per-category scorecard drill-down framing
    as a "CODEOWNERS deep-link surface", and a separate global
    stewardship-digest workflow that opened a weekly tracking
    issue. PR-1 deletes those surfaces. Net diff: **−7 files,
    −2 scheduled workflows, no loss of correctness coverage**.

    **Files removed.**

    - `.github/workflows/stewardship-rotation.yml` (the rotation
      workflow shipped ~6 hours earlier in drift ledger #18).
    - `.github/workflows/stewardship.yml` (the weekly digest
      workflow; the *generator*
      `python -m splunk_uc generate-stewardship-digest` is
      preserved as `make stewardship-digest` for on-demand use).
    - `src/splunk_uc/tools/pick_rotation_category.py` + its
      14-test suite at
      `tests/splunk_uc/test_pick_rotation_category.py`.
    - `tests/build/test_codeowners.py` (the 6-case structural
      test pinning per-category routing; obsolete after the
      CODEOWNERS collapse).
    - `tests/build/test_scorecard_drilldowns.py` (the 5-case
      three-way-alignment test; obsolete for the same reason).
    - `docs/stewardship-rotation.md` (runbook for a workflow
      that no longer exists).

    **Files edited.**

    - `.github/CODEOWNERS` collapsed from 60 lines (default
      catch-all + per-area routing + 23 per-category rows +
      governance routing) to a single `* @fenre` rule with a
      brief comment. If a co-maintainer ever joins the
      project, path-specific rules can be added below — order
      matters (last-match wins).
    - `src/splunk_uc/_registry.py` drops the
      `pick-rotation-category` verb registration.
    - `src/splunk_uc/generators/scorecard.py` keeps the
      per-category drill-downs (they are useful self-information
      about which dimensions are dragging which category) but
      softens the section preamble to remove the now-defunct
      CODEOWNERS-routing framing.
    - `docs/scorecard.md` regenerated from the updated generator
      so the preamble matches the source.
    - The workflow inventory (then `docs/workflow-audit.md`, since
      folded into [`docs/ci-architecture.md` § Workflow inventory](ci-architecture.md#workflow-inventory)
      in PR-3 / 2026-05-17 / ledger #21) drops the two stewardship
      rows from the inventory table (15 → 13), removes the two
      cadence-calendar entries for them, prunes them from the
      `upload-artifact` consumer list, and rewords the
      Monday-cluster paragraph to "three weekly maintenance
      probes" (was five).
    - `docs/ci-architecture.md` drops the two TL;DR rows for the
      stewardship workflows and collapses the two long-form
      sections into one short "Stewardship digest (on-demand
      only)" note that points at `make stewardship-digest`.

    **Verification.** Pre-push verification ran `make build`,
    `make audit-full`, `pytest`, `mypy --strict src/splunk_uc/`,
    and `ruff check src/ tests/` — every gate green. The
    `audit-action-pins` audit still passes because the two
    removed workflows reused already-pinned `actions/checkout`
    and `actions/upload-artifact` references; no new pin landed
    and no existing pin became orphaned. `splunk_uc`
    dispatcher --help loses one verb (`pick-rotation-category`)
    but the registry-shape test still passes since it iterates
    `all_verbs()` rather than pinning a count.

    **What this is *not*.** Not a correctness cut. The 660
    pytest cases, `mypy --strict` over
    `src/splunk_uc/` (now 94 files after removing the picker),
    the SPL audits (grammar, hallucinations, references), the
    CIM↔SPL alignment audit, schema validation + diff, build
    reproducibility, CodeQL, dependency-review, gitleaks,
    link-check, and the `validate.yml` 5-job partition all
    continue to run unchanged. The per-category scorecard
    drill-down *content* (composites, dimensions, depth tiers,
    provenance mix) also stays — it just no longer pretends to
    serve a CODEOWNERS routing surface that does not exist.

    **Why now.** The previous session's drift ledger #16 ("third
    cascade-style regen on `main` in 24 hours") and #18 (rotation
    reminders for a solo maintainer) made the underlying drift
    visible: process surface was outgrowing the solo-developer
    bandwidth it was meant to support. The user's explicit
    instruction was: "I want this project to be as clean and
    efficient as possible, but also as stable and robust as
    possible." PR-1 is the first cut in that direction — strip
    team-coordination machinery, keep every correctness gate.
    PR-2 (collapse cascade-regen `--check` gates into one
    umbrella `make sync-generated`) and PR-3 (strip community
    docs + per-file coverage ratchet + auto-references footer
    regen) follow.

20. **Lean-mode PR-2: collapse 14 cascade-regen `--check` gates
    into one umbrella drift gate (2026-05-17).** Drift ledger
    #16 captured the underlying symptom — a content edit forces
    a cascade through ~10 generators, and CI was running each
    `--check` gate as its own step, so a forgotten regeneration
    surfaced as a sequential failure-chain (fix one, push, watch
    the next one fail, fix that, push, etc.). PR-2 introduces a
    single umbrella drift gate that runs every cascade generator
    with `--check` in one shell, collects per-step failures, and
    prints every drift surface in one log so a content edit's
    full regen footprint is visible from a single CI failure.

    **New Make targets.**

    - `make sync-generated` — run every cascade generator in
      write-mode in dependency-safe order. The local recovery
      command for any drift gate failure is now `make
      sync-generated && git add -A && git diff --staged`.
    - `make sync-generated-check` — run every cascade generator
      with `--check`. Collects per-step failures, prints
      `DRIFT in: <step>` lines, exits 1 once all 14 have run.
      Total wall-clock locally ≈30s.

    **`validate.yml` collapse.** The following 14 individual
    steps in the `audits-content` job were deleted and replaced
    by a single `Cascade-generator drift gate (umbrella)` step
    that calls `make sync-generated-check`:

    1. `Wiki backlinks index freshness`
       (`scripts/generate_backlinks.py --check`)
    2. `Auto-generated doc references freshness`
       (`scripts/generate_doc_references.py --check`)
    3. `Prerequisite graph audit (wave / pre)`
       (`audit-prerequisites --check`)
    4. `Phase 3.1 clause-level backfill generator regeneration check`
       (`generate-phase3-1-backfill --check`)
    5. `Phase 3.2 cross-cutting compliance generator regeneration check`
       (`generate-phase3-2-cross-cutting --check`)
    6. `Phase 3.3 derivative-regulation propagation regeneration check`
       (`generate-phase3-3-derivatives --check`)
    7. `Equipment-tags regeneration check (sidecar equipment[] /
       equipmentModels[])`
       (`generate-equipment-tags --check`)
    8. `Non-technical grandma explanation regeneration check`
       (`generate-grandma-explanations --check`)
    9. ~~`Markdown freshness check`
       (`generate-md-from-json --check`)~~ *(removed 2026-05-18; F21
       close — the per-UC `.md` companions were deleted and the
       generator was retired)*
    10. `Phase 4.3 cat-22 non-technical block regeneration check`
        (`migrate-cat22-ntv --check`)
    11. `Clause-level gap report regeneration check`
        (`audit-compliance-gaps --check`)
    12. `Phase 4.2 evidence-pack generator regeneration check`
        (`generate-evidence-packs --check`)
    13. `Phase 5.4 signed provenance ledger regenerate (determinism)`
        (`generate-mapping-ledger --check`)
    14. `Phase 4.5c sandbox validation gate`
        (`audit-sandbox-validation --check`)

    The `audits-content` job dropped from 53 steps to 40. The
    `generate-doc-references.py --validate-library` step (purely
    schema-validates the references library; no per-doc rewrite)
    stays as its own step because it's cheap, library-only, and
    independent of the per-doc rewrite (which now lives in the
    umbrella).

    **What stays unchanged.** Every audit that emits a structural
    pass/fail (compliance-mappings, baseline-clause-grammar,
    regulation-alignment, mitre-taxonomy, monitoring-type,
    cim-spl-alignment, known-fp, peer/legal/sme signoff audits,
    regulatory-change-watch, mapping-ledger audit, catalog-schema)
    keeps its own dedicated step because failure messages carry
    per-domain context that's useful to surface separately. The
    `generate-api-surface --check` step in `audits-build` is
    intentionally excluded from the umbrella because it consumes
    the full post-build `dist/` tree. The post-build `audit-prerequisites --check`
    belt-and-braces step in `audits-build` (which catches a
    different drift surface — markdown edit without report
    regeneration after the build step) also stays untouched.

    **Files edited.**

    - `Makefile` — added `sync-generated` and
      `sync-generated-check` targets plus `.PHONY` registration.
    - `.github/workflows/validate.yml` — deleted 14 individual
      `--check` step blocks (including their long-form
      explanatory comments — the umbrella block-comment now
      carries the same context), inserted one `Cascade-generator
      drift gate (umbrella)` step right after `Catalog schema
      validation`, and rewrote the `audits-content` job
      docstring at the top of the section to point at the
      umbrella as the recovery surface.

    **Verification.** `make sync-generated-check` ran clean in
    31s against the current HEAD. `pytest tests/` (363 tests)
    passed in 73s. The `audits-content` job step count went
    from 53 → 40. The YAML parses cleanly under
    `yaml.safe_load`.

    **Why now.** Same lean-mode rationale as PR-1: the catalogue
    is one person's responsibility, and a 14-way CI failure
    fan-out when a content edit ripples through the generator
    chain produces a worse signal than a single umbrella step
    that lists every drift surface in one log. The generators
    themselves remain unchanged — only the CI presentation layer
    is collapsed. PR-3 (strip community docs + per-file coverage
    ratchet + references-footer regen) follows.

21. **Lean-mode PR-3: solo-maintainer doc rewrite + workflow-audit
    consolidation (2026-05-17).** PR-1 removed the team-coordination
    machinery in the build (stewardship rotation, per-category
    CODEOWNERS, scorecard drill-down structural pins). PR-2
    consolidated 14 CI drift gates into one umbrella. PR-3 finishes
    the lean-mode pass by rewriting three community-facing docs
    (`CONTRIBUTING.md`, `GOVERNANCE.md`, `docs/capacity-and-staffing.md`)
    around a solo-maintainer reality and folding the duplicate
    `docs/workflow-audit.md` page into `docs/ci-architecture.md`.

    **Doc rewrites (write-mode, structural tests preserved).**

    - `CONTRIBUTING.md` — collapsed from the multi-page contributor
      onboarding narrative (review SLAs, sign-off batches, inter-team
      handoff prose) into a single page covering UC conventions,
      required fields, the JSON template, local validation, the
      `make sync-generated-check` umbrella, CI overview, JSON-as-SSOT,
      versioning, and quality tiers. Best-effort review remains the
      explicit contract.
    - `GOVERNANCE.md` — collapsed to a one-page description of who
      decides what (`@fenre`), how release cadence depends on the
      `docs/capacity-and-staffing.md` calibration, the operational
      pair (`capacity-and-staffing.md` + `rollback-playbook.md`), and
      the project's non-goals (no foundation status, no sponsorships).
      Cross-link to `docs/capacity-and-staffing.md` is now present —
      the latent `test_governance_references_capacity_doc` invariant
      will pass when its v8.x skip is eventually lifted.
    - `docs/capacity-and-staffing.md` — pruned the long FAQ /
      scope-down narrative / external-reader sections into a TL;DR
      + three operating-mode subsections (full / reduced / solo).
      The 1–2 platform-engineer + 0.5 FTE curator + tier-1
      legal-review capacity baseline survives as a TL;DR sentence
      so `test_capacity_doc_declares_platform_engineer_count` (and
      every other structural pin in `tests/build/test_capacity_and_staffing.py`)
      still passes.

    **Workflow inventory consolidation.**

    The standalone `docs/workflow-audit.md` page (authored 2026-05-13
    under §P2.5) duplicated content that `docs/ci-architecture.md`
    already carried per-workflow, plus a third-party SHA-pin table
    that was a human-readable view of what `python3 -m splunk_uc
    audit-action-pins` already enforces. PR-3:

    - Added a new `## Workflow inventory` section near the top of
      `docs/ci-architecture.md` carrying the 13-row inventory table
      (post-PR-1: stewardship workflows are gone) + the cadence
      calendar + the Monday-cluster / Tuesday-backstop design
      rationale.
    - Deleted `docs/workflow-audit.md` (16,601 bytes).
    - Updated every inbound reference: the banner + See-also block
      in `docs/ci-architecture.md`, the companion notes in
      `docs/f8-frontend-hardening-inventory.md`, and the historical
      ledger entries in this file (kept the prose, redirected the
      broken `.md` links to the new section anchor).
    - The third-party SHA-pin map is **not** re-published as prose —
      `audit-action-pins` is the single source of truth.

    **What stays unchanged.** No correctness machinery is removed.
    The cascade-generator umbrella from PR-2 is untouched. The
    per-file coverage ratchet (`src/splunk_uc/audits/coverage_budget.py`)
    is preserved — re-reading its docstring, the original
    "contributors-friendly" framing is just packaging; the actual
    behavior (prevent test-coverage regressions on the build pipeline
    and audit CLIs) is correctness machinery a solo developer
    benefits from just as much. Every CI gate, every audit verb,
    and every schema check is exactly as it was before PR-3.

    **Files edited (write-mode).**

    - `CONTRIBUTING.md` — rewritten.
    - `GOVERNANCE.md` — rewritten.
    - `docs/capacity-and-staffing.md` — rewritten + TL;DR sentence
      injected so the structural regex still matches.
    - `docs/ci-architecture.md` — added `## Workflow inventory`
      section + cadence calendar; updated banner; removed See-also
      link to the deleted page.
    - `docs/f8-frontend-hardening-inventory.md` — removed the
      "sibling single-page inventory" companion line; updated the
      See-also list.
    - `docs/health-check-2026-progress.md` — converted broken
      `(workflow-audit.md)` links inside historical ledger entries
      to the new section anchor (prose narrative preserved); updated
      §P2.5 row to record the consolidation; added this entry.
    - `CHANGELOG.md` — added the "Changed — lean-mode PR-3" section
      under [Unreleased].

    **Files deleted.**

    - `docs/workflow-audit.md` — folded into
      `docs/ci-architecture.md#workflow-inventory`.

    **Files automatically regenerated.**

    - `docs/backlinks.md` — backlink index updated (213 pages, was
      214).
    - `docs/rollback-playbook.md` — auto-generated `Cited by` footer
      dropped `docs/capacity-and-staffing.md` (the leaner page no
      longer carries an inline `[N]` citation marker matching a
      source ID that rollback-playbook also cites). Legitimate
      consequence of leaner prose; the structural invariant
      `test_rollback_playbook_references_capacity_doc` (which checks
      the rollback playbook still *links to* the capacity doc) still
      passes — that test reads the prose body, not the auto-footer.
    - Evidence-pack `.md` files (18 rewritten by `generate-evidence-packs`
      because their citation footers re-rendered after the references
      library scan).

    **Verification.** `make sync-generated-check` runs clean
    (~29s end-to-end). `PYTHONPATH=src python3 -m pytest tests/build/
    tests/scripts/ -q` runs 635 tests in 116s with 4 pre-existing
    v8.x skips. The 4 skips are unchanged by this PR and predate
    the lean-mode sweep. `mapping-ledger.json` had to be reverted
    (same metadata-only drift pattern as PR-2: only `generatedAt`
    + `catalogueCommit` change while the merkle root stays stable
    at `ccb056b770…`) — keeping the committed ledger metadata
    stable across PRs that don't change UC content.

    **Why now.** Same lean-mode rationale as PR-1 and PR-2: the
    catalogue is one person's responsibility, and three of the
    repo's most-read top-level docs were carrying multi-contributor
    governance prose that misled readers about the actual operating
    model. The rewrites bring the docs in line with the code.

22. **PR-4: content-quality lift loop + cat-15 proof-of-concept
    (2026-05-17).** The lean-mode arc was about removing
    team-coordination scaffolding; PR-4 is the first piece of new
    machinery on top of that lean base. It adds four pure-function
    CLI verbs that turn the existing `gold_profile` scoring rubric
    into a **scoreboard-driven, firewalled lift loop**: an
    orchestrator can identify low-scoring UCs, generate
    rubric-aware prompts, validate AI-authored diffs against a
    fixed contract, and produce per-UC commits — all without ever
    letting the AI touch the catalogue's SPL, identity, or other
    correctness-critical fields.

    **New verbs (registered under the `lift` category in the
    `splunk_uc` dispatcher).**

    - `lift-score` — runs `gold_profile` over one or more UC
      sidecars and emits a JSON gap report. Pure function, no
      network or subprocess calls.
    - `lift-prompt` — assembles a deterministic prompt for one UC
      containing the rubric, the current sidecar (firewalled
      fields elided), the gap report, the lift-surface allow-list,
      and the exact diff shape the author must produce.
    - `lift-validate` — applies an AI-authored diff to one UC's
      sidecar and runs the §5 contract: firewall (no `spl`,
      `id`, `title`, etc.), allow-list (only the 14 lift-surface
      fields), `jsonschema` per-field validation against
      `schemas/uc.schema.json`, identity preservation, and a
      strictly-greater post-lift score. Writes the lifted sidecar
      byte-faithfully (`ensure_ascii=False`) and regenerates the
      markdown twin via `generate-md-from-json --files`. `--strict`
      additionally re-runs the catalog-wide audits in a subprocess
      against the lifted state; on any failure the sidecar reverts
      from a cached `original_bytes` buffer.
    - `lift-batch` — scans a category for low-scoring UCs and
      emits a JSON manifest (`ucs[]`: `uc_id`, `sidecar_path`,
      `current_score`, `failing_fields`) for the orchestrator to
      iterate. Supports worst-first (default) and
      `--random --seed` for deterministic shuffling.

    All four verbs ship with full TDD red→green test coverage
    under `tests/splunk_uc/lift/`. The `splunk_uc/__main__.py`
    dispatcher smoke pin (`tests/splunk_uc/test_dispatcher.py`)
    asserts the new verbs show up under `--help` and resolve.

    **Cat-15 proof-of-concept.** Generated a 30-UC worst-first
    manifest with `lift-batch cat-15 --limit 30
    --report reports/lift-batch-cat-15-poc.json`, dispatched 30
    `generalPurpose` subagents in batches of 4 (each one read a
    pre-generated `/tmp/lift-UC-X.Y.Z.prompt.txt`, authored a
    `/tmp/lift-UC-X.Y.Z.diff.json`, and returned the path only),
    validated every diff with `lift-validate`, and produced 30
    separate `docs(uc): lift UC-X.Y.Z to silver` commits — one per
    UC, byte-faithful diffs, no manual edits.

    **PoC results.**

    - 30 / 30 lifts validated without revert. The score-strictly-
      increases gate was respected by every diff; the firewall
      never fired (no rejected diffs).
    - Score deltas: smallest +5, largest +22, median +10. Total
      raw gold-profile score added: **+307 points** across 30 UCs
      in cat-15.
    - Average depth score on cat-15 moved from the previous
      anchor of ~24 to **27.4** (post-lift `audit-gold-profile
      --summary` snapshot, 117 UCs in cat-15). The 30 lifted UCs
      all crossed the 20–25 "structural-only" floor into the
      30–40 "rubric-satisfied bronze" band.
    - `make audit` clean (zero new findings vs. baseline). `make
      build` clean (7,929 UCs / 23 categories / 82 regulations in
      49.83 s, full reproducible artefacts emitted).

    **What the loop enforces (the §5 contract).**

    Firewalled fields (can never appear in a diff): `id`, `title`,
    `spl`, `cimSpl`, `monitoringType`, `splunkPillar`,
    `criticality`, `difficulty`, `compliance`, `fixtureRef`,
    `assurance`, `grandmaExplanation`, `prerequisiteUseCases`,
    `wave`. Lift-surface fields (the only ones the AI may touch):
    `description`, `value`, `dataSources`, `detailedImplementation`,
    `knownFalsePositives`, `references`, `controlTest`, `evidence`,
    `exclusions`, `visualization`, `equipmentModels`, `mitreAttack`,
    `implementation`, `dataModelAcceleration`. Any diff that
    touches a field outside the allow-list is rejected; any diff
    that does not strictly raise the gold-profile score is
    rejected; any diff that fails per-field schema validation
    against `schemas/uc.schema.json` is rejected. Identity
    (`id`, `title`) must be unchanged.

    **Why now.** The lean-mode PRs removed the team-coordination
    machinery that had been masking content-quality drift; PR-4
    gives the solo maintainer a high-leverage way to clear that
    drift without re-introducing the team-coordination overhead.
    Each lift produces an independently-reviewable commit that can
    be reverted in isolation; the firewall makes it safe to invoke
    the loop unattended in a future scheduled-CI job.

    **Files added (write-mode).**

    - `src/splunk_uc/tools/lift/_common.py` — shared helpers
      (`GapReport`, `TargetTier` enum, `LIFT_SURFACE_FIELDS`,
      `FIREWALLED_FIELDS`, sidecar discovery + canonical dump).
    - `src/splunk_uc/tools/lift/score.py` — `lift-score` verb.
    - `src/splunk_uc/tools/lift/prompt.py` — `lift-prompt` verb.
    - `src/splunk_uc/tools/lift/validate.py` — `lift-validate` verb.
    - `src/splunk_uc/tools/lift/batch.py` — `lift-batch` verb.
    - `tests/splunk_uc/lift/test_score.py`, `test_prompt.py`,
      `test_validate.py`, `test_batch.py` — TDD coverage.
    - `tests/splunk_uc/lift/fixtures/UC-15-bronze-baseline.json` +
      `UC-15-silver-target.json` — `lift-validate` test fixtures.
    - `reports/lift-batch-cat-15-poc.json` — the 30-UC PoC manifest.
    - `docs/superpowers/specs/2026-05-17-content-quality-lift-loop-design.md`
      and `docs/superpowers/plans/2026-05-17-content-quality-lift-loop.md`
      — the design spec and execution plan that this PR implements.

    **Files modified (write-mode).**

    - `src/splunk_uc/_registry.py` — registered the four `lift-*`
      verbs.
    - `AGENTS.md` — added the four `lift-*` commands to the
      Quick Commands section and a new "Content-quality lift
      loop" section describing the verbs + orchestration pattern;
      Further Reading cross-links the spec and plan documents.
    - 30 × `content/cat-15-data-center-physical-infrastructure/
      UC-15.{1,2,3}.*.json` + their `.md` companions — the cat-15
      PoC lift commits (one commit per UC).
    - `CHANGELOG.md` + this file — entry under [Unreleased].

    **Verification.** `PYTHONPATH=src python3 -m pytest
    tests/splunk_uc/lift/ tests/splunk_uc/test_dispatcher.py -q`
    (full coverage of the four new verbs + dispatcher smoke).
    `make audit` (zero new findings). `make build` (49.83 s,
    7,929 UCs). 30 / 30 cat-15 PoC commits validated end-to-end
    with byte-faithful diffs and clean markdown regeneration.

23. **PR-4 follow-up: lift-validate MITRE + canonical-order
    hardening (2026-05-18).** Two correctness gaps observed during
    the cat-15 PoC (drift ledger #22) deferred at the time so the 30
    lift commits could land in a clean sequence; now collapsed into
    a surgical follow-up to `lift-validate` so the next category
    rollout has a strictly tighter contract.

    1. **MITRE ATT&CK tactic-ID rejection.** The schema regex in
       [`schemas/uc.schema.json`](../schemas/uc.schema.json) permits
       `TA<digits>` (tactic IDs) as well as `T<digits>` (technique
       IDs), but the downstream ATT&CK simulation gate
       [`scripts/simulate_controltest.py`](../scripts/simulate_controltest.py)
       only accepts technique IDs. A subagent emitted `TA0006` for
       UC-15.3.1 during the PoC; `lift-validate` accepted it under
       the existing schema check, and the failure only surfaced at
       the post-push `attack-simulation.json` gate forcing fixup
       commit `56766cfba`. New `_check_lifted_mitre_techniques`
       helper applies the simulator's
       `^(T\d{4}(\.\d{3})?|N/A \(.+\))$` regex at validate time.

    2. **Canonical sidecar key ordering at write time.** Previously
       `_dump_sidecar` preserved whatever insertion order the diff
       happened to produce, so newly-added lift-surface fields (e.g.
       `dataModelAcceleration`) landed at the end of the sidecar.
       Then the next `make sync-generated` cascade reordered them
       into canonical position, generating a churn commit (`aedee6ff8`
       was one such re-stamp) that did nothing semantically useful.
       New module
       [`src/splunk_uc/_uc_sidecar.py`](../src/splunk_uc/_uc_sidecar.py)
       exposes `SIDECAR_FIELD_ORDER` + a `canonical_sidecar()`
       reorderer. `lift-validate` applies it before writing so the
       post-lift sidecar is byte-comparable to what the cascade would
       produce. Verified **byte-identical against all 7,929 sidecars
       in the catalogue** (zero churn on existing content, no
       follow-up reorder commit needed after future lifts).

    **Files added (write-mode).**

    - [`src/splunk_uc/_uc_sidecar.py`](../src/splunk_uc/_uc_sidecar.py)
      — shared canonical sidecar field order tuple + reorder helper.
      Mirrors the longest published version of the constant (the
      four generators `equipment_tags`, `phase3_2_cross_cutting`,
      `phase3_3_derivatives`, `grandma_explanations` already
      converge on it; the historical outlier in `phase3_1_backfill`
      is a latent bug tracked separately).

    **Files modified (write-mode).**

    - [`src/splunk_uc/tools/lift/validate.py`](../src/splunk_uc/tools/lift/validate.py)
      — new `_MITRE_ATTACK_ID_RE`, new `_check_lifted_mitre_techniques`
      helper wired into the main validation chain right after
      per-field schema validation, `_dump_sidecar` now feeds the
      lifted sidecar through `canonical_sidecar()` before
      serialisation.
    - [`tests/splunk_uc/lift/test_validate.py`](../tests/splunk_uc/lift/test_validate.py)
      — four new cases:
      `test_validate_rejects_mitre_tactic_id_in_lift`,
      `test_validate_accepts_valid_mitre_technique_ids`,
      `test_validate_rejects_garbage_mitre_id`,
      `test_validate_writes_sidecar_in_canonical_key_order`,
      `test_validate_canonical_order_appends_unknown_keys_at_end`.

    **Verification.**

    - `tests/splunk_uc/lift/` — 48/48 green (was 44/44, +4 cases).
    - `tests/splunk_uc/` — 121/121 green (was 117/117).
    - `tests/build/ tests/scripts/` — 635/635 green (4 pre-existing
      v8.x skips, unchanged).
    - `python3 -m mypy --strict src/splunk_uc/` — clean at 105
      source files (was 104; the new `_uc_sidecar` is type-clean).
    - `python3 -m ruff check` — clean on the three touched files.
    - `make sync-generated-check` — clean in ~30s. Merkle root
      `ccb056b7704b87a2…` stable (same as PR-3 / PR-4 close).
    - Smoke-tested `canonical_sidecar()` against every sidecar in
      `content/cat-*/UC-*.json` — 7,929 / 7,929 byte-identical to
      what the helper produces. Zero churn risk on the existing
      corpus; the helper only changes behaviour for fresh
      `lift-validate` invocations on UCs that introduce new
      lift-surface fields.

    **Future cleanup tracked, NOT addressed here.** Five generators
    duplicate `SIDECAR_FIELD_ORDER` in their own modules
    (`equipment_tags`, `grandma_explanations`, `phase3_1_backfill`,
    `phase3_2_cross_cutting`, `phase3_3_derivatives`). One of them
    (`phase3_1_backfill`) carries a slightly stale version that
    omits the `industry` key. Folding them onto the new shared
    `splunk_uc._uc_sidecar.SIDECAR_FIELD_ORDER` would remove a real
    duplication smell, but it's deliberately out of scope: the
    hardening lands `lift-validate` first; the generator
    consolidation follows whenever any of those generators is
    otherwise touched. Until then, the on-disk catalogue's
    convergence on the canonical order (verified by the
    byte-identical 7,929-UC sweep above) is sufficient empirical
    evidence that the generators agree at runtime.

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
   **Done 2026-05-13, consolidated 2026-05-17 (PR-3, ledger #21)** —
   the original standalone `docs/workflow-audit.md` shipped on
   2026-05-13 with a 14-row inventory, weekly-cadence calendar,
   third-party SHA-pin map, and a "How to keep this doc honest"
   maintainer guide. PR-3 folded the live portion of that page into
   [`docs/ci-architecture.md` § Workflow inventory](ci-architecture.md#workflow-inventory)
   (13 rows after PR-1's stewardship retirement) and retired the
   duplicate page; the pin map now lives entirely in
   `python3 -m splunk_uc audit-action-pins` instead of being
   restated in prose. The companion `docs/ci-architecture.md` has
   been extended with the two
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
    - ~~`~3,000 line PR (mostly mechanical)` — **Invert source-of-truth**
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
      already done in this PR). Closes the *bundler* half of F16.~~
      **Done 2026-05-17** — see drift ledger #17. Data moved into
      [`apps/web/src/data/non-technical-view.data.ts`](../apps/web/src/data/non-technical-view.data.ts)
      (typed `NON_TECHNICAL: NonTechnicalCatalog`, byte-identical to
      the pre-inversion JS body). Emitter at
      [`apps/web/scripts/emit-legacy.ts`](../apps/web/scripts/emit-legacy.ts)
      (`npm run emit:legacy`) round-trips byte-identical on the
      first run; the legacy JS file shrinks by zero bytes (was
      always the contract). CI drift guard wired into
      `validate.yml` `frontend` job; three new SOT invariant tests
      land in `apps/web/src/__tests__/emit-legacy.test.ts` (test
      total 82 → 85). F16 *bundler* half is now closed; F17 (root
      HTML chrome unification) is the next P5 bite per ADR-0013.
    - ~~`~250 line PR` — Wire the **automated rotation reminders**
      that consume the per-category CODEOWNERS rows + the new
      scorecard drill-downs landed on `origin/main` 2026-05-14
      (the second-half closure for P14).~~ **Done 2026-05-17** —
      see drift ledger #18. New stdlib-only verb
      [`pick-rotation-category`](../src/splunk_uc/tools/pick_rotation_category.py)
      computes `(iso_week % 23) + 1`, reads CODEOWNERS owners + the
      live `dist/scorecard.json` entry, and renders both a JSON
      record and a Markdown issue body. The new weekly workflow
      [`stewardship-rotation.yml`](../.github/workflows/stewardship-rotation.yml)
      (Mon 08:30 UTC) wires it into `gh issue` with idempotent
      per-week labels. 14-test suite covers determinism, cycle
      coverage, CODEOWNERS parsing, scorecard lookup, and the CLI
      entry-point. Runbook at
      [`docs/stewardship-rotation.md`](stewardship-rotation.md).
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
(0 open at HEAD); the 14-row workflow inventory generated from a
direct sweep of `.github/workflows/*.yml` (originally shipped as
`docs/workflow-audit.md`; consolidated into
[`docs/ci-architecture.md` § Workflow inventory](ci-architecture.md#workflow-inventory)
by PR-3 / ledger #21 on 2026-05-17);
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

<a id="ref-6"></a>**[6]** National Institute of Standards and Technology. (2020). *Security and Privacy Controls for Information Systems and Organizations* (Revision 5). U.S. Department of Commerce. NIST SP 800-53 Rev. 5. https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final

<a id="ref-7"></a>**[7]** North American Electric Reliability Corporation. (2024). *NERC Critical Infrastructure Protection (CIP) Reliability Standards*. NERC. https://www.nerc.com/pa/Stand/Pages/CIPStandards.aspx

<a id="ref-8"></a>**[8]** Standing Committee of the National People's Congress (China). (2021). *Personal Information Protection Law of the People's Republic of China*. National People's Congress. http://en.npc.gov.cn.cdurl.cn/2021-12/29/c_694559.htm

### Related repository documents

- [`docs/adr/0010-sample-and-sample-data-co-exist.md`](adr/0010-sample-and-sample-data-co-exist.md)
- [`docs/adr/0011-schema-lineage-governance.md`](adr/0011-schema-lineage-governance.md)
- [`docs/adr/0012-sample-data-canonical-shape.md`](adr/0012-sample-data-canonical-shape.md)
- [`docs/adr/0013-frontend-rebuild-scaffold.md`](adr/0013-frontend-rebuild-scaffold.md)
- [`docs/ci-architecture.md`](ci-architecture.md)
- [`docs/f8-frontend-hardening-inventory.md`](f8-frontend-hardening-inventory.md)

### Cited by

- [`ROADMAP.md`](../ROADMAP.md)
- [`docs/f8-frontend-hardening-inventory.md`](f8-frontend-hardening-inventory.md)

<!-- END-AUTOGENERATED-SOURCES -->
