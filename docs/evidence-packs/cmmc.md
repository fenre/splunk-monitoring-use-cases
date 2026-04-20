# Evidence Pack — CMMC

> **Tier**: Tier 1 &nbsp;·&nbsp; **Jurisdiction**: US &nbsp;·&nbsp; **Version**: `2.0`
>
> **Full name**: Cybersecurity Maturity Model Certification
> **Authoritative source**: [https://dodcio.defense.gov/CMMC/](https://dodcio.defense.gov/CMMC/)
> **Effective from**: 2024-12-16

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

Cybersecurity Maturity Model Certification 2.0 is the US Department of Defense framework for protecting Federal Contract Information (FCI) and Controlled Unclassified Information (CUI) in the Defense Industrial Base (DIB). CMMC 2.0 (revised October 2021, final rule 32 CFR Part 170 published 15 October 2024, effective 16 December 2024) replaces the five-level CMMC 1.0 with three levels: Level 1 (Foundational, FCI only), Level 2 (Advanced, CUI), Level 3 (Expert, highest-priority programs). Independent third-party assessments (C3PAOs) perform Level 2 certifications; DoD DIBCAC performs Level 3.

## 2. Scope and applicability

All DoD contractors and subcontractors handling FCI or CUI. Level 1: 15 basic safeguarding practices from FAR 52.204-21. Level 2: 110 practices derived from NIST SP 800-171 Rev. 2. Level 3: 110 Level-2 practices plus enhanced NIST SP 800-172 controls.

**Territorial scope.** DoD contract scope globally; any organisation in the DIB supply chain regardless of country of registration.

## 3. Catalogue coverage at a glance

- **Clauses tracked**: 9
- **Clauses covered by at least one UC**: 9 / 9 (100.0%)
- **Priority-weighted coverage**: 100.0%
- **Contributing UCs**: 18

Coverage methodology is documented in [`docs/coverage-methodology.md`](../coverage-methodology.md). Priority weights come from `data/regulations.json` commonClauses entries (see [`data/regulations.json`](../../data/regulations.json) priorityWeightRubric).

## 4. Clause-by-clause coverage

Clauses are listed in the order defined by `data/regulations.json commonClauses` for this regulation version. A clause is considered covered when at least one UC sidecar has a `compliance[]` entry matching `(regulation, version, clause)`. Assurance is the maximum across contributing UCs.

| Clause | Topic | Priority | Assurance | UCs |
|---|---|---|---|---|
| [`AC.L2-3.1.1`](https://dodcio.defense.gov/CMMC/#AC.L2-3.1.1) | Authorized access to systems | 1.0 | `partial` | [UC-22.20.1](#uc-22-20-1), [UC-22.20.10](#uc-22-20-10), [UC-22.20.11](#uc-22-20-11), [UC-22.20.12](#uc-22-20-12), [UC-22.20.13](#uc-22-20-13), [UC-22.20.14](#uc-22-20-14) (+2 more) |
| [`AC.L2-3.1.5`](https://dodcio.defense.gov/CMMC/#AC.L2-3.1.5) | Least privilege | 1.0 | `partial` | [UC-22.20.2](#uc-22-20-2) |
| [`AU.L2-3.3.1`](https://dodcio.defense.gov/CMMC/#AU.L2-3.3.1) | Create audit records | 1.0 | `partial` | [UC-22.20.3](#uc-22-20-3) |
| [`AU.L2-3.3.2`](https://dodcio.defense.gov/CMMC/#AU.L2-3.3.2) | Ensure unique user traceability | 1.0 | `partial` | [UC-22.20.4](#uc-22-20-4) |
| [`AU.L2-3.3.5`](https://dodcio.defense.gov/CMMC/#AU.L2-3.3.5) | Audit reporting and correlation | 1.0 | `partial` | [UC-22.20.5](#uc-22-20-5), [UC-22.32.19](#uc-22-32-19) |
| [`CM.L2-3.4.1`](https://dodcio.defense.gov/CMMC/#CM.L2-3.4.1) | Baseline configurations | 1.0 | `partial` | [UC-22.20.6](#uc-22-20-6) |
| [`IR.L2-3.6.1`](https://dodcio.defense.gov/CMMC/#IR.L2-3.6.1) | Incident handling capability | 1.0 | `partial` | [UC-22.20.7](#uc-22-20-7) |
| [`SC.L2-3.13.8`](https://dodcio.defense.gov/CMMC/#SC.L2-3.13.8) | Cryptographic mechanisms for CUI in transit | 1.0 | `partial` | [UC-22.20.8](#uc-22-20-8) |
| [`SI.L2-3.14.6`](https://dodcio.defense.gov/CMMC/#SI.L2-3.14.6) | Monitor for attacks | 1.0 | `partial` | [UC-22.20.9](#uc-22-20-9), [UC-22.32.21](#uc-22-32-21) |

### 4.1 Contributing UC detail

<a id='uc-22-20-1'></a>
- **UC-22.20.1** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-20-10'></a>
- **UC-22.20.10** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-20-11'></a>
- **UC-22.20.11** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-20-12'></a>
- **UC-22.20.12** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-20-13'></a>
- **UC-22.20.13** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-20-14'></a>
- **UC-22.20.14** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-20-15'></a>
- **UC-22.20.15** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-20-16'></a>
- **UC-22.20.16** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-20-2'></a>
- **UC-22.20.2** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-20-3'></a>
- **UC-22.20.3** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-20-4'></a>
- **UC-22.20.4** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-20-5'></a>
- **UC-22.20.5** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-20-6'></a>
- **UC-22.20.6** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-20-7'></a>
- **UC-22.20.7** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-20-8'></a>
- **UC-22.20.8** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-20-9'></a>
- **UC-22.20.9** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-32-19'></a>
- **UC-22.32.19** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-32-21'></a>
- **UC-22.32.21** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)

## 5. Evidence collection

### 5.1 Common evidence sources

Auditors typically request the following records when examining this regulation:

- System Security Plan (SSP) and supporting control-family documentation
- POA&M with implementation milestones
- NIST SP 800-171A assessment objectives mapped to evidence
- SPRS score and supporting evidence
- Vulnerability-management records with remediation tracking
- Configuration-management tooling output (SCAP scans)
- Access-review and account-management records
- CUI-marking training and awareness records
- Incident-response records (including DIBNet / DC3 reporting)

### 5.2 Retention requirements

| Artifact | Retention | Legal basis |
|---|---|---|
| System Security Plan (SSP) | Duration of contract + 6 years | DFARS 252.204-7012 (b)(4); NARA GRS 4.2 |
| Plan of Actions & Milestones (POA&M) | Duration of contract + 6 years | DFARS 252.204-7012 |
| Incident-report records per DFARS 252.204-7012(c)(1)(i) | 6 years post-contract closeout | DFARS 252.204-7012; FAR Part 4 |
| CMMC assessment evidence (C3PAO work papers) | 6 years from certification issue | 32 CFR 170.17; CyberAB policy |
| SPRS score submission records | 6 years | NIST SP 800-171A; DFARS 252.204-7019 |
| Subcontractor CMMC attestations | Duration of subcontract + 6 years | DFARS 252.204-7021 |

> Retention figures above are the legal minimums or regulator-stated expectations. Organisation-specific retention schedules may be longer where business, tax, litigation-hold, or contractual obligations apply. Where a figure conflicts with local data-protection law (e.g. GDPR Art.5(1)(e) storage-limitation principle), the shorter conformant period governs for personal-data content; the evidence-of-compliance retention retains the longer period for audit purposes, scrubbed of excess personal data.

### 5.3 Evidence integrity expectations

Regulators increasingly cite **evidence-integrity failures** as aggravating factors in enforcement actions. Cross-regulation baseline expectations:

- Time-stamped, tamper-evident storage (WORM, cryptographic chaining, or append-only indexes).
- Chain-of-custody for any evidence removed from the SIEM / production system for audit or legal purposes.
- Synchronised clocks (NTP stratum ≤ 3 or equivalent) across all in-scope sources so timeline reconstruction is defensible.
- Documented retention enforcement — not just retention policy — so that deletion is auditable.

See cat-22.35 "Evidence continuity and log integrity" for UCs that implement these controls.

## 6. Control testing procedures

Level 1: annual self-assessment with executive affirmation in SPRS. Level 2: triennial C3PAO assessment (for most scope); some sub-contracts allow Level 2 self-assessment with annual executive affirmation. Level 3: triennial DIBCAC assessment. Assessment follows NIST SP 800-171A objectives, using examine, interview, test methods. Scoring is pass/fail per practice — a single missed practice below the 'MET' threshold prevents certification unless the POA&M rule applies (limited to a specific practice subset).

**Reporting cadence.** SPRS score update annually (NIST SP 800-171 self-assessment) or upon material system change. CMMC certification renewal every 3 years (Levels 2 and 3). Annual executive affirmation for any self-assessed scope. Incident reporting to DoD CyberCrime Center (DC3) within 72 hours of discovery.

## 7. Roles and responsibilities

| Role | Responsibility |
|---|---|
| **Prime Contractor** | Holds the primary contractual obligation; must flow CMMC requirements down to subcontractors handling CUI. |
| **Subcontractor** | Must achieve CMMC level appropriate to the information they handle; DFARS 252.204-7021 flow-down. |
| **C3PAO (CMMC Third-Party Assessor Organisation)** | CyberAB-accredited body performing Level 2 certifications; maintains Certified CMMC Assessor (CCA) staff. |
| **DIBCAC (Defense Industrial Base Cybersecurity Assessment Center)** | Conducts Level 3 assessments and joint surveillance of C3PAOs. |
| **DoD Chief Information Officer (DoD CIO)** | Owns CMMC program; issues policy and rule changes (32 CFR Part 170). |
| **CyberAB (Cyber Accreditation Body)** | Accredits C3PAOs, CCAs, RPOs (Registered Practitioner Organisations); maintains CMMC Marketplace. |
| **DIB CS Program** | Voluntary information-sharing program for DoD Defence Industrial Base. |

## 8. Authoritative guidance

- **32 CFR Part 170 — Cybersecurity Maturity Model Certification (CMMC) Program** — DoD — [https://www.ecfr.gov/current/title-32/subtitle-A/chapter-I/subchapter-M/part-170](https://www.ecfr.gov/current/title-32/subtitle-A/chapter-I/subchapter-M/part-170)
- **NIST SP 800-171 Rev. 2 / Rev. 3** — NIST — [https://csrc.nist.gov/publications/detail/sp/800-171/rev-2/final](https://csrc.nist.gov/publications/detail/sp/800-171/rev-2/final)
- **NIST SP 800-172 Enhanced Security Requirements** — NIST — [https://csrc.nist.gov/publications/detail/sp/800-172/final](https://csrc.nist.gov/publications/detail/sp/800-172/final)
- **DoD CMMC Program Documents** — DoD CIO — [https://dodcio.defense.gov/CMMC/](https://dodcio.defense.gov/CMMC/)
- **Cyber AB CMMC Marketplace and Program Documents** — Cyber AB — [https://cyberab.org/](https://cyberab.org/)
- **DFARS 252.204-7012 Safeguarding Covered Defense Information and Cyber Incident Reporting** — Office of the Under Secretary of Defense (Acquisition and Sustainment) — [https://www.acquisition.gov/dfars/252.204-7012-safeguarding-covered-defense-information-and-cyber-incident-reporting](https://www.acquisition.gov/dfars/252.204-7012-safeguarding-covered-defense-information-and-cyber-incident-reporting)

## 9. Common audit deficiencies

Findings frequently cited by regulators, certification bodies, and external auditors for this regulation. These should be pre-tested as part of readiness reviews.

- SSP references NIST 800-171 practices but implementation evidence does not satisfy NIST SP 800-171A assessment objectives.
- POA&M items exceed the 180-day remediation window without explicit DoD approval for extended timelines.
- SPRS score submission is stale (> 3 years) or based on self-assessment claims not supported by artefacts.
- Cloud services in scope use FedRAMP 'Ready' (not Authorised) or commercial cloud without FedRAMP Moderate equivalence.
- Subcontractor flow-down is contractually present but no evidence of actual CMMC-level verification exists.
- CUI-markings on physical and digital artefacts are inconsistent; data that should be marked CUI is handled as non-CUI.

## 10. Enforcement and penalties

CMMC non-compliance prevents contract award or continuation — the operational penalty. False Claims Act exposure (31 USC §§3729-33) for misrepresented compliance: treble damages plus per-claim penalties (USD 13,508-27,018 per claim in 2024). DoJ Civil Cyber-Fraud Initiative launched 2021 has produced multiple million-dollar settlements for misrepresented cybersecurity compliance. Debarment or suspension from federal contracting under FAR 9.406. Criminal penalties for fraud under 18 USC §1001 (up to USD 10,000 + 5 years per count).

## 11. Pack gaps and remediation backlog

All clauses tracked in `data/regulations.json` for this regulation version are covered by at least one UC. **100 % common-clause coverage**. Remaining work is assurance-upgrade (for example, moving `contributing` entries to `partial` or `full` via explicit control tests) rather than new clause authoring.

## 12. Questions an auditor should ask

These are the questions a regulator, certification body, or external auditor is likely to ask. The pack helps preparers stage evidence and pre-test responses before the review opens.

- Produce the CMMC-level determination for each contract in scope; show the DFARS clause that applied (7012, 7019, 7020, 7021).
- Produce the System Security Plan (SSP) and demonstrate coverage of all 110 NIST SP 800-171 Rev. 2 practices (Level 2) or the 134 practices (Level 3).
- Produce the POA&M with explicit due dates; demonstrate that no POA&M item is open beyond the permitted windows (generally 180 days).
- Show the Supplier Performance Risk System (SPRS) score submission and the supporting evidence for each practice-level scoring decision.
- For Level 2, demonstrate the triennial C3PAO assessment; for Level 3, demonstrate the DIBCAC assessment.
- Show evidence of incident reporting to DoD CyberCrime Center (DC3) within 72 hours per DFARS 252.204-7012(c).
- For cloud services in scope, demonstrate FedRAMP Moderate baseline (or equivalent) compliance of the CSP and that CUI is stored only within the authorised environment.
- For subcontractor flow-down, produce evidence per DFARS 252.204-7021 that every subcontractor in scope has the correct CMMC level.

## 13. Machine-readable twin

The machine-readable companion of this pack lives at [`api/v1/evidence-packs/cmmc.json`](../../api/v1/evidence-packs/cmmc.json). It contains the same clause-level coverage, retention guidance, role matrix, and gap list in JSON form, and is regenerated in lockstep with this markdown pack so content stays in sync. Consumers integrating the pack into GRC tools, audit-request portals, or evidence pipelines should consume the JSON document; human readers should consume this markdown.

Related API surfaces (all under [`api/v1/`](../../api/README.md)):

- [`api/v1/compliance/regulations/cmmc.json`](../../api/v1/compliance/regulations/cmmc.json) — regulation metadata and per-version coverage metrics
- [`api/v1/compliance/ucs/`](../../api/v1/compliance/ucs/index.json) — individual UC sidecars
- [`api/v1/compliance/coverage.json`](../../api/v1/compliance/coverage.json) — global coverage snapshot
- [`api/v1/compliance/gaps.json`](../../api/v1/compliance/gaps.json) — global gap report

## 14. Provenance and regeneration

This pack is **generated**, not hand-authored. Re-running the generator produces byte-identical output (deterministic sort, stable serialisation, no free-form timestamps outside the block below). CI enforces regeneration drift via `--check` mode.

**Inputs to this pack**

- [`data/regulations.json`](../../data/regulations.json) — commonClauses, priority weights, authoritative URLs
- [`data/evidence-pack-extras.json`](../../data/evidence-pack-extras.json) — retention, roles, authoritative guidance, penalty, testing approach
- [`use-cases/cat-*/uc-*.json`](../../use-cases) — UC sidecars containing compliance[] entries, controlFamily, owner, evidence fields
- [`api/v1/compliance/regulations/cmmc@*.json`](../../api/v1/compliance/regulations/) — pre-computed coverage metrics (when present)

- Generator: [`scripts/generate_evidence_packs.py`](../../scripts/generate_evidence_packs.py)
- Evidence-pack directory index: [`docs/evidence-packs/README.md`](README.md)

**Generation metadata**

```
catalogue_version: 7.0
generator_script:  scripts/generate_evidence_packs.py
inputs_sha256:     87ca49d6acc66fffd2727baa9b1604042f957a52233be589707aed6e224dd4b3
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
