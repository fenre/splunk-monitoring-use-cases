# Evidence Pack — DORA

> **Tier**: Tier 1 &nbsp;·&nbsp; **Jurisdiction**: EU &nbsp;·&nbsp; **Version**: `Regulation (EU) 2022/2554`
>
> **Full name**: EU Digital Operational Resilience Act
> **Authoritative source**: [https://eur-lex.europa.eu/eli/reg/2022/2554/oj](https://eur-lex.europa.eu/eli/reg/2022/2554/oj)
> **Effective from**: 2025-01-17

> This evidence pack is the auditor-facing view of the Splunk monitoring catalogue's coverage of the regulation. Every clause coverage claim is traceable to a specific UC sidecar JSON file (`use-cases/cat-*/uc-*.json`); every retention figure cites its legal basis; every URL resolves to an official regulator or standards-body source. The pack does **not** assert legal conclusions — it tabulates what the catalogue covers, names the authoritative source, and flags gaps. Interpretation stays with counsel.

> **Live views.** [Buyer narrative (`compliance-story.html?reg=dora`)](../../compliance-story.html?reg=dora) · [Auditor clause navigator (`clause-navigator.html#reg=dora`)](../../clause-navigator.html#reg=dora) · [JSON twin (`api/v1/compliance/story/dora.json`)](../../api/v1/compliance/story/dora.json)

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

Digital Operational Resilience Act is the EU regulation (applicable from 17 January 2025) that harmonises ICT risk-management, incident-reporting, resilience testing, and third-party risk-management requirements for the financial sector. Replaces fragmented national ICT oversight regimes (e.g. EBA GL, BAIT/KAIT Germany, Italian Circolare 285). Supported by 9 Level-2 Regulatory Technical Standards (RTS) and Implementing Technical Standards (ITS) developed by the European Supervisory Authorities (ESAs).

## 2. Scope and applicability

Over 20 types of financial entities: credit institutions, investment firms, payment institutions, electronic-money institutions, CSDs, CCPs, trading venues, trade repositories, insurance/reinsurance undertakings, intermediaries, crypto-asset service providers, crowdfunding service providers, ICT third-party service providers designated as critical (CTPPs).

**Territorial scope.** EU financial sector; ICT third-party providers designated as critical are subject to EU oversight regardless of establishment.

## 3. Catalogue coverage at a glance

- **Clauses tracked**: 14
- **Clauses covered by at least one UC**: 14 / 14 (100.0%)
- **Priority-weighted coverage**: 100.0%
- **Contributing UCs**: 52

Coverage methodology is documented in [`docs/coverage-methodology.md`](../coverage-methodology.md). Priority weights come from `data/regulations.json` commonClauses entries (see [`data/regulations.json`](../../data/regulations.json) priorityWeightRubric).

## 4. Clause-by-clause coverage

Clauses are listed in the order defined by `data/regulations.json commonClauses` for this regulation version. A clause is considered covered when at least one UC sidecar has a `compliance[]` entry matching `(regulation, version, clause)`. Assurance is the maximum across contributing UCs.

| Clause | Topic | Priority | Assurance | UCs |
|---|---|---|---|---|
| [`Art.5`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.5) | ICT risk-management governance | 1.0 | `contributing` | [UC-22.3.1](#uc-22-3-1), [UC-22.3.19](#uc-22-3-19), [UC-22.3.21](#uc-22-3-21), [UC-22.3.22](#uc-22-3-22), [UC-22.3.24](#uc-22-3-24), [UC-22.3.26](#uc-22-3-26) (+2 more) |
| [`Art.6`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.6) | ICT risk-management framework | 1.0 | `full` | [UC-22.11.106](#uc-22-11-106), [UC-22.3.1](#uc-22-3-1), [UC-22.3.41](#uc-22-3-41), [UC-22.6.46](#uc-22-6-46) |
| [`Art.7`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.7) | ICT systems, protocols and tools | 1.0 | `full` | [UC-22.3.1](#uc-22-3-1), [UC-22.3.42](#uc-22-3-42), [UC-22.8.32](#uc-22-8-32) |
| [`Art.8`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.8) | Identification | 1.0 | `full` | [UC-22.11.103](#uc-22-11-103), [UC-22.3.1](#uc-22-3-1), [UC-22.3.43](#uc-22-3-43) |
| [`Art.9`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.9) | Protection and prevention | 1.0 | `partial` | [UC-22.11.97](#uc-22-11-97), [UC-22.3.1](#uc-22-3-1), [UC-22.41.3](#uc-22-41-3) |
| [`Art.10`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.10) | Detection | 1.0 | `partial` | [UC-22.3.1](#uc-22-3-1), [UC-22.3.7](#uc-22-3-7), [UC-22.8.33](#uc-22-8-33) |
| [`Art.11`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.11) | Response and recovery | 1.0 | `contributing` | [UC-22.3.1](#uc-22-3-1), [UC-22.3.5](#uc-22-3-5), [UC-22.3.8](#uc-22-3-8) |
| [`Art.12`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.12) | Backup policies and recovery methods | 1.0 | `full` | [UC-22.3.1](#uc-22-3-1), [UC-22.3.5](#uc-22-3-5), [UC-22.3.9](#uc-22-3-9), [UC-22.35.3](#uc-22-35-3), [UC-22.45.1](#uc-22-45-1), [UC-22.45.3](#uc-22-45-3) |
| [`Art.17`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.17) | ICT-related incident management process | 1.0 | `full` | [UC-22.3.2](#uc-22-3-2), [UC-22.3.23](#uc-22-3-23), [UC-22.3.31](#uc-22-3-31), [UC-22.3.44](#uc-22-3-44), [UC-22.6.51](#uc-22-6-51), [UC-22.6.52](#uc-22-6-52) (+2 more) |
| [`Art.18`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.18) | Classification of ICT-related incidents | 1.0 | `contributing` | [UC-22.3.11](#uc-22-3-11), [UC-22.3.2](#uc-22-3-2) |
| [`Art.19`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.19) | Reporting of major ICT-related incidents | 1.0 | `full` | [UC-22.3.12](#uc-22-3-12), [UC-22.3.2](#uc-22-3-2), [UC-22.3.38](#uc-22-3-38), [UC-22.39.1](#uc-22-39-1) |
| [`Art.24`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.24) | Digital operational-resilience testing | 0.7 | `full` | [UC-22.11.105](#uc-22-11-105), [UC-22.3.25](#uc-22-3-25), [UC-22.3.27](#uc-22-3-27), [UC-22.3.28](#uc-22-3-28), [UC-22.3.3](#uc-22-3-3), [UC-22.3.39](#uc-22-3-39) (+1 more) |
| [`Art.26`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.26) | Threat-led penetration testing | 0.7 | `contributing` | [UC-22.3.17](#uc-22-3-17), [UC-22.3.3](#uc-22-3-3) |
| [`Art.28`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.28) | ICT third-party risk | 1.0 | `full` | [UC-22.3.4](#uc-22-3-4), [UC-22.3.40](#uc-22-3-40), [UC-22.38.3](#uc-22-38-3), [UC-22.44.1](#uc-22-44-1), [UC-22.44.2](#uc-22-44-2), [UC-22.44.3](#uc-22-44-3) (+1 more) |

### 4.1 Contributing UC detail

<a id='uc-22-11-103'></a>
- **UC-22.11.103** —
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
<a id='uc-22-11-97'></a>
- **UC-22.11.97** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-1'></a>
- **UC-22.3.1** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-11'></a>
- **UC-22.3.11** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-12'></a>
- **UC-22.3.12** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-17'></a>
- **UC-22.3.17** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-19'></a>
- **UC-22.3.19** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-2'></a>
- **UC-22.3.2** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-21'></a>
- **UC-22.3.21** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-22'></a>
- **UC-22.3.22** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-23'></a>
- **UC-22.3.23** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-24'></a>
- **UC-22.3.24** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-25'></a>
- **UC-22.3.25** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-26'></a>
- **UC-22.3.26** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-27'></a>
- **UC-22.3.27** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-28'></a>
- **UC-22.3.28** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-29'></a>
- **UC-22.3.29** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-3'></a>
- **UC-22.3.3** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-30'></a>
- **UC-22.3.30** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-31'></a>
- **UC-22.3.31** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-38'></a>
- **UC-22.3.38** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-39'></a>
- **UC-22.3.39** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-4'></a>
- **UC-22.3.4** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-40'></a>
- **UC-22.3.40** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-41'></a>
- **UC-22.3.41** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-42'></a>
- **UC-22.3.42** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-43'></a>
- **UC-22.3.43** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-44'></a>
- **UC-22.3.44** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-45'></a>
- **UC-22.3.45** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-5'></a>
- **UC-22.3.5** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-7'></a>
- **UC-22.3.7** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-8'></a>
- **UC-22.3.8** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-3-9'></a>
- **UC-22.3.9** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-35-3'></a>
- **UC-22.35.3** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-38-3'></a>
- **UC-22.38.3** —
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
<a id='uc-22-41-3'></a>
- **UC-22.41.3** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-44-1'></a>
- **UC-22.44.1** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-44-2'></a>
- **UC-22.44.2** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-44-3'></a>
- **UC-22.44.3** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-45-1'></a>
- **UC-22.45.1** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-45-3'></a>
- **UC-22.45.3** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-6-46'></a>
- **UC-22.6.46** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-6-51'></a>
- **UC-22.6.51** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-6-52'></a>
- **UC-22.6.52** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-32'></a>
- **UC-22.8.32** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-33'></a>
- **UC-22.8.33** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-34'></a>
- **UC-22.8.34** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-35'></a>
- **UC-22.8.35** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-37'></a>
- **UC-22.8.37** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)

## 5. Evidence collection

### 5.1 Common evidence sources

Auditors typically request the following records when examining this regulation:

- ICT risk-management framework and policies
- Incident-management system (tickets with severity, classification per RTS 2024/1772, timelines)
- ICT asset inventory with function-criticality rating
- Third-party register / contract database (Art.28)
- Resilience-testing records (vulnerability scans, red-team exercises, DR drills)
- TLPT reports (for entities above thresholds)
- Cryptographic-controls evidence
- Business-continuity and crisis-management test records
- ICT Risk Officer / Internal Audit reports to management body

### 5.2 Retention requirements

| Artifact | Retention | Legal basis |
|---|---|---|
| ICT risk-management framework documentation (Art.6) | Duration of operation + 5 years | DORA Art.6; Commission Delegated Regulation (EU) 2024/1774 |
| ICT incident-notification records (Art.19) | 5 years post-incident | DORA Art.19(9); Commission Delegated Regulation (EU) 2024/1772 |
| TLPT (Threat-Led Penetration Testing) records (Art.26) | 5 years | DORA Art.26; Commission Delegated Regulation (EU) 2025/302 |
| ICT third-party register (Art.28) | 5 years post-termination of relationship | DORA Art.28; Commission Implementing Regulation (EU) 2024/2956 |
| Operational-resilience testing records (Art.24) | 5 years | DORA Art.24(5) |
| Information-sharing arrangements (Art.45) | Duration of arrangement + 5 years | DORA Art.45 |

> Retention figures above are the legal minimums or regulator-stated expectations. Organisation-specific retention schedules may be longer where business, tax, litigation-hold, or contractual obligations apply. Where a figure conflicts with local data-protection law (e.g. GDPR Art.5(1)(e) storage-limitation principle), the shorter conformant period governs for personal-data content; the evidence-of-compliance retention retains the longer period for audit purposes, scrubbed of excess personal data.

### 5.3 Evidence integrity expectations

Regulators increasingly cite **evidence-integrity failures** as aggravating factors in enforcement actions. Cross-regulation baseline expectations:

- Time-stamped, tamper-evident storage (WORM, cryptographic chaining, or append-only indexes).
- Chain-of-custody for any evidence removed from the SIEM / production system for audit or legal purposes.
- Synchronised clocks (NTP stratum ≤ 3 or equivalent) across all in-scope sources so timeline reconstruction is defensible.
- Documented retention enforcement — not just retention policy — so that deletion is auditable.

See cat-22.35 "Evidence continuity and log integrity" for UCs that implement these controls.

## 6. Control testing procedures

Supervisory-testing and independent-audit model. National competent authorities conduct on-site inspections and document-based supervision. Third-party reliance is tested via the third-party register and contractual clauses (Art.30). TLPT is a specific substantive test applied to larger entities (thresholds in RTS 2025/302) using red-team exercises with threat intelligence and lead-overseer notification. External auditors are expected to attest to the ICT risk-management framework as part of the annual supervisory review.

**Reporting cadence.** Incident notifications on 24h / 72h / 1-month cadence. Annual cybersecurity-risk-management reports to competent authority. TLPT every 3 years for entities meeting thresholds. Third-party register updated at contract inception / material change / at least annually.

## 7. Roles and responsibilities

| Role | Responsibility |
|---|---|
| **Management Body (Board / Executive Committee)** | Art.5: ultimate accountability for digital operational resilience; approves ICT risk-management framework; receives periodic reports. |
| **ICT Risk-Management Function (first line)** | Operates the ICT risk-management framework and controls. |
| **Control Function (second line, e.g. ICT Risk Officer)** | Independent monitoring of ICT risk-management. |
| **Internal Audit (third line)** | Independent audit of ICT risk-management; reports directly to management body. |
| **Competent Authority (CA)** | National regulator (e.g. ECB, ACPR, BaFin, Consob); receives incident reports and supervises compliance. |
| **European Supervisory Authorities (ESAs: EBA, EIOPA, ESMA)** | Jointly develop Level-2 standards; coordinate oversight of critical ICT third-party providers (CTPPs). |
| **Lead Overseer (for CTPPs)** | One of the ESAs designated per CTPP; conducts oversight and issues recommendations to the CTPP. |

## 8. Authoritative guidance

- **Regulation (EU) 2022/2554 (DORA)** — EU Council + Parliament — [https://eur-lex.europa.eu/eli/reg/2022/2554/oj](https://eur-lex.europa.eu/eli/reg/2022/2554/oj)
- **DORA Level-2 Regulatory Technical Standards (RTS) and ITS** — ESAs (ESMA/EBA/EIOPA) — [https://www.esma.europa.eu/rules/dora](https://www.esma.europa.eu/rules/dora)
- **Commission Delegated Regulation (EU) 2024/1774 on ICT risk management** — European Commission — [https://eur-lex.europa.eu/eli/reg_del/2024/1774/oj](https://eur-lex.europa.eu/eli/reg_del/2024/1774/oj)
- **Commission Delegated Regulation (EU) 2024/1772 on ICT incident classification and reporting** — European Commission — [https://eur-lex.europa.eu/eli/reg_del/2024/1772/oj](https://eur-lex.europa.eu/eli/reg_del/2024/1772/oj)
- **Commission Delegated Regulation (EU) 2025/302 on TLPT** — European Commission — [https://eur-lex.europa.eu/eli/reg_del/2025/302/oj](https://eur-lex.europa.eu/eli/reg_del/2025/302/oj)

## 9. Common audit deficiencies

Findings frequently cited by regulators, certification bodies, and external auditors for this regulation. These should be pre-tested as part of readiness reviews.

- ICT risk-management framework is not reviewed at least annually by the management body (Art.5(2)).
- Third-party register is incomplete; sub-contractors supporting critical/important functions are not captured.
- Incident-classification does not align with RTS 2024/1772 criteria (severity, transactions affected, data lost).
- TLPT test scope is not aligned with critical/important functions; findings are closed at technical level without management-body awareness.
- Concentration-risk analysis (Art.29) focuses on cloud providers only and ignores software/framework dependencies.
- Incident notification to the CA misses the 24h early-warning window; staff treat the 72h incident-notification as the primary deadline.

## 10. Enforcement and penalties

Administrative sanctions per Art.50: up to 2 % of total annual worldwide turnover for legal persons (upper threshold). Corrective measures: binding instructions, orders to take specific measures, suspension of activities, operational restrictions (Art.52). Personal sanctions on management: periodic penalty payments up to 1 % of daily average worldwide turnover (Art.50). Criminal penalties under member-state laws. CTPP-level oversight under Art.35 enables ESAs to impose periodic penalty payments up to 1 % of average daily worldwide turnover.

## 11. Pack gaps and remediation backlog

All clauses tracked in `data/regulations.json` for this regulation version are covered by at least one UC. **100 % common-clause coverage**. Remaining work is assurance-upgrade (for example, moving `contributing` entries to `partial` or `full` via explicit control tests) rather than new clause authoring.

## 12. Questions an auditor should ask

These are the questions a regulator, certification body, or external auditor is likely to ask. The pack helps preparers stage evidence and pre-test responses before the review opens.

- Produce the ICT risk-management framework per Art.6; demonstrate approval by the management body (Art.5).
- Show the ICT third-party register per Art.28(3); how is each contract categorised (critical vs non-critical)? When was the last review?
- For the last 12 months, produce every major ICT-related incident report (Art.19); demonstrate the 24h / 72h / 1-month timeline (RTS 2024/1772).
- Produce the digital operational resilience testing programme per Art.24; show test results and corrective-action tracking.
- For entities subject to TLPT (Art.26), demonstrate the last test (every 3 years), threat-intelligence input, remediation tracking, and lead-overseer notification.
- For ICT concentration risk per Art.29, produce the analysis of single-provider dependencies for critical/important functions.
- Demonstrate the information-sharing arrangements per Art.45 — participation in sectoral ISACs or ESAs-coordinated exercises.
- For CTPPs under EU-level oversight (Art.31), produce the annual oversight-plan input and compliance with designated Lead Overseer instructions.

## 13. Machine-readable twin

The machine-readable companion of this pack lives at [`api/v1/evidence-packs/dora.json`](../../api/v1/evidence-packs/dora.json). It contains the same clause-level coverage, retention guidance, role matrix, and gap list in JSON form, and is regenerated in lockstep with this markdown pack so content stays in sync. Consumers integrating the pack into GRC tools, audit-request portals, or evidence pipelines should consume the JSON document; human readers should consume this markdown.

Related API surfaces (all under [`api/v1/`](../../api/README.md)):

- [`api/v1/compliance/regulations/dora.json`](../../api/v1/compliance/regulations/dora.json) — regulation metadata and per-version coverage metrics
- [`api/v1/compliance/ucs/`](../../api/v1/compliance/ucs/index.json) — individual UC sidecars
- [`api/v1/compliance/coverage.json`](../../api/v1/compliance/coverage.json) — global coverage snapshot
- [`api/v1/compliance/gaps.json`](../../api/v1/compliance/gaps.json) — global gap report

## 14. Provenance and regeneration

This pack is **generated**, not hand-authored. Re-running the generator produces byte-identical output (deterministic sort, stable serialisation, no free-form timestamps outside the block below). CI enforces regeneration drift via `--check` mode.

**Inputs to this pack**

- [`data/regulations.json`](../../data/regulations.json) — commonClauses, priority weights, authoritative URLs
- [`data/evidence-pack-extras.json`](../../data/evidence-pack-extras.json) — retention, roles, authoritative guidance, penalty, testing approach
- [`use-cases/cat-*/uc-*.json`](../../use-cases) — UC sidecars containing compliance[] entries, controlFamily, owner, evidence fields
- [`api/v1/compliance/regulations/dora@*.json`](../../api/v1/compliance/regulations/) — pre-computed coverage metrics (when present)

- Generator: [`scripts/generate_evidence_packs.py`](../../scripts/generate_evidence_packs.py)
- Evidence-pack directory index: [`docs/evidence-packs/README.md`](README.md)

**Generation metadata**

```
catalogue_version: 7.1
generator_script:  scripts/generate_evidence_packs.py
inputs_sha256:     377470c73dba056ab0cbf2997ee97a0efe523076b02f1b8df1f89082c148fe99
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
