# Evidence Pack — HIPAA Security

> **Tier**: Tier 1 &nbsp;·&nbsp; **Jurisdiction**: US &nbsp;·&nbsp; **Version**: `2013-final`
>
> **Full name**: HIPAA Security Rule
> **Authoritative source**: [https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C)
> **Effective from**: 2013-09-23

> This evidence pack is the auditor-facing view of the Splunk monitoring catalogue's coverage of the regulation. Every clause coverage claim is traceable to a specific UC sidecar JSON file (`use-cases/cat-*/uc-*.json`); every retention figure cites its legal basis; every URL resolves to an official regulator or standards-body source. The pack does **not** assert legal conclusions — it tabulates what the catalogue covers, names the authoritative source, and flags gaps. Interpretation stays with counsel.

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

The HIPAA Security Rule (45 CFR Part 164 Subpart C) sets national standards for the confidentiality, integrity, and availability of electronic protected health information (ePHI). Enforced by the HHS Office for Civil Rights (OCR) through corrective-action plans, resolution agreements, and civil monetary penalties. Often audited together with the Privacy Rule (Subpart E) and Breach Notification Rule (Subpart D).

## 2. Scope and applicability

Applies to covered entities (health plans, healthcare clearinghouses, most healthcare providers who conduct electronic transactions) and business associates who create, receive, maintain, or transmit ePHI on behalf of a covered entity. Business associates are directly liable for Security Rule compliance since the 2013 Omnibus Rule.

**Territorial scope.** United States, with extraterritorial reach to any entity processing ePHI of US patients.

## 3. Catalogue coverage at a glance

- **Clauses tracked**: 15
- **Clauses covered by at least one UC**: 15 / 15 (100.0%)
- **Priority-weighted coverage**: 100.0%
- **Contributing UCs**: 35

Coverage methodology is documented in [`docs/coverage-methodology.md`](../coverage-methodology.md). Priority weights come from `data/regulations.json` commonClauses entries (see [`data/regulations.json`](../../data/regulations.json) priorityWeightRubric).

## 4. Clause-by-clause coverage

Clauses are listed in the order defined by `data/regulations.json commonClauses` for this regulation version. A clause is considered covered when at least one UC sidecar has a `compliance[]` entry matching `(regulation, version, clause)`. Assurance is the maximum across contributing UCs.

