# Capacity and staffing

> **Audience.** Maintainers, would-be maintainers, contributors deciding
> whether to take on a long-running phase of the repo-overhaul plan, and
> anyone reading [`ROADMAP.md`](../ROADMAP.md) trying to figure out why
> a particular item is "in scope this year" or "deferred to v8".

## TL;DR

The repo-overhaul plan (P0 → P19, plus cross-cutting policy work) was
sized for the following standing capacity:

| Role | FTE | What they do |
|---|---|---|
| **Platform engineer** | 1–2 (peak), 1.0 typical | Build pipeline, audits, CI, scripts, frontend chrome, security gates, schema work. |
| **Curator** | 0.5 | Gold-standard authoring, GE review, prereq-graph maintenance, regulatory primer upkeep, SME outreach. |
| **Tier-1 legal reviewer** | as-needed (≈0.1 over the year) | Cat-22 evidence-pack review for tier-1 regulations (GDPR, HIPAA, PCI, SOX, NIS2, DORA, ISO 27001, NIST 800-53, NIST CSF, SOC 2, UK GDPR, CMMC). |

Below that line we move to **reduced mode**; below the reduced-mode
floor we move to **solo mode**. Both modes scope down the plan;
neither lets the catalogue rot. See "Operating modes" below for the
concrete scope-down lists.

When you read a plan item that says "deferred under solo mode", that
maps to a row in the table further down — it isn't a hand-wave.

## Why this document exists

The plan deliberately splits the overhaul into ~50 PRs across 11
phases. That cadence assumes someone is **on the queue every week**
to review, merge, and unblock. If the maintainer pool drops to one
part-time person over a quarter:

1. **Quality gates degrade silently.** Without a written scope-down,
   the rational thing for an overloaded maintainer is to merge
   smaller PRs first, leaving big migrations half-done — exactly the
   shape that produces the [rollback hazards](rollback-playbook.md)
   the playbook exists to prevent.
2. **Cat-22 falls into "stale-but-claimed" mode.** Compliance content
   is the most-trafficked use-case, but it's also the part that can
   most easily drift from current regulatory reality. Without legal
   reviewer time, evidence packs can stay nominally checked-in but
   become misleading.
3. **External consumers are misled by the roadmap.** The plan in
   `ROADMAP.md` is written as if all phases will land. Without an
   explicit capacity contract, downstream users plan against a
   schedule we cannot honour.

This document is the calibration: it states what we assumed, what
breaks if that assumption fails, and what we will explicitly *not*
do at reduced capacity. It is paired with
[`docs/rollback-playbook.md`](rollback-playbook.md) (what to do when
a merged PR breaks something) and the per-phase rollback profiles
in [GOVERNANCE.md](../GOVERNANCE.md).

## Where the capacity goes

The following is the full-mode steady-state, broken out by activity.
Time is per quarter, so 0.5 FTE = 130 person-hours per quarter at
40h/week × 0.65 utilisation.

| Activity | Owner | Quarterly hours | Notes |
|---|---|---|---|
| Build & audit upkeep | Platform engineer | 40 | Keeping `make build` + `make audit-full` green; bumping pinned action SHAs; fixing flaky tests. |
| Schema & enrichment evolution | Platform engineer | 30 | New JSON fields, TypedDict additions, parity-test snapshots. |
| Frontend & static-site upkeep | Platform engineer | 25 | CSP fixes, accessibility regressions, dashboard polish. |
| Security gates & supply-chain | Platform engineer | 20 | CodeQL findings, dependency-review remediation, SBOM tag drift, gitleaks rule tuning. |
| Release management | Platform engineer | 15 | Cutting tags, writing release notes, validating Sigstore attestation chain. |
| Gold-standard authoring | Curator | 60 | New UCs to "gold" tier, refinements to "silver"-tier UCs, GE review. |
| Cat-22 regulatory upkeep | Curator + legal reviewer | 30 | Watching for regulation amendments, refreshing primer anchors, expiring evidence packs. |
| SME outreach & PR review | Curator | 30 | Shepherding contributor PRs, soliciting category-owner reviews, closing stale issues. |
| Documentation upkeep | Curator | 10 | Keeping `docs/`, ADRs, and this document in sync with reality. |
| Tier-1 evidence-pack review | Legal reviewer | as-needed | Reviewing each tier-1 regulation primer for legal-accuracy at least once a year. |

Total: ~260 hours/quarter — roughly 1.5 FTE-equivalent if everyone
worked full time, but spread across 1-2 part-time platform engineers
+ 0.5 FTE curator + sporadic legal review.

## Operating modes

The plan has three calibrated operating modes. Each declares the set
of activities **promised to ship** at that capacity tier; everything
else is explicitly out of scope.

### Full mode (default)

