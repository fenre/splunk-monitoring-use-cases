# Evidence Pack — NCA OTCC

> **Tier**: Tier 2 &nbsp;·&nbsp; **Jurisdiction**: SA &nbsp;·&nbsp; **Version**: `1:2022`
>
> **Full name**: NCA Operational Technology Cybersecurity Controls
> **Authoritative source**: [https://nca.gov.sa/en/regulatory-documents/controls-list/3](https://nca.gov.sa/en/regulatory-documents/controls-list/3)
> **Effective from**: 2022-10-01

> This evidence pack is the auditor-facing view of the Splunk monitoring catalogue's coverage of the regulation. Every clause coverage claim is traceable to a specific UC sidecar JSON file (`content/cat-*/UC-*.json`); every retention figure cites its legal basis; every URL resolves to an official regulator or standards-body source. The pack does **not** assert legal conclusions — it tabulates what the catalogue covers, names the authoritative source, and flags gaps. Interpretation stays with counsel.

> **Live views.** [Buyer narrative (`compliance-story.html?reg=nca-otcc`)](../../compliance-story.html?reg=nca-otcc) · [Auditor clause navigator (`clause-navigator.html#reg=nca-otcc`)](../../clause-navigator.html#reg=nca-otcc) · [JSON twin (`api/v1/compliance/story/nca-otcc.json`)](../../api/v1/compliance/story/nca-otcc.json)

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

The NCA Operational Technology Cybersecurity Controls (OTCC-1:2022) is the Saudi National Cybersecurity Authority's binding framework for Operational Technology (OT) environments within Critical National Infrastructure (CNI). Published in October 2022, OTCC extends the NCA Essential Cybersecurity Controls (ECC-1:2018) into OT and applies to any organisation in the Kingdom that operates Industrial Control Systems (ICS), Distributed Control Systems (DCS), Supervisory Control and Data Acquisition (SCADA), Programmable Logic Controllers (PLC), Safety Instrumented Systems (SIS), or other OT components which, if disrupted, would affect national security, economic stability, social welfare, or the safety of citizens. OTCC contains 27 main controls across four domains: Governance, Defence, Resilience, and Third-Party. Compliance is mandatory; non-compliance can result in administrative sanctions, operational restrictions, and personal liability for accountable executives. NCA conducts on-site inspections and document-based supervision; significant incidents must be reported to the NCA Haseen portal within 24 hours of decision and final reports within 72 hours.

## 2. Scope and applicability

Applies to entities operating Critical National Infrastructure (CNI) OT in the Kingdom of Saudi Arabia: oil and gas (Saudi Aramco supply chain, NGL, refineries), petrochemicals (SABIC supply chain), electricity (SEC, ENOWA, NEOM), water (SWPC, NWC), and any other sector designated as critical by the NCA. Also applies to OT-engaging service providers, system integrators, and vendors with privileged access into KSA CNI OT environments regardless of country of registration.

**Territorial scope.** Kingdom of Saudi Arabia plus extraterritorial reach for any vendor, integrator, or service provider with privileged access into KSA CNI OT, irrespective of where the vendor is established. Data resulting from OT monitoring should remain within KSA boundaries unless the NCA has approved an exception.

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
| [`OTCC-1-2-1-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-1-2-1-1) | OT cybersecurity policy approval and communication | 1.0 | `partial` | [UC-22.51.1](#uc-22-51-1) |
| [`OTCC-1-5-1-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-1-5-1-1) | OT cybersecurity risk management | 1.0 | `partial` | [UC-22.51.2](#uc-22-51-2) |
| [`OTCC-1-7-1-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-1-7-1-1) | OT personnel cybersecurity awareness and training | 0.7 | `full` | [UC-22.51.25](#uc-22-51-25) |
| [`OTCC-1-9-1-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-1-9-1-1) | OT cybersecurity audits and reviews | 1.0 | `full` | [UC-22.51.27](#uc-22-51-27) |
| [`OTCC-2-1-1-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-1-1-1) | OT asset inventory and classification | 1.0 | `full` | [UC-22.51.3](#uc-22-51-3) |
| [`OTCC-2-2-1-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-2-1-1) | OT privileged access management | 1.0 | `full` | [UC-22.51.4](#uc-22-51-4) |
| [`OTCC-2-2-3-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-2-3-1) | Vendor and third-party remote access to OT | 1.0 | `full` | [UC-22.51.24](#uc-22-51-24) |
| [`OTCC-2-3-1-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-3-1-1) | OT system secure configuration baselines | 1.0 | `partial` | [UC-22.51.6](#uc-22-51-6) |
| [`OTCC-2-3-2-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-3-2-1) | OT change management | 1.0 | `full` | [UC-22.51.9](#uc-22-51-9) |
| [`OTCC-2-3-3-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-3-3-1) | OT malware protection | 1.0 | `full` | [UC-22.51.10](#uc-22-51-10) |
| [`OTCC-2-5-1-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-5-1-1) | Removable media controls on OT | 1.0 | `full` | [UC-22.51.11](#uc-22-51-11) |
| [`OTCC-2-5-2-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-5-2-1) | Wireless access controls on OT networks | 0.7 | `full` | [UC-22.51.12](#uc-22-51-12) |
| [`OTCC-2-5-3-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-5-3-1) | OT network segmentation and zone enforcement | 1.0 | `full` | [UC-22.51.5](#uc-22-51-5) |
| [`OTCC-2-8-1-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-8-1-1) | OT cryptographic controls and key management | 0.7 | `partial` | [UC-22.51.26](#uc-22-51-26) |
| [`OTCC-2-9-1-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-9-1-1) | OT backup integrity and recovery testing | 1.0 | `full` | [UC-22.51.22](#uc-22-51-22) |
| [`OTCC-2-10-1-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-10-1-1) | OT vulnerability assessment and management | 1.0 | `partial` | [UC-22.51.7](#uc-22-51-7) |
| [`OTCC-2-10-2-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-10-2-1) | OT patch management with safety validation | 1.0 | `full` | [UC-22.51.8](#uc-22-51-8) |
| [`OTCC-2-12-1-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-12-1-1) | OT event logging completeness and retention | 1.0 | `full` | [UC-22.51.13](#uc-22-51-13) |
| [`OTCC-2-12-2-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-12-2-1) | OT industrial protocol monitoring | 1.0 | `full` | [UC-22.51.14](#uc-22-51-14) |
| [`OTCC-2-12-3-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-12-3-1) | OT-tier phishing and email-borne threat detection | 0.7 | `partial` | [UC-22.51.15](#uc-22-51-15) |
| [`OTCC-2-13-1-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-13-1-1) | OT cybersecurity incident detection and classification | 1.0 | `full` | [UC-22.51.16](#uc-22-51-16) |
| [`OTCC-2-13-2-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-13-2-1) | OT cybersecurity incident reporting to NCA | 1.0 | `full` | [UC-22.51.17](#uc-22-51-17) |
| [`OTCC-2-14-1-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-14-1-1) | Physical access control to OT environments | 1.0 | `full` | [UC-22.51.18](#uc-22-51-18) |
| [`OTCC-2-15-1-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-15-1-1) | Safety Instrumented System (SIS) cybersecurity protection | 1.0 | `full` | [UC-22.51.19](#uc-22-51-19) |
| [`OTCC-3-1-1-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-3-1-1-1) | OT business continuity exercise programme | 1.0 | `full` | [UC-22.51.20](#uc-22-51-20) |
| [`OTCC-3-1-2-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-3-1-2-1) | OT recovery time and recovery point objectives | 0.7 | `full` | [UC-22.51.21](#uc-22-51-21) |
| [`OTCC-4-1-1-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-4-1-1-1) | Third-party and supply-chain cybersecurity assurance for OT | 1.0 | `full` | [UC-22.51.23](#uc-22-51-23) |
| [`OTCC-4-2-1-1`](https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-4-2-1-1) | OT cloud and hosting cybersecurity assurance | 0.7 | `full` | [UC-22.51.28](#uc-22-51-28) |

### 4.1 Contributing UC detail

<a id='uc-22-51-1'></a>
- **UC-22.51.1** — OT Cybersecurity Policy Approval, Publication, and Annual-Review Evidence
  - Control family: `policy-to-control-traceability`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.1.json`](../../content/cat-22-regulatory-compliance/UC-22.51.1.json)
<a id='uc-22-51-10'></a>
- **UC-22.51.10** — OT Malware Protection Coverage and Detection Evidence
  - Control family: `endpoint-protection`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.10.json`](../../content/cat-22-regulatory-compliance/UC-22.51.10.json)
<a id='uc-22-51-11'></a>
- **UC-22.51.11** — Removable Media Controls on OT Endpoints
  - Control family: `media-protection`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.11.json`](../../content/cat-22-regulatory-compliance/UC-22.51.11.json)
<a id='uc-22-51-12'></a>
- **UC-22.51.12** — Wireless Access Controls and Rogue-AP Detection on OT Networks
  - Control family: `wireless-control`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.12.json`](../../content/cat-22-regulatory-compliance/UC-22.51.12.json)
<a id='uc-22-51-13'></a>
- **UC-22.51.13** — OT Event Logging Completeness, Continuity, and Retention
  - Control family: `audit-logging`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.13.json`](../../content/cat-22-regulatory-compliance/UC-22.51.13.json)
<a id='uc-22-51-14'></a>
- **UC-22.51.14** — Industrial Protocol Monitoring: Unauthorised Function Codes and Anomalous Operations
  - Control family: `industrial-protocol`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.14.json`](../../content/cat-22-regulatory-compliance/UC-22.51.14.json)
<a id='uc-22-51-15'></a>
- **UC-22.51.15** — OT-Tier Phishing and Email-Borne Threat Detection
  - Control family: `anti-phishing`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.15.json`](../../content/cat-22-regulatory-compliance/UC-22.51.15.json)
<a id='uc-22-51-16'></a>
- **UC-22.51.16** — OT Cybersecurity Incident Detection and Classification
  - Control family: `incident-detection`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.16.json`](../../content/cat-22-regulatory-compliance/UC-22.51.16.json)
<a id='uc-22-51-17'></a>
- **UC-22.51.17** — OT Cybersecurity Incident Reporting to NCA: Deadline and Evidence Pack Tracking
  - Control family: `regulatory-reporting`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.17.json`](../../content/cat-22-regulatory-compliance/UC-22.51.17.json)
<a id='uc-22-51-18'></a>
- **UC-22.51.18** — Physical Access Control to OT Environments
  - Control family: `physical-access`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.18.json`](../../content/cat-22-regulatory-compliance/UC-22.51.18.json)
<a id='uc-22-51-19'></a>
- **UC-22.51.19** — Safety Instrumented System (SIS) Cybersecurity Protection
  - Control family: `safety-system`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.19.json`](../../content/cat-22-regulatory-compliance/UC-22.51.19.json)
<a id='uc-22-51-2'></a>
- **UC-22.51.2** — OT Cybersecurity Risk Register Staleness, Ownership, and Treatment Tracking
  - Control family: `policy-to-control-traceability`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.2.json`](../../content/cat-22-regulatory-compliance/UC-22.51.2.json)
<a id='uc-22-51-20'></a>
- **UC-22.51.20** — OT Business Continuity Exercise Programme Evidence
  - Control family: `resilience`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.20.json`](../../content/cat-22-regulatory-compliance/UC-22.51.20.json)
<a id='uc-22-51-21'></a>
- **UC-22.51.21** — OT Recovery Time and Recovery Point Objectives Evidence
  - Control family: `resilience`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.21.json`](../../content/cat-22-regulatory-compliance/UC-22.51.21.json)
<a id='uc-22-51-22'></a>
- **UC-22.51.22** — OT Backup Integrity and Recovery Testing Evidence
  - Control family: `backup`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.22.json`](../../content/cat-22-regulatory-compliance/UC-22.51.22.json)
<a id='uc-22-51-23'></a>
- **UC-22.51.23** — Third-Party and Supply-Chain Cybersecurity Assurance for OT
  - Control family: `third-party`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.23.json`](../../content/cat-22-regulatory-compliance/UC-22.51.23.json)
<a id='uc-22-51-24'></a>
- **UC-22.51.24** — Third-Party Remote Access to OT Environments
  - Control family: `remote-access`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.24.json`](../../content/cat-22-regulatory-compliance/UC-22.51.24.json)
<a id='uc-22-51-25'></a>
- **UC-22.51.25** — OT Cybersecurity Training and Awareness Compliance
  - Control family: `training`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.25.json`](../../content/cat-22-regulatory-compliance/UC-22.51.25.json)
<a id='uc-22-51-26'></a>
- **UC-22.51.26** — OT Cryptographic Controls and Key Management Evidence
  - Control family: `cryptography`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.26.json`](../../content/cat-22-regulatory-compliance/UC-22.51.26.json)
<a id='uc-22-51-27'></a>
- **UC-22.51.27** — OT Compliance Programme Posture and KPI Reporting
  - Control family: `governance`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.27.json`](../../content/cat-22-regulatory-compliance/UC-22.51.27.json)
<a id='uc-22-51-28'></a>
- **UC-22.51.28** — OT Cloud and Hosting Cybersecurity Assurance
  - Control family: `cloud`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.28.json`](../../content/cat-22-regulatory-compliance/UC-22.51.28.json)
<a id='uc-22-51-3'></a>
- **UC-22.51.3** — OT Asset Inventory Reconciliation: Discovered vs Registered (Cisco Cyber Vision<sup class="ref">[<a href="#ref-1">1</a>]</sup>)
  - Control family: `log-source-completeness`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.3.json`](../../content/cat-22-regulatory-compliance/UC-22.51.3.json)
<a id='uc-22-51-4'></a>
- **UC-22.51.4** — OT Privileged Session Activity: Out-of-Window, Unticketed, and Over-Scope Detection
  - Control family: `privileged-session-recording`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.4.json`](../../content/cat-22-regulatory-compliance/UC-22.51.4.json)
<a id='uc-22-51-5'></a>
- **UC-22.51.5** — OT Network Segmentation and Zone-Conduit Enforcement (Purdue Model)
  - Control family: `regulation-specific`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.5.json`](../../content/cat-22-regulatory-compliance/UC-22.51.5.json)
<a id='uc-22-51-6'></a>
- **UC-22.51.6** — OT System Configuration Baseline Drift Detection
  - Control family: `evidence-continuity`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.6.json`](../../content/cat-22-regulatory-compliance/UC-22.51.6.json)
<a id='uc-22-51-7'></a>
- **UC-22.51.7** — OT Vulnerability Management SLA and Coverage Tracking
  - Control family: `regulation-specific`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.7.json`](../../content/cat-22-regulatory-compliance/UC-22.51.7.json)
<a id='uc-22-51-8'></a>
- **UC-22.51.8** — OT Patch Deployment Evidence: Window, Validation, and Vendor Approval
  - Control family: `evidence-continuity`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.8.json`](../../content/cat-22-regulatory-compliance/UC-22.51.8.json)
<a id='uc-22-51-9'></a>
- **UC-22.51.9** — OT Change-Control Evidence Chain: Authorisation, Impact Assessment, Validation
  - Control family: `evidence-continuity`
  - Owner: `Head of OT Security`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.51.9.json`](../../content/cat-22-regulatory-compliance/UC-22.51.9.json)

## 5. Evidence collection

### 5.1 Common evidence sources

Auditors typically request the following records when examining this regulation:

- OT asset inventory (Cisco Cyber Vision, Claroty, Nozomi, Forescout, Microsoft Defender for IoT)
- OT identity and privileged access (CyberArk PSM, BeyondTrust PRA, Wallix Bastion, Senhasegura PAM, Microsoft Entra)
- OT secure-configuration baselines (Rockwell FactoryTalk AssetCentre, Schneider EcoStruxure System Backup, Siemens TIA Portal Project Backup)
- OT firewall and segmentation (Palo Alto Networks, Fortinet, Cisco ASA/Firepower, Check Point, Hirschmann, Tofino)
- OT vulnerability management (Tenable.ot, Nessus, Qualys, Rapid7, CISA KEV)
- OT event-stream logging (Windows Event Forwarding, syslog over Splunk Universal Forwarder, OT vendor diagnostic logs)
- Industrial protocol monitoring (Splunk Stream, Cisco Cyber Vision passive sensor, Claroty CTD)
- Physical access control (Genetec Security Center, Lenel OnGuard, Honeywell Pro-Watch, AMAG Symmetry)
- Safety Instrumented Systems (Schneider Triconex, Honeywell Safety Manager, Siemens SIMATIC Safety, ABB SafetyGuard, Emerson DeltaV SIS)
- Backup and restore (Commvault, Veeam, Dell EMC NetWorker, Veritas NetBackup, OT vendor backup tools)
- Change and incident management (ServiceNow, BMC Helix, Cherwell, Atlassian Jira Service Management)
- Training and awareness (KnowBe4, SANS, NINJIO, OpsCloud, internal LMS)

### 5.2 Retention requirements

| Artifact | Retention | Legal basis |
|---|---|---|
| OT cybersecurity policies, procedures, and approval records (OTCC-1-2-1-1) | Duration of operation + 5 years | NCA OTCC-1:2022 §1-2; aligns with NCA ECC §1-2 retention guidance |
| OT risk register and treatment evidence (OTCC-1-5-1-1) | Duration of operation + 5 years; on-going changes superseded but historical records retained | NCA OTCC-1:2022 §1-5 |
| OT personnel training and awareness records (OTCC-1-7-1-1) | Employment duration + 5 years | NCA OTCC-1:2022 §1-7 |
| OT internal audit and external assessment reports (OTCC-1-9-1-1) | 10 years from report issue date | NCA OTCC-1:2022 §1-9; SAMA Cyber Security Framework Annex retention guidance |
| OT event logs (firewall, identity, configuration, protocol monitoring, physical access) (OTCC-2-12-1-1) | Minimum 12 months online + 5 years archive | NCA OTCC-1:2022 §2-12; NCA ECC-1:2018 §2-12 retention guidance |
| OT cybersecurity incident records and NCA reports (OTCC-2-13-1-1, OTCC-2-13-2-1) | 10 years from incident closure | NCA OTCC-1:2022 §2-13; NCA incident reporting guidelines |
| Vendor remote-access session recordings (OTCC-2-2-3-1, OTCC-4-1-2-1) | 5 years from session end | NCA OTCC-1:2022 §2-2-3 and §4-1-2 |
| OT backup integrity and restore-test evidence (OTCC-2-9-1-1) | 5 years from test date | NCA OTCC-1:2022 §2-9 |
| OT business continuity exercise records (OTCC-3-1-1-1) | 10 years from exercise date | NCA OTCC-1:2022 §3-1; SAMA BCP guidance |

> Retention figures above are the legal minimums or regulator-stated expectations. Organisation-specific retention schedules may be longer where business, tax, litigation-hold, or contractual obligations apply. Where a figure conflicts with local data-protection law (e.g. GDPR<sup class="ref">[<a href="#ref-3">3</a>]</sup> Art.5(1)(e) storage-limitation principle), the shorter conformant period governs for personal-data content; the evidence-of-compliance retention retains the longer period for audit purposes, scrubbed of excess personal data.

### 5.3 Evidence integrity expectations

Regulators increasingly cite **evidence-integrity failures** as aggravating factors in enforcement actions. Cross-regulation baseline expectations:

- Time-stamped, tamper-evident storage (WORM, cryptographic chaining, or append-only indexes).
- Chain-of-custody for any evidence removed from the SIEM / production system for audit or legal purposes.
- Synchronised clocks (NTP stratum ≤ 3 or equivalent) across all in-scope sources so timeline reconstruction is defensible.
- Documented retention enforcement — not just retention policy — so that deletion is auditable.

See cat-22.35 "Evidence continuity and log integrity" for UCs that implement these controls.

## 6. Control testing procedures

Mandatory regulatory framework with on-site NCA inspections plus document-based supervision. The NCA inspector typically begins with the OT cybersecurity policy approval chain (OTCC-1-2), then walks the inventory (OTCC-2-1), privileged access (OTCC-2-2), incident records (OTCC-2-13), and the NCA Haseen submission trail. Independent external assessments are required at least every three years per OTCC-1-9-1-1; internal cybersecurity reviews must occur at least annually. Penetration testing of OT is encouraged but performed under strict change-control to avoid disturbing safe operation; passive observation and review of engineering controls is preferred where active testing is infeasible. Inspections may be planned or unannounced; an inspector may request live evidence on demand — the practical implication is that evidence must be continuously available rather than reconstructed annually.

**Reporting cadence.** OT cybersecurity policy review at minimum annually plus after every major change or incident (OTCC-1-2-1-1). Risk register review at minimum annually (OTCC-1-5-1-1). Internal audit at minimum annually (OTCC-1-9-1-1). External assessment at minimum every three years (OTCC-1-9-1-1). Incident reporting: a decision-to-report must be reached within 24 hours of incident detection; final report submitted to NCA Haseen portal within 72 hours of decision (OTCC-2-13-2-1). Annual self-assessment attestation submitted to the senior executive responsible for cybersecurity and retained for NCA inspection.

## 7. Roles and responsibilities

| Role | Responsibility |
|---|---|
| **Senior Executive Responsible for Cybersecurity (CISO or equivalent)** | Approves OT cybersecurity policies per OTCC-1-2; accountable to the NCA for compliance; signs the annual OT cybersecurity attestation. |
| **Head of OT Security** | Operational owner of the OT cybersecurity programme; ensures continuous control operation across OTCC domains 2 and 3; primary point of contact for the NCA inspector during audits. |
| **OT Cybersecurity Steering Committee** | Cross-functional governance body (CISO, Head of OT Security, OT Operations Director, Plant Manager, Procurement, HR, Legal); reviews OTCC posture quarterly; approves KPI thresholds, exceptions, and roadmap. |
| **OT Operations Director** | Accountable for safe and reliable operation of the OT environment; owns OT business continuity exercises, RTO/RPO targets, and process-recovery procedures. |
| **Plant Cybersecurity Champion (per site)** | Site-level operational liaison to the OT cybersecurity programme; coordinates physical and logical access reviews, change-control evidence collection, and incident response activation. |
| **National Cybersecurity Authority (NCA)** | Saudi national regulator; publishes OTCC; conducts inspections; receives incident reports via the Haseen portal; can issue corrective instructions and impose sanctions. |
| **Saudi Information Technology Company (SITE) and sector-specific regulators (e.g. SEC for electricity, SWPC for water)** | Supporting regulators that may require additional sector-specific notifications and certifications. |

## 8. Authoritative guidance

- **NCA Operational Technology Cybersecurity Controls (OTCC-1:2022) — control list portal** — National Cybersecurity Authority (NCA), Kingdom of Saudi Arabia — [https://nca.gov.sa/en/regulatory-documents/controls-list/3](https://nca.gov.sa/en/regulatory-documents/controls-list/3)
- **NCA Essential Cybersecurity Controls (ECC-1:2018)** — National Cybersecurity Authority (NCA), Kingdom of Saudi Arabia — [https://nca.gov.sa/en/regulatory-documents/controls-list/1](https://nca.gov.sa/en/regulatory-documents/controls-list/1)
- **NCA Haseen Incident Reporting Portal** — National Cybersecurity Authority (NCA), Kingdom of Saudi Arabia — [https://haseen.sa/](https://haseen.sa/)
- **NIST SP 800-82r3 — Guide to OT Security** — NIST — [https://csrc.nist.gov/publications/detail/sp/800-82/rev-3/final](https://csrc.nist.gov/publications/detail/sp/800-82/rev-3/final)
- **ISA/IEC 62443<sup class="ref">[<a href="#ref-6">6</a>]</sup> series** — ISA / IEC — [https://www.isa.org/standards-and-publications/isa-standards/isa-iec-62443-series-of-standards](https://www.isa.org/standards-and-publications/isa-standards/isa-iec-62443-series-of-standards)
- **CISA Industrial Control Systems recommended practices** — CISA — [https://www.cisa.gov/news-events/ics-recommended-practices](https://www.cisa.gov/news-events/ics-recommended-practices)

## 9. Common audit deficiencies

Findings frequently cited by regulators, certification bodies, and external auditors for this regulation. These should be pre-tested as part of readiness reviews.

- OT cybersecurity policy is approved but not communicated to all OT personnel; some plants operate from outdated local procedures (OTCC-1-2).
- OT asset inventory is paper-only or last reconciled more than 6 months ago; passive-discovery feeds present but not joined with engineering workstation registries (OTCC-2-1).
- Privileged session recording exists but coverage is incomplete: emergency break-glass accounts and shared OEM accounts bypass the PSM (OTCC-2-2-1).
- Vendor remote access enforced through PSM but Layer 3/4 enforcement is partial; some vendors retain direct connectivity to engineering workstations via vendor-installed cellular routers (OTCC-2-2-3 / OTCC-4-1-2).
- OT secure-configuration baselines exist but drift detection is run only quarterly; PLC programme changes from engineering workstations are not flagged in real time (OTCC-2-3-1).
- OT change-control evidence is fragmented: change ticket exists but post-change validation is informal; rollback plan is not produced on inspector demand (OTCC-2-3-2).
- Vulnerability management SLA is documented but coverage is incomplete: SIS and PLC firmware versions are not scanned because the vendor advises against active scanning; passive inventory not joined to CISA KEV (OTCC-2-10).
- OT event-stream logging is inconsistent across plants; some sites retain logs only 30 days due to local Splunk storage constraints (OTCC-2-12-1).
- Incident classification per OTCC-2-13 is performed manually after the fact; the 24h NCA decision and 72h Haseen submission clocks are missed during ambiguous incidents.
- Physical access into OT zones records entry but not egress for some zones; tailgating and anti-passback violations are detected but not investigated to closure (OTCC-2-14).
- Safety Instrumented Systems carry programme-mode keyswitches in cabinets without lock-out / tag-out integration; bypass events are recorded in diagnostics but not joined to management-of-change tickets (OTCC-2-15).
- OT business continuity exercises are documented as completed but observed RTO/RPO are not captured; the BIA target table is paper-only and not reconciled with exercise reality (OTCC-3-1).

## 10. Enforcement and penalties

OTCC compliance is mandatory under the NCA's enabling statutes. Non-compliance can result in: (a) NCA-issued corrective instructions with statutory deadlines; (b) administrative sanctions per the NCA's mandate including fines (specific amounts not publicly disclosed but reported in NCA enforcement actions); (c) operational restrictions or suspension of activities affecting national critical infrastructure; (d) personal accountability of the senior executive responsible for cybersecurity; (e) referral to other authorities including the Ministry of Interior and the Public Prosecution where the non-compliance constitutes a criminal offence or affects national security. CNI sectors face additional sector-specific consequences (e.g. operating-licence implications for electricity providers under the Saudi Electricity Regulatory Authority, water-supply licence implications under SWPC, refinery operating-permit implications).

## 11. Pack gaps and remediation backlog

All clauses tracked in `data/regulations.json` for this regulation version are covered by at least one UC. **100 % common-clause coverage**. Remaining work is assurance-upgrade (for example, moving `contributing` entries to `partial` or `full` via explicit control tests) rather than new clause authoring.

## 12. Questions an auditor should ask

These are the questions a regulator, certification body, or external auditor is likely to ask. The pack helps preparers stage evidence and pre-test responses before the review opens.

- Produce the OT cybersecurity policy approved by the senior executive responsible for cybersecurity per OTCC-1-2-1-1; show approval date and last review date, and demonstrate annual review plus post-major-change reviews.
- Produce the current OT risk register per OTCC-1-5-1-1 and demonstrate continuous monitoring; show treatment decisions for every risk with residual risk above defined tolerance.
- Produce the OT asset inventory per OTCC-2-1-1-1; demonstrate reconciliation with passive discovery (Cyber Vision or equivalent), engineering workstation registry, change tickets, and procurement records — show variance trend over the last 13 months.
- Produce the privileged-access policy and demonstrate every privileged session is recorded with full session-video or keystroke logging per OTCC-2-2-1-1; show 30 sample sessions with linked tickets and recordings.
- Demonstrate that vendor remote access per OTCC-2-2-3-1 / OTCC-4-1-2-1 traverses the centralised jump infrastructure, with MFA, change-ticket linkage, recording, and time-bound approval; show 30 vendor sessions over the last 90 days and their evidence chain.
- Produce the OT secure-configuration baselines per OTCC-2-3-1-1 and demonstrate continuous drift detection; show every baseline-drift event in the last 90 days and its disposition (remediated or formally accepted).
- Produce the OT change-control records per OTCC-2-3-2-1 with evidence of impact assessment, approval, implementation, post-change validation, and rollback plan for every change in the last 90 days.
- Demonstrate continuous OT vulnerability management per OTCC-2-10-1-1 with SLA evidence; show overdue vulnerabilities, risk-accepted vulnerabilities, and remediation timelines.
- Produce OT logging-completeness evidence per OTCC-2-12-1-1; demonstrate every asset class is producing logs into Splunk continuously with retention compliant with the NCA cadence.
- Produce industrial-protocol monitoring evidence per OTCC-2-12-2-1; show detection of unauthorised function codes, write operations from unapproved engineering workstations, or writes to forbidden register ranges.
- Produce OT incident records per OTCC-2-13-1-1; demonstrate classification, severity assignment, response timeline, and final closure; for each major incident demonstrate the 24h decision and 72h NCA Haseen submission per OTCC-2-13-2-1.
- Produce physical access control evidence per OTCC-2-14-1-1; demonstrate every entry to an OT-classified zone in the last 90 days against the access matrix and door-state.
- Produce SIS protection evidence per OTCC-2-15-1-1; demonstrate every bypass, programme-mode entry, and partial-stroke test against the management-of-change record.
- Produce OT business-continuity exercise evidence per OTCC-3-1-1-1; show observed RTO/RPO against targets per asset class per OTCC-3-1-2-1.
- Produce backup-integrity and restore-test evidence per OTCC-2-9-1-1; demonstrate immutable / off-site storage, cadence, and successful restore tests.
- Produce vendor assurance evidence per OTCC-4-1-1-1; for every OT-engaging vendor, demonstrate annual assessment, signed contractual security addendum, SBOM for software components, and breach-history monitoring.

## 13. Machine-readable twin

The machine-readable companion of this pack lives at [`api/v1/evidence-packs/nca-otcc.json`](../../api/v1/evidence-packs/nca-otcc.json). It contains the same clause-level coverage, retention guidance, role matrix, and gap list in JSON form, and is regenerated in lockstep with this markdown pack so content stays in sync. Consumers integrating the pack into GRC tools, audit-request portals, or evidence pipelines should consume the JSON document; human readers should consume this markdown.

Related API surfaces (all under [`api/v1/`](../../api/README.md)):

- [`api/v1/compliance/regulations/nca-otcc.json`](../../api/v1/compliance/regulations/nca-otcc.json) — regulation metadata and per-version coverage metrics
- [`api/v1/compliance/ucs/`](../../api/v1/compliance/ucs/index.json) — individual UC sidecars
- [`api/v1/compliance/coverage.json`](../../api/v1/compliance/coverage.json) — global coverage snapshot
- [`api/v1/compliance/gaps.json`](../../api/v1/compliance/gaps.json) — global gap report

## 14. Provenance and regeneration

This pack is **generated**, not hand-authored. Re-running the generator produces byte-identical output (deterministic sort, stable serialisation, no free-form timestamps outside the block below). CI enforces regeneration drift via `--check` mode.

**Inputs to this pack**

- [`data/regulations.json`](../../data/regulations.json) — commonClauses, priority weights, authoritative URLs
- [`data/evidence-pack-extras.json`](../../data/evidence-pack-extras.json) — retention, roles, authoritative guidance, penalty, testing approach
- [`content/cat-*/UC-*.json`](../../content) — UC sidecars containing compliance[] entries, controlFamily, owner, evidence fields
- [`api/v1/compliance/regulations/nca-otcc@*.json`](../../api/v1/compliance/regulations/) — pre-computed coverage metrics (when present)

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

<a id="ref-1"></a>**[1]** Cisco Systems, Inc. (2026). *Cisco Cyber Vision Documentation*. Retrieved May 11, 2026, from https://www.cisco.com/c/en/us/support/security/cyber-vision/series.html

<a id="ref-2"></a>**[2]** Cybersecurity and Infrastructure Security Agency. (2026). *CISA Known Exploited Vulnerabilities Catalog*. U.S. Department of Homeland Security. Retrieved May 11, 2026, from https://www.cisa.gov/known-exploited-vulnerabilities-catalog

<a id="ref-3"></a>**[3]** European Parliament and Council of the European Union. (2016, April). *Regulation (EU) 2016/679 — General Data Protection Regulation*. Official Journal of the European Union, L 119. ELI: reg/2016/679. https://eur-lex.europa.eu/eli/reg/2016/679/oj

<a id="ref-4"></a>**[4]** Fortinet, Inc. (2026). *Fortinet FortiOS Documentation*. Retrieved May 11, 2026, from https://docs.fortinet.com/product/fortigate

<a id="ref-5"></a>**[5]** Gerhards, R. (2009, March). *The Syslog Protocol*. Internet Engineering Task Force. RFC 5424. https://www.rfc-editor.org/rfc/rfc5424

<a id="ref-6"></a>**[6]** International Electrotechnical Commission. (2018). *IEC 62443 — Industrial communication networks — Network and system security*. IEC. https://webstore.iec.ch/en/publication/7029

<a id="ref-7"></a>**[7]** Palo Alto Networks, Inc. (2026). *Palo Alto Networks PAN-OS Documentation*. Retrieved May 11, 2026, from https://docs.paloaltonetworks.com/pan-os

<details>
<summary>Additional online sources cited in the document body (34)</summary>

<a id="ref-8"></a>**[8]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3

<a id="ref-9"></a>**[9]** nca.gov.sa. *nca.gov.sa: 1*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/1

<a id="ref-10"></a>**[10]** haseen.sa. *haseen.sa*. Retrieved May 11, 2026, from https://haseen.sa/

<a id="ref-11"></a>**[11]** csrc.nist.gov. *NIST: Final*. Retrieved May 11, 2026, from https://csrc.nist.gov/publications/detail/sp/800-82/rev-3/final

<a id="ref-12"></a>**[12]** isa.org. *isa.org: Isa Iec 62443 Series Of Standards*. Retrieved May 11, 2026, from https://www.isa.org/standards-and-publications/isa-standards/isa-iec-62443-series-of-standards

<a id="ref-13"></a>**[13]** cisa.gov. *CISA: Ics Recommended Practices*. Retrieved May 11, 2026, from https://www.cisa.gov/news-events/ics-recommended-practices

<a id="ref-14"></a>**[14]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-1-2-1-1

<a id="ref-15"></a>**[15]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-1-5-1-1

<a id="ref-16"></a>**[16]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-1-7-1-1

<a id="ref-17"></a>**[17]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-1-9-1-1

<a id="ref-18"></a>**[18]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-1-1-1

<a id="ref-19"></a>**[19]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-2-1-1

<a id="ref-20"></a>**[20]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-2-3-1

<a id="ref-21"></a>**[21]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-3-1-1

<a id="ref-22"></a>**[22]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-3-2-1

<a id="ref-23"></a>**[23]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-3-3-1

<a id="ref-24"></a>**[24]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-5-1-1

<a id="ref-25"></a>**[25]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-5-2-1

<a id="ref-26"></a>**[26]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-5-3-1

<a id="ref-27"></a>**[27]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-8-1-1

<a id="ref-28"></a>**[28]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-9-1-1

<a id="ref-29"></a>**[29]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-10-1-1

<a id="ref-30"></a>**[30]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-10-2-1

<a id="ref-31"></a>**[31]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-12-1-1

<a id="ref-32"></a>**[32]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-12-2-1

<a id="ref-33"></a>**[33]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-12-3-1

<a id="ref-34"></a>**[34]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-13-1-1

<a id="ref-35"></a>**[35]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-13-2-1

<a id="ref-36"></a>**[36]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-14-1-1

<a id="ref-37"></a>**[37]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-2-15-1-1

<a id="ref-38"></a>**[38]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-3-1-1-1

<a id="ref-39"></a>**[39]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-3-1-2-1

<a id="ref-40"></a>**[40]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-4-1-1-1

<a id="ref-41"></a>**[41]** nca.gov.sa. *nca.gov.sa: 3*. Retrieved May 11, 2026, from https://nca.gov.sa/en/regulatory-documents/controls-list/3#OTCC-4-2-1-1

</details>

<!-- END-AUTOGENERATED-SOURCES -->
