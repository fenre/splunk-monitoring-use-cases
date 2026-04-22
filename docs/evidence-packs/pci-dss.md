# Evidence Pack — PCI DSS

> **Tier**: Tier 1 &nbsp;·&nbsp; **Jurisdiction**: GLOBAL &nbsp;·&nbsp; **Version**: `v4.0`
>
> **Full name**: Payment Card Industry Data Security Standard
> **Authoritative source**: [https://www.pcisecuritystandards.org/document_library/](https://www.pcisecuritystandards.org/document_library/)
> **Effective from**: 2022-03-31

> This evidence pack is the auditor-facing view of the Splunk monitoring catalogue's coverage of the regulation. Every clause coverage claim is traceable to a specific UC sidecar JSON file (`use-cases/cat-*/uc-*.json`); every retention figure cites its legal basis; every URL resolves to an official regulator or standards-body source. The pack does **not** assert legal conclusions — it tabulates what the catalogue covers, names the authoritative source, and flags gaps. Interpretation stays with counsel.

> **Live views.** [Buyer narrative (`compliance-story.html?reg=pci-dss`)](../../compliance-story.html?reg=pci-dss) · [Auditor clause navigator (`clause-navigator.html#reg=pci-dss`)](../../clause-navigator.html#reg=pci-dss) · [JSON twin (`api/v1/compliance/story/pci-dss.json`)](../../api/v1/compliance/story/pci-dss.json)

## Table of contents

1. [Purpose of this evidence pack](#1-purpose-of-this-evidence-pack)
2. [Scope and applicability](#2-scope-and-applicability)
3. [Catalogue coverage at a glance](#3-catalogue-coverage-at-a-glance)
4. [Clause-by-clause coverage](#4-clause-by-clause-coverage)
5. [Evidence collection](#5-evidence-collection)
6. [Control testing procedures](#6-control-testing-procedures)
7. [Roles and responsibilities](#7-roles-and-responsibilities)
8. [Authoritative guidance](#8-authoritative-guidance)
9. [Common audit deficiencies](#9-common-audit-deficiencies)
10. [Enforcement and penalties](#10-enforcement-and-penalties)
11. [Pack gaps and remediation backlog](#11-pack-gaps-and-remediation-backlog)
12. [Questions an auditor should ask](#12-questions-an-auditor-should-ask)
13. [Machine-readable twin](#13-machine-readable-twin)
14. [Provenance and regeneration](#14-provenance-and-regeneration)

## 1. Purpose of this evidence pack

Payment Card Industry Data Security Standard v4.0 (effective 31 March 2024, future-dated requirements effective 31 March 2025) is the industry-mandated control baseline for any organisation that stores, processes, or transmits cardholder data or that can impact the security of the cardholder data environment. v4.0 replaces v3.2.1 entirely and introduces the Customised Approach to demonstrate control objectives through alternative implementation.

## 2. Scope and applicability

All merchants, service providers, issuers, and acquirers that handle primary account numbers (PANs), sensitive authentication data (SAD), or that can impact the security of the cardholder data environment (CDE). Compliance scope extends to any system component in the CDE or connected to the CDE.

**Territorial scope.** Global, contractually enforced by the payment card brands (Visa, Mastercard, American Express, Discover, JCB) and acquirers. Not a statute; a contractual standard.

## 3. Catalogue coverage at a glance

- **Clauses tracked**: 22
- **Clauses covered by at least one UC**: 22 / 22 (100.0%)
- **Priority-weighted coverage**: 100.0%
- **Contributing UCs**: 23

Coverage methodology is documented in [`docs/coverage-methodology.md`](../coverage-methodology.md). Priority weights come from `data/regulations.json` commonClauses entries (see [`data/regulations.json`](../../data/regulations.json) priorityWeightRubric).

## 4. Clause-by-clause coverage

Clauses are listed in the order defined by `data/regulations.json commonClauses` for this regulation version. A clause is considered covered when at least one UC sidecar has a `compliance[]` entry matching `(regulation, version, clause)`. Assurance is the maximum across contributing UCs.

| Clause | Topic | Priority | Assurance | UCs |
|---|---|---|---|---|
| [`1.2`](https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf#clause=1.2) | Network security controls configuration | 1.0 | `partial` | [UC-22.42.2](#uc-22-42-2) |
| [`1.3`](https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf#clause=1.3) | CDE network boundary | 1.0 | `full` | [UC-22.11.91](#uc-22-11-91) |
| [`2.2`](https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf#clause=2.2) | Secure system component configuration | 1.0 | `full` | [UC-22.11.92](#uc-22-11-92) |
| [`3.3`](https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf#clause=3.3) | Sensitive authentication data not stored | 1.0 | `full` | [UC-22.11.93](#uc-22-11-93) |
| [`3.5`](https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf#clause=3.5) | PAN protection | 1.0 | `full` | [UC-22.41.1](#uc-22-41-1) |
| [`4.2`](https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf#clause=4.2) | Strong cryptography for CHD in transit | 1.0 | `full` | [UC-22.41.2](#uc-22-41-2) |
| [`5.2`](https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf#clause=5.2) | Anti-malware mechanisms | 1.0 | `full` | [UC-22.11.94](#uc-22-11-94) |
| [`6.2`](https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf#clause=6.2) | Bespoke software developed securely | 1.0 | `full` | [UC-22.11.95](#uc-22-11-95) |
| [`6.3`](https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf#clause=6.3) | Vulnerabilities identified and addressed | 1.0 | `full` | [UC-22.43.1](#uc-22-43-1), [UC-22.43.2](#uc-22-43-2) |
| [`7.2`](https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf#clause=7.2) | Access granted on least privilege | 1.0 | `partial` | [UC-22.48.1](#uc-22-48-1) |
| [`8.3`](https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf#clause=8.3) | Strong authentication | 1.0 | `full` | [UC-22.11.96](#uc-22-11-96) |
| [`8.4`](https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf#clause=8.4) | MFA | 1.0 | `full` | [UC-22.11.97](#uc-22-11-97) |
| [`8.6`](https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf#clause=8.6) | Application and system accounts | 1.0 | `full` | [UC-22.11.98](#uc-22-11-98) |
| [`10.2`](https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf#clause=10.2) | Audit logs captured for all system components | 1.0 | `partial` | [UC-22.40.1](#uc-22-40-1) |
| [`10.3`](https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf#clause=10.3) | Audit logs protected from modification | 1.0 | `full` | [UC-22.11.99](#uc-22-11-99) |
| [`10.4`](https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf#clause=10.4) | Time synchronised | 1.0 | `full` | [UC-22.11.100](#uc-22-11-100) |
| [`10.6`](https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf#clause=10.6) | Logs reviewed | 1.0 | `full` | [UC-22.11.101](#uc-22-11-101) |
| [`10.7`](https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf#clause=10.7) | Log retention | 1.0 | `full` | [UC-22.11.102](#uc-22-11-102) |
| [`11.3`](https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf#clause=11.3) | External and internal vulnerabilities identified | 1.0 | `full` | [UC-22.11.103](#uc-22-11-103) |
| [`11.4`](https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf#clause=11.4) | Intrusion detection / prevention | 1.0 | `full` | [UC-22.11.104](#uc-22-11-104) |
| [`12.3`](https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf#clause=12.3) | Targeted risk analysis | 0.7 | `full` | [UC-22.11.106](#uc-22-11-106) |
| [`12.10`](https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf#clause=12.10) | Security incident response | 1.0 | `full` | [UC-22.11.105](#uc-22-11-105) |

### 4.1 Contributing UC detail

<a id='uc-22-11-100'></a>
- **UC-22.11.100** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-11-101'></a>
- **UC-22.11.101** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-11-102'></a>
- **UC-22.11.102** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-11-103'></a>
- **UC-22.11.103** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-11-104'></a>
- **UC-22.11.104** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-11-105'></a>
- **UC-22.11.105** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-11-106'></a>
- **UC-22.11.106** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-11-91'></a>
- **UC-22.11.91** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-11-92'></a>
- **UC-22.11.92** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-11-93'></a>
- **UC-22.11.93** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-11-94'></a>
- **UC-22.11.94** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-11-95'></a>
- **UC-22.11.95** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-11-96'></a>
- **UC-22.11.96** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-11-97'></a>
- **UC-22.11.97** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-11-98'></a>
- **UC-22.11.98** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-11-99'></a>
- **UC-22.11.99** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-40-1'></a>
- **UC-22.40.1** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-41-1'></a>
- **UC-22.41.1** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-41-2'></a>
- **UC-22.41.2** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-42-2'></a>
- **UC-22.42.2** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-43-1'></a>
- **UC-22.43.1** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-43-2'></a>
- **UC-22.43.2** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-48-1'></a>
- **UC-22.48.1** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)

## 5. Evidence collection

### 5.1 Common evidence sources

Auditors typically request the following records when examining this regulation:

- Firewall and router configuration exports
- CDE-boundary network diagrams and data-flow diagrams
- Identity/IAM logs for all CDE access
- Database audit logs for PAN-containing tables
- FIM (file-integrity monitoring) event streams
- Change-management ticketing system records
- Vulnerability-scan reports (ASV + internal)
- Penetration-test reports with remediation evidence
- Training records for all personnel with CDE access

### 5.2 Retention requirements

| Artifact | Retention | Legal basis |
|---|---|---|
| Audit log records (Req 10) | Minimum 12 months retained; 3 months immediately accessible | PCI DSS v4.0 Req 10.5.1 |
| Quarterly internal vulnerability-scan records (Req 11.3.1) | 12 months minimum | PCI DSS v4.0 Req 11.3.1.1 |
| ASV external scan records (Req 11.3.2) | 12 months minimum | ASV Program Guide |
| Penetration-test reports (Req 11.4) | 3 years minimum | PCI SSC Penetration Testing Guidance |
| Attestation of Compliance (AOC) / Report on Compliance (ROC) | 3 years minimum | PCI SSC QSA program requirements |
| Key-management records (Req 3.6, 3.7) | Duration of key + 1 year | PCI DSS v4.0 Req 3.7 |

> Retention figures above are the legal minimums or regulator-stated expectations. Organisation-specific retention schedules may be longer where business, tax, litigation-hold, or contractual obligations apply. Where a figure conflicts with local data-protection law (e.g. GDPR Art.5(1)(e) storage-limitation principle), the shorter conformant period governs for personal-data content; the evidence-of-compliance retention retains the longer period for audit purposes, scrubbed of excess personal data.

### 5.3 Evidence integrity expectations

Regulators increasingly cite **evidence-integrity failures** as aggravating factors in enforcement actions. Cross-regulation baseline expectations:

- Time-stamped, tamper-evident storage (WORM, cryptographic chaining, or append-only indexes).
- Chain-of-custody for any evidence removed from the SIEM / production system for audit or legal purposes.
- Synchronised clocks (NTP stratum ≤ 3 or equivalent) across all in-scope sources so timeline reconstruction is defensible.
- Documented retention enforcement — not just retention policy — so that deletion is auditable.

See cat-22.35 "Evidence continuity and log integrity" for UCs that implement these controls.

## 6. Control testing procedures

QSAs conduct a Report on Compliance (ROC) annually for Level 1 merchants (>6M card transactions/year) and many service providers. Lower-volume merchants complete Self-Assessment Questionnaires (SAQ A, A-EP, B, B-IP, C, C-VT, D, D-SP, P2PE-HW, SPoC). QSA testing combines interview, documentation review, configuration sampling, and observation. Penetration testing (Req 11.4) is a substantive external control; failure to close criticals blocks AOC sign-off.

**Reporting cadence.** Annual AOC/ROC signed by QSA (Level 1) or executive attestation (SAQ levels). Quarterly ASV scans required. Segmentation testing: quarterly (service providers), annually (merchants). Penetration testing: annually + after significant change.

## 7. Roles and responsibilities

| Role | Responsibility |
|---|---|
| **Merchant / Service Provider** | Maintain continuous compliance with all applicable PCI DSS requirements; produce AOC or ROC annually. |
| **Acquirer (merchant bank)** | Verify merchant compliance status; enforce compliance contractually; report to card brands. |
| **QSA (Qualified Security Assessor)** | Perform ROC-level assessments; sign AOC/ROC; maintain QSA qualification with PCI SSC. |
| **ASV (Approved Scanning Vendor)** | Conduct external vulnerability scans under Req 11.3.2; maintain ASV qualification. |
| **PCI SSC** | Standards-setting body; maintains PCI DSS, QSA/ASV programs, and audit-methodology documents. |
| **Payment brands (Visa, Mastercard, Amex, Discover, JCB)** | Enforce compliance; set merchant levels; impose fines for non-compliance and breaches. |

## 8. Authoritative guidance

- **PCI DSS v4.0 Requirements and Testing Procedures** — PCI SSC — [https://www.pcisecuritystandards.org/document_library](https://www.pcisecuritystandards.org/document_library)
- **PCI DSS v4.0 Report on Compliance (ROC) Reporting Template** — PCI SSC — [https://www.pcisecuritystandards.org/document_library](https://www.pcisecuritystandards.org/document_library)
- **PCI SSC Penetration Testing Guidance** — PCI SSC — [https://www.pcisecuritystandards.org/document_library](https://www.pcisecuritystandards.org/document_library)
- **PCI DSS v4.0 Summary of Changes** — PCI SSC — [https://www.pcisecuritystandards.org/documents/PCI-DSS-v4-0-Summary-of-Changes-r1.pdf](https://www.pcisecuritystandards.org/documents/PCI-DSS-v4-0-Summary-of-Changes-r1.pdf)
- **PCI SSC Scoping and Segmentation Guidance** — PCI SSC — [https://www.pcisecuritystandards.org/document_library](https://www.pcisecuritystandards.org/document_library)

## 9. Common audit deficiencies

Findings frequently cited by regulators, certification bodies, and external auditors for this regulation. These should be pre-tested as part of readiness reviews.

- CDE scoping fails to include systems that authenticate to or otherwise impact CDE components (Req 2.2.1).
- Log-review evidence under Req 10.4.1 is checkbox-only; no documented triage outcome.
- Quarterly vulnerability scans have failing scans not re-run until the next quarter (Req 11.3.1.2).
- Change-management records do not show security impact assessment (Req 6.5.2).
- SAD retention controls (Req 3.3) are missing for call-centre or IVR recordings containing card data.
- Multi-factor authentication gaps for non-console administrative access (Req 8.4.2).

## 10. Enforcement and penalties

No statutory penalty structure; enforcement is contractual. Payment brands (via acquirers) impose non-compliance fines of USD 5,000-100,000+ per month and can increase interchange fees or terminate merchant relationships. In the event of a breach with confirmed non-compliance, fraud-loss recovery, forensic-investigation costs (PFI program), card-reissuance costs, and permanent loss of merchant privileges are all possible.

## 11. Pack gaps and remediation backlog

All clauses tracked in `data/regulations.json` for this regulation version are covered by at least one UC. **100 % common-clause coverage**. Remaining work is assurance-upgrade (for example, moving `contributing` entries to `partial` or `full` via explicit control tests) rather than new clause authoring.

## 12. Questions an auditor should ask

These are the questions a regulator, certification body, or external auditor is likely to ask. The pack helps preparers stage evidence and pre-test responses before the review opens.

- Produce the current PCI DSS scoping document; demonstrate how systems connected to the CDE are identified and justified.
- Show me 90 days of log records covering Req 10.2.1 (all individual user accesses to cardholder data); demonstrate the logs have been reviewed daily per Req 10.4.1.
- Demonstrate FIM (file-integrity monitoring) alerting under Req 11.5.2; produce the last three investigations of detected changes.
- Show evidence that sensitive authentication data (SAD) is not retained after authorisation per Req 3.3.
- Produce the last penetration test (Req 11.4.3 external, 11.4.4 internal) and the remediation tracking for each finding.
- Demonstrate segmentation testing under Req 11.4.5 — at least quarterly for service providers, annually for merchants.
- For Customised Approach items, produce the Targeted Risk Analysis (TRA) that justifies the alternative implementation.

## 13. Machine-readable twin

The machine-readable companion of this pack lives at [`api/v1/evidence-packs/pci-dss.json`](../../api/v1/evidence-packs/pci-dss.json). It contains the same clause-level coverage, retention guidance, role matrix, and gap list in JSON form, and is regenerated in lockstep with this markdown pack so content stays in sync. Consumers integrating the pack into GRC tools, audit-request portals, or evidence pipelines should consume the JSON document; human readers should consume this markdown.

Related API surfaces (all under [`api/v1/`](../../api/README.md)):

- [`api/v1/compliance/regulations/pci-dss.json`](../../api/v1/compliance/regulations/pci-dss.json) — regulation metadata and per-version coverage metrics
- [`api/v1/compliance/ucs/`](../../api/v1/compliance/ucs/index.json) — individual UC sidecars
- [`api/v1/compliance/coverage.json`](../../api/v1/compliance/coverage.json) — global coverage snapshot
- [`api/v1/compliance/gaps.json`](../../api/v1/compliance/gaps.json) — global gap report

## 14. Provenance and regeneration

This pack is **generated**, not hand-authored. Re-running the generator produces byte-identical output (deterministic sort, stable serialisation, no free-form timestamps outside the block below). CI enforces regeneration drift via `--check` mode.

**Inputs to this pack**

- [`data/regulations.json`](../../data/regulations.json) — commonClauses, priority weights, authoritative URLs
- [`data/evidence-pack-extras.json`](../../data/evidence-pack-extras.json) — retention, roles, authoritative guidance, penalty, testing approach
- [`use-cases/cat-*/uc-*.json`](../../use-cases) — UC sidecars containing compliance[] entries, controlFamily, owner, evidence fields
- [`api/v1/compliance/regulations/pci-dss@*.json`](../../api/v1/compliance/regulations/) — pre-computed coverage metrics (when present)

- Generator: [`scripts/generate_evidence_packs.py`](../../scripts/generate_evidence_packs.py)
- Evidence-pack directory index: [`docs/evidence-packs/README.md`](README.md)

**Generation metadata**

```
catalogue_version: 7.1
generator_script:  scripts/generate_evidence_packs.py
inputs_sha256:     d182323bff36ebe11168f94776fbb9639b116f5b15f71d1bf7d161c41626f5bc
```

To re-generate:

```bash
python3 scripts/generate_evidence_packs.py
```

To verify no drift in CI:

```bash
python3 scripts/generate_evidence_packs.py --check
```

---

**Licensed under the terms in [`LICENSE`](../../LICENSE).** This pack is provided for compliance-readiness and evidence-collection purposes. It does **not** constitute legal advice. Interpretation of clauses and applicability to a specific organisation requires counsel review. Retention figures are minimum defaults; organisation-specific schedules may extend.
