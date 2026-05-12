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
| PR-5 (P2 split `validate.yml` into 6–8 jobs) | **NOT DONE** | — |
| PR-6 (P1 step 3 — delete legacy `build.py`) | DONE | v8.0.0 |

The biggest remaining gap from the plan's recommended sequence is
**PR-5: split `validate.yml`** (still a single 1,073-line sequential job).
The infrastructure to do it cleanly is already in place (`splunk_uc`
dispatcher, pyproject.toml, pre-commit, CodeQL / dependency-review /
gitleaks as separate workflows).

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
| F10 | H | `secrets.env` not in `.cursorignore` | **NOT DONE** | `.cursorignore` covers generated artefacts (`catalog.json`, `data.js`, `dist/`, etc.) but does NOT list `secrets.env`, `secrets.env.local`, `.env`, `.env.local`. |
| F11 | M | `scripts/` 105 files, no taxonomy, archived trees | DONE | 76 deliberate Python files remain in `scripts/`, mapped to taxonomy in `docs/scripts-taxonomy.md`. Archived trees (`scripts/_archived/`, `scripts/archive/`) deleted. Closed in v8.2.0 (P6 closure). |
| F12 | M | `validate.yml` 953 lines, single-job, 18 `--check` guards, slow | **NOT DONE — slightly worse** | Now **1,073 lines** (+120). Single job `validate:` at line 84. No parallelization. |
| F13 | M | `dist-before/` 6,449-entry stale snapshot | PARTIAL | `dist-before/` gone ✓. But `dist-content/` and `dist-legacy/` still present on disk (gitignored, but ~200 MB of dev clutter). |
| F14 | M | `api/v1/_evidence-packs-bak/`, `_draft_uc_*`, `_fix_*` clutter | PARTIAL | `api/v1/_evidence-packs-bak/` gone ✓. But `scripts/_draft_uc_18_1_15.py`, `scripts/_fix_broken_fixture_refs.py`, `scripts/_meraki_*.py`, etc. retained — explicitly listed as deliberate "one-shots" in v8.2.0 CHANGELOG narrative. |
| F15 | M | No repo-wide `pyproject.toml` for build pipeline | DONE | `pyproject.toml` with `[project]`, `[project.scripts]`, `[tool.ruff]`, `[tool.mypy]`, `[tool.coverage]`, `[tool.pytest]` configs. `splunk-uc` console script wired (v8.2.0 P6 Tier 4). |
| F16 | M | Frontend committed HTML rewritten by Python; no test runner | **NOT DONE** | `index.html` still 645 KB committed-and-rewritten. No `apps/web/` directory. No Vite / TS bundler. Frontend rebuild (P5) not started. |
| F17 | L | 11 root HTML pages duplicate chrome | PARTIAL | **9 root HTML files now** (was 11): `api-docs.html`, `clause-navigator.html`, `compliance-story.html`, `docs.html`, `graph.html`, `guide-reader.html`, `index.html`, `regulatory-primer.html`, `scorecard.html`. Chrome still duplicated across all 9. |
| F18 | L | Root `openapi.yaml` legacy vs. `api/v1/openapi.yaml` canonical | **NOT DONE** | Both still exist: `./openapi.yaml` 20,371 bytes, `./api/v1/openapi.yaml` 7,602 bytes. Root not yet marked `**LEGACY**` at top or scheduled for v8 deletion. |
| F19 | M | 7 other workflows unaudited | PARTIAL | 14 workflows now total (added: `codeql`, `dependency-review`, `gitleaks`, `splunkbase-sync`, `stewardship` since plan). No formal per-workflow audit doc (`docs/workflow-audit.md` does not exist). |
| F20 | M | Thin test coverage (10 Python + 5 mjs) | DONE on count, **NOT** on % | **47 test files / 660 collected tests** in `tests/` + `mcp/tests/`. The "<10 tests" plan baseline is far surpassed. P16 coverage % targets not yet baselined; `data/baselines/coverage-v7.4.2.json` does not exist (per F20 in plan §11). |
| F21 | L | 7,657 markdown companions tracked alongside JSON | **NOT DONE** | **7,677 `.md` + 7,677 `.json` matched pairs** under `content/cat-*/UC-*.{md,json}`. Markdown corpus still committed. `--check` gate for parity is now blocking (F7 closed 2026-05-12) but the markdown files themselves are still committed — F21 is about removing them from git, not the gate. |
| F22 | L | Two parallel sample regimes (95 dirs + 97 files) | **NOT DONE** | **94 `samples/UC-*/` directories + 97 `sample-data/uc-*-fixture.json` files** (numbers shifted slightly). P12's "pick one" first deliverable not yet done. |
| F23 | L | 12+ schemas, no governance plan | PARTIAL | **18 schemas** under `schemas/` (up from "12+"): the 9 in plan, plus `coverage-baseline`, `baselines`, `license-inventory`, and the `v2/` tree (`catalog-index`, `metrics-history-index`, `stewardship-digest`, `search-index`, `build-telemetry`, `metrics`). Schema lineage ADR not yet authored. |

## Phases (P0–P19)

