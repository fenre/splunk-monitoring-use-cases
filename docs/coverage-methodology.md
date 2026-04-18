# Coverage Methodology

Version: 1.1.0 — locked at Phase 1.5c. History: 1.0.0 (Phase 1.5a); 1.1.0
adds § 12 (baseline mechanism) and restates § 6.1 to distinguish
baselineable findings from unconditional blockers.

This document defines, precisely and reproducibly, **how the Splunk
Monitoring Use Cases catalogue measures regulatory coverage**. It is the
contract between:

- the UC authors (who claim coverage in `compliance[]` entries),
- the audit script `scripts/audit_compliance_mappings.py` (which computes
  the metrics and blocks merges on drift), and
- downstream consumers (dashboards, scorecards, AI agents, auditors).

Three metrics are emitted, always as a triple: **clause %**,
**priority-weighted %**, and **assurance-adjusted %**. Never publish one
in isolation.

> All three metrics are **engineering metrics**, not certification
> scores. See `LEGAL.md` § 4.

---

## 1. Inputs

| Source                                   | Role                                                                                        |
|------------------------------------------|---------------------------------------------------------------------------------------------|
| `use-cases/cat-*/uc-*.json`              | Every UC's `compliance[]` array: tuples of (regulation, version, clause, mode, assurance). |
| `data/regulations.json`                  | Multi-version framework catalogue: `commonClauses[].priorityWeight` is the denominator.    |
| `data/provenance/ingest-manifest.json`   | SHA-256 provenance of upstream crosswalks used for reconciliation.                         |
| `data/crosswalks/olir/*.normalised.json` | Authoritative capability ↔ ATT&CK mappings used as a sanity check.                         |

The numerator for any metric is derived only from `compliance[]`
entries with `status != "draft"` (see § 7). The denominator is fixed
per regulation-version at the set of clauses in the relevant
`commonClauses[]` list. Clauses outside that list still contribute to
the numerator when a UC maps to them (they become "bonus coverage"
but never inflate the denominator and never become the only evidence
of coverage for a common clause).

## 2. Scope selector

All three metrics are computed at four scopes, in this order:

1. **Global** — every regulation-version in `data/regulations.json`.
2. **Per regulation** — e.g. `gdpr@2016/679`.
3. **Per family** — groups of derivative regulations share a denominator
   via the `derives_from` graph (§ 5).
4. **Per tier** — tier-1, tier-2, tier-3 regulations reported separately
   so release gates only block on tier-1 regressions.

Every report emits the triple at every scope. Only the global tier-1
triple is a release-gate signal.

## 3. Weight tables

### 3.1 Priority weights (denominator)

From `priorityWeightRubric` in `data/regulations.json`:

| Regulator language           | `priorityWeight` |
|------------------------------|------------------|
| `must` / mandatory / baseline| **1.0**          |
| `should` / moderate-baseline | **0.7**          |
| `may` / addressable / recommended | **0.4**     |
| informative / appendix only  | **0.2**          |

These weights apply to each clause in `commonClauses[]` for every
regulation-version.

### 3.2 Assurance weights (numerator multiplier)

From `schemas/uc.schema.json`, `compliance[].assurance.enum`:

| Assurance level | Multiplier | Semantic rule                                                                   |
|-----------------|------------|---------------------------------------------------------------------------------|
| `full`          | **1.0**    | UC alone is sufficient evidence for the clause.                                 |
| `partial`       | **0.5**    | UC is one of several controls needed to meet the clause.                        |
| `contributing`  | **0.25**   | UC is useful context but not a primary control.                                 |

When a clause is covered by **multiple** UCs, the effective assurance
for that clause is the **maximum** of the per-UC multipliers; lower
assurance entries do not stack (§ 4.3 explains why).

## 4. The three metrics

Let `C` be the set of in-scope `(regulation, version, clause)` triples
taken from `commonClauses[]`. Let `covered?(c)` be `True` if any non-
draft UC has a `compliance[]` entry mapping to `c`. Let `pw(c)` be the
clause's `priorityWeight`. Let `a*(c)` be the maximum assurance
multiplier across all non-draft UCs mapping to `c`, or `0` if the
clause is not covered.

### 4.1 Clause coverage %

Primary signal of raw breadth.