**Trigger.** The standing capacity above is available.

**In scope.**

- All P0–P19 phases on their plan-of-record cadence.
- Quarterly minor releases (per
  [GOVERNANCE.md](../GOVERNANCE.md): "Publishing at least one patch
  or minor release per quarter").
- Tier-1 cat-22 regulations refreshed within 30 days of any
  amendment we observe.
- Contributor PR median triage time ≤ 10 business days.
- Security findings from CodeQL / Dependency Review acknowledged
  within 24 hours.

**Cadence example.** P1 SSOT migration lands across one minor
version (~6 weeks). P5 frontend bundler ships in increments of one
page per minor.

### Reduced mode

**Trigger.** Any **one** of:

- One active maintainer for ≥ 30 consecutive days (CODEOWNERS shows
  ≥ 2 names, but git history shows a single committer).
- Curator capacity drops to ≤ 0.25 FTE over a 90-day window.
- CI green-rate on `main` drops below 90% over 30 days.

**In scope (kept).**

- All P0, P1, P2, P3, P4 phases (the SSOT and CI hardening backbone).
- Security gates: CodeQL, Dependency Review, gitleaks, SBOM,
  Sigstore. **These are non-negotiable** because their failure
  silently widens supply-chain risk for every consumer.
- Audit suite stays green (`make audit-full`).
- Cat-22 in current state — no regression, no new regulations,
  no version uplift.
- Bi-annual minor releases (down from quarterly).

**Out of scope (deferred).**

- P5 frontend bundler ramp (apps/web/ scaffold can sit, but no new
  pages bundle until full-mode capacity returns).
- P9 monorepo restructure — too much downstream churn for a single
  person to absorb.
- P10 perf budgets enforcement (budgets land but stay advisory).
- P19 i18n — translation pipeline cannot be reviewed without
  curator + bilingual reviewer capacity.
- P5 component-library expansion beyond the components already
  shipped.
- New cat-22 tier-1 regulations beyond the existing 12.

**Triage discipline.** Reviewers in reduced mode must add the
`reduced-mode-deferred` label to any non-emergency contributor PR
that targets a deferred phase. The PR description gets a comment:
"This phase is deferred under our current capacity (see
[`docs/capacity-and-staffing.md`](docs/capacity-and-staffing.md)).
Will revisit when full mode resumes." Do not close the PR — leave
it open with the label so the contributor's work is preserved.

### Solo mode

**Trigger.** Any **one** of:

- One active maintainer with < 0.5 FTE for ≥ 60 consecutive days.
- Zero curator capacity for ≥ 90 days (no PRs from anyone in the
  curator role landed in the audit window).
- A founding maintainer is unavailable for an extended period
  (medical / personal) without a designated deputy.

**In scope (kept).**

- Audit suite stays green. Period.
- Security gates remain enforced. CodeQL findings are still
  triaged. Dependency-review high-severity blocks are still hard
  gates.
- The catalogue compiles: `make build` succeeds on every push to
  `main`.
- Cat-22 evidence packs remain valid (no edits, but their
  signatures and links remain unbroken).
- Yearly tag (vX.Y), with a release note that says "minimal
  release; capacity-constrained".

**Out of scope (deferred).**

- P5 frontend bundler / component library / data.js retire.
- P6 scripts taxonomy.
- P7 search-API edge layer.
- P8 metrics emission.
- P9 monorepo.
- P10 perf budgets.
- P11 release polish beyond security baseline.
- P16 coverage burndown.
- P17 AI-readiness / LLM eval.
- P18 Splunk version compat matrix beyond what already ships.
- P19 i18n.
- New use cases — content additions are paused; only **content
  corrections** (factually wrong queries, broken links, schema
  validation failures) are accepted.

**Critically.** Solo mode preserves the SSOT (P0/P1/P2/P3/P4 + the
ADRs they constrain). When capacity returns, the deferred phases
can resume from a known-good base.

## Triggers and transitions

Mode transitions are explicit, not silent. The lead maintainer (or
in their absence, the most-recently-active maintainer) declares the
transition by:

1. **Opening an issue** with the `capacity-mode` label, naming the
   trigger (which row above), the start date, and the planned
   review date (30 days for reduced, 90 days for solo).
2. **Updating the project status banner** in `README.md` (top of
   file, just under the project description) so external readers
   see the calibration.
3. **Adding a `CHANGELOG.md` entry** under "Unreleased":
   `Operating mode: <mode> (<trigger>)`. This becomes part of the
   permanent project record at the next release.
4. **Posting in the active discussion thread** (currently GitHub
   Discussions) so contributors with PRs in flight know what to
   expect.

The transition stays in effect until either:
- The trigger condition resolves (and is re-asserted clear at the
  review date), or
- A subsequent transition declaration changes the mode.

