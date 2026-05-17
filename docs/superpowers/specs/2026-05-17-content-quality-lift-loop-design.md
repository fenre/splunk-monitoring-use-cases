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

The lift loop is split cleanly between **deterministic CLI primitives**
(implemented in Python under `python -m splunk_uc`) and an
**agent-driven orchestration loop** (implemented as a Cursor agent
workflow using the `dispatching-parallel-agents` skill). The
separation is forced by the toolchain: a Python subprocess cannot
invoke Cursor's `Task` tool, so all AI dispatch has to happen in the
orchestration layer that owns the tool. Keeping the boundary explicit
also keeps the Python side pure-function and trivially testable.

```
Cursor agent (orchestrator) — has the Task tool:
   loops over UCs in the chosen batch (sorted by current depth):
       │
       ▼
   1. shell: splunk_uc lift-score UC-X.Y.Z
          → JSON gap report (current depth + per-rubric-field gaps)
   2. shell: splunk_uc lift-prompt UC-X.Y.Z
          → deterministic AI prompt (rubric + UC JSON + gaps +
            lift surface + firewall + expected output shape)
   3. dispatch Task subagent (generalPurpose, readonly=false)
          → diff JSON returned in agent message
   4. write diff to /tmp/lift-UC-X.Y.Z.diff.json
   5. shell: splunk_uc lift-validate UC-X.Y.Z --diff <path>
          → apply diff in-memory; run §5 validation contract;
            on pass write sidecar + regenerate .md companion;
            on fail print reason and exit non-zero
   6. shell: git add + git commit (one commit per UC)
       │
       ▼
   write reports/lift-batch-<timestamp>.json summary
```

Each commit covers one UC. CI runs unchanged. The Python primitives
have zero AI dependency — they are unit-testable from `pytest` without
Cursor in the loop.

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

## 6. CLI surface — three deterministic primitives + one batch helper

All four verbs are pure-function from the AI's perspective: zero AI
calls, zero subagent dispatch, zero network. The agent-driven
orchestration loop in §3 calls them as building blocks.

### `lift-score`

```
python -m splunk_uc lift-score UC-X.Y.Z
    [--target-tier silver|gold|gold-v2]   default: silver
    [--json]                               default: human-readable
```

Reads the UC sidecar, runs the gold-profile audit, prints the current
depth score and a per-rubric-field gap report. With `--json`, the
output is machine-parseable for the orchestration loop.

### `lift-prompt`

```
python -m splunk_uc lift-prompt UC-X.Y.Z
    [--target-tier silver|gold|gold-v2]   default: silver
```

Reads the UC sidecar + the rubric (from `gold_profile.py` /
`gold_profile_v2.py`), emits a deterministic AI prompt to stdout:
rubric excerpt + current UC JSON + enumerated gaps + lift surface +
firewall + expected output shape (unified JSON diff). The orchestration
agent feeds this prompt to a `Task` subagent.

### `lift-validate`

```
python -m splunk_uc lift-validate UC-X.Y.Z
    --diff <path>                         JSON diff produced by the AI step
    [--dry-run]                            print would-be sidecar, don't write
    [--strict]                             exit 1 on first validation failure
```

Applies the diff in-memory, runs the §5 validation contract, writes
the sidecar on pass + regenerates the `.md` companion. On fail prints
the reason. This is the only verb that touches disk.

### `lift-batch`

```
python -m splunk_uc lift-batch
    --category cat-NN
    [--limit N]                            default: 30
    [--worst-first | --random]             default: worst-first
    [--target-tier silver|gold|gold-v2]
    [--report PATH]                        default: reports/lift-batch-<TIMESTAMP>.json
```

A thin helper that enumerates the N target UCs in a category sorted
by current depth and emits a JSON manifest (`{ucs: [...], target_tier:
...}`). The orchestration agent reads this manifest and runs the
per-UC loop. `lift-batch` itself does not dispatch subagents — it
only picks the UCs and produces the work list. Picking the work
list is itself worth a dedicated, audit-traceable command so the
batch composition is reproducible across runs.