\[
\text{Clause }\% \;=\; \frac{\bigl|\{ c \in C : \text{covered?}(c)\}\bigr|}{|C|} \times 100
\]

Interpretation: "what fraction of the in-scope clauses has at least one
UC pointing at it, irrespective of rigour". It is the easiest metric
to improve and therefore the easiest to over-optimise.

### 4.2 Priority-weighted %

Weights raw coverage by regulator intent so `must` clauses carry more
than `may` clauses.

\[
\text{Priority-weighted }\% \;=\; \frac{\sum_{c \in C} pw(c) \cdot \mathbb{1}[\text{covered?}(c)]}{\sum_{c \in C} pw(c)} \times 100
\]

Interpretation: "what fraction of the regulator's *stated* effort is
covered". Covering ten `may` clauses cannot mask a missing `must`
clause.

### 4.3 Assurance-adjusted %

Weights priority-adjusted coverage by how strong the evidence is.

\[
\text{Assurance-adjusted }\% \;=\; \frac{\sum_{c \in C} pw(c) \cdot \tilde{a}(c)}{\sum_{c \in C} pw(c)} \times 100
\]

where \(\tilde{a}(c) = \max_{u \in U_c} \text{cap}(\text{status}(u), a_u(c))\)
taken over every non-draft UC \(u\) that maps to clause \(c\), with
\(a_u(c) \in \{0.25, 0.5, 1.0\}\) the declared multiplier and
\(\text{cap}(s, a)\) defined as:

- \(s \in \{\text{verified}\}\): no cap, return \(a\).
- \(s \in \{\text{community}, \text{unset}\}\): cap at \(0.5\), i.e.
  return \(\min(a, 0.5)\).
- \(s = \text{draft}\): excluded entirely (return \(0\)).

Interpretation: "what fraction of the regulator's *stated* effort is
covered **with primary, verified evidence**". A `contributing` UC
still moves the number, but only a quarter as far as a `full` one —
and only a verified `full` UC can drive \(\tilde{a}(c)\) to \(1.0\).

Why **maximum** and not **sum**? A clause only ever needs one
sufficient piece of evidence. Stacking e.g. four `contributing` UCs to
synthesise a `full` rating is not defensible to an auditor. The audit
script rejects any UC set where this is attempted (§ 6.3).

## 5. Derivative regulations (`derives_from` graph)

Some regulations extend or restate a parent framework. `derives_from`
in `data/regulations.json` propagates coverage:

1. For each derivative clause, look up the parent clause it derives
   from. If the derivative clause has no direct UC mapping but its
   parent is covered, the derivative inherits coverage at the parent's
   assurance level **minus one step** (`full` → `partial`, `partial`
   → `contributing`, `contributing` → 0). This reflects that the
   derivative may introduce extra obligations not tested by the parent
   UC.
2. A direct UC mapping always wins over inherited coverage.
3. Divergent clauses marked `divergent: true` in the derivation graph
   never inherit; they require explicit UCs.

Per-family metrics (§ 2) are always reported alongside per-regulation
metrics so stakeholders can see both the inherited and the explicit
numbers.

## 6. Gate rules

### 6.1 Merge-blocking gates (CI)

Gate failures fall into two buckets. Anything in the *unconditional*
bucket blocks the merge immediately, period. Anything in the
*baselineable* bucket blocks only if it is **new** — i.e. its fingerprint
is not in `tests/golden/audit-baseline.json` (see § 12).

**Unconditional (never baselineable)**

- **Schema**: every `uc-*.json` file validates against
  `schemas/uc.schema.json`.
- **Regulation lookup**: every `compliance[].regulation` + `version`
  resolves to a real entry in `data/regulations.json` (alias resolution
  allowed).
- **Rationale**: every entry has an `assurance_rationale` of at least
  10 characters, and a valid `assurance` level.
- **Golden set**: every tuple in `tests/golden/compliance-mappings.yaml`
  is present in at least one UC and has assurance ≥ the expected
  minimum.
- **Regression protection**: no previously-clean finding fingerprint
  appears.

**Baselineable (blocks only if new or unresolved)**

- **Clause shape**: every `compliance[].clause` matches the
  `clauseGrammar` regex of the target version.

A finding is "new" if its fingerprint (`<code>\t<uc>\t<path>\t<message>`)
is absent from the baseline file. Fixing an existing finding requires
an accompanying `--update-baseline` run so the baseline shrinks as
cleanup ships.

