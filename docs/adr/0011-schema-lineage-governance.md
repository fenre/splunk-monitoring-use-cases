# ADR-0011: Schema lineage governance — ratify the lifecycle contract

- **Status:** Accepted
- **Date:** 2026-05-13
- **Deciders:** Repository maintainers
- **Closes plan finding:** F23 — "12+ schemas, no governance plan"

## Context

The repository ships **18** JSON Schemas (plus one non-schema authoring
profile, `schemas/uc-profile-gold.json`, and one vendored upstream
fragment, `schemas/oscal/v1.1.1/`):

| Path                                              | x-stability | x-since | Validated artefact / consumer                                  |
|---------------------------------------------------|-------------|---------|----------------------------------------------------------------|
| `schemas/uc.schema.json`                          | stable      | v6.0    | `content/cat-*/UC-*.json` (the authoring source of truth)      |
| `schemas/category.schema.json`                    | stable      | v7.3    | `content/cat-*/​_category.json`                                  |
| `schemas/mapping-ledger.schema.json`              | stable      | v6.0    | `data/mapping-ledger.json`                                     |
| `schemas/regulations-watch.schema.json`           | stable      | v6.0    | `data/regulations-watch.json` (nightly diff)                   |
| `schemas/per-regulation-phase3.2.schema.json`     | stable      | v6.0    | `data/regulations/*.json` Phase-3.2 metadata                   |
| `schemas/evidence-pack-extras.schema.json`        | stable      | v6.0    | `data/evidence-pack-extras.json`                               |
| `schemas/legal-review-signoff.schema.json`        | stable      | v6.0    | `data/provenance/legal-signoffs.json`                          |
| `schemas/sme-review-signoff.schema.json`          | stable      | v6.0    | `data/provenance/sme-signoffs.json`                            |
| `schemas/peer-review-signoff.schema.json`         | stable      | v6.0    | `data/provenance/peer-signoffs.json`                           |
| `schemas/baselines.schema.json`                   | preview     | v8.0    | `data/baselines/v<VERSION>.json`                               |
| `schemas/coverage-baseline.schema.json`           | preview     | v8.0    | `data/coverage-baseline.json`                                  |
| `schemas/license-inventory.schema.json`           | preview     | v8.0    | `data/license-inventory.json`                                  |
| `schemas/v2/catalog-index.schema.json`            | preview     | v7.0    | `dist/api/v2/catalog-index.json`                               |
| `schemas/v2/search-index.schema.json`             | preview     | v7.0    | `dist/api/v2/search-index.json`                                |
| `schemas/v2/metrics.schema.json`                  | stable      | v8.0    | `dist/metrics.json`                                            |
| `schemas/v2/metrics-history-index.schema.json`    | stable      | v8.0    | `data/metrics-history/index.json`                              |
| `schemas/v2/stewardship-digest.schema.json`       | stable      | v8.1    | `dist/stewardship-digest.{json,md}`                            |
| `schemas/v2/build-telemetry.schema.json`          | stable      | v8.0    | `dist/build-telemetry.json` (non-reproducible builds only)     |

The original plan finding F23 read **"12+ schemas, no governance plan"**.
A read of HEAD at commit `f65e4ee67` (2026-05-13) shows that the lower
bound is now 18, and the "no governance plan" half of the finding is
substantially out of date:

| Governance asset                                             | Status at HEAD                                                                                   |
|--------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| Per-schema lifecycle contract (`docs/schema-versioning.md`)  | Authored at v7.0.0. Defines required metadata keywords, stability levels, semver rules, breaking-change table, distribution plan, lifecycle stages. |
| Per-schema CHANGELOG                                         | 18/18 schemas have an entry under `schemas/changelogs/<slug>.md`.                                |
| Required schema metadata (`$schema`, `$id`, `version`, `x-stability`, `x-since`, `x-changelog`) | 18/18 schemas declare all six. Verified by `tools/audits/schema_meta.py` (live in CI). |
| Breaking-change detector                                     | `tools/audits/schema_diff.py` runs in CI against the most recent `v*` git tag (validate.yml lines 404-413). |
| Migration plan template                                      | Documented in `docs/schema-versioning.md` §Migration guides + §Lifecycle of a schema major.      |

The only thing missing was a visible **decision record** ratifying the
contract. Without an ADR, the governance was a contract document that
could be changed by any PR without an explicit decision trail. F23 was
not "we don't have governance"; F23 was "the governance is not
ratified."

This ADR is that ratification.

### What the audit found that is **not** yet right