All four verbs live under `src/splunk_uc/tools/lift/` (one module
per verb, with shared helpers in `_common.py`); each is registered
in `src/splunk_uc/_registry.py`.

## 7. AI authoring step — agent-driven orchestration

The AI authoring step lives in the **orchestration agent layer** (a
Cursor session), not inside any of the four Python verbs. For the
PoC the orchestration is run by the `@fenre` Cursor session
(currently me, Claude). The pattern follows the
`dispatching-parallel-agents` superpowers skill:

- The orchestration agent runs `lift-batch` once to get the work list.
- For each UC in the work list:
  - Run `lift-score UC-X.Y.Z` and `lift-prompt UC-X.Y.Z` via the
    shell tool. These are read-only Python calls.
  - Dispatch a `Task` subagent (`subagent_type=generalPurpose`,
    `readonly=false` so the subagent can write the diff file) with
    the prompt from `lift-prompt` as its body. The subagent's
    instruction is exactly: "Read this prompt, write the unified
    JSON diff that satisfies it, save it to /tmp/lift-<UC>.diff.json,
    return the path. Do nothing else."
  - When the subagent returns the diff path, run
    `lift-validate UC-X.Y.Z --diff <path>`. Validation either writes
    the sidecar or prints why it refused.
  - On validation pass, run `git add` + `git commit` (one commit
    per UC).
- After the batch completes, regenerate the scorecard with
  `splunk_uc generate-scorecard` so the composite movement is
  visible in `docs/scorecard.md`.

**Parallelism model:**

- Each subagent dispatch is scoped to one UC. The §5 validation
  contract is per-UC, so there is no cross-UC race.
- The orchestration agent dispatches multiple subagents
  concurrently (default: 4 in flight). Diffs are validated and
  committed sequentially even though dispatch is parallel — git
  stays linear, one commit per UC.
- The `dispatching-parallel-agents` skill governs the per-batch
  dispatch ceiling and the retry policy.

Why this split (deterministic Python primitives + agent
orchestration), not a single `lift-uc` verb that does everything:

- **Toolchain constraint.** Python subprocesses do not have access
  to Cursor's `Task` tool. The AI dispatch has to live in the agent.
- **Testability.** The Python verbs are pure-function. `lift-score`,
  `lift-prompt`, and `lift-validate` each get a unit-test suite that
  runs without Cursor in the loop.
- **Auditability.** `lift-batch` produces a reproducible work list.
  Re-running `lift-score` on a committed UC yields the same gap
  report. The agent's per-UC subagent dispatches are the only
  non-deterministic step, and they are bounded by `lift-validate`.

Future enhancement (out of PoC scope): an external-CLI variant
(`splunk_uc lift-run`) that shells to `cursor-agent` via
`@cursor/sdk` to do the AI step from a `make` target or cron. Adding
that later does not change any of the four Python primitives — it
just adds a fifth verb that wraps the agent loop.

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

1. The four CLI primitives (`lift-score`, `lift-prompt`,
   `lift-validate`, `lift-batch`) are implemented, registered, and
   covered by unit tests.
2. The orchestration loop documented in §7 runs against cat-15 with
   `--limit 30 --worst-first` and lands 30 commits, one per UC, each
   passing the §5 validation contract.
3. `python -m splunk_uc generate-scorecard` shows cat-15 composite
   ≥ 75 (Bronze → Silver).
4. `make sync-generated-check` green.
5. `PYTHONPATH=src python3 -m pytest tests/build/ tests/scripts/
   tests/splunk_uc/ -q` green.
6. Drift-ledger entry recorded in `docs/health-check-2026-progress.md`.
7. CHANGELOG.md entry under "Added" / "Changed".

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
