# `splunk_uc` package and `python -m splunk_uc <verb>` dispatcher

Repo-overhaul plan §P6 (scripts taxonomy), 2026-05-09.

## Why

The repository has accumulated 120+ ad-hoc scripts under `scripts/`
covering audits, generators, migrations, ingestion, and feasibility
analyses. Discoverability is poor (no help index), invocation is
inconsistent (some need `pip install`, some don't), and the layout
makes it hard to reason about which scripts are still load-bearing.

P6 introduces a single Python package — `splunk_uc` — at
`src/splunk_uc/` with five subpackages aligned with the
established script categories. A unified `python -m splunk_uc <verb>`
dispatcher resolves verb names to their implementations through a
small registry. The migration is incremental: each batch moves
N scripts at a time and leaves thin shims at the old `scripts/<name>.py`
paths so existing CI workflows and Makefile targets keep working
unchanged.

## Layout

```
src/splunk_uc/
├── __init__.py        # version is read from VERSION
├── __main__.py        # python -m splunk_uc <verb>  dispatcher
├── _registry.py       # verb -> module mapping
├── audits/            # quality / structure / drift / reproducibility
├── generators/        # text + structured artefact emitters
├── ingest/            # external-data ingestion (regulations, vendors)
├── migrations/        # one-shot data migrations
└── feasibility/       # ROI / coverage / gap analyses
```

## Invocation

The package is not yet `pip install -e`-d in CI. Until it is, the
canonical invocation puts `src/` on `PYTHONPATH` on demand. Both
shells work:

    # Through the dispatcher (preferred, exercises the new CLI surface):
    PYTHONPATH=src python3 -m splunk_uc --help
    PYTHONPATH=src python3 -m splunk_uc audit-reproducibility
    PYTHONPATH=src python3 -m splunk_uc audit-reproducibility --first-build-only

    # Through the legacy shim path (still works for one release of soak):
    python3 scripts/audit_build_reproducibility.py
    python3 scripts/audit_build_reproducibility.py --first-build-only

The Makefile sets `PYTHONPATH=src` automatically via the `SPLUNK_UC`
variable so `make audit-reproducibility` and `make
audit-reproducibility-fast` go through the dispatcher with no extra
ceremony. After `pip install -e .` the `PYTHONPATH=src` prefix is
unnecessary.

## Migrating a script

Each migration is a focused PR that moves one script. The recipe:

1. Copy the script body to
   `src/splunk_uc/<subpackage>/<module_name>.py`. Keep the
   ``main(argv: list[str] | None = None) -> int`` contract.
2. Adjust any `Path(__file__).resolve().parents[N]` constants for
   the new depth (scripts is one level deep; the new location is
   three levels deep, so most ``parent.parent`` chains become
   ``parents[3]``).
3. Replace the original `scripts/<name>.py` with a 30-line shim
   that puts `src/` on `sys.path` and re-exports the public
   names. The shim documents the relocation and explains why it
   exists. See `scripts/audit_build_reproducibility.py` for the
   canonical example.
4. Register the verb in `src/splunk_uc/_registry.py` with a
   kebab-case name, the dotted module path (relative to
   `splunk_uc`), a one-line help string, and a category label.
5. Update any tests that monkeypatch module-level state to patch
   the **implementation** module under `splunk_uc`, not the shim
   in `scripts/`. The shim only re-exports — patching it does
   not propagate into the closures of the implementation's
   functions. Tests that read shim module attributes (e.g. `main`,
   `_run_build`) keep working unchanged because they read through
   the re-exports.
6. If the script is invoked from the Makefile or a CI workflow,
   update those call-sites to use `python -m splunk_uc <verb>`
   in the same PR. The legacy `python3 scripts/<name>.py`
   invocation continues to work via the shim, so external callers
   are not broken.
7. Add a CI smoke step or a unit test exercising the new
   dispatcher path so the migration is not silently bypassed.

## Verb registry

Verbs are registered in `src/splunk_uc/_registry.py` with the
``Verb`` dataclass:

```python
register(
    Verb(
        name="audit-reproducibility",
        module="audits.build_reproducibility",
        help="Run two --reproducible builds and verify byte-identical output.",
        category="audits",
    )
)
```

Rules:

* `name` is kebab-case. Aligns with Makefile target naming.
* `module` is dotted relative to `splunk_uc` (no leading `splunk_uc.`).
* `help` is a single line ≤ 80 chars. Surfaced in
  `python -m splunk_uc --help`.
* `category` is one of `audits`, `generators`, `ingest`,
  `migrations`, `feasibility`. Verb appearance in the help table
  groups by category.

The dispatcher resolves modules **lazily**: importing
`splunk_uc.__main__` does not import the implementation module
until the user actually invokes that verb. The dispatcher
test_suite asserts this property so future migrations can't
silently introduce eager-import side-effects.

## CI gates

| Workflow                                  | What it checks                                                                              |
|-------------------------------------------|---------------------------------------------------------------------------------------------|
| `validate.yml` lint job                   | `python -m splunk_uc --help` and `--version` succeed (per-PR, sub-second).                  |
| `validate.yml` lint job (existing)        | `tests/splunk_uc/test_dispatcher.py` (21 tests) covers the registry / help / argv handoff.  |
| `build-reproducibility.yml` (nightly + PR)| `audit-reproducibility` runs through the dispatcher, asserting byte-identical builds.       |

## Migrated verbs

| Verb                          | Implementation module                       | Migrated  |
|-------------------------------|---------------------------------------------|-----------|
| `audit-reproducibility`       | `splunk_uc.audits.build_reproducibility`    | 2026-05-09 (Tier 0) |
| `audit-roadmap-consistency`   | `splunk_uc.audits.roadmap_consistency`      | 2026-05-09 (Tier 1, batch 1) |
| `audit-license-inventory`     | `splunk_uc.audits.license_inventory`        | 2026-05-09 (Tier 1, batch 1) |
| `audit-legacy-orphans`        | `splunk_uc.audits.legacy_orphans`           | 2026-05-09 (Tier 1, batch 2) |
| `audit-coverage-budget`       | `splunk_uc.audits.coverage_budget`          | 2026-05-09 (Tier 1, batch 2) |
| `audit-action-pins`           | `splunk_uc.audits.action_pins`              | 2026-05-09 (Tier 1, batch 2) |
| `audit-uc-structure`          | `splunk_uc.audits.uc_structure`             | 2026-05-09 (Tier 1, batch 3) |
| `audit-dashboard-spl`         | `splunk_uc.audits.dashboard_spl`            | 2026-05-09 (Tier 1, batch 3) |
| `audit-cim-spl-alignment`     | `splunk_uc.audits.cim_spl_alignment`        | 2026-05-09 (Tier 1, batch 4) |
| `audit-legal-review-signoffs` | `splunk_uc.audits.legal_review_signoffs`    | 2026-05-09 (Tier 1, batch 4) |
| `audit-regulatory-primer`     | `splunk_uc.audits.regulatory_primer`        | 2026-05-09 (Tier 1, batch 4) |
| `audit-mitre-taxonomy`        | `splunk_uc.audits.mitre_taxonomy`           | 2026-05-09 (Tier 1, batch 4) |
| `audit-placeholders`          | `splunk_uc.audits.placeholders`             | 2026-05-09 (Tier 1, batch 4) |
| `audit-design-doc-freshness`  | `splunk_uc.audits.design_doc_freshness`     | 2026-05-09 (Tier 1, batch 5) |
| `audit-uc-ids`                | `splunk_uc.audits.uc_ids`                   | 2026-05-09 (Tier 1, batch 5) |
| `audit-splunkbase-ids`        | `splunk_uc.audits.splunkbase_ids`           | 2026-05-09 (Tier 1, batch 5) |
| `audit-known-fp`              | `splunk_uc.audits.known_fp`                 | 2026-05-09 (Tier 1, batch 5) |
| `audit-non-technical-sync`    | `splunk_uc.audits.non_technical_sync`       | 2026-05-09 (Tier 1, batch 5) |
| `audit-monitoring-type`       | `splunk_uc.audits.monitoring_type`          | 2026-05-09 (Tier 1, batch 5) |
| `audit-changelog-uc-refs`     | `splunk_uc.audits.changelog_uc_refs`        | 2026-05-09 (Tier 1, batch 6) |
| `audit-repo-consistency`      | `splunk_uc.audits.repo_consistency`         | 2026-05-09 (Tier 1, batch 6) |
| `audit-catalog-schema`        | `splunk_uc.audits.catalog_schema`           | 2026-05-09 (Tier 1, batch 6) |
| `audit-quality-metadata`      | `splunk_uc.audits.quality_metadata`         | 2026-05-09 (Tier 1, batch 6) |
| `audit-spl-duplicates`        | `splunk_uc.audits.spl_duplicates`           | 2026-05-09 (Tier 1, batch 6) |
| `audit-links`                 | `splunk_uc.audits.links`                    | 2026-05-09 (Tier 1, batch 6) |
| `audit-regulation-alignment`  | `splunk_uc.audits.regulation_alignment`     | 2026-05-09 (Tier 1, batch 7) |
| `audit-nis2-no-gap`           | `splunk_uc.audits.nis2_no_gap`              | 2026-05-09 (Tier 1, batch 7) |
| `audit-oscal-roundtrip`       | `splunk_uc.audits.oscal_roundtrip`          | 2026-05-09 (Tier 1, batch 7) |
| `audit-regulatory-change-watch` | `splunk_uc.audits.regulatory_change_watch` | 2026-05-09 (Tier 1, batch 7) |
| `audit-compliance-gaps`       | `splunk_uc.audits.compliance_gaps`          | 2026-05-09 (Tier 1, batch 8) |
| `audit-compliance-mappings`   | `splunk_uc.audits.compliance_mappings`      | 2026-05-09 (Tier 1, batch 8) |
| `audit-guide-xrefs`           | `splunk_uc.audits.guide_xrefs`              | 2026-05-09 (Tier 1, batch 8) |
| `audit-doc-counts`            | `splunk_uc.audits.doc_counts`               | 2026-05-09 (Tier 1, batch 9) |
| `audit-openapi-drift`         | `splunk_uc.audits.openapi_drift`            | 2026-05-09 (Tier 1, batch 9) |
| `audit-content-quality`       | `splunk_uc.audits.content_quality`          | 2026-05-09 (Tier 1, batch 9) |
| `audit-baseline-clause-grammar-free` | `splunk_uc.audits.baseline_clause_grammar_free` | 2026-05-09 (Tier 1, batch 9) |
| `audit-peer-review-signoffs`  | `splunk_uc.audits.peer_review_signoffs`     | 2026-05-09 (Tier 1, batch 9) |
| `audit-mcp-tool-schemas`      | `splunk_uc.audits.mcp_tool_schemas`         | 2026-05-09 (Tier 1, batch 9) |
| `audit-gold-profile-v2`       | `splunk_uc.audits.gold_profile_v2`          | 2026-05-09 (Tier 1, batch 10) |
| `audit-prerequisites`         | `splunk_uc.audits.prerequisites`            | 2026-05-09 (Tier 1, batch 10) |
| `audit-sandbox-validation`    | `splunk_uc.audits.sandbox_validation`       | 2026-05-09 (Tier 1, batch 10) |
| `audit-sme-review-signoffs`   | `splunk_uc.audits.sme_review_signoffs`      | 2026-05-09 (Tier 1, batch 10) |
| `audit-mapping-ledger`        | `splunk_uc.audits.mapping_ledger`           | 2026-05-09 (Tier 1, batch 10) |

## Soak schedule

| Stage                         | Status (2026-05-09)         |
|-------------------------------|-----------------------------|
| Package skeleton + dispatcher | ✅ Landed                   |
| Tier 0 — first migration      | ✅ `audit-reproducibility`  |
| Tier 1 — audit batch 1        | ✅ `audit-roadmap-consistency` + `audit-license-inventory` |
| Tier 1 — audit batch 2        | ✅ `audit-legacy-orphans` + `audit-coverage-budget` + `audit-action-pins` |
| Tier 1 — audit batch 3        | ✅ `audit-uc-structure` + `audit-dashboard-spl` |
| Tier 1 — audit batch 4        | ✅ `audit-cim-spl-alignment` + `audit-legal-review-signoffs` + `audit-regulatory-primer` + `audit-mitre-taxonomy` + `audit-placeholders` |
| Tier 1 — audit batch 5        | ✅ `audit-design-doc-freshness` + `audit-uc-ids` + `audit-splunkbase-ids` + `audit-known-fp` + `audit-non-technical-sync` + `audit-monitoring-type` |
| Tier 1 — audit batch 6        | ✅ `audit-changelog-uc-refs` + `audit-repo-consistency` + `audit-catalog-schema` + `audit-quality-metadata` + `audit-spl-duplicates` + `audit-links` |
| Tier 1 — audit batch 7        | ✅ `audit-regulation-alignment` + `audit-nis2-no-gap` + `audit-oscal-roundtrip` + `audit-regulatory-change-watch` |
| Tier 1 — audit batch 8        | ✅ `audit-compliance-gaps` + `audit-compliance-mappings` |
| Tier 1 — audit batch 9        | ✅ `audit-doc-counts` + `audit-openapi-drift` + `audit-content-quality` + `audit-baseline-clause-grammar-free` + `audit-peer-review-signoffs` + `audit-mcp-tool-schemas` |
| Tier 1 — audit batch 10       | ✅ `audit-gold-profile-v2` + `audit-prerequisites` + `audit-sandbox-validation` + `audit-sme-review-signoffs` + `audit-mapping-ledger` |
| Tier 1 — remaining audits (5 files: `audit_gold_profile.py` v1 + `audit_perf_a11y.py` + `audit_spl_grammar.py` + `audit_spl_hallucinations.py` + `audit_splunk_cloud_compat.py`; intentionally non-verb one-shot driver `audit_guide_external_links_oneshot.py` stays in `scripts/`) | 🔜 Subsequent PRs (one cluster at a time) |
| Tier 2 — generators           | 🔜 After audits             |
| Tier 2 — ingest + migrations + feasibility | 🔜 In parallel |
| Tier 3 — delete legacy `scripts/` shims | 🔒 Blocked on full migration + one minor release of soak |
| Tier 4 — wheel-package + `pip install -e .` | 🔒 Blocked on P9 monorepo decision |

## Tests

The dispatcher contract is pinned by
`tests/splunk_uc/test_dispatcher.py`:

* registry shape (every verb resolves to a real `main` callable)
* help formatting (`--help`, `-h`, no-args, `--version`, `-V`)
* error handling (unknown verb, category-name typo, deterministic stderr)
* argv forwarding (verb args reach the implementation verbatim)
* exit-code propagation (verb's non-zero exit propagates)
* lazy import (resolving one verb does not import unrelated subpackages)
* package surface (every subpackage imports cleanly)

Migrated scripts retain their original test files, with one rule:
tests that monkeypatch module-level state must patch the
**implementation** module (e.g. `splunk_uc.audits.build_reproducibility`),
not the shim. See `tests/scripts/test_audit_build_reproducibility.py`
for the canonical pattern.

## Related plan items

* **P9 (monorepo):** Once P6 is complete the package becomes
  `packages/splunk_uc/` next to `apps/web/` and `apps/mcp/`. The
  `[tool.hatch.build.targets.wheel]` config in `pyproject.toml`
  becomes meaningful at that point.
* **P11 CONTRIBUTING rewrite:** Held until P6 lands so the doc
  doesn't reference scripts/ paths that are about to move.