Three drift items surfaced while gathering evidence for this ADR. None
of them block ratification; all are tracked here as known issues and as
the follow-on plan in [Consequences](#consequences):

1. **Inventory drift in the contract doc.** `docs/schema-versioning.md`
   §"Where schemas live" lists 11 schemas (the v7.0.0 baseline plus a
   `v2/` placeholder). The actual count is 18. Same section's planned
   list (`stewardship-digest`, `metrics`, `metrics-history-index`,
   `build-telemetry`) is now committed but still labelled "planned"; the
   "planned" `tools/audits/schema_meta.py` is live, has been since v7.4.
2. **`$id` host-name inconsistency.** The schemas were authored across
   five different ownership eras and disagree on the canonical hostname:
   `fenre.github.io` (most pre-v8 entries), `github.com/fenre/` (three
   `preview`s under `data/`), `splunk-monitoring-use-cases.github.io`
   (`evidence-pack-extras`), `github.com/fsudmann/` (typo on
   `regulations-watch` — wrong user), `splunk-monitoring.io` (the
   aspirational future-org domain on every `v2/` entry), and one missing
   `.github.io` suffix (`metrics-history-index`). The drift is
   contained — every `$id` is a syntactically valid URL — but consumers
   who use `$id` to dereference the schema will hit five different
   origins and one 404. The fix is mechanical and is folded into the
   follow-on plan below.
3. **`uc-profile-gold.json` is not a schema.** It lives next to the
   schemas, has no `$schema` keyword, and is a **profile** (a curated
   subset of `uc.schema.json`'s constraints used to tier UCs into
   Gold / Silver / Bronze). `schema_meta.py` correctly ignores it
   because the audit globs `*.schema.json`, not `*.json`. Calling that
   out here so a future maintainer does not think it is missing
   metadata.

## Decision

The maintainers ratify `docs/schema-versioning.md` as the canonical
lifecycle contract for every JSON Schema in the repository, with the
following three reinforcements:

1. **The contract is now ADR-backed.** Any change to the lifecycle
   contract (stability levels, semver bump rules, the breaking-change
   table, the migration window, the `$id` policy) ships as a new ADR
   that supersedes this one. The contract document continues to be the
   operational manual; the ADR is the load-bearing decision.

2. **The two CI audits are non-negotiable gates.** Both
   `tools/audits/schema_meta.py` (every schema declares the six
   required keywords) and `tools/audits/schema_diff.py` (breaking
   changes require a major bump and a fresh `$id` on stable schemas)
   stay wired into `.github/workflows/validate.yml`. Removing or
   relaxing either gate requires a new ADR.

3. **Every new schema is an ADR-worthy addition by default.** Adding
   a new schema under `schemas/` is one of the four
   "decision-worthy" events listed in `docs/adr/README.md` §"When to
   write an ADR" — it adds a public artefact contract. ADRs for new
   schemas can be short (decision + consequences); the point is to
   force authors to ask the questions the contract requires:
   * What is the artefact this schema validates?
   * Who is the owned consumer?
   * Stability tier on day one (`preview` while iterating;
     `stable` only when consumers commit to the additive-only rule)?
   * What is the migration plan if v1 ever becomes incompatible?

   Tiny schema additions that are clearly internal-only (e.g., a new
   `data/coverage-baseline.schema.json`) can be batched into a single
   "infrastructure schemas" ADR rather than one ADR per file — but the
   decision still has to be visible.

## Consequences

### Positive

- F23 is closed: the governance plan exists, is ratified, and has CI
  enforcement. The decision trail is visible in this ADR and in the
  per-schema changelogs.
- New schemas cannot land silently. The combination of `schema_meta.py`
  (metadata enforced) + ADR-as-default-for-new-schemas + the
  per-schema changelog requirement means a future contributor who
  drops a new file under `schemas/` gets three independent reminders to
  document their decision before merge.
- Breaking changes to `stable` schemas cannot land silently. The
  `schema_diff.py` gate catches them on every PR; the major-bump +
  fresh-`$id` requirement keeps the v1 schemas online for the 12-month
  parallel-support window per `docs/api-versioning.md`.
- The contract is now portable. The combination of this ADR + the
  contract doc + the two audits + the per-schema changelogs is a
  complete answer to "how do schemas evolve here?" — a question
  external consumers (SIEM vendors, MCP servers, OSCAL validators) are
  entitled to ask.

### Negative

- One more ADR to keep current. The mitigation is that this ADR is
  intentionally short and points at the contract doc for the
  operational detail; only the **decision** lives here.
- The contract doc (`docs/schema-versioning.md`) and this ADR can
  drift if a maintainer updates one without the other. The mitigation
  is the same as for every other ADR-backed doc: the contract doc's
  "Status" line cites this ADR explicitly, and the doc-references
  generator will surface any rename or path move in the backlinks
  index.

### Neutral

- The contract continues to be `preview`-by-default for new schemas
  and `stable`-only-on-commitment. That is the existing policy; this
  ADR does not change it.

## Migration plan

This ADR is the decision; mechanical follow-ups are documented here
but not all performed in this PR. Three of them land in this PR for
discoverability; the rest are tracked as known follow-on items in
`docs/health-check-2026-progress.md` §F23 (now `DONE` with caveat).

**In this PR**

1. The ADR itself, with the full inventory table above.
2. Inventory refresh in `docs/schema-versioning.md` §"Where schemas
   live" — drop the "planned" labels for the four `v2/` schemas that
   are now committed and live, mark `schema_meta.py` and
   `schema_diff.py` as live (they are), and add the six schemas not
   on the v7.0.0 inventory (`baselines`, `coverage-baseline`,
   `license-inventory`, `build-telemetry`, `metrics`,
   `metrics-history-index`, `stewardship-digest`). Status line at the
   top of `schema-versioning.md` cites ADR-0011.
3. Index entry in `docs/adr/README.md` for ADR-0011.

**Follow-on (tracked, not in this PR)**

4. `$id` rationalisation. Settle on a single canonical hostname (most
   likely `https://splunk-monitoring.io/schemas/v{N}/...` when the
   project owns that domain, or `https://fenre.github.io/...` as the
   transitional default while the v8 series is current). A new ADR
   accompanies the change because moving a `$id` is a breaking event
   for any consumer that dereferences. Until the rationalisation
   ships, the existing URLs continue to work because the schemas are
   served from GitHub Pages at multiple paths.
5. `regulations-watch.schema.json` `$id` typo fix (`fsudmann` →
   `fenre`). Patch bump only; the schema content is unchanged.
6. `metrics-history-index.schema.json` `$id` typo fix (missing
   `.github.io`). Patch bump.
7. Type-generator outputs (`dist/schemas/v{N}/types.d.ts` and
   `types.py`) are listed under §Tooling-friendly outputs in
   `schema-versioning.md` but not yet emitted by the build. They are
   not a F23 close criterion and remain on the §P14 / §P15 backlog.

## Alternatives considered

### A. Don't write an ADR; the contract doc is already enough

Rejected. `docs/schema-versioning.md` is a manual, not a decision.
The plan-level finding F23 names "no governance plan" as the issue;
the absence of a ratified decision is half of that finding. Writing
the ADR closes F23 without changing the contract content (which is
already correct).

### B. Promote `docs/schema-versioning.md` to ADR-0011

Rejected. ADRs are short, dated decisions. The schema-versioning doc
is a 300+-line operational manual that needs to evolve faster than
ADRs are appropriate for — additions to the breaking-change table,
new distribution channels, new schema metadata keywords, etc. The
clean separation is: ADR is the decision (this file); manual is the
how-to (`schema-versioning.md`).

### C. Pre-allocate ADR slots for the promised follow-ups in ADR-0010

ADR-0010's migration plan named "ADR-0011 (~Q3-2026)" for sample-data
shape rationalisation and "ADR-0012 (~Q4-2026)" for the cross-tree
fixture guard. Both of those decisions are still un-authored. We use
ADR-0011 here for schema lineage because ADRs are numbered by
acceptance date, not by reservation. ADR-0010's two future-ADR
references are now placeholders — when those ADRs are written, they
take the **next** available numbers. ADR-0010 was updated in the
same PR to remove the hard-coded numbers.

### D. Wait until ADR-0012 / ADR-0013 are written so the numbering is "clean"

Rejected because F23 has been open for two months and the governance
is already in place. Holding the ADR for an unrelated scheduling
question optimises for the wrong thing.

## References

- F23 in `/Users/fsudmann/.cursor/plans/repo_health_and_architecture_overhaul_b0cd1852.plan.md`
- [`docs/schema-versioning.md`](../schema-versioning.md) — the lifecycle contract this ADR ratifies
- [`docs/api-versioning.md`](../api-versioning.md) — the 12-month parallel-major support window
- [`tools/audits/schema_meta.py`](../../tools/audits/schema_meta.py) — required-metadata gate (live in `.github/workflows/validate.yml` line 137)
- [`tools/audits/schema_diff.py`](../../tools/audits/schema_diff.py) — breaking-change gate (live in `.github/workflows/validate.yml` line 413)
- [`schemas/changelogs/`](../../schemas/changelogs/) — per-schema lifecycle log directory (18 changelogs at HEAD)
- [`docs/health-check-2026-progress.md`](../health-check-2026-progress.md) §F23, §P3 — open finding and the surrounding phase
- [ADR-0007](0007-json-as-source-of-truth.md) — JSON sidecars as source of truth; this ADR is a leaf decision under that umbrella
- [ADR-0008](0008-canonical-constants.md) — every constant has exactly one home; the schemas in this ADR are one such canonical home
- [ADR-0009](0009-generated-artefact-policy.md) — schema-validated `dist/` artefacts are generated; the schemas themselves are committed

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Related repository documents

- [`docs/adr/0007-json-as-source-of-truth.md`](0007-json-as-source-of-truth.md)
- [`docs/adr/0008-canonical-constants.md`](0008-canonical-constants.md)
- [`docs/adr/0009-generated-artefact-policy.md`](0009-generated-artefact-policy.md)

### Cited by

- [`docs/DESIGN.md`](../DESIGN.md)
- [`docs/adr/README.md`](README.md)
- [`docs/health-check-2026-progress.md`](../health-check-2026-progress.md)
- [`docs/schema-versioning.md`](../schema-versioning.md)

<!-- END-AUTOGENERATED-SOURCES -->