| Phase | Status | Notes |
|---|---|---|
| **P0** Hygiene + secrets hardening | PARTIAL | `.cursorignore` ✓, pre-commit ✓ (`.pre-commit-config.yaml`), archived script dirs gone ✓. **Gaps:** F10 (no `secrets.env` in `.cursorignore`), `data/baselines/v7.4.x.json` baselines file not visible — verify or back-author. |
| **P1** One build pipeline | DONE | Legacy `build.py` deleted (v8.0.0); `use-cases/` retired (v8.2.0); F1/F2/F3 all resolved. Vestigial `reset_legacy_module_cache()` stub at `tools/build/parse_content.py:1058` is minor dead code. |
| **P2** CI overhaul | PARTIAL | CodeQL ✓ + dependency-review ✓ + gitleaks ✓ as separate workflows. F7 closed (2026-05-12): zero `continue-on-error: true` directives left across `.github/workflows/`. **Gaps:** `validate.yml` not split into 6–8 parallel jobs (F12); no `data/baselines/` wall-clock baseline visible. |
| **P2.5** Audit other 7 workflows | NOT DONE | No `docs/workflow-audit.md`; 14 workflows total now; SHA-pinning status of third-party actions not verified per-workflow. |
| **P3** ADR + docs reconciliation | DONE (mostly) | ADR-0001 `Superseded by: ADR-0007` ✓; AGENTS.md says 11 tools ✓; `docs/architecture-2027.md` not created (was "proposed" in plan). |
| **P4** Typed Python pipeline | PARTIAL | `pyproject.toml` ✓; ruff + mypy + coverage configs ✓; `[project.scripts]` ✓ (P6 Tier 4); per-module mypy strictness gradient in place. **Gaps:** `mypy --strict` not yet enabled globally; no typed `UseCase` / `Catalog` Pydantic/dataclass model in `src/splunk_uc/`. |
| **P5** Frontend rebuild | NOT STARTED | No `apps/web/`. F8/F16/F17 all unresolved. |
| **P6** Scripts taxonomy | DONE | Just closed in v8.2.0 (commit `a36aa4db4`). 83-verb dispatcher + Tier 4 packaging. |
| **P7** Server-side search + API gateway | NOT STARTED | — |
| **P8** Observability + content metrics | PARTIAL | `dist/metrics.json` per AGENTS.md ✓, `data/metrics-history/<VERSION>.json` snapshot pattern ✓ (just added `8.2.0.json`). Slack/email weekly digest unclear (`stewardship.yml` exists). Build telemetry exists (`dist/build-telemetry.json`). |
| **P9** Monorepo split (apps/ + packages/) | NOT STARTED | — |
| **P10** Performance + a11y hardening | NOT STARTED | F8 (index.html size, CSP, innerHTML) is the prerequisite; no Lighthouse CI yet. |
| **P11** OSS release polish | NOT STARTED | No `.devcontainer/`; no public roadmap board sync from `ROADMAP.md` (and `ROADMAP.md` itself still says v7.1 as the "Current release"). |
| **P12** Splunk content quality moonshot | NOT STARTED | F22 (two sample regimes) unresolved; no per-UC `thresholds` field in schema; no SPL formatter; no AppInspect gate. |
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

1. **ROADMAP.md is 3 minor versions stale.** "Current release" still says
   v7.1 (line 9); we are now at v8.2.0. Should be refreshed in the next
   doc PR.
2. **`reset_legacy_module_cache()` vestigial stub** at
   `tools/build/parse_content.py:1058` and its `__all__` export — dead
   code remaining after F1 closure. Plus stale docstrings in
   `tools/build/build.py:39-43` and `tools/build/enrichment.py:5-11`
   still describe the deleted `_legacy_module()` flow.
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
   - `validate.yml` 953 lines → 1,073 lines
   The plan's next refresh should re-anchor these numbers.

## Recommended next actions, in size order

1. **Quick win (~50 line PR):** Close **F10** by adding `secrets.env`,
   `secrets.env.local`, `.env`, `.env.local`, `mcp/.pytest_cache/`,
   `__pycache__/` to `.cursorignore`. Plus refresh `ROADMAP.md`
   "Current release" from v7.1 to v8.2.0. Plus the `reset_legacy_module_cache()`
   + stale-docstring cleanup. Plus delete `dist-content/` /
   `dist-legacy/` local directories.
2. ~~**Medium win (~50–100 line PR):** Close **F7**.~~ **Done
   2026-05-12** — both backlogs were already zero, so the
   `continue-on-error: true` flags on `audit-gold-profile --summary`
   and `generate-md-from-json --check` were dropped from
   `validate.yml`. See CHANGELOG `[Unreleased]` for the bullet.
3. **Plan's headline next PR (~500 lines):** **Phase 2 main work** —
   split `validate.yml` into 6–8 parallel jobs per the plan §P2 sketch.
   This is PR-5 from §9 of the plan. Largest single impact remaining.
4. **Phase 4 first canary (~150 lines):** Enable `mypy --strict` on
   `src/splunk_uc/audits/` only (already typed-ish after the v8.2.0
   migration); ratchet outward in subsequent PRs.
5. **Lay P12 groundwork (~no code, 1 PR):** Pick one of the two sample
   regimes (F22). The plan §P12 first deliverable says the choice
   itself is the deliverable.
6. **`docs/health-check-2026-progress.md`** (this file) refreshed every
   minor version to keep "what's done" honest.

## Method note

Status here is derived from: actual file contents at HEAD `a36aa4db4`;
the v8.2.0 CHANGELOG narrative; the `docs/migration-status.md` ledger;
`git log --oneline -30`; live `wc -l` on the workflow / build files;
test collection via `pytest --collect-only`; and direct grep / glob of
the repo. No claim above is based on the plan's self-reported state at
plan-writing time without verification at HEAD.
