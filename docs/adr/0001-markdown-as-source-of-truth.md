# ADR-0001: Markdown as source of truth for UC content

- **Status:** Accepted
- **Date:** 2023-03-15 (ratified retroactively 2026-04-16)
- **Deciders:** Repository maintainers

## Context

The catalog holds ≥6,300 use cases. Each UC carries structured fields (Criticality, Difficulty, Value, App/TA, Data Sources, SPL, Implementation, CIM Models, Visualization, …) plus free-form prose. The authoring population is a mix of Splunk SEs, detection engineers, and community contributors, few of whom work daily with YAML/JSON and almost none of whom want to touch a database.

We needed a source format that is:

- Reviewable in a pull request without special tooling.
- Editable by humans who do not write Python.
- Diffable line-by-line in `git log`.
- Parseable by a 100% stdlib script.
- Tolerant of embedded SPL code blocks with arbitrary characters.
- Friendly to the `Edit on GitHub` link.

## Decision

**Store all UC content as plain markdown under `use-cases/cat-*.md`**, one file per category, using a fixed heading hierarchy and a bulleted field list as the schema. Machine-readable projections (`catalog.json`, `api/cat-N.json`, `data.js`, `llms*.txt`) are **derived** from the markdown by [`build.py`](../../build.py) on every build.

The markdown is the canonical form. If a generated file disagrees with the markdown, the generated file is wrong.

## Consequences

**Positive:**

- Pull-request reviews show the exact change a contributor made, including their SPL, in the native GitHub UI. No tooling needed.
- Contributors can edit a single UC in the GitHub web editor and merge a PR without ever cloning the repo.
- Embedded SPL is stored inside `` ```spl `` fences, which GitHub renders natively and which are trivial to extract with a regex.
- `git blame` is meaningful for every field of every UC.
- The three generated JSON files (`catalog.json`, `api/index.json`, `api/cat-N.json`) stay in lock-step because they share the single parser invocation.

**Negative:**

- The parser in [`build.py:parse_category_file()`](../../build.py) is hand-written and must be re-verified every time we add a field. Mitigation: `audit_uc_structure.py` enforces the expected shape and catches drift.
- A malformed UC (e.g. a missing `- **SPL:**` line before a fenced block) silently produces an incomplete JSON record. Mitigation: the structure audit runs on every PR.
- Cannot express relationships like "this UC supersedes UC-X.Y.Z" without a new field. Mitigation: add a new optional field; the parser is extensible.

## Alternatives considered

- **YAML front-matter + markdown body.** Rejected: YAML is picky about indentation, and a multi-line SPL block inside a YAML string requires escaping that is hostile to authors.
- **Single `catalog.yaml`.** Rejected: one file with 6,300 entries is unreviewable. Sharded YAML has the same indentation trap.
- **SQLite database with a web admin UI.** Rejected: introduces a back-end; forks would need to stand up infrastructure; diffs are opaque.
- **Spreadsheet (Google Sheets, Airtable).** Rejected: lives outside the repo, not versioned, not reviewable as code.

## Links

- Implementation: [`build.py:parse_category_file()`](../../build.py)
- Validation: [`scripts/audit_uc_structure.py`](../../scripts/audit_uc_structure.py)
- Field taxonomy: [docs/use-case-fields.md](../use-case-fields.md)
- Superseded by: —
