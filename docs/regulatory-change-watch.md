# Regulatory change-watch (Phase 5.3)

> Status: **required** for any change to
> `data/regulations-watch.json`, `schemas/regulations-watch.schema.json`,
> `scripts/audit_regulatory_change_watch.py`, or the `.github/workflows/regulatory-watch.yml` job.
>
> Scope: tier-1 regulations plus the MITRE ATT&CK / D3FEND crosswalks we rely on.

This repository aspires to be the international gold standard for
compliance-monitoring use cases. That promise is only as strong as the
regulatory provenance behind it. Phase 5.3 adds an auditable change-watch
layer that (a) records every regulatory artefact we depend on, (b) probes
them on a weekly cadence, and (c) fails CI if the ledger is allowed to go
stale.

## 1. Components

| File | Purpose |
| --- | --- |
| `data/regulations-watch.json` | Ledger of every regulation we track, the detection strategy, and the last observed state. |
| `schemas/regulations-watch.schema.json` | JSON Schema (Draft 2020-12) that governs the ledger. |
| `scripts/audit_regulatory_change_watch.py` | Audit + fetch + freeze tool. Three modes: `--check` (hermetic CI), `--fetch` (network probe), `--freeze` (seed/reset timestamps). |
| `.github/workflows/validate.yml` | Runs `--check` on every pull request; fails CI when the ledger is too stale. |
| `.github/workflows/regulatory-watch.yml` | Runs `--fetch` weekly (Monday 09:00 UTC), commits the refreshed ledger, and opens a GitHub issue when upstream changes are detected. |
| `reports/regulatory-change-watch.json` | Latest fetch snapshot — bundled into the QA-gates artifact. |

## 2. Detection strategies

Every watchlist entry picks one of five strategies. The strategy dictates how
`--fetch` probes the upstream publisher and what fields `--check` validates.

| `strategy.type` | When to use | State tracked |
| --- | --- | --- |
| `sha256-vendor` | OSCAL-content and similar machine-readable artefacts that are already mirrored via `data/provenance/ingest-manifest.json`. | `lastObservedHash` (SHA256 of the fetched body); compared to the primary `source_id` on every check. |
| `github-release` | Upstream projects with a semver tag cadence (MITRE CTI sub-repos, Sigma rules, etc.). | `lastObservedVersion` (release tag name); optional `versionPattern` regex filter. |
| `http-head` | Publisher landing pages that expose stable `ETag` / `Last-Modified` headers (EUR-Lex, legislation.gov.uk, DoD CMMC). | `lastObservedEtag` (ETag, fallback to Last-Modified). |
| `rss-atom` | Publishers with a news feed (HHS/OCR HIPAA feed). | `lastObservedVersion` (count + titles of recent matches); `matchTerms` allow-lists relevant feed entries. |
| `manual-review` | Regulators without a machine-friendly feed (PCAOB, AICPA, ISO, PCI SSC). | `lastObservedVersion` (human-entered version string). A manual `--freeze` stamps a fresh `lastCheckedAt`. |

## 3. Cadence and staleness thresholds

Thresholds live in the ledger's top-level `stalenessPolicy` block so they can
be tuned without editing code:

```json
{
  "tier1WarnDays": 60,
  "tier1FailDays": 180,
  "tier2WarnDays": 90,
  "tier2FailDays": 270
}
```

Semantics:

- **Warn** — PR CI prints a warning but the gate passes. Treat as a reminder
  that the weekly job has not run (or has been silently broken).
- **Fail** — PR CI blocks the merge. Fix by running `--fetch` locally or
  re-triggering the scheduled workflow, then commit the refreshed ledger.

Tier is chosen per entry. Use **tier 1** for any regulation that Phase 5.1
ships a Splunk app for (GDPR, HIPAA Security, PCI DSS, SOC 2, SOX ITGC,
ISO 27001, NIST CSF, NIST 800-53, NIS2, DORA, CMMC). Use **tier 2** for
derivative jurisdictions (UK GDPR, CCPA, nFADP, LGPD, APPI), MITRE
frameworks, and anything else where a slow cadence is acceptable.

## 4. Operator workflows

### 4.1 Daily — reviewer responding to a PR check failure

1. Read the CI failure output. It will identify the affected watchlist
   entries and the number of stale days.
