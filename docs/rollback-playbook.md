# Rollback playbook

> **Audience.** Maintainers and on-call reviewers. This document tells you
> what to do when a merged PR breaks the catalogue, the build, the API, or
> a downstream consumer — and tells the authors of risky PRs what they must
> hand over so a rollback is mechanical instead of heroic.

## TL;DR

Every architecture / CI / framework / security PR (anything authored against
[`PULL_REQUEST_TEMPLATE/architecture.md`](../.github/PULL_REQUEST_TEMPLATE/architecture.md)
or [`PULL_REQUEST_TEMPLATE/security.md`](../.github/PULL_REQUEST_TEMPLATE/security.md))
**must declare its rollback path in the PR description**, with:

1. The exact `git revert` command — usually `git revert <merge-sha>`, but
   if the work landed as a squash merge of a multi-step migration, name
   the squash SHA and any data-migration scripts that need un-running.
2. A kill switch — env var, feature flag, or `if`-gate — that lets us
   disable the change without redeploying. `none` is acceptable but
   must be explicit.
3. A soak window — how long we expect the change to ride main before we
   trust it (defaults: P1 → 1 minor version, P2/P4 → 7 days, P5 → 14 days,
   P9 → 1 minor version, security hardening → 24 hours).

The PR templates pre-fill these fields. Reviewers must not approve a PR
where they read `Revert command: TBD` or `Soak window: ???` — those are
unfinished merge requirements, not defaults.

## Why this exists

The repo-overhaul plan (P0 → P19) deliberately lands large architectural
changes in small PRs. Two failure modes are paid for by the rollback
investment:

1. **Silent reversibility loss.** Some changes appear self-contained but
   couple to downstream artefacts — a schema change that lands without
   regenerating `dist/api/v1/uc.schema.json` propagates a stale wire
   contract to MCP and external consumers. Once a third-party caches
   the broken artefact, "just revert" no longer fully unwinds the
   damage; the rollback playbook is what tells you which caches to
   invalidate.
2. **Heroic-revert anti-pattern.** Without a written plan, an outage
   pushes the on-call author into improvisation under stress. Every
   migration done in this codebase has a rollback path; writing it
   down at PR time costs minutes and saves hours.

This is the standard "every irreversible operation has a documented
undo" guardrail. We treat merging to `main` as deployment-class work
even though there is no live service, because:

- GitHub Pages is auto-deployed on every push to `main`.
- Tagged releases trigger Sigstore-attested artefacts that real
  consumers pin.
- The MCP server, the api/v1/ tree, and `catalog.json` are all
  consumed by external scripts on a freshness contract.

## Per-phase contract

Each phase of the repo-overhaul has a default rollback profile.
Override per PR if your specific change is more or less risky than
the phase default; **never silently take a weaker profile**.

| Phase | Default revert | Default soak window | Default kill switch | Notes |
|---|---|---|---|---|
| **P0** Hygiene | `git revert <sha>` | none | none | Pre-commit hooks + cleanups; reverting is symmetric. |
| **P1** SSOT migration | `git revert <sha>` + rerun `make build` | one minor version | toggle in `tools/build/build.py:_PROJECT_STATIC_FILES` | Deletions of legacy artefacts are one-way; gated by `tests/build/test_legacy_artifacts_parity.py`. |
| **P2** CI hardening | `git revert <sha>` | 7 days | `continue-on-error: true` on the offending step | New gates land green on `main` first, then are made required. |
| **P2.5** Action pinning | `git revert <sha>` | 7 days | none | Pinning is purely defensive; the only failure mode is a missed upgrade. |
| **P3** Docs / ADR | `git revert <sha>` | none | none | ADRs are append-only; reverts that remove an ADR are forbidden once `Accepted`. |
| **P4** Typed models | `git revert <sha>` | 7 days | `_TYPED_MODELS_ENABLED = False` | Typed-model adoption is consumer-by-consumer; each PR is small. |
| **P5** Frontend | `git revert <sha>` + clear Pages cache | 14 days | feature flag in `index.html` | The biggest user-facing surface; warrants the longest soak. |
| **P6** Scripts taxonomy | `git revert <sha>` + rerun `make audit-full` | 7 days | redirect shims in `scripts/` | Renames preserve a one-release-cycle redirect shim. |
| **P7** Search API | `git revert <sha>` + DNS rollback | 7 days | feature flag at edge | Optional Cloudflare/Deno layer; falls through to Pages if disabled. |
| **P8** Observability | `git revert <sha>` | none | none | `dist/metrics.json` is informational; consumers don't pin to it. |
| **P9** Monorepo | `git revert <sha>` | one minor version | none — this is a structural change | Restructuring is the highest-risk operation; gate behind explicit go/no-go. |
| **P10** Perf budgets | relax the budget | 7 days | budget threshold in `lighthouse-budgets.json` | Budgets ride main before being enforced. |
| **P11–P19** | per-PR | per-PR | per-PR | These phases are heterogeneous; declare explicitly. |
| **Security** (any phase) | `git revert <sha>` | 24 hours active monitoring | feature flag where defensible | A security regression is a P0 incident; bias toward fast rollback. |

## What the PR description must spell out

Architecture / security PR templates already include the **Rollback**
heading; this section pins what each line in that heading actually
requires.

### Revert command

- **Self-contained PR**: `git revert <merge-sha>`.
- **Squash-merge of a multi-step migration**: name the squash SHA *and*
  list the un-migrate script if a data migration ran. Example:
  > `git revert <squash-sha> && python3 scripts/migrations/p1_step5b_undo.py`
