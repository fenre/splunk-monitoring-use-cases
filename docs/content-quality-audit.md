# Content quality audit

The `audit-content-quality` verb surfaces catalogue prose and metadata
issues that block operational utility. It **never edits sidecars** —
maintainers (Lane N) drain the queue by handwriting better text. The
AI-assisted [content-quality lift loop](superpowers/specs/2026-05-17-content-quality-lift-loop-design.md)
consumes per-UC gates from this audit during `lift-validate`.

## Running the audit

```bash
# Full corpus scan (legacy mode — fails on unbaselined legacy violations)
PYTHONPATH=src python3 -m splunk_uc audit-content-quality

# CI gate: write report + apply generous fail-level cap (ratchet over time)
PYTHONPATH=src python3 -m splunk_uc audit-content-quality \
  --check --severity fail --max-findings 6500

# Per-UC lift-loop gate
PYTHONPATH=src python3 -m splunk_uc audit-content-quality \
  --files content/cat-01-server-compute/UC-1.1.1.json

# Report only
PYTHONPATH=src python3 -m splunk_uc audit-content-quality --report
```

Makefile shortcut: `make audit-content-quality`.

## Report shape

The audit writes `reports/content-quality-audit.json` (schema `2.0`) with:

| Section | Purpose |
|---------|---------|
| `findings_summary` | Roll-up counts by dimension and severity |
| `legacy_violations` | Hard checks carried forward from v1 |
| `description_findings` | Heuristic description queue |
| `value_findings` | Heuristic value-statement queue |

## Legacy checks (v1)

These pre-date the description/value dimensions and remain unchanged:

1. **`description_equals_value`** — `description` and `value` are byte-identical after strip.
2. **`jargon_in_grandma`** — `grandmaExplanation` contains SPL/CIM jargon reserved for technical fields.
3. **`broken_fixtureRef`** — `controlTest.fixtureRef` points at a missing file under the repo root.

Use `--baseline path.json` with `--generate-baseline` output to gate only **new**
legacy violations. This mode is backwards-compatible with pre-B-6 CI wiring.

## Description and value quality dimensions

Added in Lane B Task B-6. Each row is a **heuristic queue item**, not a schema
failure. Thresholds tighten beyond `schemas/uc.schema.json` (`minLength: 20`)
and `schemas/uc-profile-gold.json` tier ladders — they do not modify schema.

### Description heuristics

| Dimension | Severity | Rule | Why heuristic |
|-----------|----------|------|---------------|
| `description.too_short` | **fail** | `len(description) < 120` | Gold-tier guidance expects 60–80+ chars; 120 catches one-liners that fail the "what does this detect?" test without blocking every Bronze draft. |
| `description.boilerplate` | warn | Opens with "this use case/rule/detection", duplicates `title`, or matches templated stems (`monitors the`, `use case for`, …) | Template residue is common in bulk imports; warn surfaces it without blocking CI while debt is burned down. |
| `description.too_thin` | warn | Exactly one sentence **and** `< 200` chars | Single-sentence descriptions often omit scope/threshold context; length guard reduces false positives on tight but complete sentences. |
| `description.no_action_verb` | info | Does not start with an action verb (`detects`, `identifies`, `alerts`, `monitors`, `finds`, …) | Style nudge only — valid descriptions sometimes lead with context clauses. |

### Value heuristics

| Dimension | Severity | Rule | Why heuristic |
|-----------|----------|------|---------------|
| `value.too_short` | **fail** | `len(value) < 80` | Value must articulate business impact; 80 chars is above schema minimum but below Gold-tier depth. |
| `value.no_outcome` | warn | Missing measurable-outcome keywords (`reduce`, `detect`, `prevent`, `comply`, `ensure`, `improve`, …) | Keyword list catches generic prose; false positives possible when impact is implied numerically. |
| `value.too_generic` | warn | Text is essentially only "best practice / industry standard / improve security" | Flags placeholder value statements; SME review decides whether to keep or rewrite. |
| `value.duplicates_description` | warn | Case-folded equality or ≥ 90 % sequence overlap with `description` | Gold profile requires distinct *what* vs *why*; overlap ratio tolerates minor rephrasing. |

### Severity mapping

| Severity | CI default | Maintainer action |
|----------|--------------|-------------------|
| `fail` | Counted toward `--max-findings` cap | Prioritise in Lane N queue |
| `warn` | Reported, not gated at `fail` | Schedule during category burndown |
| `info` | Reported only | Optional style polish |

### CLI flags (additive)

| Flag | Default | Effect |
|------|---------|--------|
| `--include-description` / `--no-include-description` | on | Toggle description heuristics |
| `--include-value` / `--no-include-value` | on | Toggle value heuristics |
| `--severity {info,warn,fail}` | `fail` in `--check` mode | Filter findings for exit-code gating |
| `--max-findings N` | unset | Exit 1 when surfaced findings exceed `N` |
| `--files PATH…` | full corpus | Scope to specific sidecars (lift loop) |

## Threshold ratchet

CI runs with a **generous initial cap** so the live corpus passes while the
queue is visible in reports:

```yaml
# .github/workflows/validate.yml — Content quality audit (B-6)
# Cap counts legacy violations + fail-level description/value findings.
# Lower --max-findings as Lane N burns down the queue (~5929 surfaced at launch).
run: PYTHONPATH=src python3 -m splunk_uc audit-content-quality --check --severity fail --max-findings 6500
```

Ratchet protocol:

1. Lane N clears a batch of `fail` findings.
2. Lower `--max-findings` in `validate.yml` toward the new steady-state count.
3. Never raise schema `minLength` in the same PR — schema cycle (F-1) owns that slot.

## Related tooling

- `python3 -m splunk_uc lift-score` — rubric depth score for a single UC
- `python3 -m splunk_uc audit-gold-profile` — tier classifier used by the lift loop
- `python3 -m splunk_uc audit-placeholders` — TBD/FIXME/template stub gate (orthogonal)

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

### Related repository documents

- [`docs/superpowers/specs/2026-05-17-content-quality-lift-loop-design.md`](superpowers/specs/2026-05-17-content-quality-lift-loop-design.md)

<!-- END-AUTOGENERATED-SOURCES -->
