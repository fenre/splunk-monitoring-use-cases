# Contributing

The **v7** catalog pipeline is the only supported path: `content/cat-*/UC-*.json` → `tools/build/build.py` → `dist/`.

## Getting started

```bash
git clone https://github.com/fenre/splunk-monitoring-use-cases.git
cd splunk-monitoring-use-cases
make build
```

Open `dist/index.html` in a browser (via `make serve`, or any static server rooted at `dist/`). The site loads data from the API endpoints in `dist/api/`.

## Adding use cases

### Files and IDs

- **Category directories:** `content/cat-XX-descriptive-name/` containing `UC-X.Y.Z.json` files, where `XX` is the two-digit category.
- **UC files:** `UC-X.Y.Z.json` with `id` (`X.Y.Z`) and `title` fields — category `X`, subcategory `Y`, use case `Z`.
- **ID rules (`scripts/audit_uc_ids.py`):** `X` must match the directory’s `cat-XX-`. Within each subcategory `(X.Y)`, `Z` values must be **strictly increasing with no gaps** (e.g. …2 then …4 is invalid). The `id` values (and thus `UC-X.Y.Z`) must be unique repo-wide.

### Required UC fields (CI)

Structure and enums are enforced against [`schemas/uc.schema.json`](schemas/uc.schema.json). `scripts/audit_uc_structure.py` and the build treat that schema (plus CI rules) as the contract. The table below lists JSON properties commonly required for catalog UCs; see the schema for the full required/optional set and valid `monitoringType` values.

| JSON property | Notes |
|--------|--------|
| `criticality` | One of: `critical`, `high`, `medium`, `low` |
| `difficulty` | One of: `beginner`, `intermediate`, `advanced`, `expert` |
| `monitoringType` | Non-empty array; values must match the schema enum (e.g. `Security`, `Performance`, …) |
| `value` | Why this matters |
| `app` | Splunk app or add-on id — catalog “primary app” |
| `dataSources` | What feeds the detection |
| `spl` | Primary SPL string (plain text in JSON, no markdown fencing) |
| `implementation` | Deployment / tuning guidance |
| `visualization` | Suggested views |
| `cimModels` | Model name(s); omit or use `[]` / entries as appropriate per schema |

Common optional properties (not all enforced on every UC): `mitreAttack`, `cimSpl`, `references`, `wave`, `prerequisiteUseCases`, and other fields documented in the schema.

### Implementation ordering (optional)

Curators can mark each UC with an **implementation wave** and list **UCs that must be implemented first** so readers know which order to roll things out:

| Field | Values / format | Notes |
|--------|------------------|-------|
| `wave` | `crawl`, `walk`, `run` | `crawl` = foundation (platform + data sources + primary TAs); `walk` = extends or correlates foundation data; `run` = cross-source correlation, ML, or multi-UC orchestration. |
| `prerequisiteUseCases` | Array of `UC-X.Y.Z` strings | UCs that must be implemented first (data sources, macros, lookups, upstream detections). Validated at build time — unknown ids, self-references, and dependency cycles fail the build. |

