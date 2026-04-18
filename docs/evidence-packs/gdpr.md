# Evidence Pack — GDPR

> **Tier**: Tier 1 &nbsp;·&nbsp; **Jurisdiction**: EU, EEA &nbsp;·&nbsp; **Version**: `2016/679`
>
> **Full name**: General Data Protection Regulation
> **Authoritative source**: [https://eur-lex.europa.eu/eli/reg/2016/679/oj](https://eur-lex.europa.eu/eli/reg/2016/679/oj)
> **Effective from**: 2018-05-25

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

Regulation (EU) 2016/679 is the comprehensive EU framework for the protection of natural persons with regard to the processing of personal data and on the free movement of such data. It imposes accountability obligations on data controllers and processors, grants enforceable rights to data subjects, and empowers supervisory authorities to impose administrative fines of up to EUR 20 million or 4 % of worldwide annual turnover.

## 2. Scope and applicability

Applies to any organisation processing personal data of individuals located in the European Union or European Economic Area, regardless of where the organisation is established. Processing by households for purely personal activities is excluded; processing by competent authorities for criminal law enforcement is governed by the Law Enforcement Directive 2016/680, not GDPR.

**Territorial scope.** EU/EEA territorial scope plus extraterritorial reach under Art.3(2) for any controller or processor established outside the EU that offers goods/services to EU data subjects or monitors their behaviour within the EU.

## 3. Catalogue coverage at a glance

- **Clauses tracked**: 20
- **Clauses covered by at least one UC**: 20 / 20 (100.0%)
- **Priority-weighted coverage**: 100.0%
- **Contributing UCs**: 37

Coverage methodology is documented in [`docs/coverage-methodology.md`](../coverage-methodology.md). Priority weights come from `data/regulations.json` commonClauses entries (see [`data/regulations.json`](../../data/regulations.json) priorityWeightRubric).

## 4. Clause-by-clause coverage

Clauses are listed in the order defined by `data/regulations.json commonClauses` for this regulation version. A clause is considered covered when at least one UC sidecar has a `compliance[]` entry matching `(regulation, version, clause)`. Assurance is the maximum across contributing UCs.

| Clause | Topic | Priority | Assurance | UCs |
|---|---|---|---|---|
| [`Art.5`](https://eur-lex.europa.eu/eli/reg/2016/679/oj#Art.5) | Principles of processing | 1.0 | `full` | [UC-22.49.1](#uc-22-49-1), [UC-22.49.2](#uc-22-49-2) |
| [`Art.6`](https://eur-lex.europa.eu/eli/reg/2016/679/oj#Art.6) | Lawful basis | 1.0 | `partial` | [UC-22.37.1](#uc-22-37-1) |
| [`Art.7`](https://eur-lex.europa.eu/eli/reg/2016/679/oj#Art.7) | Conditions for consent | 0.7 | `full` | [UC-22.1.46](#uc-22-1-46), [UC-22.1.5](#uc-22-1-5), [UC-22.37.1](#uc-22-37-1), [UC-22.37.2](#uc-22-37-2), [UC-22.8.39](#uc-22-8-39) |
| [`Art.15`](https://eur-lex.europa.eu/eli/reg/2016/679/oj#Art.15) | Right of access | 1.0 | `full` | [UC-22.36.1](#uc-22-36-1) |
| [`Art.16`](https://eur-lex.europa.eu/eli/reg/2016/679/oj#Art.16) | Right to rectification | 0.7 | `partial` | [UC-22.1.2](#uc-22-1-2) |
| [`Art.17`](https://eur-lex.europa.eu/eli/reg/2016/679/oj#Art.17) | Right to erasure | 1.0 | `full` | [UC-22.1.11](#uc-22-1-11), [UC-22.36.2](#uc-22-36-2) |
| [`Art.18`](https://eur-lex.europa.eu/eli/reg/2016/679/oj#Art.18) | Right to restrict processing | 0.7 | `partial` | [UC-22.1.16](#uc-22-1-16) |
| [`Art.20`](https://eur-lex.europa.eu/eli/reg/2016/679/oj#Art.20) | Right to data portability | 0.7 | `full` | [UC-22.36.3](#uc-22-36-3) |
| [`Art.21`](https://eur-lex.europa.eu/eli/reg/2016/679/oj#Art.21) | Right to object | 0.7 | `partial` | [UC-22.1.46](#uc-22-1-46) |
| [`Art.22`](https://eur-lex.europa.eu/eli/reg/2016/679/oj#Art.22) | Automated decision making | 0.7 | `contributing` | [UC-22.1.18](#uc-22-1-18) |
| [`Art.25`](https://eur-lex.europa.eu/eli/reg/2016/679/oj#Art.25) | Data protection by design and by default | 1.0 | `contributing` | [UC-22.1.9](#uc-22-1-9) |
| [`Art.28`](https://eur-lex.europa.eu/eli/reg/2016/679/oj#Art.28) | Processor obligations | 1.0 | `full` | [UC-22.1.15](#uc-22-1-15), [UC-22.44.2](#uc-22-44-2) |
| [`Art.30`](https://eur-lex.europa.eu/eli/reg/2016/679/oj#Art.30) | Records of processing | 1.0 | `contributing` | [UC-22.1.43](#uc-22-1-43), [UC-22.1.8](#uc-22-1-8) |
| [`Art.32`](https://eur-lex.europa.eu/eli/reg/2016/679/oj#Art.32) | Security of processing | 1.0 | `partial` | [UC-22.1.10](#uc-22-1-10), [UC-22.1.41](#uc-22-1-41), [UC-22.1.7](#uc-22-1-7), [UC-22.35.2](#uc-22-35-2), [UC-22.35.3](#uc-22-35-3), [UC-22.41.1](#uc-22-41-1) |
| [`Art.33`](https://eur-lex.europa.eu/eli/reg/2016/679/oj#Art.33) | Breach notification to supervisory authority | 1.0 | `full` | [UC-22.1.29](#uc-22-1-29), [UC-22.1.3](#uc-22-1-3), [UC-22.39.1](#uc-22-39-1), [UC-22.39.2](#uc-22-39-2), [UC-22.9.4](#uc-22-9-4) |
| [`Art.34`](https://eur-lex.europa.eu/eli/reg/2016/679/oj#Art.34) | Breach communication to data subjects | 1.0 | `full` | [UC-22.1.13](#uc-22-1-13), [UC-22.39.3](#uc-22-39-3) |
| [`Art.35`](https://eur-lex.europa.eu/eli/reg/2016/679/oj#Art.35) | DPIA | 0.7 | `contributing` | [UC-22.1.14](#uc-22-1-14) |
| [`Art.44`](https://eur-lex.europa.eu/eli/reg/2016/679/oj#Art.44) | International transfers — general principle | 1.0 | `full` | [UC-22.38.1](#uc-22-38-1), [UC-22.38.3](#uc-22-38-3) |
| [`Art.45`](https://eur-lex.europa.eu/eli/reg/2016/679/oj#Art.45) | Transfers via adequacy decision | 0.7 | `partial` | [UC-22.1.39](#uc-22-1-39), [UC-22.38.2](#uc-22-38-2) |
| [`Art.46`](https://eur-lex.europa.eu/eli/reg/2016/679/oj#Art.46) | Transfers subject to safeguards | 0.7 | `full` | [UC-22.38.1](#uc-22-38-1), [UC-22.38.2](#uc-22-38-2) |

### 4.1 Contributing UC detail

<a id='uc-22-1-10'></a>
- **UC-22.1.10** — GDPR Privileged Access to Personal Data Stores
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.1.10.json`](../../use-cases/cat-22/uc-22.1.10.json)
<a id='uc-22-1-11'></a>
- **UC-22.1.11** — GDPR Right to Erasure Verification
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.1.11.json`](../../use-cases/cat-22/uc-22.1.11.json)
<a id='uc-22-1-13'></a>
- **UC-22.1.13** — GDPR High-Risk Breach Communication to Data Subjects
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.1.13.json`](../../use-cases/cat-22/uc-22.1.13.json)
<a id='uc-22-1-14'></a>
- **UC-22.1.14** — GDPR Data Protection Impact Assessment Coverage
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.1.14.json`](../../use-cases/cat-22/uc-22.1.14.json)
<a id='uc-22-1-15'></a>
- **UC-22.1.15** — GDPR Third-Party Processor Compliance Monitoring
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.1.15.json`](../../use-cases/cat-22/uc-22.1.15.json)
<a id='uc-22-1-16'></a>
- **UC-22.1.16** — GDPR Consent Withdrawal Processing Enforcement
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.1.16.json`](../../use-cases/cat-22/uc-22.1.16.json)
<a id='uc-22-1-18'></a>
- **UC-22.1.18** — GDPR Automated Decision-Making and Profiling Transparency
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.1.18.json`](../../use-cases/cat-22/uc-22.1.18.json)
<a id='uc-22-1-2'></a>
- **UC-22.1.2** — GDPR Data Subject Access Request Fulfillment Tracking
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.1.2.json`](../../use-cases/cat-22/uc-22.1.2.json)
<a id='uc-22-1-29'></a>
- **UC-22.1.29** — GDPR Processor Personal Data Breach Notification SLA
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.1.29.json`](../../use-cases/cat-22/uc-22.1.29.json)
<a id='uc-22-1-3'></a>
- **UC-22.1.3** — GDPR Breach Notification Timeline Monitoring
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.1.3.json`](../../use-cases/cat-22/uc-22.1.3.json)
<a id='uc-22-1-39'></a>
- **UC-22.1.39** — GDPR Adequacy Decision and Legal Basis Change Monitoring
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.1.39.json`](../../use-cases/cat-22/uc-22.1.39.json)
<a id='uc-22-1-41'></a>
- **UC-22.1.41** — GDPR Unauthorized Cloud Service Detection (Shadow SaaS)
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.1.41.json`](../../use-cases/cat-22/uc-22.1.41.json)
<a id='uc-22-1-43'></a>
- **UC-22.1.43** — GDPR Personal Data in Non-Approved Systems (ROPA Drift Detection)
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.1.43.json`](../../use-cases/cat-22/uc-22.1.43.json)
<a id='uc-22-1-46'></a>
- **UC-22.1.46** — GDPR Consent Mechanism Audit (Lawful Basis Alignment)
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.1.46.json`](../../use-cases/cat-22/uc-22.1.46.json)
<a id='uc-22-1-5'></a>
- **UC-22.1.5** — GDPR Consent Management Audit Trail
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.1.5.json`](../../use-cases/cat-22/uc-22.1.5.json)
<a id='uc-22-1-7'></a>
- **UC-22.1.7** — GDPR Security of Processing — Encryption and Pseudonymisation Coverage
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.1.7.json`](../../use-cases/cat-22/uc-22.1.7.json)
<a id='uc-22-1-8'></a>
- **UC-22.1.8** — GDPR Records of Processing Activities Completeness
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.1.8.json`](../../use-cases/cat-22/uc-22.1.8.json)
<a id='uc-22-1-9'></a>
- **UC-22.1.9** — GDPR Data Protection by Design — Data Minimisation Validation
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.1.9.json`](../../use-cases/cat-22/uc-22.1.9.json)
<a id='uc-22-35-2'></a>
- **UC-22.35.2** — Log tamper detection via write-once-read-many chain-of-custody
  - Control family: `evidence-continuity`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.35.2.json`](../../use-cases/cat-22/uc-22.35.2.json)
<a id='uc-22-35-3'></a>
- **UC-22.35.3** — Indexer replication lag exposing evidence to single-point failure
  - Control family: `evidence-continuity`
  - Owner: `Head of Platform`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.35.3.json`](../../use-cases/cat-22/uc-22.35.3.json)
<a id='uc-22-36-1'></a>
- **UC-22.36.1** — DSAR fulfillment SLA tracker with verification evidence trail
  - Control family: `data-subject-request-lifecycle`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.36.1.json`](../../use-cases/cat-22/uc-22.36.1.json)
<a id='uc-22-36-2'></a>
- **UC-22.36.2** — Right-to-erasure propagation completeness across downstream systems
  - Control family: `data-subject-request-lifecycle`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.36.2.json`](../../use-cases/cat-22/uc-22.36.2.json)
<a id='uc-22-36-3'></a>
- **UC-22.36.3** — Portability export integrity — signed manifest verification
  - Control family: `data-subject-request-lifecycle`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.36.3.json`](../../use-cases/cat-22/uc-22.36.3.json)
<a id='uc-22-37-1'></a>
- **UC-22.37.1** — Consent capture evidence freshness — stale-consent alerting
  - Control family: `data-subject-request-lifecycle`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.37.1.json`](../../use-cases/cat-22/uc-22.37.1.json)
<a id='uc-22-37-2'></a>
- **UC-22.37.2** — Consent withdrawal propagation SLA — downstream stop-processing evidence
  - Control family: `data-subject-request-lifecycle`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.37.2.json`](../../use-cases/cat-22/uc-22.37.2.json)
<a id='uc-22-38-1'></a>
- **UC-22.38.1** — Cross-border personal-data flow anomaly — egress to unsanctioned jurisdictions
  - Control family: `data-flow-cross-border`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.38.1.json`](../../use-cases/cat-22/uc-22.38.1.json)
<a id='uc-22-38-2'></a>
- **UC-22.38.2** — SCC / adequacy decision reference freshness — stale-safeguard detector
  - Control family: `data-flow-cross-border`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.38.2.json`](../../use-cases/cat-22/uc-22.38.2.json)
<a id='uc-22-38-3'></a>
- **UC-22.38.3** — Data localization enforcement — regulated-data must-stay-in-region
  - Control family: `data-flow-cross-border`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.38.3.json`](../../use-cases/cat-22/uc-22.38.3.json)
<a id='uc-22-39-1'></a>
- **UC-22.39.1** — Multi-regulator breach-notification SLA tracker (24h NIS2 / 72h GDPR / 72h HIPAA)
  - Control family: `ir-drill-evidence`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.39.1.json`](../../use-cases/cat-22/uc-22.39.1.json)
<a id='uc-22-39-2'></a>
- **UC-22.39.2** — Regulator-portal submission evidence — one-way API acknowledgement audit
  - Control family: `ir-drill-evidence`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.39.2.json`](../../use-cases/cat-22/uc-22.39.2.json)
<a id='uc-22-39-3'></a>
- **UC-22.39.3** — Data-subject breach communication timeline tracker (Art.34 / §164.404)
  - Control family: `ir-drill-evidence`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.39.3.json`](../../use-cases/cat-22/uc-22.39.3.json)
<a id='uc-22-41-1'></a>
- **UC-22.41.1** — Encryption-at-rest coverage gap — unencrypted storage with regulated data
  - Control family: `crypto-drift`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.41.1.json`](../../use-cases/cat-22/uc-22.41.1.json)
<a id='uc-22-44-2'></a>
- **UC-22.44.2** — Subprocessor inventory change — notification SLA to data controllers
  - Control family: `third-party-activity`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.44.2.json`](../../use-cases/cat-22/uc-22.44.2.json)
<a id='uc-22-49-1'></a>
- **UC-22.49.1** — Retention execution evidence — records past retention still present
  - Control family: `retention-end-enforcement`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.49.1.json`](../../use-cases/cat-22/uc-22.49.1.json)
<a id='uc-22-49-2'></a>
- **UC-22.49.2** — Disposal workflow completion — failed disposals requiring manual review
  - Control family: `retention-end-enforcement`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.49.2.json`](../../use-cases/cat-22/uc-22.49.2.json)
<a id='uc-22-8-39'></a>
- **UC-22.8.39** — SOC 2 P1.1 — Privacy notice: consent-record freshness for privacy-notice version changes
  - Control family: `data-subject-request-lifecycle`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.8.39.json`](../../use-cases/cat-22/uc-22.8.39.json)
<a id='uc-22-9-4'></a>
- **UC-22.9.4** — Regulatory Incident Response Time Trending
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`use-cases/cat-22/uc-22.9.4.json`](../../use-cases/cat-22/uc-22.9.4.json)

## 5. Evidence collection

### 5.1 Common evidence sources

Auditors typically request the following records when examining this regulation:

- Identity-management system logs (SSO, IAM, directory services)
- Database audit trails (read/write/delete of personal-data tables)
- Application access logs (CRM, ERP, HR systems)
- DLP and CASB event streams
- Email security gateways (for data exfiltration evidence)
- Backup and recovery job logs (for Art.32 resilience)
- Vulnerability-management reports (Art.32 security-testing evidence)

### 5.2 Retention requirements

| Artifact | Retention | Legal basis |
|---|---|---|
| Records of processing activities (Art.30) | Duration of processing + 3 years | EDPB Guidelines 4/2019 §43 |
| Breach-notification records (Art.33(5)) | Minimum 3 years; ICO default is 6 years | GDPR Art.33(5); ICO Accountability Framework |
| Consent records (Art.7) | Duration of processing + 3 years after withdrawal | EDPB Guidelines 05/2020 §58 |
| DPIA documentation (Art.35) | Duration of processing + 3 years | Art.29 WP WP248 rev.01 |
| Access, rectification, erasure request logs (Arts.15-22) | Minimum 3 years post-closure; most member states require 6 | National implementing laws (e.g. DSGVO-BDSG Germany, Data Protection Act 2018 UK) |
| Data-transfer impact assessments (Art.46) | Duration of transfer + 3 years | EDPB Recommendations 01/2020 |

> Retention figures above are the legal minimums or regulator-stated expectations. Organisation-specific retention schedules may be longer where business, tax, litigation-hold, or contractual obligations apply. Where a figure conflicts with local data-protection law (e.g. GDPR Art.5(1)(e) storage-limitation principle), the shorter conformant period governs for personal-data content; the evidence-of-compliance retention retains the longer period for audit purposes, scrubbed of excess personal data.

### 5.3 Evidence integrity expectations

Regulators increasingly cite **evidence-integrity failures** as aggravating factors in enforcement actions. Cross-regulation baseline expectations:

- Time-stamped, tamper-evident storage (WORM, cryptographic chaining, or append-only indexes).
- Chain-of-custody for any evidence removed from the SIEM / production system for audit or legal purposes.
- Synchronised clocks (NTP stratum ≤ 3 or equivalent) across all in-scope sources so timeline reconstruction is defensible.
- Documented retention enforcement — not just retention policy — so that deletion is auditable.

See cat-22.35 "Evidence continuity and log integrity" for UCs that implement these controls.

## 6. Control testing procedures

Supervisory authorities and external auditors test GDPR compliance through a combination of documentation review (RoPA, DPIAs, policies), technical interviews (DPO, CISO, IT operations), evidence-sampling (pull last 30 days of data-subject requests and trace them through the logs), and substantive control testing (attempt a simulated access request, breach-notification drill, or data-transfer audit). Enforcement actions frequently cite log-integrity failures: detection occurred but the evidence chain was lost, or notification occurred but the supporting timeline was not preserved.

**Reporting cadence.** No GDPR certification equivalent to ISO 27001 exists (although Art.42 certification schemes are emerging slowly). Accountability is demonstrated on-demand: the controller must be able to produce Art.30 records, DPIAs, transfer safeguards, and breach logs when requested by the SA. Most organisations align internal attestation with financial-year audit or ISO 27001 surveillance (annual). DPO advisory opinions are typically refreshed quarterly.

## 7. Roles and responsibilities

| Role | Responsibility |
|---|---|
| **Data Controller** | Determines the purposes and means of processing; accountable for compliance with Art.5 principles. |
| **Data Processor** | Processes personal data on behalf of the controller; bound by Art.28 processing agreements. |
| **Data Protection Officer (DPO)** | Informs and advises the controller/processor, monitors compliance, cooperates with supervisory authorities (Arts.37-39). |
| **Representative in the Union** | Non-EU controllers/processors under Art.3(2) must appoint a Union representative (Art.27). |
| **Supervisory Authority (SA)** | National regulator with investigative, corrective and authorisation powers under Art.58. One-stop-shop mechanism under Art.56 for cross-border processing. |

## 8. Authoritative guidance

- **European Data Protection Board Guidelines** — EDPB — [https://edpb.europa.eu/our-work-tools/our-documents/guidelines_en](https://edpb.europa.eu/our-work-tools/our-documents/guidelines_en)
- **ICO Guide to the UK GDPR** — ICO (UK) — [https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/)
- **CNIL Guide de la sécurité des données personnelles** — CNIL (France) — [https://www.cnil.fr/fr/la-securite-des-donnees-personnelles](https://www.cnil.fr/fr/la-securite-des-donnees-personnelles)
- **BfDI GDPR Compliance Resources** — BfDI (Germany) — [https://www.bfdi.bund.de/EN/Home/home_node.html](https://www.bfdi.bund.de/EN/Home/home_node.html)
- **EDPB Guidelines 9/2022 on personal data breach notification** — EDPB — [https://edpb.europa.eu/our-work-tools/our-documents/guidelines/guidelines-92022-personal-data-breach-notification-under_en](https://edpb.europa.eu/our-work-tools/our-documents/guidelines/guidelines-92022-personal-data-breach-notification-under_en)

## 9. Common audit deficiencies

Findings frequently cited by regulators, certification bodies, and external auditors for this regulation. These should be pre-tested as part of readiness reviews.

- Records of Processing Activities are template-only and do not reflect actual processing.
- Breach-notification timeline evidence does not clearly demonstrate the 72-hour Art.33 window was met (missing timestamps on detection / triage / notification events).
- Data-subject request logs do not record the identity-verification steps required under Art.12(6).
- International-transfer evidence cites outdated SCCs (pre-2021 EU decision 2021/914) with no remediation date.
- Encryption keys for pseudonymisation are co-located with the data (defeating Art.4(5) pseudonymisation definition).
- DPIA is performed once and never reviewed despite material changes to processing purpose or scope.

## 10. Enforcement and penalties

Art.83 tiered administrative fines: up to EUR 10 million or 2 % of worldwide annual turnover (whichever higher) for most obligations; up to EUR 20 million or 4 % for breaches of Arts.5, 6, 7, 9, 12-22 and 44-49. SAs may also impose corrective measures under Art.58 (orders to bring processing into compliance, temporary or definitive processing bans, data-flow suspensions). Private claims under Art.82 allow material and non-material damage recovery. Criminal penalties are left to member-state law.

## 11. Pack gaps and remediation backlog

All clauses tracked in `data/regulations.json` for this regulation version are covered by at least one UC. **100 % common-clause coverage**. Remaining work is assurance-upgrade (for example, moving `contributing` entries to `partial` or `full` via explicit control tests) rather than new clause authoring.

## 12. Questions an auditor should ask

These are the questions a regulator, certification body, or external auditor is likely to ask. The pack helps preparers stage evidence and pre-test responses before the review opens.

- Show me the Article 30 Record of Processing Activities for the processing in scope; is it current within the last 12 months?
- Where are breach-detection logs stored, what is their retention, and can you prove they have not been tampered with since incident close?
- Produce the last three data-subject access requests; show timestamps proving the response was delivered within 30 days.
- Show evidence that pseudonymisation / encryption controls required under Art.32(1)(a) are in place for the relevant systems; include key-management records.
- Produce the DPIA for the highest-risk processing in scope and demonstrate the controls mitigating the identified risks were implemented.
- Show me the last three instances where personal data was transferred to a country outside the EU/EEA and the Art.46 safeguards that applied.
- What controls detect unauthorised access to personal data, and how have they been tested in the last 12 months?
- Where is the Data Protection Officer's independent opinion on processing operations documented?

## 13. Machine-readable twin

The machine-readable companion of this pack lives at [`api/v1/evidence-packs/gdpr.json`](../../api/v1/evidence-packs/gdpr.json). It contains the same clause-level coverage, retention guidance, role matrix, and gap list in JSON form, and is regenerated in lockstep with this markdown pack so content stays in sync. Consumers integrating the pack into GRC tools, audit-request portals, or evidence pipelines should consume the JSON document; human readers should consume this markdown.

Related API surfaces (all under [`api/v1/`](../../api/v1/README.md)):

- [`api/v1/compliance/regulations/gdpr.json`](../../api/v1/compliance/regulations/gdpr.json) — regulation metadata and per-version coverage metrics
- [`api/v1/compliance/ucs/`](../../api/v1/compliance/ucs/index.json) — individual UC sidecars
- [`api/v1/compliance/coverage.json`](../../api/v1/compliance/coverage.json) — global coverage snapshot
- [`api/v1/compliance/gaps.json`](../../api/v1/compliance/gaps.json) — global gap report

## 14. Provenance and regeneration

This pack is **generated**, not hand-authored. Re-running the generator produces byte-identical output (deterministic sort, stable serialisation, no free-form timestamps outside the block below). CI enforces regeneration drift via `--check` mode.

**Inputs to this pack**

- [`data/regulations.json`](../../data/regulations.json) — commonClauses, priority weights, authoritative URLs
- [`data/evidence-pack-extras.json`](../../data/evidence-pack-extras.json) — retention, roles, authoritative guidance, penalty, testing approach
- [`use-cases/cat-*/uc-*.json`](../../use-cases) — UC sidecars containing compliance[] entries, controlFamily, owner, evidence fields
- [`api/v1/compliance/regulations/gdpr@*.json`](../../api/v1/compliance/regulations/) — pre-computed coverage metrics (when present)

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