Any failure in the unconditional bucket, or any new finding in the
baselineable bucket, returns non-zero from
`scripts/audit_compliance_mappings.py` and blocks the merge.

### 6.2 Release-blocking gates

For a release to ship:

1. Global tier-1 **clause %** ≥ previous release's value (no
   regression).
2. Global tier-1 **priority-weighted %** ≥ previous release's value.
3. Global tier-1 **assurance-adjusted %** ≥ previous release's value
   **minus 2 points**. (A small downward move is permitted so authors
   can re-grade inflated `full` ratings down to `partial` without the
   metric blocking the release.)
4. Every tier-1 regulation has ≥ 2 SMEs signed off in
   `data/provenance/sme-signoffs.json`.
5. Every tier-1 regulation has at least one `verified` UC covering
   each `must`-weight clause in `commonClauses[]`.

### 6.3 Anti-gaming rules

- UCs mapped only to low-weight clauses cannot be used to lift global
  tier-1 assurance-adjusted %. The audit script flags any UC whose
  **sole** contribution is to clauses with `priorityWeight ≤ 0.2`.
- Stacking multiple `contributing` UCs against a `must` clause does not
  synthesise `full`; we take the max, not the sum (§ 4.3).
- `status: draft` entries never count.

## 7. Status lifecycle

The UC catalogue carries a UC-level `status` field defined in
`schemas/uc.schema.json`:

- `draft` — work in progress.
- `community` — contributed, unreviewed.
- `verified` — production-ready, SME-signed-off. Requires an entry in
  `data/provenance/sme-signoffs.json` referencing the UC.
- *(unset)* — legacy, migrated from markdown before Phase 1.3. Treated as
  `community` for coverage purposes.

Rules applied by `scripts/audit_compliance_mappings.py`:

- UCs with `status == "draft"` are **fully excluded** from every
  coverage numerator. Their mappings still validate, but do not count.
- UCs with `status == "community"` or unset contribute to **clause
  coverage %** and **priority-weighted %** at the full assurance
  multiplier declared in the entry, but are **capped at assurance
  `partial` (0.5)** for the **assurance-adjusted %** metric. This
  prevents unreviewed `full` claims from inflating the highest-integrity
  signal.
- UCs with `status == "verified"` contribute at the full declared
  assurance multiplier to all three metrics. `full` claims on verified
  UCs are the only inputs that can drive **assurance-adjusted %**
  anywhere near 100 %.

The release gate (§ 6.2) requires every tier-1 regulation to have at
least one `verified` UC covering each `must`-weight clause before a
release ships.

## 8. Worked example

Suppose `gdpr@2016/679` has three clauses in `commonClauses[]`:

| Clause  | `priorityWeight` | UC coverage                                |
|---------|------------------|--------------------------------------------|
| Art.5   | 1.0              | UC-A (`full`), UC-B (`contributing`)      |
| Art.30  | 1.0              | UC-C (`partial`)                           |
| Art.7   | 0.7              | (none)                                     |

Compute:

- `covered?(Art.5) = True`, `covered?(Art.30) = True`, `covered?(Art.7) = False`.
- Clause % = 2 / 3 × 100 ≈ **66.7 %**.
- Priority-weighted % = (1.0·1 + 1.0·1 + 0.7·0) / (1.0 + 1.0 + 0.7) × 100 = 2.0 / 2.7 × 100 ≈ **74.1 %**.
- `a*(Art.5) = max(1.0, 0.25) = 1.0`; `a*(Art.30) = 0.5`; `a*(Art.7) = 0`.
- Assurance-adjusted % = (1.0·1.0 + 1.0·0.5 + 0.7·0) / (1.0 + 1.0 + 0.7) × 100 = 1.5 / 2.7 × 100 ≈ **55.6 %**.

Even though two clauses out of three are covered (66.7 %), the weak
`partial` rating on Art.30 pulls the defensible signal to 55.6 %. This
is intentional: the triple forces an honest conversation about where
the evidence really lies.

## 9. Out-of-scope / intentionally not measured

- **Prose quality** — the SPL and `howToImplement` text is not scored
  here; the QA gate at Phase 4.5 measures it separately.
- **Runtime efficacy** — whether a deployed UC fires on real data is
  measured by ATT&CK emulation under Phase 4.5.
