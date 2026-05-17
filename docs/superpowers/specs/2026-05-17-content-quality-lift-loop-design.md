# Content-Quality Lift Loop — Design Spec

> **Status.** Proposed (2026-05-17).
> **Author.** Claude (Cursor) in collaboration with `@fenre`.
> **Supersedes.** —
> **Tracks against.** [`docs/health-check-2026-progress.md`](../../health-check-2026-progress.md) (future drift-ledger entry).

## 1. Problem

The catalogue rolls up to **composite 72.0 / Silver overall** in
[`docs/scorecard.md`](../../scorecard.md). The single dominant gap is
the `Depth` dimension: **17 of 23 categories sit at the floor value of
35**. The six categories that exceed it (cat-3 at 89, cat-18 at 87,
cat-19 at 76, cat-13 at 62, cat-5 at 61, cat-23 at 79) demonstrate
the ceiling is authoring-effort, not methodology. Until depth lifts,
the catalogue stays Silver-bound regardless of how many UCs are added.

The maintenance model is **solo developer + AI**. A manual,
human-only depth-lift pass would be infeasible at 7,929 UC scale; the
solution must be AI-driven, schema-bounded, and auditable per UC.

## 2. Goal

Lift the catalogue's composite from Silver (72) toward Gold (≥ 85) by
systematically raising the per-UC depth score against the
**code-defined rubric** in `src/splunk_uc/audits/gold_profile.py`
and `gold_profile_v2.py`. Both audits already exist as CI gates; the
lift loop authors content *against* those gates, not around them.

### Success metric

Composite score for the proof-of-concept category (cat-15 Data
Center Physical Infrastructure) climbs from **67.0 → ≥ 75** (Bronze
→ Silver), with every existing CI gate green and zero SPL changes.

### Non-goals

- Not a new UC pipeline. Lift loop only enhances existing UCs.
- Not a SPL rewriter. SPL/CIM SPL fields are firewalled (§ 4).
- Not a classification re-tagger. `monitoringType`, `pillar`,
  `criticality`, `difficulty` are immutable inside the loop.
- Not a regulatory mapper. `compliance[]` is firewalled.
- Not a fixture generator. Sample-data and `assurance` upgrades are a
  separate future workflow ("Option B" — robustness pass).

## 3. Approach

A two-verb CLI under `python -m splunk_uc` that orchestrates AI
authoring through a strict schema + audit firewall:

```
operator runs:
   splunk_uc lift-batch --category cat-15 --limit 30 --worst-first
       │
       ▼
   for each UC in batch (sorted by current depth ascending):
       splunk_uc lift-uc UC-X.Y.Z --target-tier silver
           │
           ▼
       1. read current sidecar + run gold_profile audit → enumerate gaps
       2. build deterministic prompt (rubric + UC + gaps + lift surface + firewall)
       3. dispatch Cursor subagent (generalPurpose, readonly=false) → diff
       4. validate diff (schema → audit-uc-structure → spl-hallucinations →
                        spl-grammar → known-fp → monitoring-type → content-quality)
       5. assert post-lift depth > pre-lift depth
       6. write diff, regenerate .md companion, emit commit message
       │
       ▼
   write reports/lift-batch-<timestamp>.json summary
```

Each commit covers one UC. CI runs unchanged.

## 4. Lift surface (the firewall)

The fields the loop is **allowed** to touch are exactly those the
gold-profile rubric scores. Every other field is firewalled.

| Field | Touched? | Target threshold | Source of rubric |
| --- | --- | --- | --- |
| `description` | yes | ≥ 80 chars; ≤ 60% word-stem overlap with `value` | `gold_profile_v2.py` |
| `value` | yes | ≥ 80 chars; distinct from `description` | `gold_profile_v2.py` |
| `dataSources` | yes | ≥ 80 chars; ≥ 1 Splunkbase ID + sourcetype + extracted field | `gold_profile_v2.py` |
| `detailedImplementation` | yes | ≥ 500 chars (Silver target) / 1500 chars (Gold-v2); ≥ 6 distinct product-specific indicators | `gold_profile.py`, `gold_profile_v2.py` |
| `knownFalsePositives` | yes | ≥ 4 distinct named scenarios with suppression mechanism | `gold_profile_v2.py` |
| `references` | yes | ≥ 4 entries; prefer high-provenance sources | `audit-content-quality`, `gold_profile_v2.py` |
| `controlTest.positiveScenario` / `negativeScenario` | yes | differ by ≥ 30 chars | `gold_profile_v2.py` |
| `evidence` | yes | ≥ 30 chars | `gold_profile_v2.py` |
| `exclusions` | yes | ≥ 30 chars | `gold_profile_v2.py` |
| `visualization` | yes | populated if missing | `gold_profile.py` (Gold required) |
| `equipmentModels` | yes | populated if matchable to existing registry | `gold_profile.py` (Gold required) |
| `mitreAttack[]` | yes — narrow | populated only when `pillar=security` AND currently null AND every proposed technique ID validates against `audit-mitre-taxonomy` AND the AI returns a non-empty `confidence` rationale per technique (rationale ≥ 40 chars, kept in commit message, dropped from sidecar) | scorecard `MITRE` dimension; `audit-mitre-taxonomy` |
| `app` | yes — narrow | append Splunkbase ID if missing AND known | `gold_profile_v2.py` |
| **`spl`** | **NO** | — | high-risk — SPL changes require human review |
| **`cimSpl`** | **NO** | — | derived from `spl` |
| **`id`, `title`** | **NO** | — | identity is immutable |
| **category folder** | **NO** | — | identity is immutable |
| **`monitoringType`, `splunkPillar`** | **NO** | — | classification stays |
| **`criticality`, `difficulty`** | **NO** | — | classification stays |
| **`compliance[]`** | **NO** | — | regulatory accuracy is too sensitive |
| **`fixtureRef`, `assurance`, `samples/UC-<id>/`** | **NO** | — | separate workflow ("Option B") |
| **`grandmaExplanation`** | **NO** | — | already produced by dedicated generator |

