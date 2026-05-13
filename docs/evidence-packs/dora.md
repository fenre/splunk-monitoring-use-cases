# Evidence Pack — DORA

> **Tier**: Tier 1 &nbsp;·&nbsp; **Jurisdiction**: EU &nbsp;·&nbsp; **Version**: `Regulation (EU) 2022/2554`
>
> **Full name**: EU Digital Operational Resilience Act<sup class="ref">[<a href="#ref-1">1</a>]</sup>
> **Authoritative source**: [https://eur-lex.europa.eu/eli/reg/2022/2554/oj](https://eur-lex.europa.eu/eli/reg/2022/2554/oj)
> **Effective from**: 2025-01-17

> This evidence pack is the auditor-facing view of the Splunk monitoring catalogue's coverage of the regulation. Every clause coverage claim is traceable to a specific UC sidecar JSON file (`content/cat-*/UC-*.json`); every retention figure cites its legal basis; every URL resolves to an official regulator or standards-body source. The pack does **not** assert legal conclusions — it tabulates what the catalogue covers, names the authoritative source, and flags gaps. Interpretation stays with counsel.

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
- **Contributing UCs**: 63

Coverage methodology is documented in [`docs/coverage-methodology.md`](../coverage-methodology.md). Priority weights come from `data/regulations.json` commonClauses entries (see [`data/regulations.json`](../../data/regulations.json) priorityWeightRubric).

## 4. Clause-by-clause coverage

Clauses are listed in the order defined by `data/regulations.json commonClauses` for this regulation version. A clause is considered covered when at least one UC sidecar has a `compliance[]` entry matching `(regulation, version, clause)`. Assurance is the maximum across contributing UCs.

| Clause | Topic | Priority | Assurance | UCs |
|---|---|---|---|---|
| [`Art.5`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.5) | ICT risk-management governance | 1.0 | `contributing` | [UC-17.1.28](#uc-17-1-28), [UC-17.1.61](#uc-17-1-61), [UC-22.3.1](#uc-22-3-1), [UC-22.3.19](#uc-22-3-19), [UC-22.3.21](#uc-22-3-21), [UC-22.3.22](#uc-22-3-22) (+2 more) |
| [`Art.6`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.6) | ICT risk-management framework | 1.0 | `full` | [UC-22.11.106](#uc-22-11-106), [UC-22.3.1](#uc-22-3-1), [UC-22.3.41](#uc-22-3-41), [UC-22.6.46](#uc-22-6-46) |
| [`Art.7`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.7) | ICT systems, protocols and tools | 1.0 | `full` | [UC-17.1.77](#uc-17-1-77), [UC-17.1.78](#uc-17-1-78), [UC-22.3.1](#uc-22-3-1), [UC-22.3.42](#uc-22-3-42), [UC-22.3.46](#uc-22-3-46), [UC-22.8.32](#uc-22-8-32) |
| [`Art.8`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.8) | Identification | 1.0 | `full` | [UC-22.11.103](#uc-22-11-103), [UC-22.3.1](#uc-22-3-1), [UC-22.3.43](#uc-22-3-43) |
| [`Art.9`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.9) | Protection and prevention | 1.0 | `full` | [UC-17.1.29](#uc-17-1-29), [UC-17.1.36](#uc-17-1-36), [UC-17.1.40](#uc-17-1-40), [UC-17.1.44](#uc-17-1-44), [UC-22.11.97](#uc-22-11-97), [UC-22.3.1](#uc-22-3-1) (+1 more) |
| [`Art.10`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.10) | Detection | 1.0 | `full` | [UC-17.1.33](#uc-17-1-33), [UC-22.3.1](#uc-22-3-1), [UC-22.3.47](#uc-22-3-47), [UC-22.3.7](#uc-22-3-7), [UC-22.8.33](#uc-22-8-33) |
| [`Art.11`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.11) | Response and recovery | 1.0 | `contributing` | [UC-22.3.1](#uc-22-3-1), [UC-22.3.5](#uc-22-3-5), [UC-22.3.8](#uc-22-3-8) |
| [`Art.12`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.12) | Backup policies and recovery methods | 1.0 | `full` | [UC-17.1.47](#uc-17-1-47), [UC-22.3.1](#uc-22-3-1), [UC-22.3.5](#uc-22-3-5), [UC-22.3.9](#uc-22-3-9), [UC-22.35.3](#uc-22-35-3), [UC-22.45.1](#uc-22-45-1) (+1 more) |
| [`Art.17`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.17) | ICT-related incident management process | 1.0 | `full` | [UC-17.1.30](#uc-17-1-30), [UC-17.1.42](#uc-17-1-42), [UC-17.1.80](#uc-17-1-80), [UC-17.1.82](#uc-17-1-82), [UC-22.3.2](#uc-22-3-2), [UC-22.3.23](#uc-22-3-23) (+2 more) |
| [`Art.18`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.18) | Classification of ICT-related incidents | 1.0 | `contributing` | [UC-22.3.11](#uc-22-3-11), [UC-22.3.2](#uc-22-3-2) |
| [`Art.19`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.19) | Reporting of major ICT-related incidents | 1.0 | `full` | [UC-22.3.12](#uc-22-3-12), [UC-22.3.2](#uc-22-3-2), [UC-22.3.38](#uc-22-3-38), [UC-22.39.1](#uc-22-39-1) |
| [`Art.24`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.24) | Digital operational-resilience testing | 0.7 | `full` | [UC-22.11.105](#uc-22-11-105), [UC-22.3.25](#uc-22-3-25), [UC-22.3.27](#uc-22-3-27), [UC-22.3.28](#uc-22-3-28), [UC-22.3.3](#uc-22-3-3), [UC-22.3.39](#uc-22-3-39) (+1 more) |
| [`Art.26`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.26) | Threat-led penetration testing | 0.7 | `contributing` | [UC-22.3.17](#uc-22-3-17), [UC-22.3.3](#uc-22-3-3) |
| [`Art.28`](https://eur-lex.europa.eu/eli/reg/2022/2554/oj#Art.28) | ICT third-party risk | 1.0 | `full` | [UC-17.1.60](#uc-17-1-60), [UC-17.1.62](#uc-17-1-62), [UC-22.3.4](#uc-22-3-4), [UC-22.3.40](#uc-22-3-40), [UC-22.38.3](#uc-22-38-3), [UC-22.44.1](#uc-22-44-1) (+2 more) |

### 4.1 Contributing UC detail

<a id='uc-17-1-28'></a>
- **UC-17.1.28** — Cisco ISE<sup class="ref">[<a href="#ref-3">3</a>]</sup> Deployment Replication Health and PSN Sync Lag
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.28.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.28.json)
<a id='uc-17-1-29'></a>
- **UC-17.1.29** — Cisco ISE Node Resource Saturation (CPU, Memory, Disk, Threads)
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.29.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.29.json)
<a id='uc-17-1-30'></a>
- **UC-17.1.30** — Cisco ISE Process Crash and Service-Restart Detection
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.30.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.30.json)
<a id='uc-17-1-33'></a>
- **UC-17.1.33** — Cisco ISE pxGrid Subscriber Connectivity and Topic Health
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.33.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.33.json)
<a id='uc-17-1-36'></a>
- **UC-17.1.36** — Cisco TrustSec / SGT Assignment Mismatch and SXP Listener Health
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.36.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.36.json)
<a id='uc-17-1-40'></a>
- **UC-17.1.40** — RADIUS Authentication Latency SLO and Slow PSN Detection
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.40.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.40.json)
<a id='uc-17-1-42'></a>
- **UC-17.1.42** — Adaptive Network Control (ANC) Action Auditing and Excessive Quarantine Detection
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.42.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.42.json)
<a id='uc-17-1-44'></a>
- **UC-17.1.44** — Cisco ISE External Identity Store Health (AD/LDAP/RADIUS/SAML/OAuth)
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.44.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.44.json)
<a id='uc-17-1-47'></a>
- **UC-17.1.47** — Cisco ISE Backup Job Success and Operational-Data Backup Validation
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.47.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.47.json)
<a id='uc-17-1-60'></a>
- **UC-17.1.60** — ISE on AWS / Azure / GCP — Cloud-Hosted PSN Health and Egress Cost
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.60.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.60.json)
<a id='uc-17-1-61'></a>
- **UC-17.1.61** — ISE Multi-Site Topology — Cross-Site Replication Lag and WAN Loss Impact
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.61.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.61.json)
<a id='uc-17-1-62'></a>
- **UC-17.1.62** — ISE Hybrid Deployment — On-Prem PAN to Cloud-PSN Latency and Bandwidth
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.62.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.62.json)
<a id='uc-17-1-77'></a>
- **UC-17.1.77** — Cisco ISE PSN Authentication-Per-Second (TPS) SLO and Capacity Headroom
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.77.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.77.json)
<a id='uc-17-1-78'></a>
- **UC-17.1.78** — ISE PSN Authentication Distribution Imbalance and Sticky-Session Detection
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.78.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.78.json)
<a id='uc-17-1-80'></a>
- **UC-17.1.80** — ISE ANC Closed-Loop Effectiveness — Quarantine-to-Compromise-Stop Time
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.80.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.80.json)
<a id='uc-17-1-82'></a>
- **UC-17.1.82** — Splunk SOAR<sup class="ref">[<a href="#ref-12">12</a>]</sup> + ISE Closed-Loop Playbook Audit and Mean-Time-to-Containment KPI
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.82.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.82.json)
<a id='uc-22-11-103'></a>
- **UC-22.11.103** — PCI-DSS 11.3 — Vulnerability programme: overdue scan cadence and unremediated high-severity
  - Control family: `regulation-specific`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.11.103.json`](../../content/cat-22-regulatory-compliance/UC-22.11.103.json)
<a id='uc-22-11-105'></a>
- **UC-22.11.105** — PCI-DSS 12.10 — Incident response: IR readiness — playbook exercise evidence
  - Control family: `ir-drill-evidence`
  - Owner: `Head of IR`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.11.105.json`](../../content/cat-22-regulatory-compliance/UC-22.11.105.json)
