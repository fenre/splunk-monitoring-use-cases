# ADR-0005: Three-part numeric UC ID with gap-free ordering

- **Status:** Accepted
- **Date:** 2023-03-15 (ratified retroactively 2026-04-16)
- **Deciders:** Repository maintainers

## Context

The catalog is referenced from:

- Pull-request discussion threads.
- Release notes (CHANGELOG + `index.html`).
- The non-technical executive view (`non-technical-view.js`).
- External consumers (`api/cat-N.json`, `llms-full.txt`).
- Dashboard deep-links (`#uc-X.Y.Z`).
- Internal Splunk apps built from `savedsearches.conf`, where stanza names are derived from the UC ID.

The identifier therefore needs to be:

- **Stable** under renames of the title or refactors of the SPL.
- **Opaque** (convey no semantic meaning that can become wrong).
- **Hierarchical** so a reader can see "this is cat-10, subcategory 3, UC 7" at a glance.
- **Compact** enough to fit in URL fragments and conf stanza names.
- **Sortable** to produce deterministic "latest N" and "first N" listings.

## Decision

**Every use case carries a three-part numeric identifier `UC-X.Y.Z`:**

- `X` — category ID (integer, `1..N`).
- `Y` — subcategory ordinal within the category (integer, starting at 1).
- `Z` — use-case ordinal within the subcategory (integer, starting at 1, **gap-free**).

Two rules are enforced by [`scripts/audit_uc_ids.py`](../../scripts/audit_uc_ids.py):

1. **Uniqueness.** No two UCs anywhere in the repo share an ID.
2. **Gap-free ordering.** Within a subcategory, `Z` values are `1, 2, 3, ...` with no gaps. When a UC is deleted, all following UCs in the same subcategory are renumbered in the same PR.

The `UC-` prefix is present in human-readable contexts (markdown headings, release notes, dashboard badges) and dropped in machine-readable contexts (JSON keys, URL fragments).

## Consequences

**Positive:**

- A reader can parse the location of a UC from its ID alone.
- Deep-links are stable across renames; only the hash target changes if the UC moves to a new subcategory.
- `savedsearches.conf` stanzas generated from UC IDs are legal conf keys after `.` → `_` replacement.
- The gap-free rule lets consumers page through "all UCs in cat 10.3" as a simple `for Z in 1..N` loop with a known N.
- Sorting UCs by ID yields the same order as the source markdown.

**Negative:**

- Deleting a UC is a renumbering PR that touches every subsequent UC in the subcategory, creating churn in unrelated fields (cross-refs in CHANGELOG, non-technical-view, dashboard test data).
  - Mitigation: renumber PRs are mechanical; `audit_changelog_uc_refs.py` and `audit_non_technical_sync.py` flag all the references that need updating.
- The ID encodes the current location; moving a UC between subcategories changes its ID, which breaks any external link using the old ID.
  - Mitigation: historical release-notes entries in `CHANGELOG.md` keep the original ID; consumers are expected to consult the changelog for rename trails.
- Third parties citing a UC permanently need to track a UC ID that may be renumbered. 
  - Mitigation: we will expose a permanent `uuid` alongside the positional ID in a future version if this becomes a real pain point. **Not in v5.x.**

## Alternatives considered

- **UUIDs.** Rejected: no hierarchy, no human readability.
- **Slug IDs (`uc/cisco-firewall-failed-logon`).** Rejected: unstable under renames; slug collisions are a real operational problem.
- **Category slug + ordinal (`sec.03.07`).** Rejected: verbose; renumbering hurts just as much; sorting requires parsing.
- **Allow gaps after deletion.** Rejected: gaps look like an error, and consumers coded to "count UCs by iterating Z=1..N" silently under-count. The audit makes the invariant explicit.

## Links

- Implementation: [`build.py:parse_category_file()`](../../build.py)
- Enforcement: [`scripts/audit_uc_ids.py`](../../scripts/audit_uc_ids.py)
- Cross-ref tracking: [`scripts/audit_changelog_uc_refs.py`](../../scripts/audit_changelog_uc_refs.py), [`scripts/audit_non_technical_sync.py`](../../scripts/audit_non_technical_sync.py)
- Superseded by: —
