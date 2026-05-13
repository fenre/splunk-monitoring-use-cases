# ADR-0012: `sample-data/` canonical shape is the top-level `positive` / `negative` array

- **Status:** Accepted
- **Date:** 2026-05-13
- **Deciders:** Repository maintainers
- **Closes plan finding:** F22 follow-on — the schema-shape rationalisation
  deferred from [ADR-0010](0010-sample-and-sample-data-co-exist.md)

## Context

[ADR-0010](0010-sample-and-sample-data-co-exist.md) (2026-05-13)
ratified that `samples/` and `sample-data/` stay as two distinct trees
with distinct purposes:

- `samples/UC-X.Y.Z/` — raw-event SPL fixtures (`manifest.yaml` +
  `positive.log` + optional `negative.log`) consumed by
  `audit-sandbox-validation`'s SPL harness and the `uc-tests.yml`
  workflow.
- `sample-data/uc-<id>-fixture.json` — compliance-control evidence
  fixtures referenced by `controlTest.fixtureRef` on
  `content/cat-22-*/UC-*.json` sidecars.

ADR-0010 explicitly **deferred** the question of which JSON shape
`sample-data/` should standardise on. At HEAD `8cbfe0600`
(2026-05-13) three shapes co-exist inside `sample-data/`:

| Shape       | Top-level keys                                      | Files | Populated? |
|-------------|-----------------------------------------------------|------:|------------|
| **phase3**  | `positive` / `negative` (arrays of evidence objects) |    57 | all 57 populated |
| **phase2**  | `events_positive` / `events_negative` (arrays)       |    39 | all 39 empty placeholders (`[]`) with `$comment` |
| **legacy**  | `positiveCase` / `negativeCase` (objects with `events[]`, `expectedFire`, `sourcetype`) | 1 | populated (SPL-event-shaped) |

(Counts produced by walking `sample-data/uc-*-fixture.json` and
classifying via `splunk_uc.audits.sandbox_validation._classify_fixture`
at HEAD `8cbfe0600`.)

The audit `splunk_uc.audits.sandbox_validation` accepts all three
shapes today — it counts items in the positive/negative arrays and
classifies the file as `populated` / `half-empty` / `empty` /
`missing` / `bad-json` / `malformed`. It does **not** inspect the
semantic content of each item.

163 UC sidecars under `content/cat-22-regulatory-compliance/UC-*.json`
carry a `controlTest.fixtureRef` pointer, so the choice of canonical
shape affects every cat-22 author going forward.

## Decision

The canonical shape for `sample-data/uc-<id>-fixture.json` is the
**phase3** shape: a top-level JSON object with two array fields,
`positive` and `negative`, each containing evidence-attestation
records. Optional metadata fields (`uc_id`, `description`, `$comment`)
are permitted at the top level.

Authoring template:

```json
{
  "$comment": "Optional human-readable note about the fixture's purpose.",
  "uc": "UC-X.Y.Z",
  "description": "Optional plain-language summary of what the fixture demonstrates.",
  "positive": [
    {
      "evidence_id": "ev-<uc-id>-positive",
      "owner": "<role or team>",
      "status": "complete | gap"
    }
  ],
  "negative": [
    {
      "evidence_id": "ev-<uc-id>-negative",
      "owner": "<role or team>",
      "status": "complete | gap"
    }
  ]
}
```

The required structural invariants are:

1. Top-level JSON value is an object (never an array, never `null`).
2. The object contains both `positive` and `negative` keys.
3. Both `positive` and `negative` are arrays (possibly empty).
4. Each item in either array is an object (semantic content is the
   author's responsibility; the audit does not enforce a record
   schema today).

The previously-accepted phase2 (`events_positive` / `events_negative`)
and phase-legacy (`positiveCase` / `negativeCase`) shapes are
**deprecated**. They remain readable by the audit during the
migration window so cat-22 PR throughput is not blocked, but no new
fixture may be authored in either shape.

### Why phase3

1. **Plurality and trend.** 57 of 97 fixtures (59%) are already in
   the phase3 shape, and every phase3 file is populated with real
   data. The phase3 shape was introduced by the NIS2<sup class="ref">[<a href="#ref-1">1</a>]</sup> gold-standard
   uplift and is the shape every newer fixture has settled on.
2. **Semantic fit for the compliance-evidence purpose.** Per
   ADR-0010, `sample-data/` carries **compliance-control evidence
   fixtures**, not raw Splunk events. The `positive` / `negative`
   wording reads naturally as "evidence that the control fired"
   versus "evidence that the control held" — which is what a
   compliance fixture is for. The phase2 `events_positive` /
   `events_negative` wording is borrowed from the Splunk events
   vocabulary that properly belongs to `samples/`.
