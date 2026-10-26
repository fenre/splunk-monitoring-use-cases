# UC text-quality review rubric

This rubric grades the **text** of a use case: whether it is clear, specific
to the use case, internally consistent, and factually correct. It is the
grading contract for every review tier of the UC text-quality review
(see [`docs/superpowers/plans/2026-10-26-uc-text-quality-review.md`](superpowers/plans/2026-10-26-uc-text-quality-review.md)).

It operationalises two existing standards and does not replace them:

- [`docs/content-editorial-review-standard.md`](content-editorial-review-standard.md) — per-field acceptance criteria.
- [`docs/uc-quality-mandate.md`](uc-quality-mandate.md) — the page, accuracy and value tests.

Review records validate against
[`schemas/v2/uc-review-finding.schema.json`](../schemas/v2/uc-review-finding.schema.json).
The rubric version recorded in every record is **1.0**
(`splunk_uc.review._ledger.RUBRIC_VERSION`). Bump it whenever the text between
the rubric markers below changes meaning; a bump makes every stored model
review stale, so the runner re-reviews those UCs on the next pass.

## Review tiers

| Tier | Who | Scope |
|------|-----|-------|
| `deterministic` | `audit-text-quality` (no model) | Every UC. Template families, skeleton clusters, CIM / Splunkbase / premium-app drift, spelling, placeholder titles. |
| `triage` | fast model | Every UC, batched 8–10 per call within a subcategory. |
| `deep` | heavy model | UCs the routing rule selects (below), one per call, with grounding documents. |
| `adjudication` | second model family | cat-22 blockers and low-confidence deep-review blockers. |

Deep-review routing: a UC goes to `deep` when any of these hold:

- `criticality` is `critical`
- `status` is `verified`
- triage reported a `blocker` or `major` finding in the `correctness` dimension
- triage reported a `blocker` or `major` firewalled-field flag
- triage scored `correctness` at 3 or below
- triage `confidence` is below 0.6
- it is in cat-22 and carries a `compliance[]` claim

Calibration on 2026-10-26 found that 83% of UCs need a deep correctness
review, so in practice the deep tier runs on every UC (`deep --all`); see
[`reports/uc-review/calibration/decision.md`](../reports/uc-review/calibration/decision.md).

<!-- rubric:begin -->
## Rubric (embedded verbatim in review prompts)

You are reviewing one Splunk monitoring use case (UC) from a public catalogue.
Judge the text a reader relies on to understand and implement the UC. Do not
rewrite the UC. Report findings.

### Dimensions and scores

Score each dimension from 1 to 5. 1 = unusable, 2 = misleading or mostly
generic, 3 = acceptable with edits, 4 = good, 5 = exemplary.

1. **clarity** — A reader understands what is detected, at what grain, and
   what causes a result row. No word salad, no lists of title words standing
   in for sentences, no unexplained jargon outside technical fields.
2. **specificity** — Every sentence is about this UC. Penalise generated
   template residue: the UC citing its own ID inside prose, "Purpose-built
   for ...", "Variant N confirms ...", generic suppression lookups such as
   `ops_exception_register.csv`, evidence or exclusions text that would fit
   any UC, false-positive scenarios that do not name a real cause.
3. **consistency** — Title, description, SPL, thresholds, `cimModels`,
   `cimSpl`, data sources and implementation describe the same detection.
   Thresholds in prose match the SPL. Field names in prose exist in the SPL
   or the data source. Sibling facts (TA name, sourcetype) agree with the
   grounding documents.
4. **correctness** — Product facts are true: add-on (TA) names and
   Splunkbase IDs, sourcetypes, field names, event codes and log
   mnemonics, API paths, CIM datamodel and dataset choice, UI navigation,
   RBAC roles, version numbers, vendor behaviour. A CIM datamodel must fit
   the signal (for example, interface link-state syslog is not
   `Network_Traffic`). Invented or guessed facts are errors even when they
   sound plausible.
5. **grandma_fidelity** — `grandmaExplanation` is plain language, contains
   no SPL or CIM jargon, and says the same thing the technical fields say.