<a id='uc-22-11-106'></a>
- **UC-22.11.106** — PCI-DSS 12.3 — Targeted risk analysis: frequency adherence for per-requirement TRAs
  - Control family: `policy-to-control-traceability`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.11.106.json`](../../content/cat-22-regulatory-compliance/UC-22.11.106.json)
<a id='uc-22-11-97'></a>
- **UC-22.11.97** — PCI-DSS 8.4 — MFA coverage: administrative access to CDE without MFA
  - Control family: `privileged-session-recording`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.11.97.json`](../../content/cat-22-regulatory-compliance/UC-22.11.97.json)
<a id='uc-22-3-1'></a>
- **UC-22.3.1** — DORA ICT Risk Management Dashboard
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.1.json`](../../content/cat-22-regulatory-compliance/UC-22.3.1.json)
<a id='uc-22-3-11'></a>
- **UC-22.3.11** — DORA Major ICT Incident 7-Criteria Classification
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.11.json`](../../content/cat-22-regulatory-compliance/UC-22.3.11.json)
<a id='uc-22-3-12'></a>
- **UC-22.3.12** — DORA ICT Incident Intermediate and Final Report Tracking
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.12.json`](../../content/cat-22-regulatory-compliance/UC-22.3.12.json)
<a id='uc-22-3-17'></a>
- **UC-22.3.17** — DORA Threat-Led Penetration Testing (TLPT) Lifecycle
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.17.json`](../../content/cat-22-regulatory-compliance/UC-22.3.17.json)
<a id='uc-22-3-19'></a>
- **UC-22.3.19** — DORA Management Body ICT Governance and Oversight
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.19.json`](../../content/cat-22-regulatory-compliance/UC-22.3.19.json)
<a id='uc-22-3-2'></a>
- **UC-22.3.2** — DORA ICT Incident Classification and Reporting
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.2.json`](../../content/cat-22-regulatory-compliance/UC-22.3.2.json)
<a id='uc-22-3-21'></a>
- **UC-22.3.21** — DORA ICT Concentration — Single-Provider Spend and Workload Share Thresholds
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.21.json`](../../content/cat-22-regulatory-compliance/UC-22.3.21.json)
<a id='uc-22-3-22'></a>
- **UC-22.3.22** — DORA ICT Concentration — Critical Service Dependency Fan-In by Provider
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.22.json`](../../content/cat-22-regulatory-compliance/UC-22.3.22.json)
<a id='uc-22-3-23'></a>
- **UC-22.3.23** — DORA ICT Concentration — Regional Provider Outage Correlation Exposure Score
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.23.json`](../../content/cat-22-regulatory-compliance/UC-22.3.23.json)
<a id='uc-22-3-24'></a>
- **UC-22.3.24** — DORA ICT Concentration — Substitutability and Secondary Sourcing Readiness Index
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.24.json`](../../content/cat-22-regulatory-compliance/UC-22.3.24.json)
<a id='uc-22-3-25'></a>
- **UC-22.3.25** — DORA TLPT — Test Planning Milestone and Scope Lock Audit Trail
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.25.json`](../../content/cat-22-regulatory-compliance/UC-22.3.25.json)
<a id='uc-22-3-26'></a>
- **UC-22.3.26** — DORA TLPT — Tester Independence and Conflict-of-Interest Attestation Log
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.26.json`](../../content/cat-22-regulatory-compliance/UC-22.3.26.json)
<a id='uc-22-3-27'></a>
- **UC-22.3.27** — DORA TLPT — Findings Severity, Remediation Owner, and Due Date Tracking
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.27.json`](../../content/cat-22-regulatory-compliance/UC-22.3.27.json)
<a id='uc-22-3-28'></a>
- **UC-22.3.28** — DORA TLPT — Retest and Control Effectiveness Verification Events
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.28.json`](../../content/cat-22-regulatory-compliance/UC-22.3.28.json)
<a id='uc-22-3-3'></a>
- **UC-22.3.3** — DORA Digital Operational Resilience Testing
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.3.json`](../../content/cat-22-regulatory-compliance/UC-22.3.3.json)
<a id='uc-22-3-31'></a>
- **UC-22.3.31** — DORA Information Sharing — Anonymized Incident TTP Contribution Quality Metrics
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.31.json`](../../content/cat-22-regulatory-compliance/UC-22.3.31.json)
<a id='uc-22-3-38'></a>
- **UC-22.3.38** — DORA ICT Third-Party Risk Register — Inherent vs Residual Risk Score Reconciliation
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.38.json`](../../content/cat-22-regulatory-compliance/UC-22.3.38.json)
<a id='uc-22-3-39'></a>
- **UC-22.3.39** — DORA ICT Third-Party Risk Register — Control Testing Evidence Freshness by Provider Tier
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.39.json`](../../content/cat-22-regulatory-compliance/UC-22.3.39.json)
<a id='uc-22-3-4'></a>
- **UC-22.3.4** — DORA Third-Party ICT Provider Concentration Risk
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.4.json`](../../content/cat-22-regulatory-compliance/UC-22.3.4.json)
<a id='uc-22-3-40'></a>
- **UC-22.3.40** — DORA ICT Third-Party Risk Register — Issue Density and Open Finding Trend by Provider
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.40.json`](../../content/cat-22-regulatory-compliance/UC-22.3.40.json)
<a id='uc-22-3-41'></a>
- **UC-22.3.41** — DORA Art.6 — ICT risk-management framework evidence: control catalogue drift detection
  - Control family: `policy-to-control-traceability`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.41.json`](../../content/cat-22-regulatory-compliance/UC-22.3.41.json)
<a id='uc-22-3-42'></a>
- **UC-22.3.42** — DORA Art.7 — ICT systems inventory completeness: unmanaged endpoints attached to financial services
  - Control family: `log-source-completeness`
  - Owner: `Head of IT Operations`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.42.json`](../../content/cat-22-regulatory-compliance/UC-22.3.42.json)
