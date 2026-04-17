# Architecture Decision Records

This directory contains the Architecture Decision Records (ADRs) for this project. ADRs are short documents that capture a significant architectural decision along with its context and consequences.

## What is an ADR?

An Architecture Decision Record is a lightweight way to record the decisions made on a project. It captures:

- The context that forced the decision.
- The decision itself.
- The consequences (positive and negative).
- Alternatives considered.

We use the [MADR 3.0](https://adr.github.io/madr/) template (simplified).

## Index

| ID | Title | Status |
|---|---|---|
| [ADR-0001](0001-markdown-as-source-of-truth.md) | Markdown as source of truth for UC content | Accepted |
| [ADR-0002](0002-static-single-page-app.md) | Static single-page app with no back-end | Accepted |
| [ADR-0003](0003-single-catalog-json-plus-per-category-api.md) | Emit both a single `catalog.json` and per-category `api/cat-N.json` | Accepted |
| [ADR-0004](0004-python-stdlib-only.md) | Python stdlib only for build and audits | Accepted |
| [ADR-0005](0005-uc-id-x-y-z-scheme.md) | Three-part numeric UC ID with gap-free ordering | Accepted |
| [ADR-0006](0006-single-file-design-doc.md) | Single-file DESIGN.md, split by section only if a section exceeds ~1,500 words | Accepted |

## When to write an ADR

Write an ADR when you are about to make a decision that:

- Changes the shape of a public artefact (catalog, API, file layout).
- Adds a new cross-cutting invariant (e.g. a new required field on every UC).
- Reverses a previous decision.
- Introduces a new runtime or build dependency.

Do **not** write an ADR for implementation details that are trivially reversible (a function signature, a variable name, a CI step name).

## How to write an ADR

1. Copy the file `0000-template.md` (create if missing).
2. Number it sequentially: `NNNN-short-slug.md`.
3. Fill in **Context**, **Decision**, **Consequences**, **Alternatives considered**, and **Links**.
4. Link back to the ADR from [docs/DESIGN.md §15](../DESIGN.md#15-decision-log).
5. Open a pull request. Mark the ADR `Proposed` until a maintainer accepts it; on merge, update the status to `Accepted`.

## Lifecycle

An ADR status follows this graph:

```
Proposed → Accepted → (optional) Deprecated → (optional) Superseded by ADR-NNNN
```

Do not delete ADRs, even when superseded. History is the point.
