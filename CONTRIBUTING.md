# Contributing

Practical notes for the Splunk monitoring use case catalog (markdown sources → `build.py` → `data.js` / `catalog.json`).

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

Common optional lines (not enforced by structure audit): **MITRE ATT&CK**, **CIM SPL** (see below), **References**.

## UC template

Copy verbatim shape; replace placeholders.

````markdown
---

### UC-X.Y.Z · Short descriptive title
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
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

## Version management

1. Read **`VERSION`** before editing release text.
2. **`VERSION`**, top **`CHANGELOG.md`** header (`## [x.y.z] - YYYY-MM-DD`), and the **newest** release-notes tag in **`index.html`** must all match (CI enforces this).
3. **Ask a maintainer before bumping** the version number.

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
| `audit_catalog_schema.py` | `catalog.json` schema validation: category/subcategory/UC structure, required fields, enum values |

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
git add data.js catalog.json llms.txt llm.txt llms-full.txt  # include whatever `build.py` touched
```

Commit regenerated artifacts in the same PR as the source edits.