See [`docs/use-case-fields.md#implementation-ordering-optional-v14`](docs/use-case-fields.md#implementation-ordering-optional-v14) for display details.

## UC template

Copy verbatim shape; replace placeholders.

```json
{
  "id": "X.Y.Z",
  "title": "Short descriptive title",
  "criticality": "high",
  "difficulty": "intermediate",
  "wave": "walk",
  "prerequisiteUseCases": ["UC-1.1.1", "UC-13.1.1"],
  "monitoringType": ["Security"],
  "value": "One or two sentences on impact.",
  "app": "Your_TA_id",
  "dataSources": "Sourcetypes / APIs / logs.",
  "spl": "index=... | ...",
  "implementation": "How to roll it out and tune it.",
  "visualization": "Table, single value, etc.",
  "cimModels": ["Authentication"],
  "references": [{"url": "https://...", "title": "Vendor docs"}]
}
```

## CIM SPL guidelines

- `cimSpl` must **match the UC title and intent** (same entities, actions, and time scope as the main `spl`). Do **not** paste generic `tstats` snippets from other UCs.
- If there is **no** sensible CIM datamodel for the UC, omit `cimSpl` (and avoid claiming CIM models that do not apply).

## Non-technical view

When you add a **new category** or **subcategory**, add a matching entry in `non-technical-view.js` (`window.NON_TECHNICAL`). Each `areas[]` item needs `name`, `description`, and **exactly three** `ucs` objects `{ id: "X.Y.Z", why: "..." }` that reference real UC ids present in `content/`. Run:

```bash
node -e "const window={}; eval(require('fs').readFileSync('non-technical-view.js','utf8')); console.log(Object.keys(window.NON_TECHNICAL).length+' categories OK');"
```

When you add a **new UC** or meaningfully edit an existing UC's `title` / `description` / `value`, regenerate the per-UC plain-language summary used by the non-technical view:

```bash
python3 scripts/generate_grandma_explanations.py            # fills missing UCs
python3 scripts/generate_grandma_explanations.py --only 1.1.1  # regenerate one UC
python3 scripts/generate_grandma_explanations.py --force    # overwrite (rarely needed)
python3 scripts/generate_grandma_explanations.py --check    # CI drift guard (exit 1 on missing)
```

CI runs the `--check` step on every PR and blocks merge if any UC sidecar is missing a `grandmaExplanation`. Existing curator-authored values are never overwritten unless `--force` is passed. Full authoring guide: [`docs/grandma-explanations.md`](docs/grandma-explanations.md).

## Documentation-UC map

When you add or rename a **documentation file** under `docs/`, or add a **new UC** that is a strong example for an existing doc topic, update `docs-uc-map.js`. Each entry maps a doc path to a title and an array of relevant UC IDs. The reverse index (UC → docs) is computed automatically and powers the "Related Documentation" section in the UC detail panel.

Verify with:

```bash
node -e "eval(require('fs').readFileSync('docs-uc-map.js','utf8')); console.log(Object.keys(DOC_UC_MAP).length + ' docs OK');"
```

CI runs a syntax check on every PR and the build validates that all referenced UC IDs exist in the catalog.

## Version management

1. Read **`VERSION`** before editing release text.
2. **`VERSION`**, top **`CHANGELOG.md`** header (`## [x.y.z] - YYYY-MM-DD`), and the **newest** release-notes tag in **`index.html`** must all match (CI enforces this).
3. **Ask a maintainer before bumping** the version number.

## Gold Standard — quality-over-quantity authoring

The catalog follows a **quality-over-quantity** philosophy: fewer excellent
use cases beat many shallow ones. Every UC should aim for operational utility
— can someone implement this UC end-to-end from this page alone?

### Quality tiers

| Tier | Label | Target |
|------|-------|--------|
| Gold | Deep | API-polled products, complex TAs — full 5-step implementation with product-specific depth |
| Silver | Solid | Syslog-based or simpler integrations — 3+ substantive sections, at least 1 reference |
| Bronze | Basic | Minimum viable — enough metadata and SPL to be useful |

See [`docs/gold-standard-template.md`](docs/gold-standard-template.md) for the
full quality contract and the exemplar (UC-5.13.1).

### AI-first authoring workflow

Content uplift is primarily AI-authored via Cursor agent sessions, with human
review via Pull Requests:

1. **Author** — The Cursor rule at `.cursor/rules/gold-standard-authoring.mdc`
   guides agents to produce operationally deep content
2. **Audit** — `python3 scripts/audit_gold_profile.py --files <changed files>`
   validates depth, not just field presence
3. **Generate .md** — `python3 scripts/generate_md_from_json.py --files <changed files>`
   regenerates companion markdown from JSON (JSON is the single source of truth)
4. **Review** — Open a PR; the quality audit runs in CI; human reviewers check
   product knowledge and consolidation decisions

### JSON is the source of truth

Never edit `.md` files directly under `content/`. They are auto-generated from
JSON by `scripts/generate_md_from_json.py`. Edit only the `.json` files.

### Consolidation

When uplifting a subcategory, actively look for redundant or near-duplicate UCs.
If 15 UCs are threshold variations of the same alert, consolidate into fewer UCs
with tuning guidance. See the template guide for detailed merge/keep criteria.

## Audits (`scripts/`)

Run locally before opening a PR (validates UC JSON under **`content/cat-*/UC-*.json`**):

```bash
python3 scripts/audit_uc_ids.py && python3 scripts/audit_uc_structure.py --full
```

| Script | What it checks |
|--------|----------------|
| `audit_uc_ids.py` | Duplicate UC IDs; `X` vs `cat-XX` directory; per-subcategory `Z` order and no gaps |
| `audit_uc_structure.py` | Required JSON fields, criticality/difficulty enums, and structure per CI/schema |
| `audit_non_technical_sync.py` | `non-technical-view.js` UC ids exist in content; every `cat-NN` category and subcategory has JS coverage |
| `audit_changelog_uc_refs.py` | `CHANGELOG.md` version headers (shape, dates, ordering, duplicates); `UC-*` references point to real UC ids |
| `audit_repo_consistency.py` | `INDEX.md` vs `content/cat-*` tree, icons vs `index.html` `SI_PATHS`, Quick Start UCs, `tools/build/enrichment.py` (`CAT_GROUPS`, `SPLUNK_APPS`) |
| `audit_catalog_schema.py` | `catalog.json` schema validation: category/subcategory/UC structure, required fields, enum values, optional `wv` (wave) / `pre` (prerequisite UC) fields, and the top-level `implementationRoadmap` block |
| `generate_grandma_explanations.py --check` | Every UC sidecar has a non-empty, in-bounds `grandmaExplanation` (20–400 chars); also runs as a dedicated CI step |
| `audit_gold_profile.py` | Gold Standard depth audit — measures operational completeness, detects shallow boilerplate, flags consolidation candidates |
| `generate_md_from_json.py --check` | Checks that all `.md` companion files are up-to-date with their JSON source |

Other `scripts/*` files are generators or one-off tools, not part of the default validation loop.

## CI (`.github/workflows/validate.yml`)

On pull requests (when paths under `content/`, `tools/build/`, `non-technical-view.js`, `scripts/`, `CHANGELOG.md`, `index.html`, `VERSION`, etc. change), CI runs all audits above, Node eval on `non-technical-view.js`, **version triple consistency**, then **`python3 tools/build/build.py --out dist`** and fails if tracked generated output (under `dist/` and related artefacts) would change without matching commits.

## UC test harness secrets (`.github/workflows/uc-tests.yml`)

The end-to-end test job spins up a Splunk Enterprise 9.4 service container and runs every UC with a `samples/UC-*/positive.log` fixture against its SPL. Two repository secrets gate the E2E run:

| Secret | Used for |
|---|---|
| `UC_TEST_SPLUNK_PASSWORD` | Bootstraps the Splunk service container (admin password) and authenticates REST/HEC calls from `scripts/run_uc_tests.py`. |
| `UC_TEST_HEC_TOKEN` | HEC token that `run_uc_tests.py` uses to ingest each `positive.log` into the container. |

Set both under *Settings → Secrets and variables → Actions → New repository secret*. Any strong value is acceptable — they only exist for the disposable container; they do not authenticate anywhere else.

When the password secret is missing, the `precheck` job in `uc-tests.yml` short-circuits and the E2E job is skipped cleanly (CI stays green). The pre-flight `Validate fixtures` job always runs and does not require secrets.

## Build workflow

After **any** catalog content or build-input change:

```bash
make build
```

The build regenerates the full site into `dist/` (API endpoints, search index, catalog, etc.). Commit the changed generated files in the same PR as the source edits.