<a id='uc-22-3-43'></a>
- **UC-22.3.43** — DORA Art.8 — ICT risk identification: newly discovered high-severity exposure on critical financial services
  - Control family: `regulation-specific`
  - Owner: `Head of IR`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.43.json`](../../content/cat-22-regulatory-compliance/UC-22.3.43.json)
<a id='uc-22-3-44'></a>
- **UC-22.3.44** — DORA Art.17 — ICT incident classification timeliness: major-incident clock evidence
  - Control family: `ir-drill-evidence`
  - Owner: `Head of IR`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.44.json`](../../content/cat-22-regulatory-compliance/UC-22.3.44.json)
<a id='uc-22-3-45'></a>
- **UC-22.3.45** — DORA Art.24 — Digital operational-resilience testing: test-plan execution attestation
  - Control family: `ir-drill-evidence`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.45.json`](../../content/cat-22-regulatory-compliance/UC-22.3.45.json)
<a id='uc-22-3-46'></a>
- **UC-22.3.46** — DORA Art.7 — Cisco ISE PSN Capacity SLO Evidence (ICT Resilience)
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.46.json`](../../content/cat-22-regulatory-compliance/UC-22.3.46.json)
<a id='uc-22-3-47'></a>
- **UC-22.3.47** — DORA Art.10 — Cisco ISE Multi-Site Replication Resilience Evidence
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.47.json`](../../content/cat-22-regulatory-compliance/UC-22.3.47.json)
<a id='uc-22-3-5'></a>
- **UC-22.3.5** — DORA Cross-Region Disaster Recovery Compliance
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.5.json`](../../content/cat-22-regulatory-compliance/UC-22.3.5.json)
<a id='uc-22-3-7'></a>
- **UC-22.3.7** — DORA ICT Anomaly Detection Capabilities
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.7.json`](../../content/cat-22-regulatory-compliance/UC-22.3.7.json)
<a id='uc-22-3-8'></a>
- **UC-22.3.8** — DORA ICT Incident Response and Recovery Time Tracking
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.8.json`](../../content/cat-22-regulatory-compliance/UC-22.3.8.json)
<a id='uc-22-3-9'></a>
- **UC-22.3.9** — DORA Backup Completeness and Restoration Testing
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.9.json`](../../content/cat-22-regulatory-compliance/UC-22.3.9.json)
<a id='uc-22-35-3'></a>
- **UC-22.35.3** — Indexer replication lag exposing evidence to single-point failure
  - Control family: `evidence-continuity`
  - Owner: `Head of Platform`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.35.3.json`](../../content/cat-22-regulatory-compliance/UC-22.35.3.json)
