# Exclusions coverage audit

Every use case in the catalogue should state **what it deliberately does not
cover**. That scope boundary helps reviewers triage false positives, keeps
adjacent UCs from overlapping, and gives auditors a clear limit when mapping
controls to detections.

## Why exclusions matter

- **False-positive triage** — analysts know when an alert is out of scope for
  this UC and should be handled elsewhere.
- **Scope clarity** — implementers see neighbouring UCs referenced by ID
  instead of guessing whether a gap is intentional.
- **Audit evidence** — assessors can read the exclusion alongside the SPL and
  control test without inferring limits from the title alone.

The content-quality lift loop treats `exclusions` as a curated string surface
(alongside description, value, knownFalsePositives, and references). See
[`docs/superpowers/specs/2026-05-17-content-quality-lift-loop-design.md`](superpowers/specs/2026-05-17-content-quality-lift-loop-design.md).

## String field, not an array (K-5 re-scope)

`schemas/uc.schema.json` defines `exclusions` as a **string** with
`minLength: 10`. Roughly 230 sidecars already carry handwritten exclusion
text; the gold-profile v2 rubric and `lift-validate` firewall both expect a
string.

Lane K ships an **audit-only** gate that surfaces UCs missing useful
exclusions content. Lane N backfills strings from the prioritized queue. If a
future ADR adopts structured per-exclusion metadata, that lands as a separate
schema-cycle PR with explicit migration tooling — not as part of this audit.

## Classification states

The auditor assigns every UC one of five states based on stripped string
length (default healthy boundary: 80 characters):

| State | Length (default) | Meaning |
| --- | --- | --- |
| `missing` | field absent or `null` | No scope boundary authored |
| `too_short` | 1–9 chars | Below schema minimum (defensive; schema validation should catch these) |
| `bare` | 10–79 chars | Meets schema minimum but likely under-described |
| `populated` | 80–400 chars | Healthy scope statement |
| `verbose` | >400 chars | Consider trimming for panel readability |

Override the bare/populated boundary with `--min-length N` (must stay ≥
schema minimum of 10).

## Running the audit

```bash
# Emit dist/audits/exclusions-coverage.{json,md}
python -m splunk_uc audit-exclusions-coverage

# CI warn-only gate (threshold 0 % — always passes until ratcheted)
python -m splunk_uc audit-exclusions-coverage --check --threshold 0

# Custom output directory + markdown backlog cap
python -m splunk_uc audit-exclusions-coverage --out dist/audits --limit 50

# High-criticality backlog only
python -m splunk_uc audit-exclusions-coverage --criticality high
```

Makefile target: `make audit-exclusions-coverage`.

Outputs live under `dist/audits/` and are gitignored. The JSON report is
schema-versioned (`version: "1.0"`) and includes corpus counters,
per-category histograms, and a `prioritized_queue` sorted by criticality
(descending), category (ascending), and UC id (ascending).

## Threshold-ratchet policy

CI starts at **`--threshold 0`**: the step is warn-only and documents baseline
coverage without blocking merges. As Lane N backfills exclusions strings,
maintainers ratchet the threshold upward (for example 5 → 25 → 50 percent
`populated` + `verbose`) until the catalogue reaches the target coverage
agreed with stewards.

Healthy coverage for `--check` is:

```text
(populated + verbose) / corpus_size × 100
```

## Worked example (gold-tier UC)

From `content/cat-03-containers-orchestration/UC-3.1.1.json` (critical,
560 characters):

> Does not cover Kubernetes pod CrashLoopBackOff or kubelet restart counters
> (UC-3.2.1, UC-3.2.10). Does not isolate cgroup OOM control files alone
> (UC-3.1.2). Does not monitor HEALTHCHECK state machine …

Good exclusions text:

1. Names concrete out-of-scope scenarios (not "other things").
2. Points to sibling UC ids when overlap is likely.
3. Stays within the populated band (80–400 chars) unless the domain truly
   needs more — then trim for readability or split scope across UCs.

## Maintainer workflow (Lane N)

1. Run `python -m splunk_uc audit-exclusions-coverage --out dist/audits`.
2. Open `dist/audits/exclusions-coverage.md` — work the prioritized backlog
   (high criticality first).
3. Hand-author `exclusions` on each sidecar (string, ≥10 chars, target 80+).
4. Re-run the audit locally; when corpus coverage improves, propose a higher
   `--threshold` in `.github/workflows/validate.yml`.

Do **not** bulk-generate placeholder strings — exclusions require domain
judgment about intentional scope limits.