3. **Cleanest migration story.** Every phase2 file at HEAD is an
   empty placeholder (`[]` arrays plus `$comment` / `description` /
   `uc_id` metadata). Migrating phase2 → phase3 reduces to renaming
   two keys; no data is lost. Migrating phase3 → either of the
   alternatives would have required rewriting the populated content
   in 57 files.
4. **Audit code path is already first-class.** The phase3 branch in
   `splunk_uc.audits.sandbox_validation._classify_fixture` is named
   `FIXTURE_SHAPE_PHASE3` and is identical structurally to phase2;
   collapsing phase2 into phase3 deletes a code path and a `shape`
   value, not an audit feature.

### What about the lone legacy file (`uc-22.35.1`)

`sample-data/uc-22.35.1-fixture.json` is a `positiveCase` /
`negativeCase` file that carries **raw Splunk-style event streams**
(`sourcetype`, `events[].{_time, event_rate}`, `expectedFire`,
`expectedSourcetype`). On close reading, it is a misclassified
`samples/` artefact that ended up in the wrong tree.

The follow-on PR for this ADR moves the SPL-fixture content to
`samples/UC-22.35.1/manifest.yaml` + `samples/UC-22.35.1/positive.log`
+ `samples/UC-22.35.1/negative.log`, and replaces
`sample-data/uc-22.35.1-fixture.json` with a phase3 evidence fixture
(initially empty placeholders, like the 39 phase2 files). The
`controlTest.fixtureRef` pointer on `content/cat-22-regulatory-compliance/UC-22.35.1.json`
keeps pointing at `sample-data/uc-22.35.1-fixture.json` — only the
file contents change.

## Consequences

### Positive

- One canonical shape. New cat-22 fixtures use phase3; the
  "which shape?" decision is no longer a per-PR judgement call.
- `sample-data/README.md` can describe a single shape with a single
  template. The previously-confusing three-shape table collapses to
  one paragraph plus a deprecation note.
- The audit's three-branch `_classify_fixture` collapses to one
  branch once the migration completes (deferred to the follow-on PR;
  this ADR does not change audit code).
- Re-aligns the project with ADR-0010's intent: `sample-data/` is
  for compliance-evidence records (phase3 vocabulary), `samples/`
  is for raw Splunk events. The lone legacy file's eventual move
  to `samples/UC-22.35.1/` makes the split mechanically consistent.

### Negative

- 39 phase2 files and 1 legacy file are stranded in deprecated
  shapes until the follow-on migration PR. The audit continues to
  read them as `empty` (phase2) or `populated` (legacy) so nothing
  breaks; new fixtures simply may not be authored in those shapes.
- The follow-on migration PR is a touched-files explosion (40 files
  edited in `sample-data/` + ~3 files written to `samples/UC-22.35.1/`).
  That PR is intentionally out of scope for this ADR — keeping the
  decision and the mechanical migration in separate PRs preserves
  reviewability.

### Neutral

- The `controlTest.fixtureRef` field on UC sidecars does not change
  shape, does not change pointer-target convention, and does not
  require any updates in `content/cat-22-*/UC-*.json` as part of
  this ADR or the follow-on migration. All 163 UC sidecars that
  carry `fixtureRef` today keep working.

## Migration plan

This ADR is the decision; the mechanical work is documented but
not performed in the same PR:

1. **Same PR as the ADR (this PR).**
   - Cross-link `sample-data/README.md` to this ADR; rewrite the
     "schema summary" section to declare phase3 canonical and the
     other two shapes deprecated.
   - Flip `docs/health-check-2026-progress.md` §F22 to also cite
     ADR-0012 as the deferred schema-shape rationalisation.
   - Add this ADR to `docs/adr/README.md`'s index.
   - Cite this ADR from `docs/DESIGN.md` §15 (Decision log).
2. **Follow-on PR (~2026-05/06).**
   - Rename `events_positive` → `positive` and `events_negative` →
     `negative` in all 39 phase2 fixtures (`sample-data/uc-22.35.*`
     through `sample-data/uc-22.49.*`). Top-level metadata
     (`$comment`, `uc_id`, `description`) is preserved verbatim.
   - Move the SPL content from `sample-data/uc-22.35.1-fixture.json`
     into a new `samples/UC-22.35.1/` directory using the standard
     `manifest.yaml` + `positive.log` + `negative.log` envelope,
     then replace the original `sample-data/uc-22.35.1-fixture.json`
     with a phase3 evidence fixture (initially empty placeholders).
   - Tighten `splunk_uc.audits.sandbox_validation._classify_fixture`
     to reject phase2 and phase-legacy shapes (the `STATUS_MALFORMED`
     branch absorbs both with a clear migration-pointer error message).