<a id='uc-22-38-3'></a>
- **UC-22.38.3** — Data localization enforcement — regulated-data must-stay-in-region
  - Control family: `data-flow-cross-border`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.38.3.json`](../../content/cat-22-regulatory-compliance/UC-22.38.3.json)
<a id='uc-22-39-1'></a>
- **UC-22.39.1** — Multi-regulator breach-notification SLA tracker (24h NIS2<sup class="ref">[<a href="#ref-4">4</a>]</sup> / 72h GDPR<sup class="ref">[<a href="#ref-6">6</a>]</sup> / 72h HIPAA<sup class="ref">[<a href="#ref-14">14</a>]</sup>)
  - Control family: `ir-drill-evidence`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.39.1.json`](../../content/cat-22-regulatory-compliance/UC-22.39.1.json)
<a id='uc-22-41-3'></a>
- **UC-22.41.3** — Key rotation attestation — KMS/HSM rotation SLA tracker
  - Control family: `crypto-drift`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.41.3.json`](../../content/cat-22-regulatory-compliance/UC-22.41.3.json)
<a id='uc-22-44-1'></a>
- **UC-22.44.1** — Supplier attestation currency — stale SOC 2<sup class="ref">[<a href="#ref-2">2</a>]</sup> / ISO 27001 reports for critical vendors
  - Control family: `third-party-activity`
  - Owner: `Procurement`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.44.1.json`](../../content/cat-22-regulatory-compliance/UC-22.44.1.json)