| Clause | Topic | Priority | Assurance | UCs |
|---|---|---|---|---|
| [`§164.308(a)(1)`](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-{section}#p-§164.308(a)(1)) | Security management process | 1.0 | `contributing` | [UC-22.10.1](#uc-22-10-1), [UC-22.10.2](#uc-22-10-2), [UC-22.10.22](#uc-22-10-22), [UC-22.10.55](#uc-22-10-55) |
| [`§164.308(a)(3)`](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-{section}#p-§164.308(a)(3)) | Workforce security | 1.0 | `contributing` | [UC-22.10.4](#uc-22-10-4) |
| [`§164.308(a)(4)`](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-{section}#p-§164.308(a)(4)) | Information access management | 1.0 | `full` | [UC-22.10.21](#uc-22-10-21) |
| [`§164.308(a)(5)`](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-{section}#p-§164.308(a)(5)) | Security awareness and training | 0.7 | `full` | [UC-22.10.6](#uc-22-10-6), [UC-22.46.1](#uc-22-46-1), [UC-22.6.53](#uc-22-6-53) |
| [`§164.308(a)(6)`](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-{section}#p-§164.308(a)(6)) | Security incident procedures | 1.0 | `partial` | [UC-22.10.7](#uc-22-10-7), [UC-22.39.1](#uc-22-39-1) |
| [`§164.308(a)(7)`](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-{section}#p-§164.308(a)(7)) | Contingency plan | 1.0 | `full` | [UC-22.10.8](#uc-22-10-8), [UC-22.45.2](#uc-22-45-2) |
| [`§164.308(a)(8)`](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-{section}#p-§164.308(a)(8)) | Evaluation | 0.7 | `contributing` | [UC-22.10.9](#uc-22-10-9) |
| [`§164.310(a)(1)`](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-{section}#p-§164.310(a)(1)) | Facility access controls | 1.0 | `contributing` | [UC-22.10.31](#uc-22-10-31) |
| [`§164.310(d)(1)`](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-{section}#p-§164.310(d)(1)) | Device and media controls | 0.7 | `full` | [UC-22.10.29](#uc-22-10-29), [UC-22.49.1](#uc-22-49-1), [UC-22.49.2](#uc-22-49-2) |
| [`§164.312(a)(1)`](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-{section}#p-§164.312(a)(1)) | Access control | 1.0 | `contributing` | [UC-22.10.21](#uc-22-10-21), [UC-22.10.24](#uc-22-10-24), [UC-22.10.25](#uc-22-10-25) |
| [`§164.312(a)(2)(iv)`](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-{section}#p-§164.312(a)(2)(iv)) | Encryption and decryption | 0.7 | `full` | [UC-22.10.16](#uc-22-10-16), [UC-22.41.1](#uc-22-41-1) |
| [`§164.312(b)`](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-{section}#p-§164.312(b)) | Audit controls | 1.0 | `contributing` | [UC-22.10.17](#uc-22-10-17), [UC-22.10.36](#uc-22-10-36) |
| [`§164.312(c)(1)`](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-{section}#p-§164.312(c)(1)) | Integrity | 1.0 | `full` | [UC-22.10.18](#uc-22-10-18), [UC-22.10.27](#uc-22-10-27), [UC-22.35.2](#uc-22-35-2) |
| [`§164.312(d)`](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-{section}#p-§164.312(d)) | Person or entity authentication | 1.0 | `contributing` | [UC-22.10.19](#uc-22-10-19), [UC-22.10.23](#uc-22-10-23), [UC-22.10.42](#uc-22-10-42) |
| [`§164.312(e)(1)`](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-{section}#p-§164.312(e)(1)) | Transmission security | 1.0 | `full` | [UC-22.10.20](#uc-22-10-20), [UC-22.10.22](#uc-22-10-22), [UC-22.10.26](#uc-22-10-26), [UC-22.41.2](#uc-22-41-2), [UC-22.8.31](#uc-22-8-31), [UC-22.8.38](#uc-22-8-38) |

### 4.1 Contributing UC detail

<a id='uc-22-10-1'></a>
- **UC-22.10.1** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-10-16'></a>
- **UC-22.10.16** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-10-17'></a>
- **UC-22.10.17** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-10-18'></a>
- **UC-22.10.18** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-10-19'></a>
- **UC-22.10.19** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-10-2'></a>
- **UC-22.10.2** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-10-20'></a>
- **UC-22.10.20** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-10-21'></a>
- **UC-22.10.21** — Access Control — Role-Based Violations (Coder Accessing Medication Admin)
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.10.21.json`](../../use-cases/cat-22/uc-22.10.21.json)
<a id='uc-22-10-22'></a>
- **UC-22.10.22** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-10-23'></a>
- **UC-22.10.23** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-10-24'></a>
- **UC-22.10.24** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-10-25'></a>
- **UC-22.10.25** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-10-26'></a>
- **UC-22.10.26** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-10-27'></a>
- **UC-22.10.27** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-10-29'></a>
- **UC-22.10.29** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-10-31'></a>
- **UC-22.10.31** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-10-36'></a>
- **UC-22.10.36** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-10-4'></a>
- **UC-22.10.4** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-10-42'></a>
- **UC-22.10.42** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-10-55'></a>
- **UC-22.10.55** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-10-6'></a>
- **UC-22.10.6** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-10-7'></a>
- **UC-22.10.7** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-10-8'></a>
- **UC-22.10.8** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-10-9'></a>
- **UC-22.10.9** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-35-2'></a>
- **UC-22.35.2** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-39-1'></a>
- **UC-22.39.1** —
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
<a id='uc-22-45-2'></a>
- **UC-22.45.2** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-46-1'></a>
- **UC-22.46.1** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-49-1'></a>
- **UC-22.49.1** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-49-2'></a>
- **UC-22.49.2** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-6-53'></a>
- **UC-22.6.53** — ISO/IEC 27001:2022 Clause 7.2 — Competence evidence: role-based training completion
  - Control family: `training-effectiveness`
  - Owner: `HR`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.6.53.json`](../../use-cases/cat-22/uc-22.6.53.json)
<a id='uc-22-8-31'></a>
- **UC-22.8.31** — SOC 2 CC6.6 — Encryption-in-transit validation: cleartext protocols crossing the trust boundary
  - Control family: `crypto-drift`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.8.31.json`](../../use-cases/cat-22/uc-22.8.31.json)
<a id='uc-22-8-38'></a>
- **UC-22.8.38** — SOC 2 C1.1 — Confidentiality: sensitive-data exposure at the egress boundary
  - Control family: `data-flow-cross-border`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.8.38.json`](../../use-cases/cat-22/uc-22.8.38.json)

## 5. Evidence collection

### 5.1 Common evidence sources

Auditors typically request the following records when examining this regulation:

- Electronic Health Record (EHR) system audit logs
- Medical device syslog / telemetry
- VPN and remote-access logs for clinician workstations
- Privileged-access monitoring logs (EHR admin, DBA)
- Encryption-at-rest configuration evidence (BitLocker, native DB encryption)
- Mobile device management (MDM) logs for devices with ePHI access
- Email DLP logs for outbound ePHI transmissions
- Physical-access logs (badge readers, video) for data-centre and clinical areas

### 5.2 Retention requirements

| Artifact | Retention | Legal basis |
|---|---|---|
| Policies and procedures (§164.316(a)) | 6 years from creation or last effective date, whichever is later | 45 CFR §164.316(b)(2)(i) |
| Risk-analysis documentation (§164.308(a)(1)(ii)(A)) | 6 years minimum | 45 CFR §164.316(b)(2) |
| Audit logs (§164.312(b)) | 6 years; state laws may extend | 45 CFR §164.316(b)(2); state statutes |
| Breach-notification records (§164.414) | 6 years post-notification | 45 CFR §164.316(b)(2) |
| Business Associate Agreements (BAAs) | 6 years post-termination | 45 CFR §164.316(b)(2) |
| Training records (§164.308(a)(5)) | 6 years post-employment | 45 CFR §164.316(b)(2) |

> Retention figures above are the legal minimums or regulator-stated expectations. Organisation-specific retention schedules may be longer where business, tax, litigation-hold, or contractual obligations apply. Where a figure conflicts with local data-protection law (e.g. GDPR Art.5(1)(e) storage-limitation principle), the shorter conformant period governs for personal-data content; the evidence-of-compliance retention retains the longer period for audit purposes, scrubbed of excess personal data.

### 5.3 Evidence integrity expectations

Regulators increasingly cite **evidence-integrity failures** as aggravating factors in enforcement actions. Cross-regulation baseline expectations:

- Time-stamped, tamper-evident storage (WORM, cryptographic chaining, or append-only indexes).
- Chain-of-custody for any evidence removed from the SIEM / production system for audit or legal purposes.
- Synchronised clocks (NTP stratum ≤ 3 or equivalent) across all in-scope sources so timeline reconstruction is defensible.
- Documented retention enforcement — not just retention policy — so that deletion is auditable.

See cat-22.35 "Evidence continuity and log integrity" for UCs that implement these controls.

## 6. Control testing procedures

OCR performs both complaint-driven investigations (most common) and periodic OCR audits. The OCR Audit Protocol is public and used as a testing template by most internal audit functions. External auditors test against the 45 CFR §164.308-§164.318 requirements, splitting into Administrative (§164.308), Physical (§164.310), and Technical Safeguards (§164.312). Addressable specifications must be either implemented or substituted with a documented risk-based alternative; Addressable ≠ Optional is a frequent audit finding.

**Reporting cadence.** No mandatory certification. Most covered entities align with annual internal audit + triennial external review. Business-associate monitoring should be annual minimum. OCR Phase 3 audits (2024-2026) sample covered entities and business associates for focused reviews.

## 7. Roles and responsibilities

| Role | Responsibility |
|---|---|
| **Covered Entity** | Primary obligation-bearer; must implement all Security Rule administrative, physical, and technical safeguards. |
| **Business Associate** | Directly liable under Omnibus Rule; must sign BAA; must implement Security Rule safeguards. |
| **Privacy Officer (§164.530(a))** | Designated individual responsible for Privacy Rule compliance; often bundled with Security Officer role. |
| **Security Officer (§164.308(a)(2))** | Designated individual responsible for developing and implementing security policies and procedures. |
| **HHS Office for Civil Rights (OCR)** | Federal enforcement body; conducts investigations, OCR audits, and imposes civil monetary penalties. |
| **State Attorneys General** | May bring HIPAA enforcement actions on behalf of state residents under HITECH s.13410(e). |

## 8. Authoritative guidance

- **HHS HIPAA Security Rule Guidance** — HHS OCR — [https://www.hhs.gov/hipaa/for-professionals/security/guidance/index.html](https://www.hhs.gov/hipaa/for-professionals/security/guidance/index.html)
- **NIST SP 800-66 Rev.2 Implementing the HIPAA Security Rule** — NIST — [https://csrc.nist.gov/publications/detail/sp/800-66/rev-2/final](https://csrc.nist.gov/publications/detail/sp/800-66/rev-2/final)
- **HHS OCR Audit Protocol (2016/2020)** — HHS OCR — [https://www.hhs.gov/hipaa/for-professionals/compliance-enforcement/audit/protocol/index.html](https://www.hhs.gov/hipaa/for-professionals/compliance-enforcement/audit/protocol/index.html)
- **HHS OCR Resolution Agreements & Civil Money Penalties** — HHS OCR — [https://www.hhs.gov/hipaa/for-professionals/compliance-enforcement/agreements/index.html](https://www.hhs.gov/hipaa/for-professionals/compliance-enforcement/agreements/index.html)
- **ONC SAFER Guides (Safe EHR implementation)** — ONC — [https://www.healthit.gov/topic/safety/safer-guides](https://www.healthit.gov/topic/safety/safer-guides)

## 9. Common audit deficiencies

Findings frequently cited by regulators, certification bodies, and external auditors for this regulation. These should be pre-tested as part of readiness reviews.

- Risk analysis is enterprise-wide but does not specifically address ePHI flows; Addressable specifications handled as Optional rather than documented risk-based decisions.
- Audit-log review (§164.308(a)(1)(ii)(D)) is not documented or is done only post-incident.
- BAAs are in place but never re-validated when Business Associates change scope or subcontractors.
- Encryption of ePHI at rest uses a single key for all data with no rotation; loss of a single workstation key exposes the entire estate.
- Training records cannot demonstrate role-specific content; generic HIPAA awareness is treated as meeting the §164.308(a)(5) requirement.
- Emergency-access procedure is documented but has never been tested; no drill evidence exists.

## 10. Enforcement and penalties

HITECH four-tier structure (45 CFR §160.404): Tier 1 (no knowledge) USD 137-68,928 per violation; Tier 2 (reasonable cause) USD 1,379-68,928; Tier 3 (willful neglect corrected) USD 13,785-68,928; Tier 4 (willful neglect uncorrected) USD 68,928-2,067,813 per violation. Annual cap USD 2,067,813 per violation category (2024 dollar amounts, inflation-adjusted annually). Criminal penalties under 42 USC §1320d-6 (up to USD 250,000 fine + 10 years imprisonment for malicious ePHI disclosure).

## 11. Pack gaps and remediation backlog

All clauses tracked in `data/regulations.json` for this regulation version are covered by at least one UC. **100 % common-clause coverage**. Remaining work is assurance-upgrade (for example, moving `contributing` entries to `partial` or `full` via explicit control tests) rather than new clause authoring.

## 12. Questions an auditor should ask

These are the questions a regulator, certification body, or external auditor is likely to ask. The pack helps preparers stage evidence and pre-test responses before the review opens.

- Produce your most recent Security Rule risk analysis (§164.308(a)(1)(ii)(A)); when was it last updated and what changes triggered the update?
- Show me audit logs for the last 90 days covering system activity review (§164.308(a)(1)(ii)(D)); demonstrate regular review.
- For every workforce member with ePHI access, produce the last unique-user identifier assignment (§164.312(a)(2)(i)) and their access-authorisation approval.
- Demonstrate emergency-access procedure (§164.312(a)(2)(ii)) has been tested; produce the most recent drill report.
- Show evidence of automatic logoff (§164.312(a)(2)(iii)) on systems containing ePHI.
- Produce the last three ePHI transmissions outside your network; demonstrate the encryption (§164.312(e)(1)) used and the key-management lifecycle.
- Provide the current list of Business Associates; for each, produce the BAA and the last compliance-review documentation.
- Demonstrate the breach-response playbook in action: produce the last incident that was assessed for breach-notification (60-day clock under §164.404) and show how the risk assessment was performed.

## 13. Machine-readable twin

The machine-readable companion of this pack lives at [`api/v1/evidence-packs/hipaa-security.json`](../../api/v1/evidence-packs/hipaa-security.json). It contains the same clause-level coverage, retention guidance, role matrix, and gap list in JSON form, and is regenerated in lockstep with this markdown pack so content stays in sync. Consumers integrating the pack into GRC tools, audit-request portals, or evidence pipelines should consume the JSON document; human readers should consume this markdown.

Related API surfaces (all under [`api/v1/`](../../api/v1/README.md)):

- [`api/v1/compliance/regulations/hipaa-security.json`](../../api/v1/compliance/regulations/hipaa-security.json) — regulation metadata and per-version coverage metrics
- [`api/v1/compliance/ucs/`](../../api/v1/compliance/ucs/index.json) — individual UC sidecars
- [`api/v1/compliance/coverage.json`](../../api/v1/compliance/coverage.json) — global coverage snapshot
- [`api/v1/compliance/gaps.json`](../../api/v1/compliance/gaps.json) — global gap report

## 14. Provenance and regeneration

This pack is **generated**, not hand-authored. Re-running the generator produces byte-identical output (deterministic sort, stable serialisation, no free-form timestamps outside the block below). CI enforces regeneration drift via `--check` mode.

**Inputs to this pack**

- [`data/regulations.json`](../../data/regulations.json) — commonClauses, priority weights, authoritative URLs
- [`data/evidence-pack-extras.json`](../../data/evidence-pack-extras.json) — retention, roles, authoritative guidance, penalty, testing approach
- [`use-cases/cat-*/uc-*.json`](../../use-cases) — UC sidecars containing compliance[] entries, controlFamily, owner, evidence fields
- [`api/v1/compliance/regulations/hipaa-security@*.json`](../../api/v1/compliance/regulations/) — pre-computed coverage metrics (when present)

- Generator: [`scripts/generate_evidence_packs.py`](../../scripts/generate_evidence_packs.py)
- Evidence-pack directory index: [`docs/evidence-packs/README.md`](README.md)

**Generation metadata**

```
catalogue_version: 6.0
generator_script:  scripts/generate_evidence_packs.py
inputs_sha256:     eceb48321d6d6223c896ea1309066c147e35a478780e5a8de46f2f7ad1a08de4
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
