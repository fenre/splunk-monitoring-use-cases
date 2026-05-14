# Evidence Pack — SOCI Act

> **Tier**: Tier 1 &nbsp;·&nbsp; **Jurisdiction**: AU &nbsp;·&nbsp; **Version**: `2022-SLACIP+CIRMP-2023`
>
> **Full name**: Security of Critical Infrastructure Act 2018 (Cth) and Critical Infrastructure Risk Management Program Rules 2023
> **Authoritative source**: [https://www.legislation.gov.au/C2018A00029/latest/text](https://www.legislation.gov.au/C2018A00029/latest/text)
> **Effective from**: 2023-08-17

> This evidence pack is the auditor-facing view of the Splunk monitoring catalogue's coverage of the regulation. Every clause coverage claim is traceable to a specific UC sidecar JSON file (`content/cat-*/UC-*.json`); every retention figure cites its legal basis; every URL resolves to an official regulator or standards-body source. The pack does **not** assert legal conclusions — it tabulates what the catalogue covers, names the authoritative source, and flags gaps. Interpretation stays with counsel.

> **Live views.** [Buyer narrative (`compliance-story.html?reg=soci`)](../../compliance-story.html?reg=soci) · [Auditor clause navigator (`clause-navigator.html#reg=soci`)](../../clause-navigator.html#reg=soci) · [JSON twin (`api/v1/compliance/story/soci.json`)](../../api/v1/compliance/story/soci.json)

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

The Security of Critical Infrastructure Act 2018 (Cth) (SOCI Act), as amended by the Security Legislation Amendment (Critical Infrastructure) Act 2021 (SLACIP) and the Security Legislation Amendment (Critical Infrastructure Protection) Act 2022, with the Security of Critical Infrastructure (Critical Infrastructure Risk Management Program) Rules 2023 (CIRMP Rules) in force since 17 August 2023, is the Australian Commonwealth framework for protecting critical infrastructure assets across 11 sectors (energy, communications, transport, water and sewerage, financial services and markets, data storage or processing, healthcare and medical, higher education and research, food and grocery, defence industry, and space technology). It imposes asset-register obligations (Part 2), cyber-incident reporting obligations (Part 2B), CIRMP obligations (Part 2A) for the all-hazards risk management of critical assets (cyber-and-information-security, personnel, supply-chain, physical-and-natural-hazards), Enhanced Cyber Security Obligations (ECSO, Part 2C) for Systems of National Significance (SoNS), Government Assistance Powers (Part 3A) including Information Gathering, Action, and Intervention Directions, and Protected Information offences (Part 6A). The Cyber and Infrastructure Security Centre (CISC) within the Department of Home Affairs is the regulator; the Australian Signals Directorate (ASD) is the cyber-incident response authority. Compliance is mandatory; the Minister can issue directions, the Secretary can compel actions, and offences can attract civil penalties (up to AUD 11.1 million per offence for an offence carrying 1,000 penalty units, indexed annually) and, for Part 6A on-disclosure offences, criminal penalties.

## 2. Scope and applicability

Applies to responsible entities for the assets defined in the SOCI Act as critical infrastructure assets, across 11 sectors. The CIRMP Rules apply to a narrower subset of critical-infrastructure-asset classes specified in the Rules (currently around 16 asset classes including critical electricity, critical gas, critical water, critical hospital, critical data-storage-or-processing, critical broadcasting, critical domain-name systems, etc.). The ECSO obligations apply to assets that the Minister has declared to be SoNS; declaration is confidential. Part 6A Protected Information rules apply to information obtained under SOCI by the entity, the Department, or other authorised recipients.

**Territorial scope.** Commonwealth of Australia jurisdiction. Extraterritorial reach: the SOCI Act applies to a responsible entity wherever situated if the asset is in Australia or provides services to Australia. Cross-jurisdictional cooperation arrangements exist with the Five Eyes (US, UK, Canada, NZ), Japan, EU, and Singapore for incident response and intelligence-sharing. Protected Information may be shared internationally only under section 42/43/44/45 authorisations or treaty arrangements.

## 3. Catalogue coverage at a glance

- **Clauses tracked**: 28
- **Clauses covered by at least one UC**: 0 / 28 (0.0%)
- **Priority-weighted coverage**: 0.0%
- **Contributing UCs**: 0

Coverage methodology is documented in [`docs/coverage-methodology.md`](../coverage-methodology.md). Priority weights come from `data/regulations.json` commonClauses entries (see [`data/regulations.json`](../../data/regulations.json) priorityWeightRubric).

## 4. Clause-by-clause coverage

Clauses are listed in the order defined by `data/regulations.json commonClauses` for this regulation version. A clause is considered covered when at least one UC sidecar has a `compliance[]` entry matching `(regulation, version, clause)`. Assurance is the maximum across contributing UCs.

| Clause | Topic | Priority | Assurance | UCs |
|---|---|---|---|---|
| [`SOCI-s18`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-s18) | Asset register — responsible entity reporting (Part 2) | 1.0 | `—` | _not yet covered_ |
| [`SOCI-s30AC`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-s30AC) | Duty to adopt and maintain a Critical Infrastructure Risk Management Program (CIRMP) | 1.0 | `—` | _not yet covered_ |
| [`SOCI-s30AH`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-s30AH) | Annual review of the CIRMP | 1.0 | `—` | _not yet covered_ |
| [`SOCI-s30AG`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-s30AG) | Board (or equivalent) approval and annual report | 1.0 | `—` | _not yet covered_ |
| [`SOCI-s30BC`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-s30BC) | Critical cyber-security incident — 12-hour notification (Part 2B) | 1.0 | `—` | _not yet covered_ |
| [`SOCI-s30BD`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-s30BD) | Other (significant) cyber-security incident — 72-hour notification | 1.0 | `—` | _not yet covered_ |
| [`SOCI-s30BF`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-s30BF) | Subsequent written report — 84-hour requirement | 0.7 | `—` | _not yet covered_ |
| [`SOCI-s30CB`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-s30CB) | Statutory cyber-incident response plan for Systems of National Significance (SoNS) | 1.0 | `—` | _not yet covered_ |
| [`SOCI-s30CG`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-s30CG) | Cyber-security exercise on demand for SoNS | 0.7 | `—` | _not yet covered_ |
| [`SOCI-s30CM`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-s30CM) | Vulnerability assessment on demand for SoNS | 0.7 | `—` | _not yet covered_ |
| [`SOCI-s30DJ`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-s30DJ) | System information periodic reporting (event-log telemetry) for SoNS | 0.7 | `—` | _not yet covered_ |
| [`SOCI-CIRMP-r5`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-CIRMP-r5) | CIRMP Rules — General requirements and material-risk identification | 1.0 | `—` | _not yet covered_ |
| [`SOCI-CIRMP-r6.1`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-CIRMP-r6.1) | CIRMP Rules — Cyber-and-information-security material risks (general) | 1.0 | `—` | _not yet covered_ |
| [`SOCI-CIRMP-r6.2`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-CIRMP-r6.2) | CIRMP Rules — Cyber-and-information-security continuous monitoring | 1.0 | `—` | _not yet covered_ |
| [`SOCI-CIRMP-r6.3`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-CIRMP-r6.3) | CIRMP Rules — Mandatory cyber framework adoption (Aug 2024 deadline) | 1.0 | `—` | _not yet covered_ |
| [`SOCI-CIRMP-r7.1`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-CIRMP-r7.1) | CIRMP Rules — Personnel hazards: critical-worker identification and assessment | 1.0 | `—` | _not yet covered_ |
| [`SOCI-CIRMP-r7.2`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-CIRMP-r7.2) | CIRMP Rules — Personnel hazards: insider-threat detection and removal | 1.0 | `—` | _not yet covered_ |
| [`SOCI-CIRMP-r8.1`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-CIRMP-r8.1) | CIRMP Rules — Supply-chain hazards: vendor risk register | 1.0 | `—` | _not yet covered_ |
| [`SOCI-CIRMP-r8.2`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-CIRMP-r8.2) | CIRMP Rules — Supply-chain hazards: continuous supplier monitoring | 0.7 | `—` | _not yet covered_ |
| [`SOCI-CIRMP-r9.1`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-CIRMP-r9.1) | CIRMP Rules — Physical and natural hazards: site security | 0.7 | `—` | _not yet covered_ |
| [`SOCI-CIRMP-r9.2`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-CIRMP-r9.2) | CIRMP Rules — Natural hazards and business continuity exercises | 0.7 | `—` | _not yet covered_ |
| [`SOCI-CIRMP-r10`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-CIRMP-r10) | CIRMP Rules — Annual report to the Department | 1.0 | `—` | _not yet covered_ |
| [`SOCI-ECSO-vulnerability`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-ECSO-vulnerability) | Enhanced Cyber Security Obligations — vulnerability disclosure and remediation tracking | 0.7 | `—` | _not yet covered_ |
| [`SOCI-cross-segmentation`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-cross-segmentation) | OT zone-and-conduit segmentation (Defence, Energy, Water, Critical Manufacturing) | 1.0 | `—` | _not yet covered_ |
| [`SOCI-cross-asset-inventory`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-cross-asset-inventory) | OT asset inventory with criticality classification (CISC expectation) | 1.0 | `—` | _not yet covered_ |
| [`SOCI-cross-data-residency`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-cross-data-residency) | Australian data residency and operational-data sovereignty | 0.7 | `—` | _not yet covered_ |
| [`SOCI-cross-encryption`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-cross-encryption) | Encryption of operational data in transit between zones | 0.7 | `—` | _not yet covered_ |
| [`SOCI-cross-audit-evidence`](https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-cross-audit-evidence) | Audit-evidence retention for CIRMP and incident reporting | 0.7 | `—` | _not yet covered_ |

## 5. Evidence collection

### 5.1 Common evidence sources

Auditors typically request the following records when examining this regulation:

- Asset and CMDB records (ServiceNow CMDB, BMC Helix CMDB, in-house CMDB) with SOCI in-scope flagging
- GRC compliance platform (ServiceNow IRM/GRC, Archer, MetricStream) for CIRMP risk register, supply-chain register, physical-hazard register, exercise records, Rule 10 sections
- Cyber-incident records (Splunk ES notable framework, SOAR playbooks, ASD lodgement portal)
- OT visibility (Cisco Cyber Vision<sup class="ref">[<a href="#ref-2">2</a>]</sup>, Claroty, Nozomi, Microsoft Defender for IoT) for SoNS Rule 13/14 system-information periodic reporting
- Identity and privileged access (Microsoft Entra ID<sup class="ref">[<a href="#ref-5">5</a>]</sup>, CyberArk PAM, BeyondTrust, Wallix) for critical-worker access governance and PAM session recording
- HRIS (Workday, SAP SuccessFactors, Oracle HCM) for critical-worker register and screening cadence
- DLP and CASB (Microsoft Purview, Forcepoint DLP, Microsoft Defender for Cloud Apps) for Part 6A Protected Information audit
- Sanctions and beneficial-owner data (DFAT Consolidated List, OFAC SDN, OFSI, EU consolidated list, Refinitiv World-Check, Dow Jones Risk) for Rule 8(2) screening
- Live natural-hazard feeds (Bureau of Meteorology warnings API, Geoscience Australia earthquake feed, Emergency Management Victoria flood feed) for Rule 9 monitoring
- Cyber exercise platforms (Mandiant Tabletops, Atomic Red Team, customer-led purple-team) with metrics integrations into the GRC for Rule 6(2)
- Physical access control (Genetec Security Center, Lenel OnGuard, Honeywell Pro-Watch) and HMI audit logs for cyber-physical convergence evidence

### 5.2 Retention requirements

| Artifact | Retention | Legal basis |
|---|---|---|
| Register of Critical Infrastructure Assets (Part 2) entries and supporting evidence | Duration of asset operation + 7 years | SOCI Act 2018 (Cth) s18; Archives Act 1983 (Cth) general administrative retention for regulatory records |
| CIRMP document, board approval, annual review evidence (Rule 5) | Duration of CIRMP currency + 7 years | SOCI Act 2018 (Cth) s30AC; CIRMP Rules 2023 r5 |
| Critical cyber incident notifications (s30BC, 12-hour SLA) and other cyber incident notifications (72-hour SLA) | 10 years from incident closure | SOCI Act 2018 (Cth) Part 2B; ASD incident-handling guidance |
| Rule 10 annual report and board-approval records | Duration of CIRMP currency + 10 years | SOCI Act 2018 (Cth) s30AG; CIRMP Rules 2023 r10 |
| ECSO 14-day Notice-of-Operations lodgements and acknowledgements | Duration of SoNS declaration + 10 years | SOCI Act 2018 (Cth) Part 2C ECSO obligations |
| Government Assistance Powers (Part 3A) directions, responses, and evidence artefacts | Duration of direction validity + 15 years (extended for national-security records) | SOCI Act 2018 (Cth) Part 3A; Archives Act 1983 (Cth) national-security retention |
| Cyber framework attestations (Rule 6(3)) — Essential Eight<sup class="ref">[<a href="#ref-1">1</a>]</sup>, ISO 27001<sup class="ref">[<a href="#ref-4">4</a>]</sup>, NIST CSF<sup class="ref">[<a href="#ref-6">6</a>]</sup>, AESCSF, C2M2, or Secretary-approved equivalent | Duration of CIRMP currency + 7 years | CIRMP Rules 2023 r6(3); ACSC Essential Eight Maturity Model documentation |
| Critical-worker register, screening evidence, training records (Rule 7) | Worker engagement duration + 7 years | CIRMP Rules 2023 r7; AGSVA / NCCHC retention guidance |
| Supply-chain hazard register, tier-1 attestations, sanctions-screening disposition records (Rule 8) | Engagement duration + 7 years | CIRMP Rules 2023 r8; Autonomous Sanctions Act 2011 record-keeping requirements |
| Physical and natural-hazard assessments and mitigations (Rule 9) | Duration of asset operation + 7 years | CIRMP Rules 2023 r9 |
| Protected Information access and disclosure records (Part 6A) | 10 years from disclosure event | SOCI Act 2018 (Cth) Part 6A; Archives Act 1983 (Cth) sensitive-records retention |
| Detection-effectiveness exercise records and after-action reports (Rule 6(2)) | Duration of CIRMP currency + 7 years | CIRMP Rules 2023 r6(2) |

> Retention figures above are the legal minimums or regulator-stated expectations. Organisation-specific retention schedules may be longer where business, tax, litigation-hold, or contractual obligations apply. Where a figure conflicts with local data-protection law (e.g. GDPR<sup class="ref">[<a href="#ref-3">3</a>]</sup> Art.5(1)(e) storage-limitation principle), the shorter conformant period governs for personal-data content; the evidence-of-compliance retention retains the longer period for audit purposes, scrubbed of excess personal data.

### 5.3 Evidence integrity expectations

Regulators increasingly cite **evidence-integrity failures** as aggravating factors in enforcement actions. Cross-regulation baseline expectations:

- Time-stamped, tamper-evident storage (WORM, cryptographic chaining, or append-only indexes).
- Chain-of-custody for any evidence removed from the SIEM / production system for audit or legal purposes.
- Synchronised clocks (NTP stratum ≤ 3 or equivalent) across all in-scope sources so timeline reconstruction is defensible.
- Documented retention enforcement — not just retention policy — so that deletion is auditable.

See cat-22.35 "Evidence continuity and log integrity" for UCs that implement these controls.

## 6. Control testing procedures

Compliance is mandatory; the CISC may issue an information notice (s37), an inspection direction, or commence enforcement at any time. The CISC's published Critical Infrastructure Annual Risk Review surveys current obligations. Inspections may be planned or unannounced; an inspector may request live evidence on demand. Continuous evidence collection in Splunk is the practical model. External assurance: many entities engage a Big-4 accountancy firm or specialist consultancy annually for a SOCI maturity review against the published Sector Recovery Plans, ahead of the Rule 10 board-approved report. Penetration testing of SoNS assets is encouraged but performed under strict change-control (the Department may issue ASD-led red-team engagement directions). Live exercises must include both cyber and natural-hazard scenarios per Rule 6(2) and Rule 9 alignment. Independent assurance of the cyber framework attestation (Rule 6(3)) is increasingly expected, especially where Essential Eight maturity is below ML1 across multiple controls.

**Reporting cadence.** Asset Register (s18) — 30 days for material changes. CIRMP annual review (Rule 5) — on the anniversary of board approval. Rule 10 annual report — within 90 days of the end of the financial year (typically 30 June). Critical-cyber-incident notification (s30BC) — within 12 hours of becoming aware; written follow-up within 48-72 hours (regulator-specified per incident class). Other cyber-incident notification (s30CD) — within 72 hours. ECSO 14-day Notice-of-Operations — 14 days from material change. SoNS Rule 13/14 system-information periodic reporting — as specified in the relevant direction. Cyber-exercise cadence (Rule 6(2)) — at least annually. Sanctions and FOCI screening (Rule 8(2)) — daily refresh recommended. Cyber framework attestation (Rule 6(3)) — at least annually with minimum Essential Eight ML1 (or equivalent).

## 7. Roles and responsibilities

| Role | Responsibility |
|---|---|
| **CEO of the Responsible Entity** | Accountable for SOCI compliance; signs the Rule 10 annual report board attestation; receives any Government Assistance Powers (Part 3A) direction; ultimate accountability for SoNS obligations. |
| **Company Secretary** | Coordinates board approval of the CIRMP and annual report; lodges Rule 10 report to CISC; manages corporate-governance documentation. |
| **CISO / Chief Information Security Officer** | Owns the CIRMP cyber-hazard programme (Rule 6); chairs the cyber framework attestation (Rule 6(3)) cycle; primary contact for ASD on cyber incidents. |
| **Head of Critical-Infrastructure Compliance** | Operational owner of the SOCI programme; maintains the Register of Critical Infrastructure Assets, ECSO obligations, GAP register, and Rule 10 production. |
| **Head of Third-Party Risk (Procurement)** | Owns Rule 8 supply-chain-hazard register, tier-1 supplier attestations, sanctions screening, and beneficial-owner due diligence. |
| **Head of People Security** | Owns Rule 7 critical-worker register, screening cadence, training, and insider-threat programme coordination with HR and Legal. |
| **Head of Physical Security / BCDR Lead** | Owns Rule 9 physical and natural-hazard register; integrates BoM, Geoscience Australia, EMV feeds; coordinates with the cyber team on cyber-physical convergence. |
| **Cyber and Infrastructure Security Centre (CISC)** | Australian Government regulator within the Department of Home Affairs; manages the Register of Critical Infrastructure Assets, receives Rule 10 annual reports, issues ECSO declarations, and supports Part 3A directions. |
| **Australian Signals Directorate (ASD)** | Cyber-incident response authority; receives critical-cyber-incident notifications under s30BC; coordinates the Australian Cyber Security Centre (ACSC) response. |
| **Department of Home Affairs Secretary** | Receives s30AC CIRMP filings; the Minister (via the Secretary) issues SoNS declarations and Part 3A Government Assistance Powers. |

## 8. Authoritative guidance

- **Security of Critical Infrastructure Act 2018 (Cth)** — Federal Register of Legislation, Australia — [https://www.legislation.gov.au/C2018A00029/latest/text](https://www.legislation.gov.au/C2018A00029/latest/text)
- **Security of Critical Infrastructure (Critical Infrastructure Risk Management Program) Rules 2023** — Federal Register of Legislation, Australia — [https://www.legislation.gov.au/F2023L00112/latest/text](https://www.legislation.gov.au/F2023L00112/latest/text)
- **Department of Home Affairs — Cyber and Infrastructure Security Centre (CISC)** — Department of Home Affairs, Australia — [https://www.cisc.gov.au/legislative-information-and-reforms/critical-infrastructure](https://www.cisc.gov.au/legislative-information-and-reforms/critical-infrastructure)
- **ACSC — Essential Eight Maturity Model** — Australian Cyber Security Centre — [https://www.cyber.gov.au/resources-business-and-government/essential-cybersecurity/essential-eight/essential-eight-maturity-model](https://www.cyber.gov.au/resources-business-and-government/essential-cybersecurity/essential-eight/essential-eight-maturity-model)
- **Australian Energy Sector Cyber Security Framework (AESCSF)** — Australian Energy Market Operator (AEMO) — [https://www.aemo.com.au/initiatives/major-programs/aescsf](https://www.aemo.com.au/initiatives/major-programs/aescsf)
- **DFAT Australian sanctions — Consolidated List** — Department of Foreign Affairs and Trade, Australia — [https://www.dfat.gov.au/international-relations/security/sanctions/consolidated-list](https://www.dfat.gov.au/international-relations/security/sanctions/consolidated-list)
- **Bureau of Meteorology warnings and alerts** — Bureau of Meteorology, Australia — [https://www.bom.gov.au/warnings/](https://www.bom.gov.au/warnings/)

## 9. Common audit deficiencies

Findings frequently cited by regulators, certification bodies, and external auditors for this regulation. These should be pre-tested as part of readiness reviews.

- Register of Critical Infrastructure Assets has stale operational-information or direct-interest-holder fields; s18 30-day reporting clock is missed for material changes (UC-22.52.1).
- CIRMP document exists but the residual-risk register is informal; Rule 5 currency-evidence is paper-only (UC-22.52.2).
- CIRMP annual review held but board approval is recorded only in minutes without a structured Rule 5(2) statement of compliance (UC-22.52.3 / 4).
- Critical-cyber-incident reporting (s30BC) 12-hour SLA missed because the SOC's incident-classification gate is over-conservative (UC-22.52.5).
- Written follow-up to ASD lodged late or with insufficient detail; UC-22.52.6 surfaces the SLA but not always the content quality.
- SoNS IR plan currency unmaintained between exercises (UC-22.52.7); cyber-exercise drift past the 12-month boundary (UC-22.52.8).
- Rule 6(3) cyber framework attestation is published once but not reviewed annually; some assets stuck at maturity level 0 (UC-22.52.15).
- Critical-worker register stale: workers added without screening, screenings expired without access suspension (UC-22.52.16).
- Insider-threat detection scoped too broadly; UEBA noise floods the SOC and critical-worker signals are lost (UC-22.52.17).
- Supply-chain hazard register tracks suppliers but tier-1 contractual clauses are missing or stale (UC-22.52.18).
- Sanctions and FOCI screening is performed annually rather than continuously; daily-refresh model not in place (UC-22.52.19).
- Physical and natural-hazard assessments are produced once and not refreshed; BoM / GA / EMV live feeds not integrated (UC-22.52.20).
- Cyber-physical convergence runbooks are documented but SOAR playbooks have never fired in production; SLA evidence is absent (UC-22.52.21).
- Rule 10 annual report lodged but with thin sections for Rules 4 and 8; evidence-link inventory is incomplete (UC-22.52.23).
- Part 6A Protected Information labelling is enforced but Microsoft Purview DLP exceptions accumulated without review; some Protected files travel outside via personal email (UC-22.52.24).
- Lawful-disclosure register is paper-only and not reconciled to UC-22.52.24 detections (UC-22.52.25).
- ECSO 14-day Notice-of-Operations clock is breached on a material change to a SoNS-declared asset (UC-22.52.26).
- Government Assistance Powers (Part 3A) directions are received but the entity's response tracking is ad-hoc; deadlines missed for Information Gathering Directions (UC-22.52.27).
- Cross-cutting compliance-health view (UC-22.52.28) is degraded for >7 days due to a contributing-UC failure with no detection.

## 10. Enforcement and penalties

SOCI offences carry significant civil penalties: failure to comply with key obligations such as the Asset Register (s18) or CIRMP (s30AC) is a civil-penalty offence of up to 200 penalty units per breach for an individual and up to 1,000 penalty units for a body corporate (penalty unit is AUD 313 as at 1 July 2023, indexed every 3 years). Failure to comply with a Government Assistance Powers (Part 3A) direction can attract up to 200 penalty units per day of non-compliance for an individual and up to 1,000 penalty units per day for a body corporate. Part 6A on-disclosure offences carry criminal penalties: knowingly disclosing Protected Information to an unauthorised person is an offence of up to 2 years imprisonment (s46). The Minister can issue a direction to vary or suspend an entity's operating licence (in concert with the sector-specific regulator) where non-compliance affects national security. Aggravated non-compliance can be referred to the Australian Federal Police for prosecution. Reputational damage is a material consequence: the CISC publishes anonymised regulatory-finding summaries and a regulatory letter to the entity's board can reach the entity's ASX disclosure obligations if the impact is material.

## 11. Pack gaps and remediation backlog

Clauses tracked in `data/regulations.json` that are **not yet covered** by any UC in this catalogue are listed below. These are the backlog items for the next release. Priority order follows priorityWeight.

| Clause | Topic | Priority |
|---|---|---|
| `SOCI-CIRMP-r10` | CIRMP Rules — Annual report to the Department | 1.0 |
| `SOCI-CIRMP-r5` | CIRMP Rules — General requirements and material-risk identification | 1.0 |
| `SOCI-CIRMP-r6.1` | CIRMP Rules — Cyber-and-information-security material risks (general) | 1.0 |
| `SOCI-CIRMP-r6.2` | CIRMP Rules — Cyber-and-information-security continuous monitoring | 1.0 |
| `SOCI-CIRMP-r6.3` | CIRMP Rules — Mandatory cyber framework adoption (Aug 2024 deadline) | 1.0 |
| `SOCI-CIRMP-r7.1` | CIRMP Rules — Personnel hazards: critical-worker identification and assessment | 1.0 |
| `SOCI-CIRMP-r7.2` | CIRMP Rules — Personnel hazards: insider-threat detection and removal | 1.0 |
| `SOCI-CIRMP-r8.1` | CIRMP Rules — Supply-chain hazards: vendor risk register | 1.0 |
| `SOCI-cross-asset-inventory` | OT asset inventory with criticality classification (CISC expectation) | 1.0 |
| `SOCI-cross-segmentation` | OT zone-and-conduit segmentation (Defence, Energy, Water, Critical Manufacturing) | 1.0 |
| `SOCI-s18` | Asset register — responsible entity reporting (Part 2) | 1.0 |
| `SOCI-s30AC` | Duty to adopt and maintain a Critical Infrastructure Risk Management Program (CIRMP) | 1.0 |
| `SOCI-s30AG` | Board (or equivalent) approval and annual report | 1.0 |
| `SOCI-s30AH` | Annual review of the CIRMP | 1.0 |
| `SOCI-s30BC` | Critical cyber-security incident — 12-hour notification (Part 2B) | 1.0 |
| `SOCI-s30BD` | Other (significant) cyber-security incident — 72-hour notification | 1.0 |
| `SOCI-s30CB` | Statutory cyber-incident response plan for Systems of National Significance (SoNS) | 1.0 |
| `SOCI-CIRMP-r8.2` | CIRMP Rules — Supply-chain hazards: continuous supplier monitoring | 0.7 |
| `SOCI-CIRMP-r9.1` | CIRMP Rules — Physical and natural hazards: site security | 0.7 |
| `SOCI-CIRMP-r9.2` | CIRMP Rules — Natural hazards and business continuity exercises | 0.7 |
| `SOCI-ECSO-vulnerability` | Enhanced Cyber Security Obligations — vulnerability disclosure and remediation tracking | 0.7 |
| `SOCI-cross-audit-evidence` | Audit-evidence retention for CIRMP and incident reporting | 0.7 |
| `SOCI-cross-data-residency` | Australian data residency and operational-data sovereignty | 0.7 |
| `SOCI-cross-encryption` | Encryption of operational data in transit between zones | 0.7 |
| `SOCI-s30BF` | Subsequent written report — 84-hour requirement | 0.7 |
| `SOCI-s30CG` | Cyber-security exercise on demand for SoNS | 0.7 |
| `SOCI-s30CM` | Vulnerability assessment on demand for SoNS | 0.7 |
| `SOCI-s30DJ` | System information periodic reporting (event-log telemetry) for SoNS | 0.7 |

## 12. Questions an auditor should ask

These are the questions a regulator, certification body, or external auditor is likely to ask. The pack helps preparers stage evidence and pre-test responses before the review opens.

- Produce the Register of Critical Infrastructure Assets entries for the in-scope assets per s18; demonstrate every operational-information and direct-interest-holder field is current within 30 days of any material change.
- Produce the CIRMP document approved by the board per s30AC and demonstrate the annual review on the anniversary date; show evidence of corrections, the board's review minute, and the residual-risk-register currency.
- Demonstrate every Rule 4 hazard (cyber, personnel, supply-chain, physical-and-natural) is identified, assessed, and treated, with residual risk reconciled to the annual report (Rule 10).
- Produce critical-cyber-incident notification evidence per s30BC: show the 12-hour decision and ASD lodgement, the written follow-up within 48 hours / 72 hours, and reconciliation to the Splunk evidence trail.
- Demonstrate Rule 6(3) cyber framework attestation currency: show the recognised framework (Essential Eight, ISO 27001, NIST CSF, AESCSF, C2M2, or Secretary-approved equivalent), the maturity-level evidence, and the attestation artefact for every in-scope asset.
- Produce Rule 6(2) detection-effectiveness test records for every in-scope asset; show MTTD/MTTC/MTTR metrics and the defect-burn-down for follow-up actions.
- Demonstrate Rule 7 critical-worker register currency: show how critical workers are identified, screened (AGSVA, NCCHC, or equivalent), trained, and access-managed; produce 30 sample workers with full evidence chain.
- Demonstrate Rule 7(2) insider-threat anomaly detection: show UEBA / SIEM signals scoped to the critical-worker population, signal-to-ticket conversion, and the annual removal-process test record.
- Produce Rule 8 supply-chain hazard register: show every tier-1 supplier's contractual cyber clauses, security assessment, and attestation currency.
- Produce Rule 8(2) sanctions and FOCI screening evidence: show every supplier and beneficial-owner screened against the DFAT Consolidated List and DFAT Autonomous Sanctions List; produce all matches with disposition.
- Produce Rule 9 physical and natural-hazard register: show every in-scope asset's hazard classes assessed and any live monitoring feeds (BoM warnings, Geoscience Australia earthquake feed, Emergency Management Victoria flood feed) integrated.
- Demonstrate cyber-physical convergence: show how cyber detections targeting OT control planes trigger documented physical safeguards (HMI local-mode lockdown, PACS guard dispatch) within SLA.
- Produce Rule 10 annual report lodgement evidence for the most recent financial year: show board approval, CISC lodgement timestamp, acknowledgement ID, and Section coverage across Rules 4-9 and the cyber framework.
- Demonstrate Rule 10 section-by-section completeness: show that every CIRMP rule section in the annual report has substantive content, evidence-link inventory, and board sign-off.
- Produce Part 6A Protected Information audit evidence: show DLP, email, cloud, USB monitoring of Protected-labelled documents; produce the lawful-disclosure register and reconcile authorised disclosures.
- Demonstrate ECSO 14-day Notice-of-Operations evidence for SoNS-declared assets: show material-change detection, the 14-day clock, the lodgement, and the CISC portal acknowledgement.
- Produce Government Assistance Powers (Part 3A) evidence: show every Government direction received, the deadline tracking, the action completion artefacts, and the CISC engagement.
- Produce the cross-cutting compliance health view: show the 12 SOCI KPIs across Asset Register, CIRMP lifecycle, incident reporting, SoNS obligations, cyber-hazard, personnel-hazard, supply-chain-hazard, physical-natural-hazard, annual report, Protected Information, ECSO notice, and Government Directions.

## 13. Machine-readable twin

The machine-readable companion of this pack lives at [`api/v1/evidence-packs/soci.json`](../../api/v1/evidence-packs/soci.json). It contains the same clause-level coverage, retention guidance, role matrix, and gap list in JSON form, and is regenerated in lockstep with this markdown pack so content stays in sync. Consumers integrating the pack into GRC tools, audit-request portals, or evidence pipelines should consume the JSON document; human readers should consume this markdown.

Related API surfaces (all under [`api/v1/`](../../api/README.md)):

- [`api/v1/compliance/regulations/soci.json`](../../api/v1/compliance/regulations/soci.json) — regulation metadata and per-version coverage metrics
- [`api/v1/compliance/ucs/`](../../api/v1/compliance/ucs/index.json) — individual UC sidecars
- [`api/v1/compliance/coverage.json`](../../api/v1/compliance/coverage.json) — global coverage snapshot
- [`api/v1/compliance/gaps.json`](../../api/v1/compliance/gaps.json) — global gap report

## 14. Provenance and regeneration

This pack is **generated**, not hand-authored. Re-running the generator produces byte-identical output (deterministic sort, stable serialisation, no free-form timestamps outside the block below). CI enforces regeneration drift via `--check` mode.

**Inputs to this pack**

- [`data/regulations.json`](../../data/regulations.json) — commonClauses, priority weights, authoritative URLs
- [`data/evidence-pack-extras.json`](../../data/evidence-pack-extras.json) — retention, roles, authoritative guidance, penalty, testing approach
- [`content/cat-*/UC-*.json`](../../content) — UC sidecars containing compliance[] entries, controlFamily, owner, evidence fields
- [`api/v1/compliance/regulations/soci@*.json`](../../api/v1/compliance/regulations/) — pre-computed coverage metrics (when present)

- Generator: [`scripts/generate_evidence_packs.py`](../../scripts/generate_evidence_packs.py)
- Evidence-pack directory index: [`docs/evidence-packs/README.md`](README.md)

**Generation metadata**

```
catalogue_version: 8.4.0
generator_script:  scripts/generate_evidence_packs.py
inputs_sha256:     a6f699ddf0cc3af8307960b8c3944af07e6560cd1fb779afaf1fc5666f143b1a
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

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** Australian Cyber Security Centre. (2023). *Essential Eight Maturity Model*. Australian Signals Directorate. https://www.cyber.gov.au/resources-business-and-government/essential-cybersecurity/essential-eight

<a id="ref-2"></a>**[2]** Cisco Systems, Inc. (2026). *Cisco Cyber Vision Documentation*. Retrieved May 11, 2026, from https://www.cisco.com/c/en/us/support/security/cyber-vision/series.html

<a id="ref-3"></a>**[3]** European Parliament and Council of the European Union. (2016, April). *Regulation (EU) 2016/679 — General Data Protection Regulation*. Official Journal of the European Union, L 119. ELI: reg/2016/679. https://eur-lex.europa.eu/eli/reg/2016/679/oj

<a id="ref-4"></a>**[4]** International Organization for Standardization. (2022). *ISO/IEC 27001:2022 — Information security, cybersecurity and privacy protection — Information security management systems — Requirements*. ISO/IEC. ISO/IEC 27001:2022. https://www.iso.org/standard/27001

<a id="ref-5"></a>**[5]** Microsoft Corporation. (2026). *Microsoft Entra ID Documentation*. Retrieved May 11, 2026, from https://learn.microsoft.com/en-us/entra/identity/

<a id="ref-6"></a>**[6]** National Institute of Standards and Technology. (2024). *Cybersecurity Framework (CSF) 2.0* (2.0). U.S. Department of Commerce. NIST CSWP 29. https://www.nist.gov/cyberframework

<a id="ref-7"></a>**[7]** Splunk Inc. (2026). *Splunk Enterprise Security Administration Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ES

<details>
<summary>Additional online sources cited in the document body (35)</summary>

<a id="ref-8"></a>**[8]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text

<a id="ref-9"></a>**[9]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/F2023L00112/latest/text

<a id="ref-10"></a>**[10]** cisc.gov.au. *cisc.gov.au: Critical Infrastructure*. Retrieved May 11, 2026, from https://www.cisc.gov.au/legislative-information-and-reforms/critical-infrastructure

<a id="ref-11"></a>**[11]** cyber.gov.au. *cyber.gov.au: Essential Eight Maturity Model*. Retrieved May 11, 2026, from https://www.cyber.gov.au/resources-business-and-government/essential-cybersecurity/essential-eight/essential-eight-maturity-model

<a id="ref-12"></a>**[12]** aemo.com.au. *aemo.com.au: Aescsf*. Retrieved May 11, 2026, from https://www.aemo.com.au/initiatives/major-programs/aescsf

<a id="ref-13"></a>**[13]** dfat.gov.au. *dfat.gov.au: Consolidated List*. Retrieved May 11, 2026, from https://www.dfat.gov.au/international-relations/security/sanctions/consolidated-list

<a id="ref-14"></a>**[14]** bom.gov.au. *bom.gov.au: Warnings*. Retrieved May 11, 2026, from https://www.bom.gov.au/warnings/

<a id="ref-15"></a>**[15]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-s18

<a id="ref-16"></a>**[16]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-s30AC

<a id="ref-17"></a>**[17]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-s30AH

<a id="ref-18"></a>**[18]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-s30AG

<a id="ref-19"></a>**[19]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-s30BC

<a id="ref-20"></a>**[20]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-s30BD

<a id="ref-21"></a>**[21]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-s30BF

<a id="ref-22"></a>**[22]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-s30CB

<a id="ref-23"></a>**[23]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-s30CG

<a id="ref-24"></a>**[24]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-s30CM

<a id="ref-25"></a>**[25]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-s30DJ

<a id="ref-26"></a>**[26]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-CIRMP-r5

<a id="ref-27"></a>**[27]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-CIRMP-r6.1

<a id="ref-28"></a>**[28]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-CIRMP-r6.2

<a id="ref-29"></a>**[29]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-CIRMP-r6.3

<a id="ref-30"></a>**[30]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-CIRMP-r7.1

<a id="ref-31"></a>**[31]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-CIRMP-r7.2

<a id="ref-32"></a>**[32]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-CIRMP-r8.1

<a id="ref-33"></a>**[33]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-CIRMP-r8.2

<a id="ref-34"></a>**[34]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-CIRMP-r9.1

<a id="ref-35"></a>**[35]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-CIRMP-r9.2

<a id="ref-36"></a>**[36]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-CIRMP-r10

<a id="ref-37"></a>**[37]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-ECSO-vulnerability

<a id="ref-38"></a>**[38]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-cross-segmentation

<a id="ref-39"></a>**[39]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-cross-asset-inventory

<a id="ref-40"></a>**[40]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-cross-data-residency

<a id="ref-41"></a>**[41]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-cross-encryption

<a id="ref-42"></a>**[42]** legislation.gov.au. *legislation.gov.au: Text*. Retrieved May 11, 2026, from https://www.legislation.gov.au/C2018A00029/latest/text#SOCI-cross-audit-evidence

</details>

<!-- END-AUTOGENERATED-SOURCES -->
