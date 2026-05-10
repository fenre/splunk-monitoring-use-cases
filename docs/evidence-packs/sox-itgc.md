# Evidence Pack — SOX ITGC

> **Tier**: Tier 1 &nbsp;·&nbsp; **Jurisdiction**: US &nbsp;·&nbsp; **Version**: `PCAOB AS 2201`
>
> **Full name**: SOX — PCAOB AS 2201 ITGCs
> **Authoritative source**: [https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201](https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201)
> **Effective from**: 2007-11-15

> This evidence pack is the auditor-facing view of the Splunk monitoring catalogue's coverage of the regulation. Every clause coverage claim is traceable to a specific UC sidecar JSON file (`content/cat-*/UC-*.json`); every retention figure cites its legal basis; every URL resolves to an official regulator or standards-body source. The pack does **not** assert legal conclusions — it tabulates what the catalogue covers, names the authoritative source, and flags gaps. Interpretation stays with counsel.

> **Live views.** [Buyer narrative (`compliance-story.html?reg=sox-itgc`)](../../compliance-story.html?reg=sox-itgc) · [Auditor clause navigator (`clause-navigator.html#reg=sox-itgc`)](../../clause-navigator.html#reg=sox-itgc) · [JSON twin (`api/v1/compliance/story/sox-itgc.json`)](../../api/v1/compliance/story/sox-itgc.json)

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

Sarbanes-Oxley Act of 2002 §404 requires management of public companies to establish and maintain an adequate internal control structure over financial reporting (ICFR), and the external auditor to attest to its effectiveness. IT General Controls (ITGCs) are the control domain within ICFR that governs the integrity of financial reporting system data: access controls, change controls, computer operations, and program development. PCAOB AS 2201 is the audit standard that auditors apply.

## 2. Scope and applicability

All public companies registered with the SEC (US issuers and foreign private issuers listed on US exchanges). §404(b) external audit requirement applies to accelerated filers and large-accelerated filers; §404(a) management attestation applies to all registrants.

**Territorial scope.** Any company with securities registered with the SEC, regardless of country of incorporation.

## 3. Catalogue coverage at a glance

- **Clauses tracked**: 12
- **Clauses covered by at least one UC**: 12 / 12 (100.0%)
- **Priority-weighted coverage**: 100.0%
- **Contributing UCs**: 50

Coverage methodology is documented in [`docs/coverage-methodology.md`](../coverage-methodology.md). Priority weights come from `data/regulations.json` commonClauses entries (see [`data/regulations.json`](../../data/regulations.json) priorityWeightRubric).

## 4. Clause-by-clause coverage

Clauses are listed in the order defined by `data/regulations.json commonClauses` for this regulation version. A clause is considered covered when at least one UC sidecar has a `compliance[]` entry matching `(regulation, version, clause)`. Assurance is the maximum across contributing UCs.

| Clause | Topic | Priority | Assurance | UCs |
|---|---|---|---|---|
| [`ITGC.AccessMgmt.Provisioning`](https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201#ITGC.AccessMgmt.Provisioning) | User provisioning | 1.0 | `full` | [UC-17.1.71](#uc-17-1-71), [UC-17.1.76](#uc-17-1-76), [UC-22.12.1](#uc-22-12-1), [UC-22.12.36](#uc-22-12-36), [UC-22.12.41](#uc-22-12-41), [UC-22.12.42](#uc-22-12-42) (+2 more) |
| [`ITGC.AccessMgmt.Termination`](https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201#ITGC.AccessMgmt.Termination) | Timely deprovisioning | 1.0 | `full` | [UC-22.12.37](#uc-22-12-37), [UC-22.12.5](#uc-22-12-5) |
| [`ITGC.AccessMgmt.Privileged`](https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201#ITGC.AccessMgmt.Privileged) | Privileged access | 1.0 | `full` | [UC-17.1.32](#uc-17-1-32), [UC-17.1.43](#uc-17-1-43), [UC-17.1.58](#uc-17-1-58), [UC-22.12.2](#uc-22-12-2), [UC-22.12.28](#uc-22-12-28), [UC-22.40.1](#uc-22-40-1) (+2 more) |
| [`ITGC.AccessMgmt.SOD`](https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201#ITGC.AccessMgmt.SOD) | Segregation of duties | 1.0 | `full` | [UC-22.12.3](#uc-22-12-3), [UC-22.48.1](#uc-22-48-1), [UC-22.48.2](#uc-22-48-2) |
| [`ITGC.AccessMgmt.Review`](https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201#ITGC.AccessMgmt.Review) | Periodic access review | 0.7 | `full` | [UC-22.12.26](#uc-22-12-26), [UC-22.40.3](#uc-22-40-3) |
| [`ITGC.ChangeMgmt.Authorization`](https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201#ITGC.ChangeMgmt.Authorization) | Change authorised | 1.0 | `full` | [UC-16.4.1](#uc-16-4-1), [UC-17.1.43](#uc-17-1-43), [UC-17.1.48](#uc-17-1-48), [UC-17.1.49](#uc-17-1-49), [UC-22.42.1](#uc-22-42-1), [UC-7.1.13](#uc-7-1-13) |
| [`ITGC.ChangeMgmt.Testing`](https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201#ITGC.ChangeMgmt.Testing) | Change tested | 1.0 | `full` | [UC-22.11.95](#uc-22-11-95), [UC-22.12.12](#uc-22-12-12), [UC-22.12.13](#uc-22-12-13), [UC-22.12.14](#uc-22-12-14), [UC-22.12.15](#uc-22-12-15), [UC-22.12.16](#uc-22-12-16) (+2 more) |
| [`ITGC.ChangeMgmt.Approval`](https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201#ITGC.ChangeMgmt.Approval) | Change approved | 1.0 | `full` | [UC-12.2.17](#uc-12-2-17), [UC-22.12.10](#uc-22-12-10), [UC-22.12.11](#uc-22-12-11), [UC-22.12.39](#uc-22-12-39), [UC-22.6.55](#uc-22-6-55), [UC-5.13.46](#uc-5-13-46) |
| [`ITGC.Operations.JobSchedule`](https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201#ITGC.Operations.JobSchedule) | Batch scheduling and monitoring | 0.7 | `full` | [UC-22.12.40](#uc-22-12-40) |
| [`ITGC.Operations.Backup`](https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201#ITGC.Operations.Backup) | Backup and restore | 1.0 | `full` | [UC-22.45.3](#uc-22-45-3) |
| [`ITGC.Logging.Continuity`](https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201#ITGC.Logging.Continuity) | Audit trail completeness | 1.0 | `partial` | [UC-22.35.2](#uc-22-35-2), [UC-22.9.8](#uc-22-9-8), [UC-7.1.40](#uc-7-1-40) |
| [`ITGC.Logging.Review`](https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201#ITGC.Logging.Review) | Log review | 0.7 | `partial` | [UC-22.47.2](#uc-22-47-2), [UC-22.49.3](#uc-22-49-3), [UC-5.13.45](#uc-5-13-45) |

### 4.1 Contributing UC detail

<a id='uc-12-2-17'></a>
- **UC-12.2.17** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-16-4-1'></a>
- **UC-16.4.1** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-17-1-32'></a>
- **UC-17.1.32** — Cisco ISE License Consumption, Endpoint Capacity and MnT Log Retention
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.32.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.32.json)
<a id='uc-17-1-43'></a>
- **UC-17.1.43** — Cisco ISE TACACS+ Device Administration — Privileged Command Auditing
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.43.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.43.json)
<a id='uc-17-1-48'></a>
- **UC-17.1.48** — Cisco ISE Restore Audit and Configuration-Drift Detection Post-Restore
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.48.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.48.json)
<a id='uc-17-1-49'></a>
- **UC-17.1.49** — Cisco ISE Patch and Upgrade Health — Pre/Post-Upgrade Validation
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.49.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.49.json)
<a id='uc-17-1-58'></a>
- **UC-17.1.58** — Cisco ISE Data Connect — DB-Direct Query Audit and Slow-Query Detection
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.58.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.58.json)
<a id='uc-17-1-71'></a>
- **UC-17.1.71** — Cisco ISE Admin Account Lockout, Failed-Login Burst, and Privileged-Role Audit
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.71.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.71.json)
<a id='uc-17-1-76'></a>
- **UC-17.1.76** — ISE Group-Based Policy (GBP / Microsegmentation) Effective-Policy Drift
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.76.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.76.json)
<a id='uc-22-11-95'></a>
- **UC-22.11.95** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-12-1'></a>
- **UC-22.12.1** — User provisioning evidence tied to financial application accounts
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.12.1.json`](../../content/cat-22-regulatory-compliance/UC-22.12.1.json)
<a id='uc-22-12-10'></a>
- **UC-22.12.10** — Change approval workflow evidence for financially material CIs
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.12.10.json`](../../content/cat-22-regulatory-compliance/UC-22.12.10.json)
<a id='uc-22-12-11'></a>
- **UC-22.12.11** — CAB evidence and high-risk change documentation gaps
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.12.11.json`](../../content/cat-22-regulatory-compliance/UC-22.12.11.json)
<a id='uc-22-12-12'></a>
- **UC-22.12.12** — Production change volume during financial close windows
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.12.12.json`](../../content/cat-22-regulatory-compliance/UC-22.12.12.json)
<a id='uc-22-12-13'></a>
- **UC-22.12.13** — Failed change rollback and backout evidence tracking
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.12.13.json`](../../content/cat-22-regulatory-compliance/UC-22.12.13.json)
<a id='uc-22-12-14'></a>
- **UC-22.12.14** — Changes executed outside approved maintenance windows
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.12.14.json`](../../content/cat-22-regulatory-compliance/UC-22.12.14.json)
<a id='uc-22-12-15'></a>
- **UC-22.12.15** — Financial close batch job failures and runtime SLA breaches
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.12.15.json`](../../content/cat-22-regulatory-compliance/UC-22.12.15.json)
<a id='uc-22-12-16'></a>
- **UC-22.12.16** — General ledger database backup success within policy windows
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.12.16.json`](../../content/cat-22-regulatory-compliance/UC-22.12.16.json)
<a id='uc-22-12-17'></a>
- **UC-22.12.17** — Unauthorized batch schedule or dependency modifications
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.12.17.json`](../../content/cat-22-regulatory-compliance/UC-22.12.17.json)
<a id='uc-22-12-18'></a>
- **UC-22.12.18** — ITSI service health for financial reporting dependency chain
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.12.18.json`](../../content/cat-22-regulatory-compliance/UC-22.12.18.json)
<a id='uc-22-12-2'></a>
- **UC-22.12.2** — Privileged access review completion and aging for financial systems
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.12.2.json`](../../content/cat-22-regulatory-compliance/UC-22.12.2.json)
<a id='uc-22-12-26'></a>
- **UC-22.12.26** — Sensitive management financial report access and export
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.12.26.json`](../../content/cat-22-regulatory-compliance/UC-22.12.26.json)
<a id='uc-22-12-28'></a>
- **UC-22.12.28** — Quarterly privileged ERP role population for sign-off
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.12.28.json`](../../content/cat-22-regulatory-compliance/UC-22.12.28.json)
<a id='uc-22-12-3'></a>
- **UC-22.12.3** — Segregation of duties conflicts across SAP / Oracle financial roles
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.12.3.json`](../../content/cat-22-regulatory-compliance/UC-22.12.3.json)
<a id='uc-22-12-36'></a>
- **UC-22.12.36** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-12-37'></a>
- **UC-22.12.37** —
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
<a id='uc-22-12-41'></a>
- **UC-22.12.41** — SOX / ITGC — Cisco ISE Admin Role Change Evidence (Logical Access)
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.12.41.json`](../../content/cat-22-regulatory-compliance/UC-22.12.41.json)
<a id='uc-22-12-42'></a>
- **UC-22.12.42** — SOX / ITGC — TACACS+ Privileged-Command Audit on Network Devices
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.12.42.json`](../../content/cat-22-regulatory-compliance/UC-22.12.42.json)
<a id='uc-22-12-43'></a>
- **UC-22.12.43** — SOX / ITGC — Cisco ISE Data Connect Direct DB Access Audit
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.12.43.json`](../../content/cat-22-regulatory-compliance/UC-22.12.43.json)
<a id='uc-22-12-5'></a>
- **UC-22.12.5** — Terminated-user authentication after HR termination date
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.12.5.json`](../../content/cat-22-regulatory-compliance/UC-22.12.5.json)
<a id='uc-22-35-2'></a>
- **UC-22.35.2** — Log tamper detection via write-once-read-many chain-of-custody
  - Control family: `evidence-continuity`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.35.2.json`](../../content/cat-22-regulatory-compliance/UC-22.35.2.json)
<a id='uc-22-40-1'></a>
- **UC-22.40.1** — Privileged session recording — missing recordings for elevated sessions
  - Control family: `privileged-session-recording`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.40.1.json`](../../content/cat-22-regulatory-compliance/UC-22.40.1.json)
