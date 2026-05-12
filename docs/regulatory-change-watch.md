# Regulatory change-watch (Phase 5.3)

> Status: **required** for any change to
> `data/regulations-watch.json`, `schemas/regulations-watch.schema.json`,
> `python3 -m splunk_uc audit-regulatory-change-watch`, or the `.github/workflows/regulatory-watch.yml` job.
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
| `python3 -m splunk_uc audit-regulatory-change-watch` | Audit + fetch + freeze tool. Three modes: `--check` (hermetic CI), `--fetch` (network probe), `--freeze` (seed/reset timestamps). |
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
| `rss-atom` | Publishers with a news feed (HHS/OCR HIPAA<sup class="ref">[<a href="#ref-12">12</a>]</sup> feed). | `lastObservedVersion` (count + titles of recent matches); `matchTerms` allow-lists relevant feed entries. |
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
ships a Splunk app for (GDPR<sup class="ref">[<a href="#ref-3">3</a>]</sup>, HIPAA Security, PCI DSS, SOC 2<sup class="ref">[<a href="#ref-1">1</a>]</sup>, SOX<sup class="ref">[<a href="#ref-10">10</a>]</sup> ITGC,
ISO 27001<sup class="ref">[<a href="#ref-6">6</a>]</sup>, NIST CSF, NIST 800-53, NIS2<sup class="ref">[<a href="#ref-2">2</a>]</sup>, DORA<sup class="ref">[<a href="#ref-4">4</a>]</sup>, CMMC). Use **tier 2** for
derivative jurisdictions (UK GDPR<sup class="ref">[<a href="#ref-13">13</a>]</sup>, CCPA, nFADP, LGPD, APPI), MITRE
frameworks, and anything else where a slow cadence is acceptable.

## 4. Operator workflows

### 4.1 Daily — reviewer responding to a PR check failure

1. Read the CI failure output. It will identify the affected watchlist
   entries and the number of stale days.
2. Decide if the staleness is benign (the weekly job silently failed, but
   no upstream changes exist) or material (the publisher changed and we
   have not yet adopted the change).
3. Run `python3 -m splunk_uc audit-regulatory-change-watch --fetch` locally.
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
4. Run `python3 -m splunk_uc audit-regulatory-change-watch --check` and
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
python3 -m splunk_uc audit-regulatory-change-watch --check

# Seed/reset the ledger in bulk
python3 -m splunk_uc audit-regulatory-change-watch --freeze

# Probe every entry against its publisher (requires network)
python3 -m splunk_uc audit-regulatory-change-watch --fetch

# Fail if any probe errored (for the scheduled workflow's strict mode)
python3 -m splunk_uc audit-regulatory-change-watch --fetch --strict
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

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** American Institute of Certified Public Accountants. (2017). *Trust Services Criteria (2017) for Security, Availability, Processing Integrity, Confidentiality, and Privacy*. AICPA & CIMA. SOC 2 / TSP Section 100. https://www.aicpa-cima.com/topic/audit-assurance/soc-suite-of-services

<a id="ref-2"></a>**[2]** European Parliament and Council of the European Union. (2022, December). *Directive (EU) 2022/2555 — NIS2 Directive on cybersecurity*. Official Journal of the European Union, L 333. ELI: dir/2022/2555. https://eur-lex.europa.eu/eli/dir/2022/2555/oj

<a id="ref-3"></a>**[3]** European Parliament and Council of the European Union. (2016, April). *Regulation (EU) 2016/679 — General Data Protection Regulation*. Official Journal of the European Union, L 119. ELI: reg/2016/679. https://eur-lex.europa.eu/eli/reg/2016/679/oj

<a id="ref-4"></a>**[4]** European Parliament and Council of the European Union. (2022, December). *Regulation (EU) 2022/2554 — Digital Operational Resilience Act (DORA)*. Official Journal of the European Union, L 333. ELI: reg/2022/2554. https://eur-lex.europa.eu/eli/reg/2022/2554/oj

<a id="ref-5"></a>**[5]** European Parliament and Council of the European Union. (2024, June). *Regulation (EU) 2024/1689 — EU Artificial Intelligence Act*. Official Journal of the European Union. ELI: reg/2024/1689. https://eur-lex.europa.eu/eli/reg/2024/1689/oj

<a id="ref-6"></a>**[6]** International Organization for Standardization. (2022). *ISO/IEC 27001:2022 — Information security, cybersecurity and privacy protection — Information security management systems — Requirements*. ISO/IEC. ISO/IEC 27001:2022. https://www.iso.org/standard/27001

<a id="ref-7"></a>**[7]** Payment Card Industry Security Standards Council. (2018). *Payment Card Industry Data Security Standard v3.2.1* (v3.2.1). PCI SSC. https://www.pcisecuritystandards.org/document_library/?category=pcidss

<a id="ref-8"></a>**[8]** Payment Card Industry Security Standards Council. (2022). *Payment Card Industry Data Security Standard v4.0* (v4.0). PCI SSC. https://www.pcisecuritystandards.org/document_library/?category=pcidss

<a id="ref-9"></a>**[9]** Public Company Accounting Oversight Board. (2007). *Auditing Standard 2201 — An Audit of Internal Control Over Financial Reporting*. PCAOB. PCAOB AS 2201. https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201

<a id="ref-10"></a>**[10]** U.S. Congress. (2002). *Sarbanes-Oxley Act of 2002 — Public Company Accounting Reform and Investor Protection Act*. U.S. Government. Pub. L. 107–204. https://www.sec.gov/about/laws/soa2002.pdf

<a id="ref-11"></a>**[11]** U.S. Department of Health & Human Services. (2002). *HIPAA Privacy Rule (45 CFR Parts 160 and 164, Subparts A and E)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/privacy/index.html

<a id="ref-12"></a>**[12]** U.S. Department of Health & Human Services. (2013). *HIPAA Security Rule (45 CFR Parts 160 and 164, Subparts A and C)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/security/index.html

<a id="ref-13"></a>**[13]** United Kingdom Parliament. (2018). *Data Protection Act 2018 (UK GDPR, retained EU law)*. The Stationery Office. 2018 c. 12. https://www.legislation.gov.uk/ukpga/2018/12/contents

### Cited by

- [`docs/mitre-attack-mapping.md`](mitre-attack-mapping.md)

<!-- END-AUTOGENERATED-SOURCES -->