<a id='uc-22-44-2'></a>
- **UC-22.44.2** — Subprocessor inventory change — notification SLA to data controllers
  - Control family: `third-party-activity`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.44.2.json`](../../content/cat-22-regulatory-compliance/UC-22.44.2.json)
<a id='uc-22-44-3'></a>
- **UC-22.44.3** — Fourth-party concentration risk — shared critical dependencies across vendors
  - Control family: `third-party-activity`
  - Owner: `Procurement`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.44.3.json`](../../content/cat-22-regulatory-compliance/UC-22.44.3.json)
<a id='uc-22-45-1'></a>
- **UC-22.45.1** — Backup restore test evidence — RPO/RTO SLA compliance per tier
  - Control family: `backup-restore-evidence`
  - Owner: `Head of IT Operations`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.45.1.json`](../../content/cat-22-regulatory-compliance/UC-22.45.1.json)
<a id='uc-22-45-3'></a>
- **UC-22.45.3** — Backup completeness — unprotected workloads with regulated data
  - Control family: `backup-restore-evidence`
  - Owner: `Head of IT Operations`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.45.3.json`](../../content/cat-22-regulatory-compliance/UC-22.45.3.json)
<a id='uc-22-6-46'></a>
- **UC-22.6.46** — ISO/IEC 27001:2022<sup class="ref">[<a href="#ref-8">8</a>]</sup> Clause 6.1 — Risk-assessment evidence: live risk register decay
  - Control family: `board-exec-reporting`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.6.46.json`](../../content/cat-22-regulatory-compliance/UC-22.6.46.json)
<a id='uc-22-8-32'></a>
- **UC-22.8.32** — SOC 2 CC6.7 — System boundary & data-transmission control: unapproved egress destinations
  - Control family: `data-flow-cross-border`
  - Owner: `Head of Platform`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.8.32.json`](../../content/cat-22-regulatory-compliance/UC-22.8.32.json)
