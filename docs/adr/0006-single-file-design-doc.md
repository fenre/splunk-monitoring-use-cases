# ADR-0006: Single-file DESIGN.md, split by section only if a section exceeds ~1,500 words

- **Status:** Accepted
- **Date:** 2026-04-16
- **Deciders:** Repository maintainers

## Context

Phase 0 of the Enterprise Gold Standard Roadmap mandates a product design document that (a) formalises the decisions already embedded in code, (b) lets anyone fork the product for another platform, and (c) forms the canonical reference that the three subsequent releases execute against.

We had two structural options: a single `docs/DESIGN.md` (one file the reader opens, scrolls, and can `Ctrl-F`) versus a split `docs/design/NN-*.md` tree (one file per section, a table of contents, and cross-links).

Replicators have repeatedly told us the most valuable thing a design doc can do is "let me read it cover-to-cover in an hour." That pushes toward a single file.

## Decision

**Keep `docs/DESIGN.md` as a single file.** Split a section into its own file under `docs/design/` **only when that specific section grows past approximately 1,500 words**, and keep `DESIGN.md` as the navigator (table of contents + one-paragraph summary per section) once any split happens.

## Consequences

**Positive:**

- One file to read, one file to search, one file to fork.
- Cross-references between sections are plain `#anchor` links that always work; no relative path juggling.
- The whole document is under one `git log` history.
- Easier for AI agents to ingest as a single context window.

**Negative:**

- The file is long (~5,000 words today). Mitigation: prominent table of contents at the top; use of mermaid diagrams to compress dense topology information.
- When the doc grows, two people editing different sections may conflict. Mitigation: rare; merges are usually trivial; rely on per-section PRs to avoid it.

## Alternatives considered

- **Split per-section from day one under `docs/design/01-purpose.md`, `02-goals.md`, …** Rejected: premature fragmentation; the sections are co-dependent and read better in one flow.
- **Single file with no internal split rule.** Rejected: risks a 40k-word monolith over time; the ~1,500-word trigger gives a mechanical split signal.
- **Wiki-style (GitHub Wiki).** Rejected: not versioned with the repo; not reviewable in PR; diverges from code.

## When to reconsider

When a single section exceeds ~1,500 words OR when the file exceeds ~15,000 words in total, split and update this ADR to "Superseded by ADR-NNNN". The replacement ADR documents the post-split structure.

## Links

- Implementation: [docs/DESIGN.md](../DESIGN.md)
- Freshness audit (planned): [`scripts/audit_design_doc_freshness.py`](../../scripts/audit_design_doc_freshness.py)
- Superseded by: —
