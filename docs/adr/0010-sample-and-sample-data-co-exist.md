# ADR-0010: `samples/` and `sample-data/` are separate, complementary regimes

- **Status:** Accepted
- **Date:** 2026-05-13
- **Deciders:** Repository maintainers
- **Closes plan finding:** F22 — "two parallel sample regimes (95 dirs + 97 files)"

## Context

The repository has two top-level directories whose names imply a
duplicated purpose:

| Path                | Count today | Schema                                                              | Primary consumer                                                                 |
|---------------------|------------:|---------------------------------------------------------------------|----------------------------------------------------------------------------------|
| `samples/UC-X.Y.Z/` | 94 dirs     | `manifest.yaml` + `positive.log` + optional `negative.log`          | `python3 -m splunk_uc audit-sandbox-validation` + `.github/workflows/uc-tests.yml` |
| `sample-data/uc-X.Y-fixture.json` | 97 files | Three observed shapes (see [Schema split](#schema-split) below) | `tests/scripts/test_audit_sandbox_validation.py` + the `controlTest.fixtureRef` field on `content/cat-22-*/UC-*.json` sidecars |

The §P12 line in the repo-overhaul plan called this out as F22:

> "Two parallel sample regimes (95 dirs + 97 files). The §P12 first
> deliverable is the choice itself — pick one."

The plan was correct that the duplication is a real liability, but
the framing **"pick one"** turned out to be wrong on closer
inspection: the two regimes do not in fact contain the same kind of
data. `samples/` is for **operational SPL validation** (does the
search detect what it claims to detect when fed realistic raw events
through Splunk?); `sample-data/` is for **compliance-control evidence
fixtures** (does the catalog item carry an auditor-grade representative
record that proves the control fires?). Both are needed; merging them
into one tree creates one of two failure modes:

1. If we keep the rich Splunk-style `manifest.yaml` format,
   compliance fixtures (~half of which today are aspirational
   placeholders with no live raw events at all) suddenly become
   first-class log-file artefacts that the SPL test harness will try
   to execute. That breaks `uc-tests.yml`.
2. If we keep the JSON evidence-record format, the per-UC raw log
   fixtures lose the `manifest.yaml` envelope that `samples_index.py`
   and the doc-generator chain rely on (timerange / expected counts /
   index/source/sourcetype routing).

So **"pick one"** is not the right call. The right call is to
formalise the split, eliminate the cross-talk between the two trees,
and ratchet down the secondary problem (`sample-data/` carries three
different schema shapes today — that *is* a "pick one" question
inside the compliance regime).

### Schema split inside `sample-data/`

Mining `sample-data/uc-*-fixture.json` at HEAD reveals three
conventions, all using the same `*.json` extension and the same
directory:

| Shape                                       | Approximate count | Where it appears                                  |
|---------------------------------------------|------------------:|---------------------------------------------------|
| Top-level `positive` / `negative` arrays    | ~50               | `uc-22.2.*`, original Phase-4.3 fixtures          |
| Top-level `events_positive` / `events_negative` (often `[]` placeholders with a `$comment`) | ~30               | `uc-22.35.*` – `uc-22.49.*` (cross-cutting families) |
| Nested `positiveCase` / `negativeCase` with synthetic event streams | ~17               | Mixed across newer cat-22 entries                 |

The maintainer cost of three near-identical shapes is real: each
authoring path has its own template, the `audit-sandbox-validation`
verb has three code paths to parse the file, and contributors
authoring a new fixture have to guess which shape matches the
prevailing convention in the surrounding UC range.

### Why now

The plan §P12 acceptance criterion treats "pick one" as a single PR
delivering nothing but the decision; the actual code migration is
treated as follow-on work. This ADR is that decision PR.

## Decision

The repository **retains both `samples/` and `sample-data/`** as
distinct, complementary regimes. The next ADR / PR (not this one)
collapses the three `sample-data/` schema shapes into one canonical
shape.

Concretely:

1. **`samples/UC-X.Y.Z/`** is the canonical location for **raw event
   fixtures used in SPL validation**. Its envelope is
   `manifest.yaml`, its events live in `positive.log` (mandatory)
   and `negative.log` (optional). `_schema/sample-manifest.schema.json`
   is the schema of record for the envelope.

   - Owned consumer: `python3 -m splunk_uc audit-sandbox-validation`
     plus the `uc-tests.yml` workflow that exercises the harness
     against a live Splunk instance.
   - Naming: directories are named **exactly** `UC-<full-id>`. No
     loose JSON files at the `samples/` root other than `README.md`
     and the `_schema/` directory.

2. **`sample-data/`** is the canonical location for **compliance-
   control evidence fixtures** referenced by the
   `controlTest.fixtureRef` field on `content/cat-22-*/UC-*.json`
   sidecars. Its envelope is a single `*.json` file, the file shape
   is the one ratified by the follow-on ADR (see [Consequences](#consequences)),
   and the file name pattern is `uc-<id>-fixture.json`.

   - Owned consumer: `python3 -m splunk_uc audit-sandbox-validation`
     for `fixtureRef` integrity, plus the compliance-coverage
     auditor that surfaces "evidence missing" gaps.

3. **Cross-tree references are forbidden.** A UC sidecar that needs
   both kinds of fixture carries two pointers: `controlTest.fixtureRef`
   pointing into `sample-data/`, plus an implicit `samples/UC-<id>/`
   pickup for the SPL harness. Neither tree may name the other.

4. **The auditor enforces the split.** `python3 -m splunk_uc
   audit-sandbox-validation` rejects (a) a `controlTest.fixtureRef`
   that points into `samples/`, (b) a `samples/UC-<id>/manifest.yaml`
   that names a file in `sample-data/`, and (c) a JSON file in
   `samples/` outside the `_schema/` envelope.

5. **The two READMEs cross-link.** Each tree's `README.md` opens
   with a one-sentence pointer to the other tree, so a future
   contributor cannot guess "the wrong" tree just by reading the
   first README they land on. This ADR is cited from both READMEs as
   the rationale.

## Consequences

### Positive

- The `samples/` SPL-validation regime stays untouched, which means
  `uc-tests.yml`, `scripts/run_uc_tests.py`, `samples_index.py`, and
  the doc-generator chain (`generate_backlinks.py`,
  `generate_doc_references.py`, `generate_md_from_json.py`) keep
  working without migration risk.
- Compliance fixtures get a clear single home and a clear single
  consumer, removing the "which directory should this fixture go
  in?" decision from every cat-22 PR.
- A future contributor reading either `samples/README.md` or
  `sample-data/README.md` is told **immediately and explicitly**
  that the other tree exists and what it is for, eliminating the
  current accidental-duplication risk.
- The split is **mechanically enforceable**: the audit verb above
  hard-fails CI on any cross-tree path reference. The two regimes
  cannot drift toward overlap without breaking the build.

### Negative

- The repository keeps **two** sample-related top-level directories
  forever (not one). The plan's original "pick one" simplicity goal
  is not met. The mitigation is the audit-enforced split + the
  cross-linked READMEs.
- A new contributor must still understand that fixtures for SPL
  validation and fixtures for control-evidence are different things.
  ADR-0010 is the single document that explains that — both READMEs
  cite it explicitly to keep that understanding discoverable.
- The schema-shape rationalisation inside `sample-data/` is **not**
  done by this ADR; it is deferred to a follow-on ADR (Q3-2026
  target). The three shapes co-exist until then. Authors of new
  fixtures should prefer the top-level `positive` / `negative` shape
  because it has the broadest consumer support today, but the audit
  does not currently reject the other two shapes. (When ADR-0010 was
  authored, that follow-on was tentatively numbered ADR-0011;
  ADR-0011 has since been used for the schema lineage governance
  ratification — see ADR-0011 §"Alternatives considered" point C.
  The follow-on will take the next available number when authored.)

### Neutral

- `controlTest.fixtureRef` continues to point into `sample-data/`.
  A non-trivial fraction of these references today point at files
  that do not exist on disk (see `sample-data/README.md` — these
  are intentional "evidence promises" that surface as
  `compliance-coverage` audit gaps). This ADR does not change that
  posture; it formalises that the missing-file case is a known
  gap-state, not a parse error.

## Migration plan

This ADR is the decision; the mechanical work is documented but not
performed in the same PR:

1. **Same PR as the ADR (this PR).** Cross-link both READMEs to
   this ADR; flip `docs/health-check-2026-progress.md` §F22 from
   `NOT DONE` to `DONE` (with the migration-plan caveat); add the
   ADR to `docs/adr/README.md`'s index.
2. **Follow-on PR (~Q3-2026).** Choose between the three
   `sample-data/` shapes. Most likely outcome: the top-level
   `positive` / `negative` shape is ratified; the
   `events_positive` / `events_negative` and `positiveCase` /
   `negativeCase` shapes are migrated to the canonical shape. The
   follow-on ADR will take the next available number when it is
   authored (ADR-0011 has since been used for schema lineage
   governance).
3. **Follow-on PR (~Q4-2026).** Extend
   `python3 -m splunk_uc audit-sandbox-validation` with the
   cross-tree-reference guard so the split is enforced in CI, not
   just in this ADR. (The guard is mechanically simple — match the
   path prefix of any `fixtureRef` value against `sample-data/`,
   and match the file extension of any `manifest.yaml`-listed event
   file against `samples/UC-<id>/*.log`.)

These follow-ons are tracked in `docs/health-check-2026-progress.md`
under §P12.

## References

- F22 in [`/Users/fsudmann/.cursor/plans/repo_health_and_architecture_overhaul_b0cd1852.plan.md`](../../docs/health-check-2026-progress.md)
- [`samples/README.md`](../../samples/README.md) — current SPL-fixture envelope description
- [`sample-data/README.md`](../../sample-data/README.md) — current compliance-fixture envelope description and the three-shapes inventory
- [`schemas/uc.schema.json`](../../schemas/uc.schema.json) — declares the `controlTest.fixtureRef` field referenced by this ADR
- [`samples/_schema/sample-manifest.schema.json`](../../samples/_schema/sample-manifest.schema.json) — `samples/UC-X.Y.Z/manifest.yaml` envelope schema
- [`docs/health-check-2026-progress.md`](../health-check-2026-progress.md) §F22, §P12
- [ADR-0007](0007-json-as-source-of-truth.md) — establishes JSON sidecars as the source of truth for UC content; this ADR is a leaf decision under that umbrella
- [ADR-0009](0009-generated-artefact-policy.md) — generated artefacts are uncommitted; the two sample regimes are *not* generated artefacts and are therefore committed (this is consistent with ADR-0009).

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

### Related repository documents

- [`docs/adr/0007-json-as-source-of-truth.md`](0007-json-as-source-of-truth.md)
- [`docs/adr/0009-generated-artefact-policy.md`](0009-generated-artefact-policy.md)

### Cited by

- [`docs/DESIGN.md`](../DESIGN.md)
- [`docs/adr/README.md`](README.md)
- [`docs/health-check-2026-progress.md`](../health-check-2026-progress.md)
- [`samples/README.md`](../../samples/README.md)

<!-- END-AUTOGENERATED-SOURCES -->