<a id='uc-22-8-33'></a>
- **UC-22.8.33** — SOC 2 CC7.1 — System-operations monitoring: uptime attestation and alert-noise governance
  - Control family: `log-source-completeness`
  - Owner: `Head of IT Operations`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.8.33.json`](../../content/cat-22-regulatory-compliance/UC-22.8.33.json)

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
- [`content/cat-*/UC-*.json`](../../content) — UC sidecars containing compliance[] entries, controlFamily, owner, evidence fields
- [`api/v1/compliance/regulations/dora@*.json`](../../api/v1/compliance/regulations/) — pre-computed coverage metrics (when present)

- Generator: [`scripts/generate_evidence_packs.py`](../../scripts/generate_evidence_packs.py)
- Evidence-pack directory index: [`docs/evidence-packs/README.md`](README.md)

**Generation metadata**

```
catalogue_version: 8.2.1
generator_script:  scripts/generate_evidence_packs.py
inputs_sha256:     05d15d6f921fc6af3c7dbfacf931dcfd40d45bd1e8a91ef250232b39e24f110e
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

### Primary sources

<a id="ref-1"></a>**[1]** European Parliament and Council of the European Union. (2022, December). *Regulation (EU) 2022/2554 — Digital Operational Resilience Act (DORA)*. Official Journal of the European Union, L 333. ELI: reg/2022/2554. https://eur-lex.europa.eu/eli/reg/2022/2554/oj

### Supporting sources

