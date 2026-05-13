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

All six §9 ("Where to start") plan PRs have now landed. The next
recommended sequence in the plan moves into §P5 (frontend rebuild,
F8/F16/F17) and §P2.5 (per-workflow audit document under
`docs/workflow-audit.md`), neither of which is started yet.

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
| F8 | H | `index.html` 621 KB / 162 KB gzipped, 33 `innerHTML`, `'unsafe-inline'` CSP | **NOT DONE — got slightly worse** | Now **645,766 bytes raw / 173,030 bytes gzipped** (+11 KB gzipped vs. plan baseline). Still **33 `innerHTML` sinks**, still **1 `unsafe-inline`** in CSP. |
| F9 | H | No CodeQL / dependency-review / SBOM | DONE (mostly) | `.github/workflows/codeql.yml` + `dependency-review.yml` + `gitleaks.yml` all present as separate workflows. SBOM via `anchore/sbom-action` in `release.yml` — verify in P2.5 audit. |
| F10 | H | `secrets.env` not in `.cursorignore` | **DONE** (2026-05-12) | `.cursorignore` now carries an explicit "Secrets and local environment overrides" block listing `secrets.env`, `secrets.env.local`, `.env`, `.env.local`, `.env.*.local`. `.gitignore` lines 88-90 already block them from commits; the new entries also hide them from the Cursor agent's index so a stray `Read` cannot surface credentials. |
| F11 | M | `scripts/` 105 files, no taxonomy, archived trees | DONE | 76 deliberate Python files remain in `scripts/`, mapped to taxonomy in `docs/scripts-taxonomy.md`. Archived trees (`scripts/_archived/`, `scripts/archive/`) deleted. Closed in v8.2.0 (P6 closure). |
| F12 | M | `validate.yml` 953 lines, single-job, 18 `--check` guards, slow | **DONE** (2026-05-12) | commit `62c95b5e0` (PR-5) split the monolithic job into **5 parallel jobs**: `lint` (line 115), `audits-content` (line 233), `audits-build` (line 866), `mcp` (line 1097), `frontend` (line 1187). File grew to 1,366 lines because each job carries its own setup/install block, but wall-clock time dropped — the longest critical path is now `audits-content` (~7m32s on PR #8) instead of the prior ~20m sequential run. Structural test `tests/build/test_validate_workflow_partition.py` keeps the partition wired. |
| F13 | M | `dist-before/` 6,449-entry stale snapshot | PARTIAL | `dist-before/` gone ✓. But `dist-content/` and `dist-legacy/` still present on disk (gitignored, but ~200 MB of dev clutter). |
| F14 | M | `api/v1/_evidence-packs-bak/`, `_draft_uc_*`, `_fix_*` clutter | PARTIAL | `api/v1/_evidence-packs-bak/` gone ✓. But `scripts/_draft_uc_18_1_15.py`, `scripts/_fix_broken_fixture_refs.py`, `scripts/_meraki_*.py`, etc. retained — explicitly listed as deliberate "one-shots" in v8.2.0 CHANGELOG narrative. |
| F15 | M | No repo-wide `pyproject.toml` for build pipeline | DONE | `pyproject.toml` with `[project]`, `[project.scripts]`, `[tool.ruff]`, `[tool.mypy]`, `[tool.coverage]`, `[tool.pytest]` configs. `splunk-uc` console script wired (v8.2.0 P6 Tier 4). |
| F16 | M | Frontend committed HTML rewritten by Python; no test runner | **NOT DONE** | `index.html` still 645 KB committed-and-rewritten. No `apps/web/` directory. No Vite / TS bundler. Frontend rebuild (P5) not started. |
| F17 | L | 11 root HTML pages duplicate chrome | PARTIAL | **9 root HTML files now** (was 11): `api-docs.html`, `clause-navigator.html`, `compliance-story.html`, `docs.html`, `graph.html`, `guide-reader.html`, `index.html`, `regulatory-primer.html`, `scorecard.html`. Chrome still duplicated across all 9. |
| F18 | L | Root `openapi.yaml` legacy vs. `api/v1/openapi.yaml` canonical | **DONE** (2026-05-12) | Re-verified at HEAD: `openapi.yaml` line 16 carries `> **Status: legacy (hand-maintained)**` followed by a four-paragraph block pointing readers to the canonical `/api/v1/openapi.yaml`, documenting the eventual move to `archive/openapi-legacy.yaml`, and explaining how the OpenAPI drift audit (`audit-openapi-drift`) keeps the two specs in sync. Both specs continue to coexist (root 565 lines / api/v1 210 lines), which is the documented contract — there is no in-progress deletion to wait on. |
| F19 | M | 7 other workflows unaudited | **DONE** (2026-05-12) | Closed by PR #8 (commit `85b680f5d`): every workflow under `.github/workflows/*.yml` now consumes `./.github/actions/setup-python`. The previously skipped guard `tests/build/test_composite_actions.py::test_no_workflow_pins_setup_python_directly` is unskipped and runs in the `audits-content` job, so any future direct `actions/setup-python@<sha>` pin in a workflow fails CI. The 14-workflow inventory itself moves into P2.5 below — that is the remaining work, not F19. |
| F20 | M | Thin test coverage (10 Python + 5 mjs) | DONE on count, **NOT** on % | **47 test files / 660 collected tests** in `tests/` + `mcp/tests/`. The "<10 tests" plan baseline is far surpassed. P16 coverage % targets not yet baselined; `data/baselines/coverage-v7.4.2.json` does not exist (per F20 in plan §11). |
| F21 | L | 7,657 markdown companions tracked alongside JSON | **NOT DONE** | **7,677 `.md` + 7,677 `.json` matched pairs** under `content/cat-*/UC-*.{md,json}`. Markdown corpus still committed. `--check` gate for parity is now blocking (F7 closed 2026-05-12) but the markdown files themselves are still committed — F21 is about removing them from git, not the gate. |
| F22 | L | Two parallel sample regimes (95 dirs + 97 files) | **DONE** (2026-05-13) | **94 `samples/UC-*/` directories + 97 `sample-data/uc-*-fixture.json` files.** The §P12 "pick one" framing was wrong on close inspection: the two regimes serve different purposes (raw-event SPL validation vs. compliance-control evidence fixtures) and merging them creates a worse failure mode in both directions. [ADR-0010](adr/0010-sample-and-sample-data-co-exist.md) (2026-05-13) ratifies the split, mechanically forbids cross-tree references, cross-links both READMEs to the ADR, and defers the schema-shape rationalisation inside `sample-data/` (three observed shapes today — `positive`/`negative`, `events_positive`/`events_negative`, and `positiveCase`/`negativeCase`) to follow-on ADR-0011. |
| F23 | L | 12+ schemas, no governance plan | PARTIAL | **18 schemas** under `schemas/` (up from "12+"): the 9 in plan, plus `coverage-baseline`, `baselines`, `license-inventory`, and the `v2/` tree (`catalog-index`, `metrics-history-index`, `stewardship-digest`, `search-index`, `build-telemetry`, `metrics`). Schema lineage ADR not yet authored. |

## Phases (P0–P19)

| Phase | Status | Notes |
|---|---|---|
| **P0** Hygiene + secrets hardening | PARTIAL | `.cursorignore` ✓ (with explicit secrets / dotenv block — F10 closed 2026-05-12), pre-commit ✓ (`.pre-commit-config.yaml`), archived script dirs gone ✓. **Remaining gap:** `data/baselines/v7.4.x.json` baselines file not visible — verify or back-author. |
| **P1** One build pipeline | DONE | Legacy `build.py` deleted (v8.0.0); `use-cases/` retired (v8.2.0); F1/F2/F3 all resolved. Vestigial `reset_legacy_module_cache()` stub at `tools/build/parse_content.py:1058` is minor dead code. |
| **P2** CI overhaul | DONE (mostly) | CodeQL ✓ + dependency-review ✓ + gitleaks ✓ as separate workflows. F7 closed (2026-05-12): zero `continue-on-error: true`. F12 closed (2026-05-12): `validate.yml` now 5 parallel jobs (PR-5). F19 closed (2026-05-12): every workflow uses the composite `setup-python` action (PR #8). **Remaining gap:** no `data/baselines/` wall-clock baseline file checked in to track future regressions. |
| **P2.5** Audit other 7 workflows | **DONE** (2026-05-13) | Composite-action migration done (F19, 2026-05-12) — every workflow uses the centralized `./.github/actions/setup-python` and the `audit-action-pins` audit blocks unpinned `actions/*@<sha>` references on PRs. P2.5 closure (2026-05-13): authored [`docs/workflow-audit.md`](workflow-audit.md), a single-page inventory of all **14** workflows with purpose / trigger / cadence / runs-on / timeout / writes-to-repo / pinned-third-party-actions columns, a Monday-cluster + Tuesday-backstop cadence calendar, and a per-action SHA-pin map for the 14 distinct third-party references (`actions/*`, `github/codeql-action/*`, `gitleaks/*`, `peter-evans/*`, `softprops/*`). [`docs/ci-architecture.md`](ci-architecture.md) cross-links the new audit doc from both its banner and its `## See also` block, and its TL;DR table was extended with the two previously-missing rows (`stewardship.yml`, `build-reproducibility.yml`). |
| **P3** ADR + docs reconciliation | DONE (mostly) | ADR-0001 `Superseded by: ADR-0007` ✓; AGENTS.md says 11 tools ✓; `docs/architecture-2027.md` not created (was "proposed" in plan). |
| **P4** Typed Python pipeline | PARTIAL | `pyproject.toml` ✓; ruff + mypy + coverage configs ✓; `[project.scripts]` ✓ (P6 Tier 4); per-module mypy strictness gradient in place. **Gaps:** `mypy --strict` not yet enabled globally; no typed `UseCase` / `Catalog` Pydantic/dataclass model in `src/splunk_uc/`. |
| **P5** Frontend rebuild | NOT STARTED | No `apps/web/`. F8/F16/F17 all unresolved. |
| **P6** Scripts taxonomy | DONE | Just closed in v8.2.0 (commit `a36aa4db4`). 83-verb dispatcher + Tier 4 packaging. |
| **P7** Server-side search + API gateway | NOT STARTED | — |
| **P8** Observability + content metrics | PARTIAL | `dist/metrics.json` per AGENTS.md ✓, `data/metrics-history/<VERSION>.json` snapshot pattern ✓ (just added `8.2.0.json`). Slack/email weekly digest unclear (`stewardship.yml` exists). Build telemetry exists (`dist/build-telemetry.json`). |
| **P9** Monorepo split (apps/ + packages/) | NOT STARTED | — |
| **P10** Performance + a11y hardening | NOT STARTED | F8 (index.html size, CSP, innerHTML) is the prerequisite; no Lighthouse CI yet. |
| **P11** OSS release polish | NOT STARTED | No `.devcontainer/`; no public roadmap board sync from `ROADMAP.md` (and `ROADMAP.md` itself still says v7.1 as the "Current release"). |
| **P12** Splunk content quality moonshot | NOT STARTED | F22 (two sample regimes) unresolved; no per-UC `thresholds` field in schema; no SPL formatter; no AppInspect<sup class="ref">[<a href="#ref-2">2</a>]</sup> gate. |
| **P13** Recommender TA hardening | NOT STARTED | The recommender TA was overhauled in v8.0.0 (CHANGELOG mentions "single Cloud-safe recommender app") but P13's threat model + Sigstore on `.spl` + AppInspect Cloud gate not visible. |
| **P14** Content stewardship | NOT STARTED | No per-category CODEOWNERS routing; no per-category scorecards. |
| **P15** Specification compliance moonshot | NOT STARTED | 2027 target per plan; no `clauseText[]` bindings. |
| **P16** Test coverage burndown | NOT STARTED | 660 tests collected ✓, but no `data/baselines/coverage-v8.2.0.json` floor file; no mutation testing; no property-based testing. |
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
3. **`dist-content/`, `dist-legacy/`** still on local disk
   (gitignored, but disk clutter). `make clean-tree` target from P0
   doesn't yet exist.
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
   Plus delete `dist-content/` / `dist-legacy/` local directories
   (`rm -rf` only; both are already in `.gitignore`).
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
4. **Phase 4 first canary (~150 lines):** Enable `mypy --strict` on
   `src/splunk_uc/audits/` only (already typed-ish after the v8.2.0
   migration); ratchet outward in subsequent PRs.
5. ~~**Lay P12 groundwork (~no code, 1 PR):** Pick one of the two
   sample regimes (F22). The plan §P12 first deliverable says the
   choice itself is the deliverable.~~ **Done 2026-05-13** —
   [ADR-0010](adr/0010-sample-and-sample-data-co-exist.md) ratifies
   the split (both regimes co-exist with formally distinct purposes
   and mechanically forbidden cross-tree references). The
   schema-shape rationalisation inside `sample-data/` is deferred
   to follow-on ADR-0011 (Q3-2026 target).
6. ~~**P2.5 (~no code, 1 PR):** Author `docs/workflow-audit.md`.~~
   **Done 2026-05-13** — `docs/workflow-audit.md` checked in with a
   14-row inventory, weekly-cadence calendar, third-party SHA-pin map
   covering all 14 distinct external action references, and a
   "How to keep this doc honest" maintainer guide. The companion
   `docs/ci-architecture.md` has been extended with the two
   previously-missing rows (`stewardship.yml`,
   `build-reproducibility.yml`) and cross-links the new audit doc.
7. **`docs/health-check-2026-progress.md`** (this file) refreshed every
   minor version to keep "what's done" honest.

## Method note

Status here is derived from: actual file contents at HEAD (post
2026-05-12 + 2026-05-13 closures, latest main carries PR #17 squash-merge);
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

### Cited by

- [`ROADMAP.md`](../ROADMAP.md)

<!-- END-AUTOGENERATED-SOURCES -->