<a id='uc-22-40-2'></a>
- **UC-22.40.2** — Break-glass account usage review with mandatory post-use approval
  - Control family: `privileged-session-recording`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.40.2.json`](../../content/cat-22-regulatory-compliance/UC-22.40.2.json)
<a id='uc-22-40-3'></a>
- **UC-22.40.3** — Periodic access review SLA — stale certifications by control owner
  - Control family: `privileged-session-recording`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.40.3.json`](../../content/cat-22-regulatory-compliance/UC-22.40.3.json)
<a id='uc-22-42-1'></a>
- **UC-22.42.1** — Unauthorized production change — no approved CR matches the observed change
  - Control family: `policy-to-control-traceability`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.42.1.json`](../../content/cat-22-regulatory-compliance/UC-22.42.1.json)
<a id='uc-22-45-3'></a>
- **UC-22.45.3** — Backup completeness — unprotected workloads with regulated data
  - Control family: `backup-restore-evidence`
  - Owner: `Head of IT Operations`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.45.3.json`](../../content/cat-22-regulatory-compliance/UC-22.45.3.json)
<a id='uc-22-47-2'></a>
- **UC-22.47.2** — Repeat audit findings — same control deficiency across consecutive audit cycles
  - Control family: `policy-to-control-traceability`
  - Owner: `Board / Audit Committee`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.47.2.json`](../../content/cat-22-regulatory-compliance/UC-22.47.2.json)
<a id='uc-22-48-1'></a>
- **UC-22.48.1** — Segregation of duties — toxic role combinations in IAM
  - Control family: `access-review-cadence`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.48.1.json`](../../content/cat-22-regulatory-compliance/UC-22.48.1.json)