<a id="ref-2"></a>**[2]** American Institute of Certified Public Accountants. (2017). *Trust Services Criteria (2017) for Security, Availability, Processing Integrity, Confidentiality, and Privacy*. AICPA & CIMA. SOC 2 / TSP Section 100. https://www.aicpa-cima.com/topic/audit-assurance/soc-suite-of-services

<a id="ref-3"></a>**[3]** Cisco Systems, Inc. (2026). *Cisco Identity Services Engine (ISE) Documentation*. Retrieved May 11, 2026, from https://www.cisco.com/c/en/us/support/security/identity-services-engine/series.html

<a id="ref-4"></a>**[4]** European Parliament and Council of the European Union. (2022, December). *Directive (EU) 2022/2555 — NIS2 Directive on cybersecurity*. Official Journal of the European Union, L 333. ELI: dir/2022/2555. https://eur-lex.europa.eu/eli/dir/2022/2555/oj

<a id="ref-5"></a>**[5]** European Parliament and Council of the European Union. (2014). *Directive 2014/65/EU — Markets in Financial Instruments Directive (MiFID II)*. Official Journal of the European Union, L 173. ELI: dir/2014/65. https://eur-lex.europa.eu/eli/dir/2014/65/oj

<a id="ref-6"></a>**[6]** European Parliament and Council of the European Union. (2016, April). *Regulation (EU) 2016/679 — General Data Protection Regulation*. Official Journal of the European Union, L 119. ELI: reg/2016/679. https://eur-lex.europa.eu/eli/reg/2016/679/oj

<a id="ref-7"></a>**[7]** International Organization for Standardization. (2019). *ISO 22301:2019 — Business continuity management systems — Requirements*. ISO/IEC. ISO 22301:2019. https://www.iso.org/standard/75106.html

<a id="ref-8"></a>**[8]** International Organization for Standardization. (2022). *ISO/IEC 27001:2022 — Information security, cybersecurity and privacy protection — Information security management systems — Requirements*. ISO/IEC. ISO/IEC 27001:2022. https://www.iso.org/standard/27001

<a id="ref-9"></a>**[9]** National Institute of Standards and Technology. (2024). *Cybersecurity Framework (CSF) 2.0* (2.0). U.S. Department of Commerce. NIST CSWP 29. https://www.nist.gov/cyberframework

<a id="ref-10"></a>**[10]** Splunk Inc. (2026). *Splunk Enterprise Security Administration Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ES

<a id="ref-11"></a>**[11]** Splunk Inc. (2026). *Splunk IT Service Intelligence Administration Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ITSI

<a id="ref-12"></a>**[12]** Splunk Inc. (2026). *Splunk SOAR (Cloud) Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/SOARonprem

<a id="ref-13"></a>**[13]** U.S. Department of Health & Human Services. (2002). *HIPAA Privacy Rule (45 CFR Parts 160 and 164, Subparts A and E)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/privacy/index.html

<a id="ref-14"></a>**[14]** U.S. Department of Health & Human Services. (2013). *HIPAA Security Rule (45 CFR Parts 160 and 164, Subparts A and C)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/security/index.html

<details>
<summary>Additional online sources cited in the document body (4)</summary>

<a id="ref-15"></a>**[15]** esma.europa.eu. *esma.europa.eu: Dora*. Retrieved May 11, 2026, from https://www.esma.europa.eu/rules/dora

<a id="ref-16"></a>**[16]** eur-lex.europa.eu. *EUR-Lex: Oj*. Retrieved May 11, 2026, from https://eur-lex.europa.eu/eli/reg_del/2024/1774/oj

<a id="ref-17"></a>**[17]** eur-lex.europa.eu. *EUR-Lex: Oj*. Retrieved May 11, 2026, from https://eur-lex.europa.eu/eli/reg_del/2024/1772/oj

<a id="ref-18"></a>**[18]** eur-lex.europa.eu. *EUR-Lex: Oj*. Retrieved May 11, 2026, from https://eur-lex.europa.eu/eli/reg_del/2025/302/oj

</details>

<!-- END-AUTOGENERATED-SOURCES -->