When mode is reasserted as "full", deferred phases are unblocked
in this order:

1. Security and CI gates that had been relaxed (e.g.
   `continue-on-error: true` re-disabled).
2. The phase with the most PRs labelled `reduced-mode-deferred`
   (i.e. the phase with the most queued contributor work).
3. Anything else, in plan-of-record order (P5 → P6 → P7 → ...).

## Anti-patterns

These are the failure modes capacity work explicitly tries to prevent.
Reviewers reject PRs that exhibit them:

- **Silently picking solo-mode scope while claiming full-mode
  cadence.** If the maintainer pool has shrunk, the project status
  banner must reflect it. Do not announce "v8 next quarter!" in
  release notes if reduced-mode triggers are active.
- **Letting security gates lapse to keep CI green.** Any PR that
  adds `continue-on-error: true` to a security workflow MUST cite
  the operating mode that authorises the relaxation, or it gets
  rejected. (See `validate.yml` history — we explicitly removed
  this scaffolding once content drift cleared.)
- **Backlogging cat-22 tier-1 reviews to "later".** Tier-1 evidence
  packs that go > 12 months without legal review must move to
  `assurance: contributing` (down from `partial` / `full`). The
  catalogue should be honest about what it can defend.
- **Speedrunning a deferred phase.** Phases marked deferred in
  reduced or solo mode are deferred for capacity reasons, not
  technical-debt reasons. A single contributor PR that lands the
  whole of P9 monorepo in one merge would still be too risky to
  approve under reduced mode. The phase-by-phase rollback profile
  in [`docs/rollback-playbook.md`](rollback-playbook.md) §"Per-phase
  contract" is the operational floor.
- **Shipping i18n / multi-language content without curator review.**
  P19 specifically requires curator + bilingual reviewer capacity;
  drive-by machine translations are out of scope at every mode.

## What this document does *not* commit to

- We do **not** commit to a specific person remaining in any role.
  Maintainers can step down; curators can pause; legal reviewers
  can decline new regulations. This document tells us how to
  scope-down when that happens, not how to prevent it.
- We do **not** commit to hiring, paid contracts, or sponsored
  work. The capacity numbers are the standing volunteer baseline,
  not a fundraising ask.
- We do **not** commit to time-of-day SLAs. The 24h security-gate
  acknowledgement target is best-effort by humans on volunteer
  cycles — the *audit gate* enforces the actual security floor;
  this document calibrates how fast humans turn around the audit's
  outputs.

## Recovery

When a transition out of reduced or solo mode is declared:

1. **Run `make audit-full` to re-check the floor.** Capacity-mode
   periods can let drift accumulate (especially in markdown
   companions, cat-22 primer dates, and SBOM artefacts). The audit
   tells you what to fix first.
2. **Re-run `python3 scripts/audit_action_pins.py`.** Pinned action
   SHAs go stale during low-activity periods; renew them before
   layering new feature work on top.
3. **Resume the highest-leverage deferred phase.** Look up the
   phase IDs labelled `reduced-mode-deferred` on contributor PRs.
   The phase with the most queued PRs gets unblocked first, even
   if it is later in the plan-of-record sequence — this respects
   contributor effort already invested.
4. **Announce the recovery.** README banner, `CHANGELOG.md`
   "Unreleased" entry, and a closing comment on the original
   `capacity-mode` issue.

## Links

- Repo-overhaul plan phases: tracked as todos with IDs `p0-…` to
  `p19-…` plus cross-cutting `policy-…` and `rollback-strategy`
  ids. The plan reference is the body of TODO commentary in
  agent-transcripts and the per-phase rollback profile in
  [`docs/rollback-playbook.md`](rollback-playbook.md).
- Governance: [`GOVERNANCE.md`](../GOVERNANCE.md) (roles,
  decision-making, lazy consensus).
- Contribution flow: [`CONTRIBUTING.md`](../CONTRIBUTING.md).
- Per-phase rollback contract:
  [`docs/rollback-playbook.md`](rollback-playbook.md) §"Per-phase
  contract".
- ADRs that constrain operating-mode behaviour:
  [ADR-0007](adr/0007-json-as-source-of-truth.md) (UC content),
  [ADR-0008](adr/0008-canonical-constants.md) (constants),
  [ADR-0009](adr/0009-generated-artefact-policy.md) (artefacts).
- External-consumer release contract that every operating mode
  must preserve: [`docs/external-consumer-matrix.md`](external-consumer-matrix.md).
- PR templates that hand off context to reviewers:
  [`PULL_REQUEST_TEMPLATE/architecture.md`](../.github/PULL_REQUEST_TEMPLATE/architecture.md),
  [`PULL_REQUEST_TEMPLATE/security.md`](../.github/PULL_REQUEST_TEMPLATE/security.md).