- **PR that bumps a version pin (e.g. an action SHA in `.github/workflows/`)**:
  if the upstream is irrecoverable (force-pushed tag), name the
  fallback SHA we will repin to.

### Kill switch

The mechanism that disables the change without a code revert:

- An environment variable read at process start-up.
- A feature flag in `index.html`'s embedded JSON.
- A `continue-on-error: true` on a CI step.
- A `_PROJECT_STATIC_FILES` entry that re-shadows the SSOT output
  (this is what we used as the safety mechanism while P1 step 5b
  rolled out).

If none exists, write `none — change is structurally infeasible to
toggle` and explain why. A surprising amount of the time, that
explanation reveals a kill switch we should add before merging.

### Soak window

How long the change rides `main` before we treat it as load-bearing.

- For purely additive changes (a new audit, a new ADR, a new test):
  no soak required; you can refer to and rely on the change immediately.
- For deletions of public artefacts (a script, a workflow, a
  committed JSON output): one minor version minimum, more if external
  consumers exist.
- For frontend changes: 14 days, because Pages is cached aggressively
  by some downstream readers.

### Affected releases

For any PR that may be cherry-picked into a backport branch, name the
range of releases that include the fix. The Sigstore attestation chain
on `release.yml` makes this verifiable; see `release.yml` for the
attestation format.

## Authoring the rollback section: anti-patterns

Reviewers reject these immediately:

- **`Revert command: TBD`** or `???`. The PR isn't ready for merge.
- **`Soak window: none`** on a frontend PR. Frontend PRs warrant 14
  days; if the author argues otherwise, they must put the argument
  in the PR description, not an empty line.
- **`Kill switch: feature flag` with no flag name.** Name the flag,
  the file it lives in, and the production default.
- **A revert that doesn't address an external cache.** Pages caches
  aggressively; a content revert that "wins" by getting reverted into
  Pages might still be visible to consumers pinning to a CDN
  edge for 24 hours. Document the cache-invalidation step.

## Process when a rollback is needed

1. **Confirm the regression.** Run `make audit` and `make build`
   locally on the suspected merge SHA; reproduce the failure.
   If the failure is "it builds locally but fails in CI", check
   `validate.yml` step output for environment differences.
2. **Read the PR's Rollback section.** This is what the contract is
   for. Follow the literal command.
3. **Verify the revert builds clean.** `make build && make audit-full`.
4. **Land the revert as its own PR**, citing the original merge SHA
   and the symptom that triggered the rollback. Do **not** force-push
   `main` — that would break Sigstore attestation chains for the
   affected window.
5. **Invalidate caches** if the PR description called any out.
6. **Open an autopsy issue** if the rollback was non-mechanical
   (i.e. the PR's documented revert path didn't work). The autopsy
   tightens the next iteration of this playbook.

## Tagged-release rollback

Tagged releases (driven by [`release.yml`](../.github/workflows/release.yml))
are append-only. We do not delete or repoint tags, because the
`actions/attest-build-provenance` Sigstore attestations would become
unverifiable. To roll back a release:

1. Cut a new tag (`vX.Y.Z+1`) that reverts the offending change.
2. Re-run `release.yml` to publish the corrected artefact bundle
   with a fresh attestation.
3. Update `CHANGELOG.md` to document the rollback under the new
   version, citing the regressed tag and the Sigstore signature.
4. Do **not** delete or move the regressed tag's GitHub Release —
   leave it visible with a `BROKEN — see vX.Y.Z+1` notice in the
   release body. Consumers who already pulled the broken artefact
   need to be able to verify what they have against the original
   attestation.

## Links

- PR templates: [`architecture.md`](../.github/PULL_REQUEST_TEMPLATE/architecture.md),
  [`security.md`](../.github/PULL_REQUEST_TEMPLATE/security.md)
- Release pipeline: [`release.yml`](../.github/workflows/release.yml)
- Pages pipeline: [`pages.yml`](../.github/workflows/pages.yml)
- Capacity calibration that sizes the rollback workload:
  [`docs/capacity-and-staffing.md`](capacity-and-staffing.md)
- External-consumer surfaces that any rollback must preserve:
  [`docs/external-consumer-matrix.md`](external-consumer-matrix.md)
- ADRs that constrain rollback shape: [ADR-0007](adr/0007-json-as-source-of-truth.md)
  (UC content), [ADR-0008](adr/0008-canonical-constants.md) (constants),
  [ADR-0009](adr/0009-generated-artefact-policy.md) (artefacts)
- Repo-overhaul plan: cross-cutting policy `rollback-strategy`

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** Anthropic, et al. (2026). *Model Context Protocol Specification*. Anthropic PBC. Retrieved May 11, 2026, from https://modelcontextprotocol.io/

<a id="ref-2"></a>**[2]** Splunk Inc. (2026). *Splunk Enterprise Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk

### Related repository documents

- [`docs/adr/0007-json-as-source-of-truth.md`](adr/0007-json-as-source-of-truth.md)
- [`docs/adr/0008-canonical-constants.md`](adr/0008-canonical-constants.md)
- [`docs/adr/0009-generated-artefact-policy.md`](adr/0009-generated-artefact-policy.md)

### Cited by

- [`docs/capacity-and-staffing.md`](capacity-and-staffing.md)
- [`docs/ci-architecture.md`](ci-architecture.md)

<!-- END-AUTOGENERATED-SOURCES -->