3. **Eventual cleanup (~Q3-2026, opportunistic).**
   - Populate the 39 currently-empty phase3 placeholders with real
     evidence records as the relevant cat-22 SME reviews land. This
     is content authoring, not a structural migration; tracked in
     `docs/health-check-2026-progress.md` §P12 alongside the rest of
     the content-quality moonshot.

## Alternatives considered

A. **Pick phase2 (`events_positive` / `events_negative`).** Rejected
   because (a) every phase2 file at HEAD is empty, so the vocabulary
   has no actual user data to defend, (b) the `events_*` wording
   makes the tree look like a Splunk-events fixture, conflicting
   with ADR-0010's "raw events live in `samples/`" split, and (c) it
   would force a rewrite of all 57 populated phase3 files for no
   semantic gain.

B. **Pick legacy (`positiveCase` / `negativeCase` with `expectedFire` +
   `sourcetype`).** Rejected for the same ADR-0010 reason as (A) —
   the shape is a SPL-fixture shape, not a compliance-evidence
   shape. The single file in this shape today is actually
   misplaced; the right action is to move it to `samples/`, not to
   propagate the shape across the whole tree.

C. **Keep all three shapes; only enforce structural validity.**
   Rejected because the maintainer cost of three near-identical
   shapes is real: each authoring path has its own template, the
   `audit-sandbox-validation` verb has three code paths to parse
   the file, and contributors authoring a new fixture have to guess
   which shape matches the prevailing convention in the surrounding
   UC range. ADR-0010 explicitly flagged this as the next decision
   to make; punting on it now reverses ADR-0010.

D. **Define a fourth, fully-typed canonical shape with a JSON Schema
   declaring `evidence_id` / `owner` / `status` enums.** Deferred.
   The current audit treats every item as opaque, and authoring a
   schema for the inner record will require coordinating with
   `audit_legal_review_signoffs` / `audit_sme_review_signoffs`,
   which already own evidence-record semantics elsewhere in the
   tree. That coordination is out of scope for the
   "phase3-or-phase2-or-legacy" question this ADR settles. A
   follow-on ADR (when the next available number lands) can author
   `schemas/sample-data-fixture.schema.json` if the maintainers
   later decide that structural acceptance is not enough.

## References

- [ADR-0010](0010-sample-and-sample-data-co-exist.md) — establishes
  the `samples/` vs `sample-data/` split that this ADR refines.
- [ADR-0007](0007-json-as-source-of-truth.md) — JSON sidecars are
  the source of truth for UC content; this ADR is a leaf decision
  under that umbrella.
- [ADR-0011](0011-schema-lineage-governance.md) — schema lifecycle
  contract. When the follow-on PR introduces
  `schemas/sample-data-fixture.schema.json` (alternative D), it
  will be governed by ADR-0011.
- [`sample-data/README.md`](../../sample-data/README.md) — refreshed
  by this PR to declare phase3 canonical.
- [`samples/README.md`](../../samples/README.md) — cross-linked from
  this ADR via ADR-0010.
- [`src/splunk_uc/audits/sandbox_validation.py`](../../src/splunk_uc/audits/sandbox_validation.py)
  — `_classify_fixture` is the consumer that defines the three
  shapes today; the follow-on migration PR will tighten it.
- [`docs/health-check-2026-progress.md`](../health-check-2026-progress.md)
  §F22 and §P12 — tracks the migration follow-on.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** European Parliament and Council of the European Union. (2022, December). *Directive (EU) 2022/2555 — NIS2 Directive on cybersecurity*. Official Journal of the European Union, L 333. ELI: dir/2022/2555. https://eur-lex.europa.eu/eli/dir/2022/2555/oj

<a id="ref-2"></a>**[2]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

### Related repository documents

- [`docs/adr/0007-json-as-source-of-truth.md`](0007-json-as-source-of-truth.md)
- [`docs/adr/0010-sample-and-sample-data-co-exist.md`](0010-sample-and-sample-data-co-exist.md)
- [`docs/adr/0011-schema-lineage-governance.md`](0011-schema-lineage-governance.md)

### Cited by

- [`docs/DESIGN.md`](../DESIGN.md)
- [`docs/adr/README.md`](README.md)
- [`docs/health-check-2026-progress.md`](../health-check-2026-progress.md)

<!-- END-AUTOGENERATED-SOURCES -->