Rationale: every field the loop touches has a numeric, audit-enforced
threshold. Fields without an audit are not touched.

## 5. Validation contract — per UC, before commit

In this exact order, every proposed diff must pass:

1. JSON parses; UC ID unchanged; file path unchanged.
2. `jsonschema` validation against `schemas/uc.schema.json`
   (no new fields, no type drift; the schema is `additionalProperties: false`).
3. `python -m splunk_uc audit-uc-structure --files <path>` exits 0.
4. `python -m splunk_uc audit-spl-hallucinations --files <path>` exits 0
   — proves SPL was not changed by side effect.
5. `python -m splunk_uc audit-spl-grammar --files <path>` exits 0.
6. `python -m splunk_uc audit-known-fp --files <path>` exits 0
   — KFP scenarios are well-formed.
7. `python -m splunk_uc audit-monitoring-type --files <path>` exits 0
   — classification stays consistent.
8. `python -m splunk_uc audit-content-quality --files <path>` exits 0
   — no `description == value`, no jargon in `grandmaExplanation`,
   no broken `fixtureRef`.
9. `python -m splunk_uc audit-gold-profile --files <path>` reports a
   score strictly greater than the pre-lift baseline. (If
   `--target-tier gold-v2`, also `audit-gold-profile-v2`.)

Any single failure → no write; loop logs and moves on (or exits with
the failing UC, depending on `--strict`). A passing diff is by
construction a CI-green diff.

## 6. CLI surface — two new verbs

### `lift-uc`

```
python -m splunk_uc lift-uc UC-X.Y.Z
    [--target-tier silver|gold|gold-v2]   default: silver
    [--dry-run]                            print diff, don't write
    [--print-prompt]                       emit the AI prompt and exit (manual mode)
    [--strict]                             exit 1 on first validation failure
```

Single-UC lift. Implementation lives at
`src/splunk_uc/tools/lift_uc.py`; verb is registered in
`src/splunk_uc/_registry.py`.

### `lift-batch`

```
python -m splunk_uc lift-batch
    --category cat-NN
    [--limit N]                            default: 30
    [--worst-first | --random]             default: worst-first
    [--target-tier silver|gold|gold-v2]
    [--parallel N]                         default: 4 (concurrent subagents)
    [--dry-run]
    [--report PATH]                        default: reports/lift-batch-<TIMESTAMP>.json
```

Picks N UCs from the category sorted by current depth, runs `lift-uc`
on each, aggregates results into a JSON summary
(`reports/lift-batch-<timestamp>.json` with per-UC pre/post depth
scores, validation pass/fail reason, commit-ready diff path). One
commit per UC (operator commits or scripts the commit).

## 7. AI authoring step — proof-of-concept implementation

For the PoC, the AI authoring step uses **Cursor subagents** (Task
tool, `subagent_type=generalPurpose`):

- `lift-uc` builds the prompt (rubric excerpt + current UC JSON +
  enumerated gaps + lift surface + firewall + validation contract +
  expected output shape: unified JSON diff).
- `lift-uc` dispatches a single subagent with that prompt.
- The subagent returns the proposed diff as JSON.
- `lift-uc` applies the diff in-memory, runs the validation contract,
  writes on pass.

**Parallelism model:**

- `lift-uc` dispatches **one** subagent per invocation (single-UC scope).
- `lift-batch` is the parallelism orchestrator: it dispatches up to
  `--parallel N` (default: 4) `lift-uc` subagents concurrently, each
  scoped to one UC. The validation contract (§5) is per-UC so there
  is no cross-UC state to race on. The orchestrator commits diffs
  sequentially even though dispatch is parallel — git stays clean.

Why subagents for PoC, not an external CLI integration:

- Zero new dependencies; runs today in any Cursor session.
- The orchestration session (me) is already the AI; subagent
  dispatch is a known-working primitive.
- Natural fit for the `dispatching-parallel-agents` skill.