<a id='uc-22-48-2'></a>
- **UC-22.48.2** — SoD violations via break-glass usage — emergency role abuse
  - Control family: `access-review-cadence`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.48.2.json`](../../content/cat-22-regulatory-compliance/UC-22.48.2.json)
<a id='uc-22-49-3'></a>
- **UC-22.49.3** — Litigation-hold override audit — holds applied/released without ticket
  - Control family: `retention-end-enforcement`
  - Owner: `Legal`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.49.3.json`](../../content/cat-22-regulatory-compliance/UC-22.49.3.json)
<a id='uc-22-6-55'></a>
- **UC-22.6.55** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-9-8'></a>
- **UC-22.9.8** — Compliance Trending — Auditor Evidence Pack Generation Volume and Deficiency Rate
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.9.8.json`](../../content/cat-22-regulatory-compliance/UC-22.9.8.json)
<a id='uc-5-13-45'></a>
- **UC-5.13.45** — Audit Log Activity Overview
  - Control family: `log-source-completeness`
  - Owner: `Head of IT Operations`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-05-network-infrastructure/UC-5.13.45.json`](../../content/cat-05-network-infrastructure/UC-5.13.45.json)
<a id='uc-5-13-46'></a>
- **UC-5.13.46** — Configuration Change Audit Trail
  - Control family: `log-source-completeness`
  - Owner: `Head of IT Operations`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-05-network-infrastructure/UC-5.13.46.json`](../../content/cat-05-network-infrastructure/UC-5.13.46.json)
<a id='uc-7-1-13'></a>
- **UC-7.1.13** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-7-1-21'></a>
- **UC-7.1.21** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-7-1-40'></a>
- **UC-7.1.40** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-9-5-15'></a>
- **UC-9.5.15** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)

## 5. Evidence collection

### 5.1 Common evidence sources

Auditors typically request the following records when examining this regulation:

- ERP / financial-system audit logs (SAP, Oracle Financials, Workday, NetSuite)
- Active Directory / IAM access logs for financial-system users
- Change-management / ticketing system records (ServiceNow, Jira)
- Privileged Access Management (PAM) vault and session records
- Database audit trails for financial-data tables
- Automated control-monitoring (ACM) tools
- DR/BCP test evidence
- Source-code repository commit/merge records for in-scope applications

### 5.2 Retention requirements

| Artifact | Retention | Legal basis |
|---|---|---|
| Audit work papers | 7 years | Sarbanes-Oxley §802(a); 18 USC §1520 |
| ITGC control-test evidence | 7 years | Sarbanes-Oxley §802(a); PCAOB AS 1215 |
| Change-management records for in-scope systems | 7 years | Sarbanes-Oxley §802(a) |
| Access-review evidence | 7 years | Sarbanes-Oxley §802(a) |
| Segregation-of-duties matrices and violation evidence | 7 years | Sarbanes-Oxley §802(a) |
| Disaster-recovery test evidence | 7 years | Sarbanes-Oxley §802(a) |

> Retention figures above are the legal minimums or regulator-stated expectations. Organisation-specific retention schedules may be longer where business, tax, litigation-hold, or contractual obligations apply. Where a figure conflicts with local data-protection law (e.g. GDPR Art.5(1)(e) storage-limitation principle), the shorter conformant period governs for personal-data content; the evidence-of-compliance retention retains the longer period for audit purposes, scrubbed of excess personal data.

### 5.3 Evidence integrity expectations

Regulators increasingly cite **evidence-integrity failures** as aggravating factors in enforcement actions. Cross-regulation baseline expectations:

- Time-stamped, tamper-evident storage (WORM, cryptographic chaining, or append-only indexes).
- Chain-of-custody for any evidence removed from the SIEM / production system for audit or legal purposes.
- Synchronised clocks (NTP stratum ≤ 3 or equivalent) across all in-scope sources so timeline reconstruction is defensible.
- Documented retention enforcement — not just retention policy — so that deletion is auditable.

See cat-22.35 "Evidence continuity and log integrity" for UCs that implement these controls.

## 6. Control testing procedures

AS 2201 uses a top-down, risk-based approach: identify the significant financial-reporting accounts, the relevant assertions, the business processes producing the balances, the IT systems supporting those processes, and finally the ITGCs needed. External auditors test design effectiveness (walkthroughs) and operating effectiveness (sampling, inquiry, observation, inspection, re-performance). Material weaknesses must be disclosed in the 10-K / 20-F filings; significant deficiencies are reported to the Audit Committee.

**Reporting cadence.** Annual §404(a) management attestation in Form 10-K (US domestic) or 20-F (foreign private issuer). §404(b) external audit report attached to the same filing for accelerated/large-accelerated filers. Quarterly §302 CEO/CFO certifications on Form 10-Q / 6-K. Audit Committee reports quarterly at minimum.

## 7. Roles and responsibilities

| Role | Responsibility |
|---|---|
| **Chief Executive Officer (CEO)** | Personally certifies financial reports under §302 and §906; certifies ICFR effectiveness under §404(a). |
| **Chief Financial Officer (CFO)** | Personally certifies financial reports under §302 and §906; co-attests ICFR under §404(a). |
| **Chief Information Officer (CIO)** | Accountable for ITGC design and operating effectiveness; commonly owns the control-design framework. |
| **Internal Audit** | Operates first line of internal attestation; tests ITGCs throughout the year. |
| **External Auditor (PCAOB-registered firm)** | Attests to ICFR effectiveness under AS 2201; tests ITGC design and operating effectiveness. |
| **Audit Committee** | Oversees external auditor; approves scope and non-audit services; recommends remediation. |
| **PCAOB** | Inspects registered auditors; issues enforcement findings and standards (AS 2201). |

## 8. Authoritative guidance

- **PCAOB AS 2201 Audit of Internal Control Over Financial Reporting** — PCAOB — [https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201](https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201)
- **COSO Internal Control — Integrated Framework (2013)** — COSO — [https://www.coso.org/Pages/ic.aspx](https://www.coso.org/Pages/ic.aspx)
- **COBIT 2019 / COBIT 5 (as ITGC framework)** — ISACA — [https://www.isaca.org/resources/cobit](https://www.isaca.org/resources/cobit)
- **SEC Commission Guidance Regarding Management's Report on Internal Control Over Financial Reporting** — SEC — [https://www.sec.gov/rules/interp/2007/33-8810.pdf](https://www.sec.gov/rules/interp/2007/33-8810.pdf)
- **PCAOB inspection reports** — PCAOB — [https://pcaobus.org/oversight/inspections](https://pcaobus.org/oversight/inspections)

## 9. Common audit deficiencies

Findings frequently cited by regulators, certification bodies, and external auditors for this regulation. These should be pre-tested as part of readiness reviews.

- Access-review evidence is obtained from the system rather than from a manager sign-off (system-generated but not reviewed).
- Segregation-of-duties violations are detected but compensating controls (e.g. monitoring) are not documented.
- Change-management bypass for emergency fixes is permitted but no post-implementation review (PIR) is performed.
- Privileged-access accounts (DBA, sysadmin) are in use but no session-recording or periodic access-review is performed.
- IT-dependent manual controls are tested as manual controls only; the underlying report's completeness and accuracy is not tested.
- SOC 1 Type 2 reports from subservice organisations are obtained but complementary user-entity controls (CUECs) are not tested.

## 10. Enforcement and penalties

§302 and §906 false certifications: up to USD 5 million fine + 20 years imprisonment (criminal). §1348 securities fraud: up to USD 5 million + 25 years. §1519 document destruction/alteration: up to USD 250,000 + 20 years. §802 work-paper retention failure: up to USD 10,000 + 10 years (individuals) / USD 500,000 (organisations). SEC civil enforcement: disgorgement, penalties, bars on serving as director/officer. Material-weakness disclosure carries no statutory penalty but typically destroys share value and can trigger shareholder litigation.

## 11. Pack gaps and remediation backlog

All clauses tracked in `data/regulations.json` for this regulation version are covered by at least one UC. **100 % common-clause coverage**. Remaining work is assurance-upgrade (for example, moving `contributing` entries to `partial` or `full` via explicit control tests) rather than new clause authoring.

## 12. Questions an auditor should ask

These are the questions a regulator, certification body, or external auditor is likely to ask. The pack helps preparers stage evidence and pre-test responses before the review opens.

- Produce the ITGC scoping memorandum: which systems have been identified as in-scope and why?
- Demonstrate user-access provisioning, modification, and de-provisioning for the last quarter — show approvals, effective dates, and termination timelines.
- Produce evidence of periodic access review (quarterly, minimum annually) for each in-scope system; show manager sign-offs.
- Show the segregation-of-duties analysis for the last 12 months; demonstrate how conflicts were detected and remediated.
- For the last five material changes to in-scope applications, produce: ticket, design review, UAT evidence, user acceptance, production-deployment authorisation, and post-deployment verification.
- Demonstrate change-management for infrastructure (OS patches, database upgrades) supporting in-scope systems.
- Produce the last DR/BCP test report for in-scope systems and demonstrate the recovery objectives were met.
- Show evidence of privileged-access monitoring for in-scope production systems.

## 13. Machine-readable twin

The machine-readable companion of this pack lives at [`api/v1/evidence-packs/sox-itgc.json`](../../api/v1/evidence-packs/sox-itgc.json). It contains the same clause-level coverage, retention guidance, role matrix, and gap list in JSON form, and is regenerated in lockstep with this markdown pack so content stays in sync. Consumers integrating the pack into GRC tools, audit-request portals, or evidence pipelines should consume the JSON document; human readers should consume this markdown.

Related API surfaces (all under [`api/v1/`](../../api/README.md)):

- [`api/v1/compliance/regulations/sox-itgc.json`](../../api/v1/compliance/regulations/sox-itgc.json) — regulation metadata and per-version coverage metrics
- [`api/v1/compliance/ucs/`](../../api/v1/compliance/ucs/index.json) — individual UC sidecars
- [`api/v1/compliance/coverage.json`](../../api/v1/compliance/coverage.json) — global coverage snapshot
- [`api/v1/compliance/gaps.json`](../../api/v1/compliance/gaps.json) — global gap report

## 14. Provenance and regeneration

This pack is **generated**, not hand-authored. Re-running the generator produces byte-identical output (deterministic sort, stable serialisation, no free-form timestamps outside the block below). CI enforces regeneration drift via `--check` mode.

**Inputs to this pack**

- [`data/regulations.json`](../../data/regulations.json) — commonClauses, priority weights, authoritative URLs
- [`data/evidence-pack-extras.json`](../../data/evidence-pack-extras.json) — retention, roles, authoritative guidance, penalty, testing approach
- [`content/cat-*/UC-*.json`](../../content) — UC sidecars containing compliance[] entries, controlFamily, owner, evidence fields
- [`api/v1/compliance/regulations/sox-itgc@*.json`](../../api/v1/compliance/regulations/) — pre-computed coverage metrics (when present)

- Generator: [`scripts/generate_evidence_packs.py`](../../scripts/generate_evidence_packs.py)
- Evidence-pack directory index: [`docs/evidence-packs/README.md`](README.md)

**Generation metadata**

```
catalogue_version: 8.1.0
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