- **Operational burden** — effort to deploy a UC is out of scope; use
  the controlFamily taxonomy for that signal.

## 10. Change control

This document is versioned. Any change to the weight tables, the
definition of any metric, or the gate rules requires:

1. A bump of the `Version:` header above.
2. A matching `CHANGELOG.md` entry in the `## Compliance methodology`
   section.
3. Recompute of the three metrics against the current catalogue at the
   same commit, with the old and new numbers reported side-by-side so
   downstream dashboards have a migration path.

## 11. Reference implementation

The normative implementation is `scripts/audit_compliance_mappings.py`.
Any interpreter of this document (dashboards, AI agents, external
scorecards) **must** cross-check against the script's output and file
a ticket if it diverges. The script is the tie-breaker.

## 12. Baseline mechanism

### 12.1 Why a baseline exists

Phase 1 migrated ~1,170 UCs from free-form markdown to the JSON schema
defined in Phase 1.1. The migration preserved every clause citation
verbatim, including citations that the Phase 1.2 grammars flag as
malformed (compound ranges like `Art.15-22`, placeholders like
`§policy`, and regulation names used as clauses in legacy SOX / FISMA
entries). Loosening the grammars to accept these would sacrifice the
precision every downstream auditor needs. Deleting them would destroy
information and regress coverage. The compromise is a **baseline file**
that lets CI distinguish "tolerated migration debt" from "new mistakes".

### 12.2 What is baselineable

Only *one* finding code is ever baselineable:

- `clause-grammar` — the clause text does not match the target
  version's `clauseGrammar` regex.

Every other code (schema errors, unknown regulations, unknown versions,
missing rationale, golden-test failures) is unconditional and cannot be
baselined. The set of baselineable codes is defined by the
`BASELINEABLE_CODES` constant in
`scripts/audit_compliance_mappings.py` and is deliberately narrow.

### 12.3 Fingerprints

Each finding has a stable fingerprint of the form

```
<code>\t<uc_id>\t<path>\t<message>
```

Any change in *any* of those four fields yields a different
fingerprint, and therefore a different finding. The baseline file
(`tests/golden/audit-baseline.json`) stores a sorted, de-duplicated
list of tolerated fingerprints. Matching is exact-string.

### 12.4 Behaviour

On every audit run:

1. All findings are computed exactly as before.
2. Each finding whose code is in `BASELINEABLE_CODES` is checked
   against the baseline. Matches have their `level` downgraded to
   `"baselined"` and excluded from the error count.
3. Non-matching baselineable findings remain at level `"error"` and
   count toward the exit code.
4. All non-baselineable findings always count toward the exit code.
5. The JSON report records `counts.errors` (blocking) and
   `counts.baselined` (tolerated) separately, plus a
   `baseline.unused` array listing fingerprints the baseline carries
   that were *not* observed this run. Unused fingerprints should be
   pruned — they usually indicate the underlying UC was fixed or
   deleted.

### 12.5 Workflow

- **Adding or editing a UC**: just run the audit. New clause-grammar
  errors in your changes block the merge; cleaning up pre-existing
  errors reduces the baseline automatically on the next
  `--update-baseline` run.
- **Fixing migration debt**: fix the UC(s), then run
  `python scripts/audit_compliance_mappings.py --update-baseline` and
  commit the shrunk baseline. Reviewers check that the line-count
  dropped.
- **Force-regenerate after a grammar change**: if
  `data/regulations.json` tightens a grammar, run `--update-baseline`
  in the same PR as the grammar change. The PR description must
  declare the intent and the baseline's line-count delta.

### 12.6 Release gate

The baseline is additionally gated at release time: the 4.0 release
plan targets **zero baselineable findings for tier-1 regulations**.
Until then the baseline is a budget, not a bug. CI always ensures the
budget only shrinks between merges.

### 12.7 Observability

`reports/compliance-coverage.json` and `docs/compliance-coverage.md`
record, for every run:

- `counts.errors` and `counts.baselined`,
- `baseline.total` (fingerprints in the file),
- `baseline.matched` (tolerated this run),
- `baseline.newErrors` (blocking this run),
- `baseline.unused` (fingerprints to prune).

Dashboards tracking compliance health should expose the first two
prominently; `baseline.unused` should be wired into the Phase 3.1
cleanup scoreboard.