6. **overclaiming** — No claim the UC cannot support: `status: verified`
   without evidence of SME sign-off, compliance assurance beyond what the
   detection proves, "detects all ...", certainty about field names the
   author could not verify, premium apps the SPL does not need.

### Severity

- **blocker** — Factually wrong or misleading. A reader following the text
  would build the wrong thing or draw a false conclusion. A `correctness`
  blocker MUST cite evidence: `evidence_url` (vendor or Splunk
  documentation) or `evidence_ref` (a repository file such as a guide under
  `docs/guides/` or `data/splunkbase-catalog.json`). Without evidence, use
  `needs_verification` instead.
- **major** — Templated, generic, or not actionable. The text is not wrong
  but does not help the reader implement this UC.
- **minor** — Style, wording, spelling, small omissions.
- **needs_verification** — You suspect a factual error but cannot cite
  evidence. Say exactly what to check.

### Verdict

Severities in `findings` and in `firewalled_field_flags` both count.

- `ok` — no findings and every score is at least 4.
- `polish` — only `minor` or `needs_verification` items.
- `rewrite` — at least one `major`, no blocker.
- `incorrect` — at least one `blocker`.

The runner re-derives the verdict from the severities after applying the
evidence rule, so a blocker downgraded to `needs_verification` no longer
makes a UC `incorrect`.

Set `confidence` (0 to 1) to how sure you are of the verdict as a whole.

### Firewalled fields

`spl`, `cimSpl`, `compliance`, `monitoringType`, `splunkPillar`,
`criticality`, `difficulty`, `title`, `id` and `mitreAttack` are edited only
by humans. Report problems in these fields under `firewalled_field_flags`,
not `findings`. Everything else (`description`, `value`, `dataSources`,
`app`, `implementation`, `detailedImplementation`, `knownFalsePositives`,
`controlTest`, `evidence`, `exclusions`, `visualization`, `references`,
`grandmaExplanation`, `premiumApps`, `cimModels`, `equipmentModels`) is
fixable and goes under `findings`.

### Deterministic findings

Findings from the deterministic pre-pass are attached to each UC. They are
already recorded; do not repeat them. Spend your attention on what a regex
cannot see: wrong facts, inconsistent thresholds, CIM choices that do not
fit the signal, implementation steps that would not work.

### Writing findings

- `field` — the sidecar field the problem lives in (`controlTest`,
  `knownFalsePositives`, ...). Use `cross_field` for disagreements between
  fields and name both fields in the explanation.
- `quote` — the shortest exact excerpt that shows the problem (at most 500
  characters).
- `explanation` — what is wrong and why, in one or two sentences.
- `suggested_fix` — what the corrected text should say. Do not invent facts
  here either; if the right value is unknown, say what to look up.
- Report each distinct problem once. Prefer five precise findings over
  fifteen vague ones.
<!-- rubric:end -->

## How a fix closes a finding

Findings drive the fix phase (plan Phase 6):

- **Scripted families** (`template_v2:*`, `premium_app_pillar_mismatch`,
  `v2_lantern_root_reference`, `cim_models_*`) are fixed by reviewed
  scripts, one PR per family.
- **Prose findings** are fixed through the lift loop:
  `lift-prompt UC-X.Y.Z --findings <ledger record>` feeds the findings to
  the author, and `lift-validate --require-handcraft` refuses any diff that
  leaves v2 template residue in a field it rewrites.
- **Firewalled-field flags** become issues for human-reviewed PRs.

After a UC's fixes pass, set `lastReviewed` and `reviewer` per the editorial
standard. Never set `status: verified` because a review passed; remove an
existing `verified` claim that the deep review could not support.

## Calibration thresholds

Before a model is used for triage at scale it must, on the 150-UC
calibration set graded by the deep model and spot-checked by a maintainer:

- recall of at least 0.90 on `blocker` and `major` findings (matched on UC,
  field and dimension), and
- a false-blocker rate of at most 10%.

`scripts/uc_review_runner.py calibrate` computes both numbers.
