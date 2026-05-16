# Evidence Pack — CIRCIA

> **Tier**: Tier 1 &nbsp;·&nbsp; **Jurisdiction**: US &nbsp;·&nbsp; **Version**: `2022-act-with-2024-nprm`
>
> **Full name**: Cyber Incident Reporting for Critical Infrastructure Act of 2022 (CIRCIA) + CISA 2024 NPRM (proposed final rule)
> **Authoritative source**: [https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia)
> **Effective from**: 2022-03-15

> This evidence pack is the auditor-facing view of the Splunk monitoring catalogue's coverage of the regulation. Every clause coverage claim is traceable to a specific UC sidecar JSON file (`content/cat-*/UC-*.json`); every retention figure cites its legal basis; every URL resolves to an official regulator or standards-body source. The pack does **not** assert legal conclusions — it tabulates what the catalogue covers, names the authoritative source, and flags gaps. Interpretation stays with counsel.

> **Live views.** [Buyer narrative (`compliance-story.html?reg=circia`)](../../compliance-story.html?reg=circia) · [Auditor clause navigator (`clause-navigator.html#reg=circia`)](../../clause-navigator.html#reg=circia) · [JSON twin (`api/v1/compliance/story/circia.json`)](../../api/v1/compliance/story/circia.json)

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

The Cyber Incident Reporting for Critical Infrastructure Act of 2022 (CIRCIA), enacted as Division Y of the Consolidated Appropriations Act, 2022 (Pub. L. 117-103), and codified at 6 U.S.C. § 681 et seq., requires covered entities in 16 critical-infrastructure sectors to report covered cyber incidents to CISA within 72 hours of reasonable belief and ransom payments within 24 hours. The CISA Notice of Proposed Rulemaking published 4 April 2024 (89 FR 23644) specifies the covered-entity definition, the covered-incident scope (substantial losses, operational disruption, unauthorized access to sensitive data, supply-chain compromise), the supplemental-report obligation (when new or different information becomes available), records preservation (2 years for raw evidence; 10 years for the CIRCIA report itself), and the CIRCIA Agreement pathway that lets a third party report on behalf of the covered entity. CIRCIA also created the Cyber Incident Reporting Council to harmonise pre-existing federal sector-specific reporting (NRC, FCC, FDA, FAA, FERC, SEC, EPA, FBI / Secret Service). CIRCIA submissions carry liability protection under 6 U.S.C. § 681e and are not admissible against the reporting entity in regulatory or civil proceedings.

## 2. Scope and applicability

Applies to 'covered entities' within the 16 critical-infrastructure sectors enumerated in Presidential Policy Directive 21 (Chemical, Commercial Facilities, Communications, Critical Manufacturing, Dams, Defense Industrial Base, Emergency Services, Energy, Financial Services, Food and Agriculture, Government Facilities, Healthcare and Public Health, Information Technology, Nuclear, Transportation Systems, Water and Wastewater Systems). The 2024 NPRM proposes a size threshold and sector-specific carve-outs. Covered cyber incidents include substantial loss of confidentiality, integrity, or availability of an information system or network; serious impact on safety and resiliency of operational systems; disruption of business or industrial operations including ransomware operational impact; or unauthorized access via supply chain compromise, third-party provider, or denial-of-service. Excludes incidents covered by a substantially-similar reporting obligation under another federal regime where CISA has executed a CIRCIA Agreement.

**Territorial scope.** United States and territories, plus extraterritorial reach to any non-US entity that owns, operates, or controls a covered information system or network within US critical-infrastructure sectors. CIRCIA reaches non-US parent companies of covered subsidiaries through the subsidiary's obligation. International coordination is via CISA's bilateral relationships (e.g. CISA-NCSC UK, CISA-CCCS Canada, CISA-BSI Germany, CISA-ENISA EU).

## 3. Catalogue coverage at a glance

- **Clauses tracked**: 28
- **Clauses covered by at least one UC**: 28 / 28 (100.0%)
- **Priority-weighted coverage**: 100.0%
- **Contributing UCs**: 28

Coverage methodology is documented in [`docs/coverage-methodology.md`](../coverage-methodology.md). Priority weights come from `data/regulations.json` commonClauses entries (see [`data/regulations.json`](../../data/regulations.json) priorityWeightRubric).

## 4. Clause-by-clause coverage

Clauses are listed in the order defined by `data/regulations.json commonClauses` for this regulation version. A clause is considered covered when at least one UC sidecar has a `compliance[]` entry matching `(regulation, version, clause)`. Assurance is the maximum across contributing UCs.

| Clause | Topic | Priority | Assurance | UCs |
|---|---|---|---|---|
| [`CIRCIA-s2242a`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-s2242a) | Definitions — 'covered entity' and 'covered cyber incident' | 1.0 | `full` | [UC-22.54.1](#uc-22-54-1) |
| [`CIRCIA-s2242b`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-s2242b) | Mandatory covered-cyber-incident report — within 72 hours of reasonable belief | 1.0 | `full` | [UC-22.54.2](#uc-22-54-2), [UC-22.54.26](#uc-22-54-26) |
| [`CIRCIA-s2242c`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-s2242c) | Mandatory ransom-payment report — within 24 hours | 1.0 | `full` | [UC-22.54.26](#uc-22-54-26), [UC-22.54.3](#uc-22-54-3) |
| [`CIRCIA-s2242d`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-s2242d) | Supplemental report — when new material information emerges | 1.0 | `full` | [UC-22.54.26](#uc-22-54-26), [UC-22.54.4](#uc-22-54-4) |
| [`CIRCIA-s2242f`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-s2242f) | Records preservation — preserve data and records related to the incident | 1.0 | `full` | [UC-22.54.27](#uc-22-54-27), [UC-22.54.5](#uc-22-54-5) |
| [`CIRCIA-s2242g`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-s2242g) | Liability protections and privileged-communication treatment | 0.7 | `partial` | [UC-22.54.6](#uc-22-54-6) |
| [`CIRCIA-s2242h`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-s2242h) | Enforcement — request for information and subpoena authority | 1.0 | `full` | [UC-22.54.7](#uc-22-54-7) |
| [`CIRCIA-NPRM-covered-entity`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-NPRM-covered-entity) | Covered-entity scope (proposed in 2024 NPRM) | 1.0 | `full` | [UC-22.54.8](#uc-22-54-8) |
| [`CIRCIA-NPRM-covered-incident`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-NPRM-covered-incident) | Covered-incident definition (proposed in 2024 NPRM) — 'substantial' cyber incident | 1.0 | `full` | [UC-22.54.9](#uc-22-54-9) |
| [`CIRCIA-NPRM-72hr-reporting`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-NPRM-72hr-reporting) | 72-hour reporting clock — operationalisation | 1.0 | `full` | [UC-22.54.10](#uc-22-54-10) |
| [`CIRCIA-NPRM-24hr-ransom`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-NPRM-24hr-ransom) | 24-hour ransom-payment clock — operationalisation | 1.0 | `full` | [UC-22.54.11](#uc-22-54-11) |
| [`CIRCIA-NPRM-report-content`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-NPRM-report-content) | Required report content — the CIRCIA report template | 1.0 | `full` | [UC-22.54.12](#uc-22-54-12) |
| [`CIRCIA-NPRM-third-party-reporting`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-NPRM-third-party-reporting) | Third-party reporting — incident-response firms, insurance carriers, MSSP partners | 1.0 | `full` | [UC-22.54.13](#uc-22-54-13) |
| [`CIRCIA-NPRM-data-preservation`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-NPRM-data-preservation) | Data and records preservation — 2-year retention | 1.0 | `full` | [UC-22.54.27](#uc-22-54-27), [UC-22.54.5](#uc-22-54-5) |
| [`CIRCIA-NPRM-supplemental-trigger`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-NPRM-supplemental-trigger) | Supplemental-report trigger conditions | 1.0 | `full` | [UC-22.54.4](#uc-22-54-4) |
| [`CIRCIA-NPRM-cisa-agreement`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-NPRM-cisa-agreement) | CIRCIA Agreement — sector-specific bridge to other federal reporting | 0.7 | `full` | [UC-22.54.15](#uc-22-54-15) |
| [`CIRCIA-NPRM-recordkeeping-quality`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-NPRM-recordkeeping-quality) | Recordkeeping quality — auditable timestamp evidence | 1.0 | `full` | [UC-22.54.14](#uc-22-54-14) |
| [`CIRCIA-CISA-portal`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-CISA-portal) | CISA Services Portal — the canonical reporting channel | 1.0 | `full` | [UC-22.54.16](#uc-22-54-16) |
| [`CIRCIA-CISA-interim-reporting`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-CISA-interim-reporting) | Interim reporting (pre-Final Rule) — voluntary but CISA-encouraged | 0.7 | `partial` | [UC-22.54.17](#uc-22-54-17) |
| [`CIRCIA-CISA-protected-information`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-CISA-protected-information) | Protected information handling — CISA's safeguards on the report content | 0.7 | `partial` | [UC-22.54.6](#uc-22-54-6) |
| [`CIRCIA-CISA-coordination-with-sector-srma`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-CISA-coordination-with-sector-srma) | Sector Risk Management Agency coordination (SRMA) | 0.7 | `full` | [UC-22.54.18](#uc-22-54-18) |
| [`CIRCIA-CISA-incident-classification`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-CISA-incident-classification) | Internal classification — distinguishing CIRCIA-reportable from sectoral-only | 1.0 | `full` | [UC-22.54.19](#uc-22-54-19), [UC-22.54.28](#uc-22-54-28) |
| [`CIRCIA-CISA-third-party-incident`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-CISA-third-party-incident) | Third-party incident attribution — supply chain, MSSP, cloud | 1.0 | `full` | [UC-22.54.20](#uc-22-54-20) |
| [`CIRCIA-CISA-ot-incident`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-CISA-ot-incident) | OT / ICS / SCADA incidents — explicit in-scope under CIRCIA | 1.0 | `full` | [UC-22.54.21](#uc-22-54-21) |
| [`CIRCIA-CISA-board-fiduciary`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-CISA-board-fiduciary) | Board fiduciary awareness — pre-incident assignment of responsibility | 0.7 | `full` | [UC-22.54.22](#uc-22-54-22) |
| [`CIRCIA-CISA-sec-form-8-k`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-CISA-sec-form-8-k) | SEC Form 8-K Item 1.05 alignment — materiality + CIRCIA | 0.7 | `full` | [UC-22.54.23](#uc-22-54-23) |
| [`CIRCIA-CISA-tabletop`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-CISA-tabletop) | Annual tabletop — CIRCIA reporting workflow exercise | 0.7 | `full` | [UC-22.54.24](#uc-22-54-24), [UC-22.54.28](#uc-22-54-28) |
| [`CIRCIA-CISA-records-retention`](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-CISA-records-retention) | CIRCIA-specific records retention — 2 years per NPRM | 0.7 | `full` | [UC-22.54.25](#uc-22-54-25) |

### 4.1 Contributing UC detail

<a id='uc-22-54-1'></a>
- **UC-22.54.1** — CIRCIA Covered-Entity Determination Registry — maintain authoritative scope evidence so the 72-hour clock starts the moment it must
  - Control family: `regulation-specific`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.1.json`](../../content/cat-22-regulatory-compliance/UC-22.54.1.json)
<a id='uc-22-54-10'></a>
- **UC-22.54.10** — CIRCIA 72-Hour Clock Determination-Point Detection — timestamp the 'reasonably believes' decision with auditable provenance
  - Control family: `regulation-specific`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.10.json`](../../content/cat-22-regulatory-compliance/UC-22.54.10.json)
<a id='uc-22-54-11'></a>
- **UC-22.54.11** — CIRCIA 24-Hour Ransom-Payment Clock Operationalisation — capture broadcast / debit timestamp from wallet-custodian and treasury workstation
  - Control family: `regulation-specific`
  - Owner: `CFO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.11.json`](../../content/cat-22-regulatory-compliance/UC-22.54.11.json)
<a id='uc-22-54-12'></a>
- **UC-22.54.12** — CIRCIA Report-Content Template Validator — every submission includes the 11 NPRM §226.8 required elements before transmission
  - Control family: `regulation-specific`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.12.json`](../../content/cat-22-regulatory-compliance/UC-22.54.12.json)
<a id='uc-22-54-13'></a>
- **UC-22.54.13** — CIRCIA Third-Party Reporting Authorisation — IR firm, insurer, or MSSP may submit on the covered entity's behalf with written authority
  - Control family: `regulation-specific`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.13.json`](../../content/cat-22-regulatory-compliance/UC-22.54.13.json)
<a id='uc-22-54-14'></a>
- **UC-22.54.14** — CIRCIA Recordkeeping-Quality Audit — auditable timestamp evidence for every reported determination, broadcast, and submission
  - Control family: `regulation-specific`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.14.json`](../../content/cat-22-regulatory-compliance/UC-22.54.14.json)
<a id='uc-22-54-15'></a>
- **UC-22.54.15** — CIRCIA Agreement Inventory — evidence every sectoral-bridge agreement (NRC, FCC, FDA, FAA, FERC, SEC, EPA) is current and operationalised
  - Control family: `regulation-specific`
  - Owner: `Legal`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.15.json`](../../content/cat-22-regulatory-compliance/UC-22.54.15.json)
<a id='uc-22-54-16'></a>
- **UC-22.54.16** — CIRCIA CISA Services Portal Submission Health — verify every submission is acknowledged with a portal receipt and a CISA case number
  - Control family: `regulation-specific`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.16.json`](../../content/cat-22-regulatory-compliance/UC-22.54.16.json)
<a id='uc-22-54-17'></a>
- **UC-22.54.17** — CIRCIA Interim Voluntary-Reporting Posture — documented decision-and-implementation framework for pre-Final-Rule reporting
  - Control family: `regulation-specific`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.17.json`](../../content/cat-22-regulatory-compliance/UC-22.54.17.json)
<a id='uc-22-54-18'></a>
- **UC-22.54.18** — CIRCIA Sector-SRMA Coordination Trail — evidence each CISA submission was relayed to / from the Sector Risk Management Agency
  - Control family: `regulation-specific`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.18.json`](../../content/cat-22-regulatory-compliance/UC-22.54.18.json)
<a id='uc-22-54-19'></a>
- **UC-22.54.19** — CIRCIA Internal Incident Classification Triage — distinguish CIRCIA-reportable from sectoral-only and notice-only
  - Control family: `regulation-specific`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.19.json`](../../content/cat-22-regulatory-compliance/UC-22.54.19.json)
<a id='uc-22-54-2'></a>
- **UC-22.54.2** — CIRCIA 72-Hour Covered-Cyber-Incident Reporting SLA Timer — every reasonable-belief determination must land at CISA in 72 hours
  - Control family: `regulation-specific`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.2.json`](../../content/cat-22-regulatory-compliance/UC-22.54.2.json)
<a id='uc-22-54-20'></a>
- **UC-22.54.20** — CIRCIA Third-Party Supply-Chain & MSSP Incident Attribution — detect impact from upstream cloud, SaaS, or MSSP compromise
  - Control family: `regulation-specific`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.20.json`](../../content/cat-22-regulatory-compliance/UC-22.54.20.json)
<a id='uc-22-54-21'></a>
- **UC-22.54.21** — CIRCIA OT / ICS / SCADA Incident Detection — industrial-environment substantial-incident triggers wired into the CIRCIA flow
  - Control family: `regulation-specific`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.21.json`](../../content/cat-22-regulatory-compliance/UC-22.54.21.json)
<a id='uc-22-54-22'></a>
- **UC-22.54.22** — CIRCIA Board Fiduciary Awareness — evidence pre-incident assignment of responsibility, training, and quarterly briefing
  - Control family: `regulation-specific`
  - Owner: `Legal`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.22.json`](../../content/cat-22-regulatory-compliance/UC-22.54.22.json)
<a id='uc-22-54-23'></a>
- **UC-22.54.23** — CIRCIA + SEC Form 8-K Item 1.05 Materiality-Triangulation — every public-issuer incident is dual-tracked for SEC + CIRCIA
  - Control family: `regulation-specific`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.23.json`](../../content/cat-22-regulatory-compliance/UC-22.54.23.json)
<a id='uc-22-54-24'></a>
- **UC-22.54.24** — CIRCIA Annual Tabletop — evidence end-to-end 72-hour / 24-hour reporting workflow exercised with executive participation
  - Control family: `regulation-specific`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.24.json`](../../content/cat-22-regulatory-compliance/UC-22.54.24.json)
<a id='uc-22-54-25'></a>
- **UC-22.54.25** — CIRCIA Records Retention — enforce 2-year preservation from most-recent-report, with integrity verification quarterly
  - Control family: `regulation-specific`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.25.json`](../../content/cat-22-regulatory-compliance/UC-22.54.25.json)
<a id='uc-22-54-26'></a>
- **UC-22.54.26** — CIRCIA Quarterly Compliance Attestation — General Counsel signs end-to-end compliance posture across statutory + NPRM clauses
  - Control family: `regulation-specific`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.26.json`](../../content/cat-22-regulatory-compliance/UC-22.54.26.json)
<a id='uc-22-54-27'></a>
- **UC-22.54.27** — CIRCIA Forensic Imaging Pipeline — evidence capture of affected endpoints and OT controllers with cryptographic chain of custody
  - Control family: `regulation-specific`
  - Owner: `Head of IR`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.27.json`](../../content/cat-22-regulatory-compliance/UC-22.54.27.json)
<a id='uc-22-54-28'></a>
- **UC-22.54.28** — CIRCIA Annual SLA & KPI Review — board-level review of reporting performance, miss rates, and remediation actions
  - Control family: `regulation-specific`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.28.json`](../../content/cat-22-regulatory-compliance/UC-22.54.28.json)
<a id='uc-22-54-3'></a>
- **UC-22.54.3** — CIRCIA 24-Hour Ransom-Payment Reporting SLA Timer — every ransom payment, however small, lands at CISA in 24 hours
  - Control family: `regulation-specific`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.3.json`](../../content/cat-22-regulatory-compliance/UC-22.54.3.json)
<a id='uc-22-54-4'></a>
- **UC-22.54.4** — CIRCIA Supplemental-Report Pipeline — evidence every new material finding lands at CISA promptly until the incident is fully resolved
  - Control family: `regulation-specific`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.4.json`](../../content/cat-22-regulatory-compliance/UC-22.54.4.json)
<a id='uc-22-54-5'></a>
- **UC-22.54.5** — CIRCIA Records-Preservation Activation — freeze and retain every artefact relevant to a reported incident for at least 2 years
  - Control family: `regulation-specific`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.5.json`](../../content/cat-22-regulatory-compliance/UC-22.54.5.json)
<a id='uc-22-54-6'></a>
- **UC-22.54.6** — CIRCIA Liability-Protection Coversheet Audit — every submission is marked, transmitted, and stored under the s 2242(g) privileged-communication regime
  - Control family: `regulation-specific`
  - Owner: `Legal`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.6.json`](../../content/cat-22-regulatory-compliance/UC-22.54.6.json)
<a id='uc-22-54-7'></a>
- **UC-22.54.7** — CIRCIA Request-for-Information & Subpoena Compliance Tracker — every CISA RFI is answered within the 72-hour statutory response window
  - Control family: `regulation-specific`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.7.json`](../../content/cat-22-regulatory-compliance/UC-22.54.7.json)
<a id='uc-22-54-8'></a>
- **UC-22.54.8** — CIRCIA NPRM Covered-Entity Scope Self-Assessment — SBA size + sector criteria + NAICS evidence for every legal entity
  - Control family: `regulation-specific`
  - Owner: `CFO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.8.json`](../../content/cat-22-regulatory-compliance/UC-22.54.8.json)
<a id='uc-22-54-9'></a>
- **UC-22.54.9** — CIRCIA Substantial-Cyber-Incident Classification Engine — deterministically flag every IR ticket against the NPRM §226.1 four-prong test
  - Control family: `regulation-specific`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.54.9.json`](../../content/cat-22-regulatory-compliance/UC-22.54.9.json)

## 5. Evidence collection

### 5.1 Common evidence sources

Auditors typically request the following records when examining this regulation:

- ServiceNow Security Incident Response (snow:sir) for incident tickets, classification, owner assignment, supplemental-report log.
- ServiceNow GRC for the CIRCIA covered-entity register, CIRCIA Agreements, quarterly attestations, Board brief calendar, tabletop schedule.
- Splunk SOAR<sup class="ref">[<a href="#ref-8">8</a>]</sup> (soar:audit, soar:case, soar:playbook) for CIRCIA 72-hour and 24-hour playbook execution telemetry.
- CISA Cyber Incident Reporting Portal (CIRP) submission receipts ingested via HEC (hec:circia:submission).
- Microsoft 365 / Azure AD audit logs (o365:management, azuread:audit, azure:activity) for incident-context evidence.
- AWS CloudTrail<sup class="ref">[<a href="#ref-2">2</a>]</sup> / GuardDuty / Microsoft Defender for Endpoint / CrowdStrike Falcon<sup class="ref">[<a href="#ref-4">4</a>]</sup> / Palo Alto Cortex XDR for detection telemetry.
- Cisco Cyber Vision<sup class="ref">[<a href="#ref-3">3</a>]</sup> / Claroty CTD / Nozomi Guardian / Dragos Platform for OT/ICS/SCADA operational-disruption detection.
- CyberArk PAM session records for privileged-access incident context.
- CISA Known Exploited Vulnerabilities Catalog<sup class="ref">[<a href="#ref-5">5</a>]</sup> feed for KEV-triggered incidents.
- FinCEN SAR drafts for ransomware payment regulatory disclosure parallel pathway.
- RFC 3161 time-stamping authority logs for evidence-integrity attestation.
- Microsoft Purview Records Management for the 2-year raw-evidence and 10-year report retention policy.

### 5.2 Retention requirements

| Artifact | Retention | Legal basis |
|---|---|---|
| CIRCIA covered-cyber-incident report (72-hour) | Minimum 10 years from submission (statute of limitations alignment) | CIRCIA NPRM § 226.18; 6 U.S.C. § 681b(c) |
| Ransom-payment report (24-hour) | Minimum 10 years from submission | CIRCIA NPRM § 226.18; 6 U.S.C. § 681b(c) |
| Supplemental reports and corrections | Minimum 10 years from final supplemental | CIRCIA NPRM § 226.18 |
| Raw evidence supporting the report (logs, packet captures, forensic images, malware samples, indicators of compromise) | Minimum 2 years from report submission | CIRCIA NPRM § 226.18(b); CISA guidance |
| CIRCIA Agreements (third-party-reporter authority, written authorisation, scope, expiration) | Duration of agreement plus 10 years | CIRCIA NPRM § 226.18 |
| RFI (Request For Information) and response correspondence with CISA | Minimum 10 years from final response | CIRCIA NPRM § 226.18; CIRCIA s2242a |
| SRMA (Sector Risk Management Agency) coordination correspondence | Minimum 10 years; aligned with CIRCIA report retention | PPD-21; CIRCIA Cyber Incident Reporting Council |
| Liability-protection coversheets (asserting 6 U.S.C. § 681e protection) | Minimum 10 years from submission | 6 U.S.C. § 681e |
| Quarterly compliance attestations and tabletop after-action reports | Minimum 7 years | Internal governance aligned with SEC retention norms |
| Forensic imaging chain-of-custody records | Minimum 10 years | Federal Rules of Evidence; CISA forensic guidance |

> Retention figures above are the legal minimums or regulator-stated expectations. Organisation-specific retention schedules may be longer where business, tax, litigation-hold, or contractual obligations apply. Where a figure conflicts with local data-protection law (e.g. GDPR<sup class="ref">[<a href="#ref-6">6</a>]</sup> Art.5(1)(e) storage-limitation principle), the shorter conformant period governs for personal-data content; the evidence-of-compliance retention retains the longer period for audit purposes, scrubbed of excess personal data.

### 5.3 Evidence integrity expectations

Regulators increasingly cite **evidence-integrity failures** as aggravating factors in enforcement actions. Cross-regulation baseline expectations:

- Time-stamped, tamper-evident storage (WORM, cryptographic chaining, or append-only indexes).
- Chain-of-custody for any evidence removed from the SIEM / production system for audit or legal purposes.
- Synchronised clocks (NTP stratum ≤ 3 or equivalent) across all in-scope sources so timeline reconstruction is defensible.
- Documented retention enforcement — not just retention policy — so that deletion is auditable.

See cat-22.35 "Evidence continuity and log integrity" for UCs that implement these controls.

## 6. Control testing procedures

CIRCIA is administered by CISA with the Cyber Incident Reporting Council coordinating across federal agencies. CISA's enforcement model has three layers: (a) RFI-based enforcement for non-substantive omissions, (b) civil enforcement under 6 U.S.C. § 681c for material non-compliance, and (c) criminal referral via DOJ for knowing false statements under 18 U.S.C. § 1001. Once the final rule is in force, CISA may conduct planned reviews; pre-final-rule the agency relies on voluntary interim reporting and post-incident enquiry. External assurance: many covered entities engage outside counsel and a Big-4 cybersecurity advisory to attest the CIRCIA programme annually. Tabletop exercises must include counsel, CISO, CFO, and Public Affairs to validate the 72-hour and 24-hour clocks end-to-end. SEC-registered covered entities perform parallel materiality triangulation under Item 1.05 of Form 8-K (4-business-day disclosure). The CISA Cyber Hygiene services and CIRCIA Agreement pre-negotiation pathway provide pre-incident readiness assurance.

**Reporting cadence.** Covered-cyber-incident report — within 72 hours of reasonable belief. Ransom-payment report — within 24 hours of payment. Supplemental reports — promptly when new information becomes available. RFI responses — per CISA's specific deadline (commonly 30 days). Quarterly compliance attestation — signed by CISO and General Counsel. Annual tabletop exercise end-to-end. Annual SLA / KPI review. Daily CISA Portal health check. Monthly CIRCIA covered-entity review against organic growth. Annual Board fiduciary brief.

## 7. Roles and responsibilities

| Role | Responsibility |
|---|---|
| **Chief Information Security Officer (CISO)** | Primary owner of CIRCIA programme; signs the 72-hour and 24-hour reports; certifies the CIRCIA quarterly compliance attestation; chairs incident-classification review. |
| **General Counsel** | Reviews each covered-entity determination, covered-incident classification, ransom-payment legality (OFAC screening, FinCEN SAR coordination), liability-protection assertion, and supplemental-report disclosure scope. |
| **Chief Risk Officer / Audit Committee Chair** | Reviews CIRCIA programme posture in the Board Risk Committee at least quarterly; signs Board fiduciary brief; oversees enterprise-risk integration with SEC Form 8-K materiality. |
| **Incident Commander** | Operational owner during an incident; classifies covered vs non-covered using the incident-classification runbook; coordinates with CISA Cyber Incident Response Team; tracks RFI responses. |
| **Records Custodian / Compliance Officer** | Owns the CIRCIA records-preservation register, 2-year raw-evidence retention, 10-year report retention, forensic-imaging chain-of-custody, and RFC 3161 timestamp integrity. |
| **Threat-Intel Lead** | Owns SRMA coordination correspondence, CISA portal submission health, voluntary interim reporting posture, and CIRCIA Agreement (third-party-reporter) coordination. |
| **OT / ICS Cybersecurity Lead** | Owns OT/ICS/SCADA covered-incident-detection content (operational disruption indicators), coordinates with SRMAs covering the OT-heavy critical-infrastructure sectors. |
| **Privacy Counsel / Data Protection Officer** | Reviews PII implications of CIRCIA reports; coordinates with state breach-notification laws and other US privacy frameworks where personal data was implicated. |
| **Cybersecurity and Infrastructure Security Agency (CISA)** | Federal recipient of CIRCIA reports; publishes the proposed rule; issues RFIs; coordinates the Cyber Incident Reporting Council; provides liability-protected information-sharing channels. |
| **Sector Risk Management Agency (SRMA)** | Federal coordinating agency for the specific critical-infrastructure sector (e.g. DOE for Energy, EPA for Water/Wastewater, HHS for Healthcare, DOT for Transportation); receives sector-specific reports under CISA harmonisation. |
| **FBI Internet Crime Complaint Center (IC3) / Secret Service** | Receives ransomware reports and law-enforcement coordination on cyber incidents; provides parallel pathway with CIRCIA. |

## 8. Authoritative guidance

- **Cyber Incident Reporting for Critical Infrastructure Act of 2022 (Division Y of Pub. L. 117-103)** — U.S. CISA — [https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia)
- **CIRCIA Notice of Proposed Rulemaking (89 FR 23644, April 4, 2024)** — U.S. CISA — [https://www.federalregister.gov/documents/2024/04/04/2024-06526/cyber-incident-reporting-for-critical-infrastructure-act-circia-reporting-requirements](https://www.federalregister.gov/documents/2024/04/04/2024-06526/cyber-incident-reporting-for-critical-infrastructure-act-circia-reporting-requirements)
- **Cyber Incident Reporting Council Pathways (CIRC) Report to Congress** — U.S. CISA — [https://www.cisa.gov/circia](https://www.cisa.gov/circia)
- **CISA Cyber Incident Reporting Portal (CIRP)** — U.S. CISA — [https://www.cisa.gov/report](https://www.cisa.gov/report)
- **Presidential Policy Directive 21 (Critical Infrastructure Security and Resilience)** — White House — [https://obamawhitehouse.archives.gov/the-press-office/2013/02/12/presidential-policy-directive-critical-infrastructure-security-and-resil](https://obamawhitehouse.archives.gov/the-press-office/2013/02/12/presidential-policy-directive-critical-infrastructure-security-and-resil)
- **CISA Known Exploited Vulnerabilities Catalog** — U.S. CISA — [https://www.cisa.gov/known-exploited-vulnerabilities-catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
- **SEC Final Rule on Cybersecurity Risk Management, Strategy, Governance, and Incident Disclosure (Item 1.05 Form 8-K)** — U.S. SEC — [https://www.sec.gov/files/rules/final/2023/33-11216.pdf](https://www.sec.gov/files/rules/final/2023/33-11216.pdf)
- **OFAC Ransomware Advisory (September 2021 Updated)** — U.S. Treasury OFAC — [https://home.treasury.gov/system/files/126/ofac_ransomware_advisory.pdf](https://home.treasury.gov/system/files/126/ofac_ransomware_advisory.pdf)
- **FinCEN Ransomware Advisory (FIN-2021-A004)** — U.S. FinCEN — [https://www.fincen.gov/sites/default/files/advisory/2021-11-08/FinCEN%20Ransomware%20Advisory_FINAL_508_.pdf](https://www.fincen.gov/sites/default/files/advisory/2021-11-08/FinCEN%20Ransomware%20Advisory_FINAL_508_.pdf)
- **FBI IC3 Reporting Portal** — FBI — [https://www.ic3.gov/](https://www.ic3.gov/)

## 9. Common audit deficiencies

Findings frequently cited by regulators, certification bodies, and external auditors for this regulation. These should be pre-tested as part of readiness reviews.

- Covered-entity determination performed once at programme initiation and never refreshed against the NPRM definition or sector growth (UC-22.54.1).
- Incident-classification runbook ambiguous on operational-disruption thresholds for OT/ICS/SCADA covered incidents (UC-22.54.7 / UC-22.54.15).
- 72-hour SLA missed because the 'reasonable belief' trigger was anchored to incident-confirmation rather than detection (UC-22.54.2).
- 24-hour ransom-payment SLA missed because payment-execution-time was not synchronised with the reporting clock (UC-22.54.3).
- Supplemental reports filed with delays >7 days when new information became available (UC-22.54.4).
- Raw-evidence retention shorter than 2 years; logs rolled off before CISA RFI cycle completed (UC-22.54.5 / UC-22.54.10).
- Liability-protection coversheet missing the 6 U.S.C. § 681e citation; some submissions reviewed without coversheet (UC-22.54.6).
- RFI tracking ad-hoc; no defined response SLA; some RFIs sit in inbox >14 days (UC-22.54.7).
- Report content fails validation: missing technical detail required by NPRM § 226.6 (UC-22.54.8).
- Third-party-reporter authority undocumented; vendor reports on behalf of entity without CIRCIA Agreement (UC-22.54.9).
- Records-preservation hash integrity not validated; tampering would not be detected (UC-22.54.10).
- CISA Portal submission health not monitored; portal outage missed (UC-22.54.12).
- Voluntary interim reporting posture undefined; entity unsure what to report pre-final-rule (UC-22.54.13).
- SRMA coordination ad-hoc; sector-specific channels unmapped (UC-22.54.14).
- Board fiduciary brief on CIRCIA missed in fiscal year (UC-22.54.16).
- SEC Form 8-K materiality not triangulated within 4 business days for CIRCIA-reported public-company incidents (UC-22.54.17).
- Annual tabletop exercise narrow: tested IR-team only, not end-to-end with counsel, CISO, CFO, Public Affairs (UC-22.54.18).
- Forensic imaging chain-of-custody breaks at the storage-archive step; immutability not provable (UC-22.54.22).
- Quarterly compliance attestation signed by CISO only; General Counsel signature missing (UC-22.54.21).
- Annual SLA / KPI review missing or older than 12 months (UC-22.54.24).

## 10. Enforcement and penalties

CIRCIA s 2242 establishes civil enforcement under 6 U.S.C. § 681c with civil penalty of up to $250,000 per day per violation (subject to adjustment for inflation under 28 U.S.C. § 2461 note). Knowingly false reporting under 18 U.S.C. § 1001 carries up to 5 years imprisonment. CISA may also issue subpoenas (6 U.S.C. § 681b(e)). Non-compliance can be referred to DOJ for civil enforcement. Pre-existing federal sector-specific reporting obligations (NRC, FCC, FDA, FAA, FERC, SEC, EPA, FBI) impose parallel penalties. SEC Item 1.05 Form 8-K materiality disclosure for public-company covered entities carries Section 18 liability under the Securities Exchange Act of 1934. OFAC ransomware payment screening violations (sanctioned-entity payments) carry separate strict-liability civil penalties up to $300,000 per violation or twice the transaction value. Reputational consequences for public-company covered entities are amplified by SEC Form 8-K materiality disclosure and post-incident shareholder litigation.

## 11. Pack gaps and remediation backlog

All clauses tracked in `data/regulations.json` for this regulation version are covered by at least one UC. **100 % common-clause coverage**. Remaining work is assurance-upgrade (for example, moving `contributing` entries to `partial` or `full` via explicit control tests) rather than new clause authoring.

## 12. Questions an auditor should ask

These are the questions a regulator, certification body, or external auditor is likely to ask. The pack helps preparers stage evidence and pre-test responses before the review opens.

- Show me the CIRCIA covered-entity determination for this organisation, signed by counsel, and the date it was last reviewed under the NPRM definition.
- Produce the last three covered-cyber-incident reports submitted to CISA and confirm each was submitted within 72 hours of reasonable belief that the incident was covered.
- Produce the last ransom-payment report and confirm it was submitted within 24 hours of payment, including the payment instructions and the transmittal evidence.
- Show the supplemental-report log: for each initial report, what new or different information was supplemented, and was the supplemental filed without undue delay?
- Produce the CIRCIA records-preservation register and show me the raw evidence (logs, packet captures, forensic images, malware samples) preserved for the last three reports.
- Show me the CIRCIA Agreements in force authorising third parties to report on behalf of this entity, with scope, expiration, and the underlying written authorisation.
- Where are CISA RFIs (Requests For Information) tracked, what is the response SLA, and produce the last three RFI responses with submission receipts.
- Produce the incident-classification logic that decides 'covered' vs 'non-covered' and 'ransom' vs 'non-ransom'. Show me the runbook walking through a borderline incident.
- Show me the OT/ICS/SCADA covered-incident-detection logic: how do we detect operational disruption versus IT-only incidents that don't qualify?
- Produce the Board fiduciary brief on CIRCIA: when did the Board last review CIRCIA readiness, who briefed them, and what was the residual-risk position?
- Show the SEC Form 8-K materiality triangulation: when CIRCIA reportable, was SEC materiality assessed in parallel within 4 business days?
- Produce the latest annual tabletop after-action report exercising the CIRCIA 72-hour and 24-hour pathways end-to-end with counsel, CISO, CFO, and Public Affairs.
- Show the CISA Portal submission-health monitor: when was the last successful test submission, and what is the alert path if the portal fails?
- Produce the quarterly CIRCIA compliance attestation signed by the CISO and General Counsel for the last four quarters.
- Show me the forensic-imaging pipeline: chain-of-custody, image hashes, time-stamped immutable storage, and the dual-control authorisation for image release.
- Produce the annual SLA / KPI review for CIRCIA reporting: median time-to-submit, percent submitted within SLA, RFI response time, supplemental volume.
- Show me the liability-protection coversheet for the last three submissions: who reviewed it, who signed it, and is the 6 U.S.C. § 681e citation present?
- Produce the records-preservation quality check: hash integrity, RFC 3161 timestamp validation, and storage-immutability attestation.

## 13. Machine-readable twin

The machine-readable companion of this pack lives at [`api/v1/evidence-packs/circia.json`](../../api/v1/evidence-packs/circia.json). It contains the same clause-level coverage, retention guidance, role matrix, and gap list in JSON form, and is regenerated in lockstep with this markdown pack so content stays in sync. Consumers integrating the pack into GRC tools, audit-request portals, or evidence pipelines should consume the JSON document; human readers should consume this markdown.

Related API surfaces (all under [`api/v1/`](../../api/README.md)):

- [`api/v1/compliance/regulations/circia.json`](../../api/v1/compliance/regulations/circia.json) — regulation metadata and per-version coverage metrics
- [`api/v1/compliance/ucs/`](../../api/v1/compliance/ucs/index.json) — individual UC sidecars
- [`api/v1/compliance/coverage.json`](../../api/v1/compliance/coverage.json) — global coverage snapshot
- [`api/v1/compliance/gaps.json`](../../api/v1/compliance/gaps.json) — global gap report

## 14. Provenance and regeneration

This pack is **generated**, not hand-authored. Re-running the generator produces byte-identical output (deterministic sort, stable serialisation, no free-form timestamps outside the block below). CI enforces regeneration drift via `--check` mode.

**Inputs to this pack**

- [`data/regulations.json`](../../data/regulations.json) — commonClauses, priority weights, authoritative URLs
- [`data/evidence-pack-extras.json`](../../data/evidence-pack-extras.json) — retention, roles, authoritative guidance, penalty, testing approach
- [`content/cat-*/UC-*.json`](../../content) — UC sidecars containing compliance[] entries, controlFamily, owner, evidence fields
- [`api/v1/compliance/regulations/circia@*.json`](../../api/v1/compliance/regulations/) — pre-computed coverage metrics (when present)

- Generator: [`scripts/generate_evidence_packs.py`](../../scripts/generate_evidence_packs.py)
- Evidence-pack directory index: [`docs/evidence-packs/README.md`](README.md)

**Generation metadata**

```
catalogue_version: 8.6.4
generator_script:  scripts/generate_evidence_packs.py
inputs_sha256:     d010119379cfbb44fc0feadaf5ee44b9873461a6d4bc9e2c30e797bebfe9eced
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

<a id="ref-1"></a>**[1]** Amazon Web Services, Inc. (2026). *Amazon GuardDuty User Guide*. Retrieved May 11, 2026, from https://docs.aws.amazon.com/guardduty/latest/ug/what-is-guardduty.html

<a id="ref-2"></a>**[2]** Amazon Web Services, Inc. (2026). *AWS CloudTrail User Guide*. Retrieved May 11, 2026, from https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-user-guide.html

<a id="ref-3"></a>**[3]** Cisco Systems, Inc. (2026). *Cisco Cyber Vision Documentation*. Retrieved May 11, 2026, from https://www.cisco.com/c/en/us/support/security/cyber-vision/series.html

<a id="ref-4"></a>**[4]** CrowdStrike Holdings, Inc. (2026). *CrowdStrike Falcon Documentation*. CrowdStrike. Retrieved May 11, 2026, from https://falcon.crowdstrike.com/documentation

<a id="ref-5"></a>**[5]** Cybersecurity and Infrastructure Security Agency. (2026). *CISA Known Exploited Vulnerabilities Catalog*. U.S. Department of Homeland Security. Retrieved May 11, 2026, from https://www.cisa.gov/known-exploited-vulnerabilities-catalog

<a id="ref-6"></a>**[6]** European Parliament and Council of the European Union. (2016, April). *Regulation (EU) 2016/679 — General Data Protection Regulation*. Official Journal of the European Union, L 119. ELI: reg/2016/679. https://eur-lex.europa.eu/eli/reg/2016/679/oj

<a id="ref-7"></a>**[7]** Microsoft Corporation. (2026). *Microsoft Entra ID Documentation*. Retrieved May 11, 2026, from https://learn.microsoft.com/en-us/entra/identity/

<a id="ref-8"></a>**[8]** Splunk Inc. (2026). *Splunk SOAR (Cloud) Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/SOARonprem

<details>
<summary>Additional online sources cited in the document body (37)</summary>

<a id="ref-9"></a>**[9]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia

<a id="ref-10"></a>**[10]** federalregister.gov. *federalregister.gov: Cyber Incident Reporting For Critical Infrastructure Act Circia Reporting Requirements*. Retrieved May 11, 2026, from https://www.federalregister.gov/documents/2024/04/04/2024-06526/cyber-incident-reporting-for-critical-infrastructure-act-circia-reporting-requirements

<a id="ref-11"></a>**[11]** cisa.gov. *CISA: Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/circia

<a id="ref-12"></a>**[12]** cisa.gov. *CISA: Report*. Retrieved May 11, 2026, from https://www.cisa.gov/report

<a id="ref-13"></a>**[13]** obamawhitehouse.archives.gov. *obamawhitehouse.archives.gov: Presidential Policy Directive Critical Infrastructure Security And Resil*. Retrieved May 11, 2026, from https://obamawhitehouse.archives.gov/the-press-office/2013/02/12/presidential-policy-directive-critical-infrastructure-security-and-resil

<a id="ref-14"></a>**[14]** sec.gov. *U.S. SEC: 33 11216.Pdf*. Retrieved May 11, 2026, from https://www.sec.gov/files/rules/final/2023/33-11216.pdf

<a id="ref-15"></a>**[15]** home.treasury.gov. *home.treasury.gov: Ofac Ransomware Advisory.Pdf*. Retrieved May 11, 2026, from https://home.treasury.gov/system/files/126/ofac_ransomware_advisory.pdf

<a id="ref-16"></a>**[16]** fincen.gov. *fincen.gov: Fin Cen%20Ransomware%20Advisory Final 508 .Pdf*. Retrieved May 11, 2026, from https://www.fincen.gov/sites/default/files/advisory/2021-11-08/FinCEN%20Ransomware%20Advisory_FINAL_508_.pdf

<a id="ref-17"></a>**[17]** ic3.gov. *ic3.gov*. Retrieved May 11, 2026, from https://www.ic3.gov/

<a id="ref-18"></a>**[18]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-s2242a

<a id="ref-19"></a>**[19]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-s2242b

<a id="ref-20"></a>**[20]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-s2242c

<a id="ref-21"></a>**[21]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-s2242d

<a id="ref-22"></a>**[22]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-s2242f

<a id="ref-23"></a>**[23]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-s2242g

<a id="ref-24"></a>**[24]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-s2242h

<a id="ref-25"></a>**[25]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-NPRM-covered-entity

<a id="ref-26"></a>**[26]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-NPRM-covered-incident

<a id="ref-27"></a>**[27]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-NPRM-72hr-reporting

<a id="ref-28"></a>**[28]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-NPRM-24hr-ransom

<a id="ref-29"></a>**[29]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-NPRM-report-content

<a id="ref-30"></a>**[30]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-NPRM-third-party-reporting

<a id="ref-31"></a>**[31]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-NPRM-data-preservation

<a id="ref-32"></a>**[32]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-NPRM-supplemental-trigger

<a id="ref-33"></a>**[33]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-NPRM-cisa-agreement

<a id="ref-34"></a>**[34]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-NPRM-recordkeeping-quality

<a id="ref-35"></a>**[35]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-CISA-portal

<a id="ref-36"></a>**[36]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-CISA-interim-reporting

<a id="ref-37"></a>**[37]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-CISA-protected-information

<a id="ref-38"></a>**[38]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-CISA-coordination-with-sector-srma

<a id="ref-39"></a>**[39]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-CISA-incident-classification

<a id="ref-40"></a>**[40]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-CISA-third-party-incident

<a id="ref-41"></a>**[41]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-CISA-ot-incident

<a id="ref-42"></a>**[42]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-CISA-board-fiduciary

<a id="ref-43"></a>**[43]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-CISA-sec-form-8-k

<a id="ref-44"></a>**[44]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-CISA-tabletop

<a id="ref-45"></a>**[45]** cisa.gov. *CISA: Cyber Incident Reporting Critical Infrastructure Act 2022 Circia*. Retrieved May 11, 2026, from https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia#CIRCIA-CISA-records-retention

</details>

<!-- END-AUTOGENERATED-SOURCES -->
