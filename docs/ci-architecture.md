# CI Architecture

> Maintainer reference for the GitHub Actions workflow tree. Pairs with
> [workflow-audit.md](workflow-audit.md) (single-page workflow
> inventory + SHA-pin map), [rollback-playbook.md](rollback-playbook.md),
> [external-consumer-matrix.md](external-consumer-matrix.md) and
> [capacity-and-staffing.md](capacity-and-staffing.md).

## TL;DR

| Workflow                | Purpose                                            | Wall-clock | Trigger                |
|-------------------------|----------------------------------------------------|-----------:|------------------------|
| [`validate.yml`](#validate-yml-five-parallel-jobs)        | Catalog correctness; the merge gate.   | ~30 min    | PR + push to `main`    |
| [`pages.yml`](#pages-yml)              | Build + deploy GitHub Pages.                       | ~5 min     | push to `main`         |
| [`release.yml`](#release-yml)          | Tag-driven release: SBOM, .spl, attestation.       | ~10 min    | tag `v*.*.*`           |
| [`uc-tests.yml`](#uc-tests-yml)        | Playwright UC smoke matrix (Splunk 9.4 / 10.2).    | ~15 min    | manual / nightly       |
| [`uc-manifest.yml`](#uc-manifest-yml)  | Surface manifest of every UC's exported fields.    | ~3 min     | manual                 |
| [`codeql.yml`](#codeql-yml)            | CodeQL Python + JS analysis.                       | ~8 min     | PR + push + weekly     |
| [`dependency-review.yml`](#dependency-review-yml) | License + CVE gate on PR-level dep changes.        | ~30 sec    | PR                     |
| [`gitleaks.yml`](#gitleaks-yml)        | Secret-leak detection.                             | ~30 sec    | PR + push              |
| [`splunkbase-sync.yml`](#splunkbase-sync-yml) | Refresh `data/splunkbase-catalog.json`.            | ~2 min     | weekly cron + manual   |
| [`regulatory-watch.yml`](#regulatory-watch-yml) | Refresh `data/regulations-watch.json`.             | ~3 min     | weekly cron + manual   |
| [`build-reproducibility.yml`](#build-reproducibility-yml) | Two `--reproducible` builds → byte-identical assert.   | ~3 min     | nightly cron + build-PRs |
| [`link-check.yml`](#link-check-yml)    | Markdown link-check.                               | ~2 min     | weekly cron + PR       |
| [`traffic.yml`](#traffic-yml)          | Cache GitHub repo traffic stats.                   | ~10 sec    | daily cron             |

**Composite actions** live under `.github/actions/`:

| Composite                          | Pins / behaviour                              |
|------------------------------------|-----------------------------------------------|
| [`setup-python/action.yml`](#composite-setup-python) | `actions/setup-python@<sha>` + optional `pip install -r requirements-ci.txt` + optional `pip install -e .[<extras>]`. |
| [`setup-node/action.yml`](#composite-setup-node)     | `actions/setup-node@<sha>` + optional `npm ci --no-audit --no-fund`. |

## Why composite actions?

Before §P2 (May 2026), every workflow that needed Python or Node had its
own pinned `actions/setup-python@<sha>` / `actions/setup-node@<sha>`
line. That meant 11 setup-python pin sites and 1 setup-node pin site
across 9 workflows — every Renovate bump fanned out across the tree
and the comment-drift class of bug (someone bumps the SHA without
updating the `# vX.Y.Z` comment) silently grew.

§P2-F19 (May 12 2026) completed the migration: every workflow under
`.github/workflows/*.yml` now consumes `./.github/actions/setup-python`
(and `./.github/actions/setup-node` where applicable). The active guard
at `tests/build/test_composite_actions.py::test_no_workflow_pins_setup_python_directly`
keeps it that way — a future PR that re-introduces a raw
`actions/setup-python@<sha>` pin in any workflow file fails the test
in the `audits-content` job.

The composite actions reduce that to **two** pin sites. Centralisation:

- Makes Renovate / Dependabot bumps a one-file change.
- Surfaces upstream advisories early — bumping a SHA in one place
  triggers the audit + structural tests once, not eleven times.
- Makes [`python3 -m splunk_uc audit-action-pins`](../scripts/audit_action_pins.py)'s job
  smaller — it now walks both `.github/workflows/*.yml` *and*
  `.github/actions/*/action.yml` and the surface area is smaller.
- Makes the tests in [`tests/build/test_composite_actions.py`](../tests/build/test_composite_actions.py)
  the single point of contract enforcement (Python 3.12 default,
  Node 20 default, every `run:` declares a `shell:`).

## Pinning policy

Every third-party GitHub Action is pinned to a 40-character commit
SHA, with a trailing `# vX.Y.Z` comment that names the upstream tag.
Tag-only references (e.g. `@v4`) are forbidden because:

- Tags can be force-pushed by upstream (or by an attacker who
  compromises the upstream maintainer's account); SHAs cannot.
- Renovate / Dependabot only see SHAs as content-addressable, which
  means they can only bump a pin when the upstream releases a new
  version (rather than silently inheriting a force-push).

The audit at [`python3 -m splunk_uc audit-action-pins`](../scripts/audit_action_pins.py)
enforces both the SHA-pinning and the SHA↔tag-comment integrity.
[Three classes of attack](../SECURITY.md) are caught:

1. **Comment drift** — someone bumped the comment without re-pinning.
2. **Tag-then-force-push** — upstream re-pointed the tag at malicious
   code; our pinned SHA still resolves the original safe code, but
   the audit warns when our comment claims a version that no longer
   matches the SHA at upstream.
3. **Typo / homoglyph SHA** — a copy-paste error or deliberate
   homoglyph attack that points at a backdoored fork. Rejected
   because the SHA won't resolve via GitHub's git API.

The audit runs in the `lint` job (~5 minutes from PR open).

## Validate.yml (five parallel jobs)

The merge gate. PRs cannot merge until every job in this workflow
returns success. Job dependencies are intentionally **none** — every
job is independent, so a slow audit doesn't delay the lint signal.

Cross-job artefact independence: jobs that need `api/v1/` regenerate
it locally (cheap, deterministic — ~5 seconds) rather than depending
on `audits-build`. This keeps the parallelism pure.

### Job 1: `lint` (~5 min budget)

Fast feedback. Stdlib-only Python + tiny `node -e` evaluations. No
audit dependencies install. No `npm ci`.

| Step                                         | Script / command                                    |
|----------------------------------------------|-----------------------------------------------------|
| Schema metadata validation                   | `tools/audits/schema_meta.py`                       |
| Asset drift (inline blocks vs `src/`)        | `tools/audits/asset_drift.py`                       |
| GitHub Actions pin audit                     | `python3 -m splunk_uc audit-action-pins`                      |
| Non-technical view JS syntax                 | `node -e` over `non-technical-view.js`              |
| Docs-UC map JS syntax                        | `node -e` over `docs-uc-map.js`                     |
| Version consistency                          | inline shell over `VERSION` ↔ `CHANGELOG.md` ↔ `index.html` |

**When this job fails:** something fundamental is wrong with the
PR's metadata, version triple, or supply-chain pins. Look at the
job's first failing step — every step is independent.

### Job 2: `audits-content` (~25 min budget)

UC content audits + generator `--check` guards. Reads sidecars +
scripts + reports directly; does **not** run `tools/build/build.py`.

Major sub-areas:

- **Unit tests + coverage budget** (`pytest tests/build/ tests/scripts/`,
  then `audit_coverage_budget.py`). The coverage report is captured as
  JSON and ratcheted against [`data/baselines/coverage-v9.1.0.json`]
  (../data/baselines/coverage-v9.1.0.json): tier-1 (`tools/build/`) and
  tier-2 (`scripts/audit_*.py` + named extras) per-file coverage may
  not regress more than 1.0pp from the baseline. New tier-1 files
  must clear a 60% floor; new tier-2 files must clear 40%. Tier-3
  (one-shot uplift / migration / generator helpers) is exempt by
  design; see `python3 -m splunk_uc audit-coverage-budget` for the full
  classification policy and §P16 of the overhaul plan.
- **Legacy use-cases/ guard** (`audit-no-use-cases-dir --check`).
  Hard-fails CI if the retired ``use-cases/cat-*.md`` directory is
  recreated or if a non-allowlisted tracked file gains a fresh
  ``use-cases/`` path reference. Replaces the v9.x
  ``audit-legacy-orphans`` verb that diagnosed UCs missing a JSON
  SSOT sidecar — no longer meaningful after the v8.2.0 retirement
  (2026-05-11) of the entire legacy markdown corpus. See
  ``docs/use-cases-burndown.md`` for the migration history.
- Per-UC structure (audit_uc_ids, audit_uc_structure, audit_spl_*,
  audit_mitre_taxonomy, audit_monitoring_type, audit_cim_spl_alignment,
  audit_known_fp).
- Compliance graph (audit_compliance_mappings, baseline drift guard,
  regulation alignment, generated-reports-committed).
- Generator regeneration (Phase 2.2/2.3/3.1/3.2/3.3 + Phase C tier-2
  + equipment tags + grandma explanations + Phase 4.3 cat-22 NTV +
  Phase 4.2 evidence packs + clause-level gap report).
- Quality gates (Gold Standard summary, markdown freshness).
- Phase 4.5 / 5.x signoffs (peer review, legal review, SME review,
  regulatory change-watch, mapping-ledger).

**When this job fails:** consult the failing audit's `--help` for
the regeneration command. Most failures are "you edited a JSON
sidecar but forgot to regenerate the report" — `make build` or the
specific generator with `--check` removed will fix it.

### Job 3: `audits-build` (~30 min budget)

The only job that runs `tools/build/build.py`. Drives the wall-clock.

Sequence:

1. Generate `api/v1/` tree.
2. Story-layer Node smoke tests (`tools/audits/_phase3*_smoke.js` +
   `_phase5_primer_smoke.js`).
3. Splunk UC Recommender generator regeneration check.
4. **Build check (catalog regeneration)** — runs the build, then
   `git diff` against the committed catalog/llms/api files. If
   anything changed, the PR's missing a `make build` commit.
5. Post-build audits: byte budgets, URL freeze, prerequisite drift,
   quality metadata, Splunk Cloud compatibility, Splunk Cloud audit
   committed.
6. Package the recommender `.spl` on every push.

Artefact uploads:

- `splunk-cloud-compat` — JSON of compat findings.
- `api-v1` — the regenerated `api/v1/` tree (for PR review).
- `splunk-apps` — the generated splunk-apps tree.
- `splunk-uc-recommender-spl` — `.spl` + `.sha256` + `SHA256SUMS.txt`
  + `splunk-apps-manifest.md`. Available on every push for manual
  install testing without waiting for a release tag.

**When this job fails:** the most common failure is a missing
`make build` commit. The job's diff output names the offending
files. URL freeze and byte budget failures usually mean a
deliberate URL change or asset bloat — see
[external-consumer-matrix.md](external-consumer-matrix.md) for the
URL stability contract.

### Job 4: `mcp` (~10 min budget)

Decoupled from the other jobs because `mcp/` has its own
`pyproject.toml` and editable install path.

| Step                                      | Script / command                                              |
|-------------------------------------------|---------------------------------------------------------------|
| Generate api/v1 tree                      | `python3 -m splunk_uc generate-api-surface`                             |
| Install MCP server (editable)             | `pip install -e mcp/[test]`                                   |
| MCP server unit tests (291 tests, --cov)  | `pytest mcp/tests --cov-fail-under=70`                        |
| MCP tool schema drift guard               | `python3 -m splunk_uc audit-mcp-tool-schemas`                           |

**When this job fails:** an MCP-only change broke a tool's
`outputSchema`. The drift guard names the offending tool + field.

### Job 5: `frontend` (~10 min budget)

Render-tier and Phase 4.5 drift-guard tests. The Python `--check`
halves of the Phase 4.5d/e/f gates run here too because they share
the npm-installed Node deps.

| Step                                              | Script / command                                |
|---------------------------------------------------|-------------------------------------------------|
| Recommender frontend unit tests                   | `node --test tests/recommender/match.test.mjs`  |
| Phase 4.4 scorecard.html render test              | `node --test tests/scorecard/render.test.mjs`   |
| Phase 4.5c sandbox validation Node drift guard    | `node --test tests/sandbox/validate.test.mjs`   |
| Phase 4.5d ATT&CK<sup class="ref">[<a href="#ref-2">2</a>]</sup> simulation gate (Python)        | `scripts/simulate_controltest.py --check`       |
| Phase 4.5d ATT&CK simulation Node drift guard     | `node --test tests/attack/simulate.test.mjs`    |
| Phase 4.5e OSCAL round-trip gate (Python)         | `python3 -m splunk_uc audit-oscal-roundtrip --check`      |
| Phase 4.5e OSCAL round-trip Node drift guard      | `node --test tests/oscal/roundtrip.test.mjs`    |
| Phase 4.5f perf + a11y audit gate (Python)        | `python3 -m splunk_uc audit-perf-a11y --check`            |
| Phase 4.5f perf + a11y Node drift guard           | `node --test tests/a11y/perfa11y.test.mjs`      |

**When this job fails:** UI / render regression. The Node tests
boot the inline `<script>` from the page under jsdom — most
failures are a missing field in a JSON source feed (regenerate
the upstream report) or an introduced XSS sink (innerHTML, eval,
document.write). The Python `--check` halves diff against the
committed `reports/*.json` — drift is usually a missed
regeneration.

## Composite: setup-python

`.github/actions/setup-python/action.yml`

| Input             | Default | Purpose                                                          |
|-------------------|---------|------------------------------------------------------------------|
| `python-version`  | `3.12`  | Pin override. Default is the project-wide pin.                   |
| `install-audits`  | `false` | When `true`, runs `pip install -r .github/requirements-ci.txt`.  |
| `install-extras`  | `""`    | Optional extras (e.g. `"audits,test"`). Empty string = skip.     |

The cache key is `cache-dependency-path: .github/requirements-ci.txt` —
hits stay warm across runs that don't change CI deps.

## Composite: setup-node

`.github/actions/setup-node/action.yml`

| Input          | Default | Purpose                                                |
|----------------|---------|--------------------------------------------------------|
| `node-version` | `20`    | Pin override (e.g. `"22"` for Playwright matrix).      |
| `install-deps` | `true`  | When `true`, runs `npm ci --no-audit --no-fund`.       |

## Pages.yml

Two-job workflow that builds the static site (job 1) and deploys it
to GitHub Pages (job 2). Job 2 depends on job 1 via `needs:`.

The path-based trigger filter is generous (every documentation +
content + asset path) so the site rebuilds whenever anything
user-visible changes.

## Release.yml

Triggered by tag pattern `v*.*.*`. Builds the release artefacts:

1. Full build via `tools/build/build.py`.
2. Anchore SBOM (SPDX + CycloneDX + source).
3. `.spl` packaging via `scripts/package_splunk_apps.sh`.
4. Sigstore attestation of the `.spl`.
5. GitHub release with all artefacts attached.

The mapping-ledger audit re-runs here with `--require-signature
--verify-signature` (vs `unsigned` on PR builds). Release.yml
stamps the ledger.

## UC-tests.yml

Playwright UC smoke matrix — the only workflow that uses Node 22
(via the composite override). Manual / nightly trigger; not part
of the merge gate.

## UC-manifest.yml

Manual: emits a JSON manifest of every UC's exported fields.
Useful for impact-analysis ahead of an `additionalProperties: false`
change to `uc.schema.json`.

## CodeQL.yml

CodeQL Python + JS analysis. Runs on PR + push + weekly cron.

## Dependency-review.yml

Blocks PRs that introduce non-allowlisted licenses or known CVEs.

## Gitleaks.yml

Hermetic secret-leak detection across the diff.

## Splunkbase-sync.yml

The **only** workflow that talks to splunkbase.splunk.com. Refreshes
`data/splunkbase-catalog.json` on a weekly schedule. Manually
triggerable. The catalog cache is the input to
`scripts/sync_splunkbase_catalog.py --check` in `audits-content`,
which is hermetic.

## Regulatory-watch.yml

Weekly: fetches the regulator-published artefacts named in
`data/regulations-watch.json` and computes their SHA-256s. The PR
gate (`audit_regulatory_change_watch.py --check`) is hermetic and
runs in `audits-content`; the fetch step here is the only thing
that touches the internet for regulatory data.

## Link-check.yml

Weekly + on PR (when markdown changes). Validates the markdown link
graph. Soft-fails on transient 5xx upstream — flaky external sites
are a known FP class.

## Traffic.yml

Daily: pulls GitHub repo traffic stats into `data/traffic-cache.json`
(GitHub's API only retains 14 days; the cache extends visibility).
Manual + cron.

## Stewardship digest (on-demand only)

The scheduled `stewardship.yml` and `stewardship-rotation.yml`
workflows were retired alongside the per-category CODEOWNERS routing
that fed the rotation reminders. The digest *generator* is still
wired and can be invoked on demand:

```bash
make stewardship-digest   # writes dist/stewardship-digest.{json,md}
```

Schema: `schemas/v2/stewardship-digest.schema.json`. Useful when you
want a snapshot of staleness / coverage / leaderboards across the
catalogue, but no longer noises a weekly GitHub issue.

## Build-reproducibility.yml

Continuously verifies that two consecutive `--reproducible` builds
against the same git HEAD produce byte-identical output. Asserted via
`python3 -m splunk_uc audit-reproducibility`, which compares
`dist/integrity.json` between two builds. Triggers: nightly 03:00 UTC,
`workflow_dispatch` (with `keep_artifacts` input), and `pull_request`
filtered to the build pipeline itself (`tools/build/**`,
`schemas/v2/build-info.schema.json`, `schemas/v2/integrity.schema.json`,
`src/splunk_uc/audits/build_reproducibility.py`,
`src/splunk_uc/__main__.py`, `src/splunk_uc/_registry.py`). Per-PR cost
(~90s) is acceptable here because if we change build code we must
know we didn't break reproducibility. On failure both build trees
are uploaded as artefacts so the maintainer can diff them locally.

## Test coverage

The tests under `tests/build/test_composite_actions.py` (19 tests)
and `tests/build/test_validate_workflow_partition.py` (72 tests)
encode the structural invariants of this architecture. They
intentionally do **not** snapshot the YAML — that would create a
rubber-stamp class of PR. They pin invariants:

- Five jobs exist (the partition is a partition).
- Every job uses the composite setup, never a direct SHA pin.
- Every job declares `timeout-minutes`.
- Total content-step count stays at or above the partition floor
  (drift below the floor means a step was silently dropped).
- Every critical step is present somewhere (substring match;
  insensitive to title-format edits).
- Every Python script and Node test file referenced in a `run:`
  step exists on disk.

Editing this architecture without updating the tests is intentionally
hard — the tests are the contract.

## Troubleshooting

| Symptom                                         | Diagnostic                                                                       |
|-------------------------------------------------|----------------------------------------------------------------------------------|
| `audit_action_pins.py` fails on PR              | Run locally with `GITHUB_TOKEN=$(gh auth token)` to bypass rate-limit warnings. |
| `Build check` fails — generated files out-of-date | Run `make build` and commit the diff.                                            |
| Generator `--check` fails                       | Re-run the named script without `--check` and commit the regenerated output.    |
| `Compliance audit — generated reports committed` fails | Regenerate `reports/compliance-coverage.json` + `docs/compliance-coverage.md` and commit. |
| `URL freeze` fails                              | URL change is breaking — see [external-consumer-matrix.md](external-consumer-matrix.md). |
| MCP `cov-fail-under=70` fails                   | Add tests; coverage floor is intentionally low to allow uplift.                  |
| Node test "module not found"                    | `npm ci` in the workspace root; the composite handles this in CI.                |

## See also

- [docs/workflow-audit.md](workflow-audit.md) — single-page workflow
  inventory, cadence calendar, and third-party SHA-pin map.
- [docs/rollback-playbook.md](rollback-playbook.md) — how to revert when CI lies.
- [docs/external-consumer-matrix.md](external-consumer-matrix.md) — public release contract.
- [docs/capacity-and-staffing.md](capacity-and-staffing.md) — when to skip CI work in solo mode.
- [SECURITY.md](../SECURITY.md) — supply-chain risk classes the audit catches.
- [docs/architecture.md](architecture.md) — repo-wide architecture context.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** Anthropic, et al. (2026). *Model Context Protocol Specification*. Anthropic PBC. Retrieved May 11, 2026, from https://modelcontextprotocol.io/

<a id="ref-2"></a>**[2]** MITRE Corporation. (2026). *MITRE ATT&CK Knowledge Base*. MITRE Engenuity. https://attack.mitre.org/

<a id="ref-3"></a>**[3]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

<a id="ref-4"></a>**[4]** Splunk Inc. (2026). *Splunk Cloud Platform Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/SplunkCloud

<a id="ref-5"></a>**[5]** Splunk Inc. (2026). *Splunk Enterprise Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk

<a id="ref-6"></a>**[6]** Splunk Inc. (2026). *Splunkbase — the Splunk app marketplace*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://splunkbase.splunk.com/

### Related repository documents

- [`SECURITY.md`](../SECURITY.md)
- [`docs/architecture.md`](architecture.md)
- [`docs/capacity-and-staffing.md`](capacity-and-staffing.md)
- [`docs/external-consumer-matrix.md`](external-consumer-matrix.md)
- [`docs/rollback-playbook.md`](rollback-playbook.md)
- [`docs/workflow-audit.md`](workflow-audit.md)

### Cited by

- [`docs/f8-frontend-hardening-inventory.md`](f8-frontend-hardening-inventory.md)
- [`docs/guides/datagen-top10-use-cases.md`](guides/datagen-top10-use-cases.md)
- [`docs/workflow-audit.md`](workflow-audit.md)

<!-- END-AUTOGENERATED-SOURCES -->