2. Decide if the staleness is benign (the weekly job silently failed, but
   no upstream changes exist) or material (the publisher changed and we
   have not yet adopted the change).
3. Run `python3 scripts/audit_regulatory_change_watch.py --fetch` locally.
   Requires network access. The script is hermetic: it mutates only
   `data/regulations-watch.json` and `reports/regulatory-change-watch.json`.
4. Commit the refreshed ledger alongside your PR.

### 4.2 Weekly — scheduled job maintainer

The scheduled workflow commits manifest refreshes and opens or updates a
GitHub issue labelled `regulatory-change-watch` whenever an upstream change
is observed. Rotate through the following steps:

1. Triage the open issue. For each finding:
   - Open the publisher URL in the corresponding `strategy` block.
   - Confirm the change is real (not a transient ETag flap).
2. If the change is material, bump
   `data/provenance/ingest-manifest.json` (via the ingest scripts in
   `scripts/ingest/`) so the downstream crosswalks consume the new
   artefact.
3. Update affected UC sidecars and `data/regulations.json` clauses.
4. Clear the `openFinding` block on each reviewed watchlist entry in the
   same PR. `--check` will enforce that findings are resolved before
   release.
5. Request SME sign-off (see [`docs/sme-review-guide.md`](./sme-review-guide.md)).

### 4.3 Adding a new watchlist entry

1. Pick a strategy from §2 that fits the publisher's feed.
2. Add an entry to `data/regulations-watch.json`:

   ```json
   {
     "regulationId": "new-framework-id",
     "regulationName": "Human-readable title",
     "tier": 1,
     "currentVersion": "vX.Y",
     "strategy": { "type": "http-head", "url": "https://..." },
     "lastCheckedAt": "YYYY-MM-DDT00:00:00Z",
     "notes": "Publisher cadence, known gotchas."
   }
   ```

3. Ensure `regulationId` is either in `data/regulations.json` frameworks[]
   **or** in the MITRE allow-list (`mitre-attack-enterprise`, `d3fend`).
4. Run `python3 scripts/audit_regulatory_change_watch.py --check` and
   `--fetch` to confirm both gates pass.
5. Open the PR with a peer + legal + SME signoff noting the addition.

## 5. Design principles

- **Hermetic CI** — `--check` must never make network calls. Transient
  publisher outages must not fail pull requests.
- **Provenance over prediction** — The goal is not to auto-adopt upstream
  changes but to **prove**, at audit time, that we knew about them
  within a bounded time window.
- **Single source of truth** — Watch entries backed by
  `data/provenance/ingest-manifest.json` are cross-referenced on every
  `--check` run; drift between the two files is a hard error.
- **Fail loud, fail fast** — A stale tier-1 regulation blocks release.
  This is deliberate: our customers rely on clause-level mappings being
  current, not approximately current.

## 6. Testing

```bash
# Hermetic gate (no network)
python3 scripts/audit_regulatory_change_watch.py --check

# Seed/reset the ledger in bulk
python3 scripts/audit_regulatory_change_watch.py --freeze

# Probe every entry against its publisher (requires network)
python3 scripts/audit_regulatory_change_watch.py --fetch

# Fail if any probe errored (for the scheduled workflow's strict mode)
python3 scripts/audit_regulatory_change_watch.py --fetch --strict
```

The audit honours the `stalenessPolicy` block, so a shorter deadline
(e.g., `tier1FailDays: 30`) can be used during regulatory events — set it,
let CI fail on the laggards, run `--fetch`, and relax the threshold once
the queue is clear.

## See also

- [`docs/peer-review-guide.md`](./peer-review-guide.md) — Phase 4.5a peer review gate.
- [`docs/legal-review-guide.md`](./legal-review-guide.md) — Phase 4.5b legal review gate.
- [`docs/sme-review-guide.md`](./sme-review-guide.md) — Phase 5.2 SME review gate.
- [`docs/signed-provenance.md`](./signed-provenance.md) — Phase 5.4 signed provenance ledger. Upstream regulation drift detected here cascades into the next ledger regeneration, which recomputes every affected mapping's `canonicalHash` and re-anchors the merkle root. A failed change-watch that hides a material regulation change invalidates not just the affected UCs but the attestation covering the release that shipped them.
- [`docs/coverage-methodology.md`](./coverage-methodology.md) — how watchlist changes flow into coverage metrics.
