# Evidence Pack — SOC 2

> **Tier**: Tier 1 &nbsp;·&nbsp; **Jurisdiction**: US, GLOBAL &nbsp;·&nbsp; **Version**: `2017 TSC`
>
> **Full name**: SOC 2 Trust Services Criteria
> **Authoritative source**: [https://www.aicpa-cima.com/resources/landing/system-and-organization-controls-soc-suite-of-services](https://www.aicpa-cima.com/resources/landing/system-and-organization-controls-soc-suite-of-services)
> **Effective from**: 2018-12-15

> This evidence pack is the auditor-facing view of the Splunk monitoring catalogue's coverage of the regulation. Every clause coverage claim is traceable to a specific UC sidecar JSON file (`use-cases/cat-*/uc-*.json`); every retention figure cites its legal basis; every URL resolves to an official regulator or standards-body source. The pack does **not** assert legal conclusions — it tabulates what the catalogue covers, names the authoritative source, and flags gaps. Interpretation stays with counsel.

> **Live views.** [Buyer narrative (`compliance-story.html?reg=soc-2`)](../../compliance-story.html?reg=soc-2) · [Auditor clause navigator (`clause-navigator.html#reg=soc-2`)](../../clause-navigator.html#reg=soc-2) · [JSON twin (`api/v1/compliance/story/soc-2.json`)](../../api/v1/compliance/story/soc-2.json)

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

SOC 2 reports attest to a service organisation's controls relevant to security, availability, processing integrity, confidentiality, and privacy, as defined by the AICPA 2017 Trust Services Criteria (TSC). Type 1 reports attest to control design at a point in time; Type 2 reports attest to operating effectiveness over a defined reporting period (3-12 months). SOC 2 is a trust-services engagement under SSAE 18 / AT-C 205, not a regulatory compliance regime.

## 2. Scope and applicability

Any service organisation whose customers rely on the organisation's controls for their own compliance or risk-management purposes. Common scope: SaaS platforms, managed service providers, data centres, payroll processors. Customers often contractually require SOC 2 reports to satisfy their own vendor-risk-management obligations.

**Territorial scope.** Global; issued by any AICPA-member CPA firm under AT-C 205. Reciprocal recognition with CSA STAR, ISAE 3000, and similar assurance frameworks.

## 3. Catalogue coverage at a glance

- **Clauses tracked**: 16
- **Clauses covered by at least one UC**: 16 / 16 (100.0%)
- **Priority-weighted coverage**: 100.0%
- **Contributing UCs**: 56

Coverage methodology is documented in [`docs/coverage-methodology.md`](../coverage-methodology.md). Priority weights come from `data/regulations.json` commonClauses entries (see [`data/regulations.json`](../../data/regulations.json) priorityWeightRubric).

## 4. Clause-by-clause coverage

Clauses are listed in the order defined by `data/regulations.json commonClauses` for this regulation version. A clause is considered covered when at least one UC sidecar has a `compliance[]` entry matching `(regulation, version, clause)`. Assurance is the maximum across contributing UCs.

| Clause | Topic | Priority | Assurance | UCs |
|---|---|---|---|---|
| [`CC1.1`](https://www.aicpa-cima.com/tsc2017#CC1.1) | Integrity and ethical values | 0.7 | `full` | [UC-22.8.36](#uc-22-8-36), [UC-22.8.9](#uc-22-8-9) |
| [`CC2.1`](https://www.aicpa-cima.com/tsc2017#CC2.1) | Internal communication | 0.7 | `contributing` | [UC-22.8.10](#uc-22-8-10), [UC-22.8.11](#uc-22-8-11), [UC-22.8.4](#uc-22-8-4), [UC-22.9.10](#uc-22-9-10) |
| [`CC3.1`](https://www.aicpa-cima.com/tsc2017#CC3.1) | Risk assessment | 1.0 | `partial` | [UC-22.47.2](#uc-22-47-2), [UC-22.8.12](#uc-22-8-12), [UC-22.8.19](#uc-22-8-19), [UC-22.8.23](#uc-22-8-23), [UC-22.9.9](#uc-22-9-9) |
| [`CC5.1`](https://www.aicpa-cima.com/tsc2017#CC5.1) | Control activities | 1.0 | `full` | [UC-22.47.1](#uc-22-47-1), [UC-22.8.15](#uc-22-8-15), [UC-22.9.8](#uc-22-9-8) |
| [`CC6.1`](https://www.aicpa-cima.com/tsc2017#CC6.1) | Logical access controls | 1.0 | `full` | [UC-22.11.96](#uc-22-11-96), [UC-22.40.1](#uc-22-40-1), [UC-22.8.1](#uc-22-8-1), [UC-22.8.16](#uc-22-8-16) |
| [`CC6.6`](https://www.aicpa-cima.com/tsc2017#CC6.6) | Encryption in transit | 1.0 | `full` | [UC-22.11.91](#uc-22-11-91), [UC-22.8.18](#uc-22-8-18), [UC-22.8.31](#uc-22-8-31) |
| [`CC6.7`](https://www.aicpa-cima.com/tsc2017#CC6.7) | System boundaries and data transmission | 1.0 | `full` | [UC-22.8.32](#uc-22-8-32) |
| [`CC7.1`](https://www.aicpa-cima.com/tsc2017#CC7.1) | System operations monitoring | 1.0 | `full` | [UC-22.11.101](#uc-22-11-101), [UC-22.11.104](#uc-22-11-104), [UC-22.12.40](#uc-22-12-40), [UC-22.6.49](#uc-22-6-49), [UC-22.8.1](#uc-22-8-1), [UC-22.8.33](#uc-22-8-33) |
| [`CC7.2`](https://www.aicpa-cima.com/tsc2017#CC7.2) | System monitoring for anomalies | 1.0 | `partial` | [UC-22.11.99](#uc-22-11-99), [UC-22.35.2](#uc-22-35-2), [UC-22.8.13](#uc-22-8-13), [UC-22.8.14](#uc-22-8-14), [UC-22.8.17](#uc-22-8-17), [UC-22.8.20](#uc-22-8-20) (+2 more) |
| [`CC7.3`](https://www.aicpa-cima.com/tsc2017#CC7.3) | Evaluated events and incidents | 1.0 | `full` | [UC-22.6.52](#uc-22-6-52), [UC-22.8.34](#uc-22-8-34) |
| [`CC7.4`](https://www.aicpa-cima.com/tsc2017#CC7.4) | Incident response | 1.0 | `full` | [UC-22.11.105](#uc-22-11-105), [UC-22.8.35](#uc-22-8-35) |
| [`CC8.1`](https://www.aicpa-cima.com/tsc2017#CC8.1) | Change management | 1.0 | `full` | [UC-22.11.92](#uc-22-11-92), [UC-22.11.95](#uc-22-11-95), [UC-22.12.38](#uc-22-12-38), [UC-22.12.39](#uc-22-12-39), [UC-22.42.1](#uc-22-42-1), [UC-22.6.55](#uc-22-6-55) (+2 more) |
| [`CC9.1`](https://www.aicpa-cima.com/tsc2017#CC9.1) | Risk mitigation activities | 0.7 | `full` | [UC-22.8.37](#uc-22-8-37) |
| [`A1.2`](https://www.aicpa-cima.com/tsc2017#A1.2) | Availability commitments | 0.7 | `full` | [UC-22.35.3](#uc-22-35-3), [UC-22.45.1](#uc-22-45-1), [UC-22.8.22](#uc-22-8-22), [UC-22.8.27](#uc-22-8-27), [UC-22.8.28](#uc-22-8-28) |
| [`C1.1`](https://www.aicpa-cima.com/tsc2017#C1.1) | Confidentiality | 0.7 | `full` | [UC-22.11.93](#uc-22-11-93), [UC-22.8.29](#uc-22-8-29), [UC-22.8.38](#uc-22-8-38) |
| [`P1.1`](https://www.aicpa-cima.com/tsc2017#P1.1) | Privacy notice | 0.4 | `full` | [UC-22.8.39](#uc-22-8-39) |

### 4.1 Contributing UC detail

<a id='uc-22-11-101'></a>
- **UC-22.11.101** —
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
<a id='uc-22-11-99'></a>
- **UC-22.11.99** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-12-38'></a>
- **UC-22.12.38** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-12-39'></a>
- **UC-22.12.39** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-12-40'></a>
- **UC-22.12.40** —
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
<a id='uc-22-35-3'></a>
- **UC-22.35.3** —
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
<a id='uc-22-42-1'></a>
- **UC-22.42.1** —
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
<a id='uc-22-47-1'></a>
- **UC-22.47.1** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-47-2'></a>
- **UC-22.47.2** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-6-49'></a>
- **UC-22.6.49** —
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
<a id='uc-22-6-55'></a>
- **UC-22.6.55** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-1'></a>
- **UC-22.8.1** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-10'></a>
- **UC-22.8.10** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-11'></a>
- **UC-22.8.11** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-12'></a>
- **UC-22.8.12** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-13'></a>
- **UC-22.8.13** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-14'></a>
- **UC-22.8.14** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-15'></a>
- **UC-22.8.15** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-16'></a>
- **UC-22.8.16** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-17'></a>
- **UC-22.8.17** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-18'></a>
- **UC-22.8.18** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-19'></a>
- **UC-22.8.19** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-20'></a>
- **UC-22.8.20** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-21'></a>
- **UC-22.8.21** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-22'></a>
- **UC-22.8.22** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-23'></a>
- **UC-22.8.23** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-24'></a>
- **UC-22.8.24** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-25'></a>
- **UC-22.8.25** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-27'></a>
- **UC-22.8.27** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-28'></a>
- **UC-22.8.28** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-29'></a>
- **UC-22.8.29** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-31'></a>
- **UC-22.8.31** —
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
<a id='uc-22-8-36'></a>
- **UC-22.8.36** —
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
<a id='uc-22-8-38'></a>
- **UC-22.8.38** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-39'></a>
- **UC-22.8.39** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-4'></a>
- **UC-22.8.4** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-8-9'></a>
- **UC-22.8.9** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-9-10'></a>
- **UC-22.9.10** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-9-8'></a>
- **UC-22.9.8** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-9-9'></a>
- **UC-22.9.9** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)

## 5. Evidence collection

### 5.1 Common evidence sources

Auditors typically request the following records when examining this regulation:

- Change-management / ticketing logs (ServiceNow, Jira, Shortcut)
- Access-management logs (IAM, directory services, HRIS for joiner/mover/leaver)
- Vulnerability-management records
- Configuration-management records (infrastructure-as-code, CI/CD)
- Security-monitoring logs (SIEM, EDR, CSPM)
- Incident-management logs with severity and timeline
- Backup and recovery test records
- Vendor-management and subservice-organisation monitoring records

### 5.2 Retention requirements

| Artifact | Retention | Legal basis |
|---|---|---|
| SOC 2 reports (historical) | Typically 3-5 years (user-entity and regulator request cycle) | AICPA SSAE 18 assurance-engagement record retention; service-organisation contractual obligations |
| Control-test evidence (auditor work papers) | 5-7 years | AT-C 205.91; AICPA quality-control standards |
| Incident logs (for Availability TSC) | Duration of report period + 5 years | AICPA guidance |
| Access-review evidence | Duration of report period + 5 years | AICPA guidance |
| Vendor/subservice-organisation SOC reports | Duration of reliance + 3 years | AT-C 205.A103 carve-out considerations |

> Retention figures above are the legal minimums or regulator-stated expectations. Organisation-specific retention schedules may be longer where business, tax, litigation-hold, or contractual obligations apply. Where a figure conflicts with local data-protection law (e.g. GDPR Art.5(1)(e) storage-limitation principle), the shorter conformant period governs for personal-data content; the evidence-of-compliance retention retains the longer period for audit purposes, scrubbed of excess personal data.

### 5.3 Evidence integrity expectations

Regulators increasingly cite **evidence-integrity failures** as aggravating factors in enforcement actions. Cross-regulation baseline expectations:

- Time-stamped, tamper-evident storage (WORM, cryptographic chaining, or append-only indexes).
- Chain-of-custody for any evidence removed from the SIEM / production system for audit or legal purposes.
- Synchronised clocks (NTP stratum ≤ 3 or equivalent) across all in-scope sources so timeline reconstruction is defensible.
- Documented retention enforcement — not just retention policy — so that deletion is auditable.

See cat-22.35 "Evidence continuity and log integrity" for UCs that implement these controls.

## 6. Control testing procedures

Auditors test each Common Criteria (CC1-CC9) and any additional categories elected in scope. Type 1 tests only design; Type 2 tests design AND operating effectiveness across the reporting period. Auditors employ inquiry, observation, inspection, and re-performance. Sampling is statistical or judgmental depending on population size and criticality. The report's Section III (system description) must align with Sections IV (control activities) and V (tests of controls).

**Reporting cadence.** Type 2 typically annual (12-month reporting period) with 3-6 month bridge letters permitted for gaps. Type 1 is a point-in-time snapshot, often used for a first-year engagement before Type 2 is feasible.

## 7. Roles and responsibilities

| Role | Responsibility |
|---|---|
| **Service Organisation Management** | Writes the management assertion; owns control design and operation. |
| **SOC 2 Engagement Partner (CPA)** | Signs the SOC 2 report; responsible for the quality of the assurance engagement. |
| **User Entity** | Relies on the SOC 2 report for its own compliance/risk-management; must implement Complementary User-Entity Controls (CUECs) listed in the report. |
| **Subservice Organisation** | Provides services to the service organisation that could affect the user entity's internal controls. Carve-out or inclusive method. |
| **AICPA** | Maintains SSAE 18 attestation standards and Trust Services Criteria. |

## 8. Authoritative guidance

- **AICPA Trust Services Criteria (TSC) 2017** — AICPA — [https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022](https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022)
- **AICPA SOC 2 Description Criteria** — AICPA — [https://www.aicpa-cima.com/topic/audit-assurance/audit-and-assurance-greater-than-soc-2](https://www.aicpa-cima.com/topic/audit-assurance/audit-and-assurance-greater-than-soc-2)
- **AT-C Section 205 Assertion-Based Examination Engagements** — AICPA — [https://us.aicpa.org/research/standards/auditattest/ssae](https://us.aicpa.org/research/standards/auditattest/ssae)
- **SOC 2 Reporting on Controls at a Service Organization (AICPA Guide)** — AICPA — [https://www.aicpa-cima.com/cpe-learning/publication/soc-2-reporting-on-controls-at-a-service-organization](https://www.aicpa-cima.com/cpe-learning/publication/soc-2-reporting-on-controls-at-a-service-organization)

## 9. Common audit deficiencies

Findings frequently cited by regulators, certification bodies, and external auditors for this regulation. These should be pre-tested as part of readiness reviews.

- Report period ends but samples were drawn only from the last month; population coverage is not uniform.
- CUECs are listed but the service organisation does not describe how it confirms user entities are implementing them.
- Exceptions to control operation are accepted as non-material without quantitative or qualitative evidence.
- Subservice-organisation SOC reports are not current or have qualifications that affect the in-scope carve-out.
- Management assertion is silent on whether the description faithfully represents the system in operation.
- New cloud services (IaaS/PaaS) are added to the environment but not added to the SOC 2 scope until the following year.

## 10. Enforcement and penalties

SOC 2 has no statutory penalty structure; enforcement is commercial. A qualified opinion, adverse opinion, or disclaimer of opinion typically causes customer contract cancellations, deal-loss, and vendor-risk-management downgrades. AICPA can sanction the CPA firm that issues a deficient report; the service organisation bears no direct regulatory penalty.

## 11. Pack gaps and remediation backlog

All clauses tracked in `data/regulations.json` for this regulation version are covered by at least one UC. **100 % common-clause coverage**. Remaining work is assurance-upgrade (for example, moving `contributing` entries to `partial` or `full` via explicit control tests) rather than new clause authoring.

## 12. Questions an auditor should ask

These are the questions a regulator, certification body, or external auditor is likely to ask. The pack helps preparers stage evidence and pre-test responses before the review opens.

- Produce the most recent SOC 2 Type 2 report and describe how the scope aligns with in-scope services and locations.
- For each Common Criteria (CC) control tested, produce the population and the sample selection; demonstrate independence of selection.
- Show evidence of control activities operating throughout the reporting period, not just at report-cut-off.
- For every exception noted in the Type 2 report, describe the root cause, the remediation timeline, and evidence of completion.
- Produce the management assertion for the reporting period and the supporting artefacts (policies, risk-assessment, inventory).
- Demonstrate how the Criteria Related to Additional Categories (Availability, Processing Integrity, Confidentiality, Privacy) were scoped.
- Show the Complementary Subservice-Organisation Controls (CSOCs) mapping if any subservice organisations are carved out.

## 13. Machine-readable twin

The machine-readable companion of this pack lives at [`api/v1/evidence-packs/soc-2.json`](../../api/v1/evidence-packs/soc-2.json). It contains the same clause-level coverage, retention guidance, role matrix, and gap list in JSON form, and is regenerated in lockstep with this markdown pack so content stays in sync. Consumers integrating the pack into GRC tools, audit-request portals, or evidence pipelines should consume the JSON document; human readers should consume this markdown.

Related API surfaces (all under [`api/v1/`](../../api/README.md)):

- [`api/v1/compliance/regulations/soc-2.json`](../../api/v1/compliance/regulations/soc-2.json) — regulation metadata and per-version coverage metrics
- [`api/v1/compliance/ucs/`](../../api/v1/compliance/ucs/index.json) — individual UC sidecars
- [`api/v1/compliance/coverage.json`](../../api/v1/compliance/coverage.json) — global coverage snapshot
- [`api/v1/compliance/gaps.json`](../../api/v1/compliance/gaps.json) — global gap report

## 14. Provenance and regeneration

This pack is **generated**, not hand-authored. Re-running the generator produces byte-identical output (deterministic sort, stable serialisation, no free-form timestamps outside the block below). CI enforces regeneration drift via `--check` mode.

**Inputs to this pack**

- [`data/regulations.json`](../../data/regulations.json) — commonClauses, priority weights, authoritative URLs
- [`data/evidence-pack-extras.json`](../../data/evidence-pack-extras.json) — retention, roles, authoritative guidance, penalty, testing approach
- [`use-cases/cat-*/uc-*.json`](../../use-cases) — UC sidecars containing compliance[] entries, controlFamily, owner, evidence fields
- [`api/v1/compliance/regulations/soc-2@*.json`](../../api/v1/compliance/regulations/) — pre-computed coverage metrics (when present)

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
