# Contributing

Practical notes for the Splunk monitoring use case catalog (`content/` JSON → `build.py` → `data.js` / `catalog.json`).

## Getting started

```bash
git clone https://github.com/fenre/splunk-monitoring-use-cases.git
cd splunk-monitoring-use-cases
python3 build.py
```

Open `index.html` in a browser (file:// or any static server). The site reads generated `data.js`.

## Adding use cases

### Files and IDs

- **Category files:** `use-cases/cat-XX-descriptive-name.md` where `XX` is the two-digit category (must match `INDEX.md` and `cat-XX-*.md` glob).
- **UC headers:** `### UC-X.Y.Z · Title` — category `X`, subcategory `Y`, use case `Z`.
- **ID rules (`scripts/audit_uc_ids.py`):** `X` must match the file’s `cat-XX-`. Within each subcategory `(X.Y)`, `Z` values must be **strictly increasing with no gaps** (e.g. …2 then …4 is invalid). IDs must be unique repo-wide.

### Required UC fields (CI)

Each UC block is parsed from the `### UC-…` header until the next UC or EOF. `scripts/audit_uc_structure.py` requires these bullet fields (non-empty), plus a fenced SPL block after `- **SPL:**`:

| Field | Notes |
|--------|--------|
| **Criticality:** | One of: `🔴 Critical`, `🟠 High`, `🟡 Medium`, `🟢 Low` |
| **Difficulty:** | One of: `🟢 Beginner`, `🔵 Intermediate`, `🟠 Advanced`, `🔴 Expert` |
| **Monitoring type:** | e.g. Security, Performance, … |
| **Value:** | Why this matters |
| **App/TA:** | Splunk app or add-on id (backticks ok) — this is the catalog “primary app” field |
| **Data Sources:** | What feeds the detection |
| **SPL:** | Immediately followed by a ```spl fenced block |
| **Implementation:** | Deployment / tuning guidance |
| **Visualization:** | Suggested views |
| **CIM Models:** | Model name(s) or `N/A` |

Common optional lines (not enforced by structure audit): **MITRE ATT&CK**, **CIM SPL** (see below), **References**, **Wave**, **Prerequisite UCs**.

### Implementation ordering (optional)

Curators can mark each UC with an **implementation wave** and list **UCs that must be implemented first** so readers know which order to roll things out:

| Field | Values / format | Notes |
|--------|------------------|-------|
| **Wave:** | `🐢 crawl`, `🚶 walk`, `🏃 run` (emojis optional) | `crawl` = foundation (platform + data sources + primary TAs); `walk` = extends or correlates foundation data; `run` = cross-source correlation, ML, or multi-UC orchestration. |
| **Prerequisite UCs:** | Comma-separated `UC-X.Y.Z` ids | UCs that must be implemented first (data sources, macros, lookups, upstream detections). Validated by `build.py` — unknown ids, self-references, and dependency cycles fail the build. |

See [`docs/use-case-fields.md#implementation-ordering-optional-v14`](docs/use-case-fields.md#implementation-ordering-optional-v14) for display details.

## UC template

Copy verbatim shape; replace placeholders.

````markdown
---

### UC-X.Y.Z · Short descriptive title
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Wave:** 🚶 walk
- **Prerequisite UCs:** UC-1.1.1, UC-13.1.1
- **Monitoring type:** Security
- **Value:** One or two sentences on impact.
- **App/TA:** `Your_TA_id`
- **Data Sources:** Sourcetypes / APIs / logs.
- **SPL:**
```spl
index=... 
| ...
```
- **Implementation:** How to roll it out and tune it.
- **Visualization:** Table, single value, etc.
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count from datamodel=Authentication.Authentication ...
```
- **References:** Splunk Docs / vendor links (optional but encouraged)

---
````

If there is **no** sensible CIM datamodel for the UC, use `- **CIM Models:** N/A` and **omit** the **CIM SPL:** line and its fence entirely.

## CIM SPL guidelines

- CIM SPL must **match the UC title and intent** (same entities, actions, and time scope as the main SPL). Do **not** paste generic `tstats` snippets from other UCs.
- If **CIM Models: N/A**, do not include a CIM SPL block.

## Non-technical view

When you add a **new category** or **subcategory** (`## X.Y` in markdown), add a matching entry in `non-technical-view.js` (`window.NON_TECHNICAL`). Each `areas[]` item needs `name`, `description`, and **exactly three** `ucs` objects `{ id: "X.Y.Z", why: "..." }` that reference real `### UC-X.Y.Z` headers. Run:

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

CI runs a syntax check on every PR and `build.py` validates that all referenced UC IDs exist in the catalog.

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

Run locally before opening a PR:

```bash
python3 scripts/audit_uc_ids.py && python3 scripts/audit_uc_structure.py --full
```

| Script | What it checks |
|--------|----------------|
| `audit_uc_ids.py` | Duplicate UC IDs; `X` vs filename; per-subcategory `Z` order and no gaps |
| `audit_uc_structure.py` | Required fields, criticality/difficulty enums, SPL fenced block |
| `audit_non_technical_sync.py` | `non-technical-view.js` UC ids exist in markdown; every `cat-NN` category and `## X.Y` subcategory has JS coverage |
| `audit_changelog_uc_refs.py` | `CHANGELOG.md` version headers (shape, dates, ordering, duplicates); `UC-*` references in markdown point to real headers |
| `audit_repo_consistency.py` | `INDEX.md` vs `cat-NN-*.md`, icons vs `index.html` `SI_PATHS`, Quick Start UCs, `build.py` `CAT_GROUPS` / `SPLUNK_APPS` |
| `audit_catalog_schema.py` | `catalog.json` schema validation: category/subcategory/UC structure, required fields, enum values, optional `wv` (wave) / `pre` (prerequisite UC) fields, and the top-level `implementationRoadmap` block |
| `generate_grandma_explanations.py --check` | Every UC sidecar has a non-empty, in-bounds `grandmaExplanation` (20–400 chars); also runs as a dedicated CI step |
| `audit_gold_profile.py` | Gold Standard depth audit — measures operational completeness, detects shallow boilerplate, flags consolidation candidates |
| `generate_md_from_json.py --check` | Checks that all `.md` companion files are up-to-date with their JSON source |

Other `scripts/*` files are generators or one-off tools, not part of the default validation loop.

## CI (`.github/workflows/validate.yml`)

On pull requests (when paths under use-cases, `build.py`, `non-technical-view.js`, `scripts/`, `CHANGELOG.md`, `index.html`, `VERSION`, etc. change), CI runs all audits above, Node eval on `non-technical-view.js`, **version triple consistency**, then **`python3 build.py`** and fails if `data.js` or `catalog.json` would change (stale generated files).

## UC test harness secrets (`.github/workflows/uc-tests.yml`)

The end-to-end test job spins up a Splunk Enterprise 9.4 service container and runs every UC with a `samples/UC-*/positive.log` fixture against its SPL. Two repository secrets gate the E2E run:

| Secret | Used for |
|---|---|
| `UC_TEST_SPLUNK_PASSWORD` | Bootstraps the Splunk service container (admin password) and authenticates REST/HEC calls from `scripts/run_uc_tests.py`. |
| `UC_TEST_HEC_TOKEN` | HEC token that `run_uc_tests.py` uses to ingest each `positive.log` into the container. |

Set both under *Settings → Secrets and variables → Actions → New repository secret*. Any strong value is acceptable — they only exist for the disposable container; they do not authenticate anywhere else.

When the password secret is missing, the `precheck` job in `uc-tests.yml` short-circuits and the E2E job is skipped cleanly (CI stays green). The pre-flight `Validate fixtures` job always runs and does not require secrets.

## Build workflow

After **any** catalog content or parser change:

```bash
python3 build.py
```

The build regenerates tracked artefacts (`data.js`, `catalog.json`, `llms.txt`, etc.). Commit the changed files in the same PR as the source edits.