Future enhancement (out of PoC scope): wire `lift-uc` to an external
AI CLI (e.g., `cursor-agent` via `@cursor/sdk`) so the loop becomes
runnable from `make lift-cat-15` or a cron, without an interactive
Cursor session. That's straightforward to add once the rubric +
validation chain are proven.

## 8. Proof-of-concept target — cat-15

Pick **cat-15 Data Center Physical Infrastructure**:

- **Size:** 117 UCs — fast feedback loop.
- **Current state:** Bronze 67.0, depth=34. Eight categories are
  Bronze; cat-15 is the smallest of them. Refs / KFP / provenance
  / freshness are already 100% / 100% / 75 / 23d, so depth lift
  converts ~directly to composite lift.
- **Domain:** UPS, generators, HVAC, PDUs, environmental sensors —
  well-bounded technically; AI has high prior knowledge.
- **Lift target:** bottom 30 UCs (by depth) lifted to depth ≥ 70
  (Silver depth). Re-run scorecard; cat-15 composite climbs to ≥ 75.

**Done criteria for PoC:**

1. `python -m splunk_uc lift-batch --category cat-15 --limit 30
   --worst-first` runs clean against current HEAD.
2. 30 commits land, one per UC, each passing the §5 validation
   contract.
3. `python -m splunk_uc generate-scorecard` shows cat-15 composite
   ≥ 75.
4. `make sync-generated-check` green.
5. `PYTHONPATH=src python3 -m pytest tests/build/ tests/scripts/ -q`
   green (635 tests).
6. Drift-ledger entry recorded in `docs/health-check-2026-progress.md`.

## 9. After the PoC — iteration order

If cat-15 PoC passes its done criteria, the next iterations follow
in this order (smallest Bronze first, then largest Silver to maximise
catalogue-wide composite movement):

1. **cat-7 Database** (187 UCs, 61.4 Bronze — lowest composite in the
   catalogue) — needs depth lift + freshness reset (350-day median).
2. **cat-6 Storage** (152 UCs, 64.7 Bronze).
3. **cat-8 Application Infrastructure** (241 UCs, 63.4 Bronze).
4. **cat-12 DevOps & CI/CD** (126 UCs, 67.5 Bronze).
5. **cat-15 retest** — confirm idempotent re-run does nothing.
6. Then move to the heavy Silver categories: cat-22 Regulatory
   (1,621), cat-10 Security (2,455), cat-5 Network (720).

Each iteration is its own PR. The loop is unchanged between
iterations; only the `--category` argument differs.

## 10. What this design explicitly does not solve

- **Robustness gap** (357 UCs claim `"full"` assurance without
  populated fixtures; 22 wave-monotonicity violations). Separate
  follow-on workflow.
- **Audit-verb consolidation** (47 verbs in `python -m splunk_uc`;
  several are one-time drift-guards or single-vendor). Independent
  cleanup PR; can run in parallel.
- **F21 close** (7,761 committed `.md` companions). Independent
  cleanup PR; can run in parallel.

## 11. Risks and mitigations

| Risk | Likelihood | Mitigation |
| --- | --- | --- |
| AI changes SPL by side effect | low (firewall) | `audit-spl-hallucinations` + `audit-spl-grammar` in validation contract; firewall is explicit in prompt |
| AI hallucinates references | medium | `references` entries must have non-empty `url` + `title`; future enhancement: `audit-links` on changed refs |
| AI fabricates KFP scenarios that look plausible but are vendor-incorrect | medium | per-UC commit means trivial revert; long-tail: human spot-check of N commits per batch |
| Lift loop degrades a UC that was already at Silver/Gold | low | §5 step 9 enforces `post > pre` depth score; re-running is idempotent (already-passing UCs are no-op) |
| Loop produces 30 commits per batch — git history bloat | low | one commit per UC is the desired property (clean revert surface); CHANGELOG entries are batched, not per-UC |
| `mitreAttack[]` AI tagging is wrong | medium | tag only when `pillar=security` AND currently null AND high-confidence; future enhancement: `audit-mitre-taxonomy` already validates the technique IDs |
| Subagent dispatch fails mid-batch | low | `lift-batch` retries failed UCs; on second failure, skips with warning in report |

## 12. References

- `docs/scorecard.md` — current composite + per-category breakdown.
- `src/splunk_uc/audits/gold_profile.py` — depth rubric v1 source.
- `src/splunk_uc/audits/gold_profile_v2.py` — depth rubric v2 source.
- `src/splunk_uc/generators/scorecard.py` — `_qs`/`_qt` consumer.
- `schemas/uc.schema.json` — schema firewall.
- `docs/gold-standard-authoring-playbook.md` — the authoring contract
  the v2 audit was scored against.
- [`docs/health-check-2026-progress.md`](../../health-check-2026-progress.md)
  — drift-ledger.
- Previous lean-mode arc PRs: PR-1 `d45047de6`, PR-2 `31adcf593`
  (+ fix `e3f4b5ca6`), PR-3 `913468fc2`.
