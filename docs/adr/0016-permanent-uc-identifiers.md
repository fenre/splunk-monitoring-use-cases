# ADR-0016: Permanent UC identifiers with append-only ledger

- **Status:** Accepted
- **Date:** 2026-09-01
- **Deciders:** Repository maintainers
- **Supersedes:** [ADR-0005](0005-uc-id-x-y-z-scheme.md) (gap-free ordering and renumber-on-delete)

## Context

The catalogue exposes `UC-X.Y.Z` identifiers across static HTML, `api/v1/`,
MCP tools, `.spl` packages, and downstream starter-set consumers. External
systems now treat these identifiers as **load-bearing references**.

Investigation (2026-09-01) found:

- **127 identifiers** in category 25 were silently reused for different content
  during the cat-25 subcategory consolidation (`68c7451a9`, 2026-07-24).
- Recategorisation relocations assign a **new** identifier and leave the old one
  as a permanent gap (e.g. `UC-1.2.14` → `UC-8.1.17`).
- ADR-0005 required gap-free numbering and renumber-on-delete, but CI ran
  `audit-uc-ids --warn-gaps` and tolerated **45** historical gaps.
- `docs/url-scheme.md`, ADR-0005, `docs/DESIGN.md`, and rendered page footers
  contradicted each other on whether IDs are permanent.

The suspected “delete then shift Z down” mechanism **does not occur** in this
repository. The real failure mode is **bulk restructuring**: a single commit
remapping thousands of identifiers with no identity invariant enforced.

## Decision

Adopt this policy everywhere (human docs, ADR, CI, rendered templates):

> **An identifier, once published, permanently refers to one use case. It is
> never reused and never reassigned to different content. Gaps are expected and
> correct.**

Enforcement (catalogue version **8.25.0** onward):

1. **`data/id-ledger.json`** — append-only record of every identifier ever
   issued: `id`, `status` (`active` | `removed`), `firstSeenVersion`,
   `contentFingerprint` (SHA-256 over `title` + `spl`).
2. **`audit-uc-ids`** — hard CI failures for fingerprint mismatch, reuse of a
   removed identifier, or catalogue IDs missing from the ledger. **No gap
   detection.**
3. **`audit-uc-id-migration-blast`** — fail when a PR changes more than **10**
   identifiers unless a committed manifest under `data/uc-id-migrations/`
   lists every change and `identityPreserved` per row.
4. **`data/id-ledger-collisions.json`** — documents 127 pre-guarantee reuse
   events in category 25; not remediated (hidden easter-egg category).

The positional `UC-X.Y.Z` string remains the public identifier for now. Opaque
`uid` decoupling from taxonomy position is deferred to a follow-up ADR/PR.

## Consequences

**Positive:**

- External consumers can rely on IDs not silently changing meaning after v8.25.0.
- Gaps correctly signal retired identifiers (404) instead of wrong content.
- Bulk agent-driven remaps are blocked unless a human-reviewable manifest lands.

**Negative:**

- Legitimate content edits on an active ID require regenerating the ledger
  (`python -m splunk_uc generate-id-ledger`) in the same PR.
- The ledger file is large (~19k rows including historical removals).
- Pre-guarantee collisions in category 25 remain documented but not fixed.

## Alternatives considered

- **Keep gap-free numbering** — rejected; contradicts permanent-identity goal
  and was not enforced in practice.
- **Retroactively fix 127 collisions** — rejected; category 25 has no external
  consumers; documented instead.
- **UUID primary keys in this PR** — deferred; larger schema and API surface
  change.

## Links

- Supersedes: [ADR-0005](0005-uc-id-x-y-z-scheme.md)
- Ledger generator: `src/splunk_uc/generators/id_ledger.py`
- Ledger audit: `src/splunk_uc/audits/uc_ids.py`
- Blast-radius guard: `src/splunk_uc/audits/uc_id_migration_blast.py`
- Known collisions: `data/id-ledger-collisions.json`
- Investigation context: Cloud agent report 2026-09-01
