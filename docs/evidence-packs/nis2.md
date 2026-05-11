# Evidence Pack — NIS2

> **Tier**: Tier 1 &nbsp;·&nbsp; **Jurisdiction**: EU &nbsp;·&nbsp; **Version**: `Directive (EU) 2022/2555`
>
> **Full name**: EU NIS2 Directive
> **Authoritative source**: [https://eur-lex.europa.eu/eli/dir/2022/2555/oj](https://eur-lex.europa.eu/eli/dir/2022/2555/oj)
> **Effective from**: 2024-10-17

> This evidence pack is the auditor-facing view of the Splunk monitoring catalogue's coverage of the regulation. Every clause coverage claim is traceable to a specific UC sidecar JSON file (`content/cat-*/UC-*.json`); every retention figure cites its legal basis; every URL resolves to an official regulator or standards-body source. The pack does **not** assert legal conclusions — it tabulates what the catalogue covers, names the authoritative source, and flags gaps. Interpretation stays with counsel.

> **Live views.** [Buyer narrative (`compliance-story.html?reg=nis2`)](../../compliance-story.html?reg=nis2) · [Auditor clause navigator (`clause-navigator.html#reg=nis2`)](../../clause-navigator.html#reg=nis2) · [JSON twin (`api/v1/compliance/story/nis2.json`)](../../api/v1/compliance/story/nis2.json)

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

Network and Information Security Directive 2 (NIS2) is the EU cybersecurity directive that harmonises cybersecurity requirements for 'essential' and 'important' entities across 18 sectors (energy, transport, banking, healthcare, digital infrastructure, public administration, manufacturing, food, etc.). Member states had to transpose NIS2 into national law by 17 October 2024. Replaces NIS1 (Directive 2016/1148) with significantly expanded scope, stricter incident-reporting, management accountability, and harmonised fines.

## 2. Scope and applicability

Essential entities (EE) and important entities (IE) as defined in Annex I and Annex II of the directive. Scope is generally based on size (≥ medium enterprise under EU Recommendation 2003/361/EC) and sector. Non-medium or non-sector entities may still be in scope where member states designate them.

**Territorial scope.** EU member states; extraterritorial reach via Art.26 for third-country entities providing services into the EU.

## 3. Catalogue coverage at a glance

- **Clauses tracked**: 52
- **Clauses covered by at least one UC**: 52 / 52 (100.0%)
- **Priority-weighted coverage**: 100.0%
- **Contributing UCs**: 86

Coverage methodology is documented in [`docs/coverage-methodology.md`](../coverage-methodology.md). Priority weights come from `data/regulations.json` commonClauses entries (see [`data/regulations.json`](../../data/regulations.json) priorityWeightRubric).

## 4. Clause-by-clause coverage

Clauses are listed in the order defined by `data/regulations.json commonClauses` for this regulation version. A clause is considered covered when at least one UC sidecar has a `compliance[]` entry matching `(regulation, version, clause)`. Assurance is the maximum across contributing UCs.

| Clause | Topic | Priority | Assurance | UCs |
|---|---|---|---|---|
| [`Art.2`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.2) | Art.2 | 0.6 | `partial` | [UC-22.2.47](#uc-22-2-47) |
| [`Art.3`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.3) | Art.3 | 0.6 | `partial` | [UC-22.2.47](#uc-22-2-47) |
| [`Art.12`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.12) | Art.12 | 0.6 | `partial` | [UC-22.2.51](#uc-22-2-51) |
| [`Art.20`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.20) | Governance | 1.0 | `partial` | [UC-22.2.20](#uc-22-2-20), [UC-22.2.41](#uc-22-2-41), [UC-22.2.42](#uc-22-2-42), [UC-22.2.48](#uc-22-2-48) |
| [`Art.20(1)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.20(1)) | Art.20(1) | 1.0 | `partial` | [UC-22.2.48](#uc-22-2-48), [UC-22.2.57](#uc-22-2-57) |
| [`Art.20(2)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.20(2)) | Art.20(2) | 1.0 | `partial` | [UC-22.2.48](#uc-22-2-48) |
| [`Art.21(1)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.21(1)) | Art.21(1) | 1.0 | `partial` | [UC-22.2.48](#uc-22-2-48) |
| [`Art.21(2)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.21(2)) | Legacy NIS2 mapping already present in the catalogue | 1.0 | `contributing` | [UC-22.2.21](#uc-22-2-21), [UC-22.2.22](#uc-22-2-22), [UC-22.2.32](#uc-22-2-32) |
| [`Art.21(2)(a)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.21(2)(a)) | Risk analysis and information-system security policies | 1.0 | `partial` | [UC-22.2.18](#uc-22-2-18), [UC-22.2.26](#uc-22-2-26), [UC-22.2.36](#uc-22-2-36), [UC-22.2.37](#uc-22-2-37), [UC-22.2.56](#uc-22-2-56), [UC-22.2.6](#uc-22-2-6) |
| [`Art.21(2)(b)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.21(2)(b)) | Incident handling | 1.0 | `partial` | [UC-17.1.30](#uc-17-1-30), [UC-17.1.33](#uc-17-1-33), [UC-17.1.42](#uc-17-1-42), [UC-17.1.52](#uc-17-1-52), [UC-17.1.56](#uc-17-1-56), [UC-17.1.57](#uc-17-1-57) (+2 more) |
| [`Art.21(2)(c)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.21(2)(c)) | Business continuity and crisis management | 1.0 | `partial` | [UC-17.1.29](#uc-17-1-29), [UC-17.1.40](#uc-17-1-40), [UC-17.1.47](#uc-17-1-47), [UC-17.1.48](#uc-17-1-48), [UC-17.1.61](#uc-17-1-61), [UC-17.1.73](#uc-17-1-73) (+2 more) |
| [`Art.21(2)(d)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.21(2)(d)) | Supply-chain security | 1.0 | `full` | [UC-17.1.36](#uc-17-1-36), [UC-17.1.37](#uc-17-1-37), [UC-17.1.45](#uc-17-1-45), [UC-17.1.50](#uc-17-1-50), [UC-17.1.51](#uc-17-1-51), [UC-17.1.55](#uc-17-1-55) (+2 more) |
| [`Art.21(2)(e)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.21(2)(e)) | Security in acquisition, development and maintenance | 1.0 | `partial` | [UC-17.1.41](#uc-17-1-41), [UC-17.1.49](#uc-17-1-49), [UC-17.1.53](#uc-17-1-53), [UC-22.2.15](#uc-22-2-15), [UC-22.2.27](#uc-22-2-27), [UC-22.2.3](#uc-22-2-3) (+2 more) |
| [`Art.21(2)(f)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.21(2)(f)) | Policies and procedures effectiveness | 1.0 | `partial` | [UC-22.2.39](#uc-22-2-39), [UC-22.2.43](#uc-22-2-43), [UC-22.2.51](#uc-22-2-51), [UC-22.2.57](#uc-22-2-57), [UC-22.2.9](#uc-22-2-9) |
| [`Art.21(2)(g)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.21(2)(g)) | Cyber-hygiene and training | 1.0 | `full` | [UC-17.1.28](#uc-17-1-28), [UC-17.1.34](#uc-17-1-34), [UC-17.1.59](#uc-17-1-59), [UC-17.1.70](#uc-17-1-70), [UC-22.2.10](#uc-22-2-10), [UC-22.2.28](#uc-22-2-28) (+2 more) |
| [`Art.21(2)(h)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.21(2)(h)) | Cryptography and encryption | 1.0 | `full` | [UC-17.1.31](#uc-17-1-31), [UC-22.2.11](#uc-22-2-11), [UC-22.2.29](#uc-22-2-29), [UC-22.41.2](#uc-22-41-2) |
| [`Art.21(2)(i)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.21(2)(i)) | Human resources and access control | 1.0 | `partial` | [UC-22.2.13](#uc-22-2-13), [UC-22.2.14](#uc-22-2-14), [UC-22.2.30](#uc-22-2-30), [UC-22.2.5](#uc-22-2-5), [UC-22.2.52](#uc-22-2-52) |
| [`Art.21(2)(j)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.21(2)(j)) | MFA and secure communications | 1.0 | `partial` | [UC-17.1.38](#uc-17-1-38), [UC-17.1.44](#uc-17-1-44), [UC-17.1.46](#uc-17-1-46), [UC-22.2.12](#uc-22-2-12), [UC-22.2.46](#uc-22-2-46), [UC-22.2.52](#uc-22-2-52) |
| [`Art.21(3)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.21(3)) | Art.21(3) | 1.0 | `partial` | [UC-22.2.50](#uc-22-2-50) |
| [`Art.21(4)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.21(4)) | Art.21(4) | 1.0 | `partial` | [UC-22.2.48](#uc-22-2-48) |
| [`Art.21(5)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.21(5)) | Art.21(5) | 1.0 | `partial` | [UC-22.2.56](#uc-22-2-56) |
| [`Art.22`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.22) | Art.22 | 0.6 | `partial` | [UC-22.2.50](#uc-22-2-50) |
| [`Art.23`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.23) | Reporting obligations | 1.0 | `full` | [UC-22.2.1](#uc-22-2-1), [UC-22.2.33](#uc-22-2-33), [UC-22.2.45](#uc-22-2-45), [UC-22.2.49](#uc-22-2-49), [UC-22.3.44](#uc-22-3-44), [UC-22.39.1](#uc-22-39-1) (+2 more) |
| [`Art.23(1)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.23(1)) | Legacy NIS2 mapping already present in the catalogue | 1.0 | `partial` | [UC-22.2.49](#uc-22-2-49) |
| [`Art.23(2)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.23(2)) | Legacy NIS2 mapping already present in the catalogue | 1.0 | `partial` | [UC-22.2.49](#uc-22-2-49), [UC-22.2.7](#uc-22-2-7) |
| [`Art.23(3)(a)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.23(3)(a)) | Art.23(3)(a) | 1.0 | `partial` | [UC-22.2.49](#uc-22-2-49) |
| [`Art.23(3)(b)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.23(3)(b)) | Art.23(3)(b) | 1.0 | `partial` | [UC-22.2.49](#uc-22-2-49) |
| [`Art.23(4)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.23(4)) | NIS2 clause already mapped by a catalogue UC; retained for source traceability and no-gap validation. | 1.0 | `partial` | [UC-22.2.8](#uc-22-2-8) |
| [`Art.23(4)(a)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.23(4)(a)) | Art.23(4)(a) | 1.0 | `partial` | [UC-22.2.1](#uc-22-2-1), [UC-22.2.49](#uc-22-2-49) |
| [`Art.23(4)(b)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.23(4)(b)) | Art.23(4)(b) | 1.0 | `partial` | [UC-22.2.49](#uc-22-2-49) |
| [`Art.23(4)(c)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.23(4)(c)) | Art.23(4)(c) | 1.0 | `partial` | [UC-22.2.49](#uc-22-2-49) |
| [`Art.23(4)(d)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.23(4)(d)) | Art.23(4)(d) | 1.0 | `partial` | [UC-22.2.49](#uc-22-2-49) |
| [`Art.23(4)(e)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.23(4)(e)) | Art.23(4)(e) | 1.0 | `partial` | [UC-22.2.49](#uc-22-2-49) |
| [`Art.23(5)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.23(5)) | Art.23(5) | 1.0 | `contributing` | [UC-22.2.49](#uc-22-2-49) |
| [`Art.23(6)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.23(6)) | Art.23(6) | 1.0 | `contributing` | [UC-22.2.49](#uc-22-2-49) |
| [`Art.23(7)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.23(7)) | Art.23(7) | 1.0 | `contributing` | [UC-22.2.49](#uc-22-2-49) |
| [`Art.23(10)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.23(10)) | Art.23(10) | 1.0 | `contributing` | [UC-22.2.49](#uc-22-2-49) |
| [`Art.23(11)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.23(11)) | Art.23(11) | 1.0 | `contributing` | [UC-22.2.49](#uc-22-2-49) |
| [`Art.24`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.24) | Art.24 | 0.6 | `partial` | [UC-22.2.56](#uc-22-2-56) |
| [`Art.25`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.25) | Art.25 | 0.6 | `partial` | [UC-22.2.56](#uc-22-2-56) |
| [`Art.26`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.26) | Art.26 | 0.6 | `partial` | [UC-22.2.47](#uc-22-2-47) |
| [`Art.27`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.27) | Art.27 | 0.6 | `partial` | [UC-22.2.47](#uc-22-2-47) |
| [`Art.28`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.28) | Art.28 | 0.6 | `partial` | [UC-22.2.55](#uc-22-2-55) |
| [`Art.29`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.29) | Art.29 | 0.6 | `partial` | [UC-22.2.55](#uc-22-2-55) |
| [`Art.30`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.30) | Art.30 | 0.6 | `partial` | [UC-22.2.55](#uc-22-2-55) |
| [`Art.31`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.31) | Art.31 | 0.6 | `contributing` | [UC-22.2.54](#uc-22-2-54) |
| [`Art.32`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.32) | Legacy NIS2 mapping already present in the catalogue | 0.6 | `contributing` | [UC-22.2.35](#uc-22-2-35), [UC-22.2.54](#uc-22-2-54) |
| [`Art.33`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.33) | Legacy NIS2 mapping already present in the catalogue | 0.6 | `contributing` | [UC-22.2.35](#uc-22-2-35), [UC-22.2.54](#uc-22-2-54) |
| [`Art.34`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.34) | Art.34 | 0.6 | `contributing` | [UC-22.2.54](#uc-22-2-54) |
| [`Art.35`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.35) | Art.35 | 0.6 | `contributing` | [UC-22.2.54](#uc-22-2-54) |
| [`Annex I`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Annex I) | Annex I | 0.7 | `partial` | [UC-22.2.47](#uc-22-2-47) |
| [`Annex II`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Annex II) | Annex II | 0.7 | `partial` | [UC-22.2.47](#uc-22-2-47) |

### 4.1 Contributing UC detail

<a id='uc-17-1-28'></a>
- **UC-17.1.28** — Cisco ISE<sup class="ref">[<a href="#ref-2">2</a>]</sup> Deployment Replication Health and PSN Sync Lag
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
<a id='uc-17-1-31'></a>
- **UC-17.1.31** — Cisco ISE Certificate Expiry and Trust-Chain Health
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.31.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.31.json)
<a id='uc-17-1-33'></a>
- **UC-17.1.33** — Cisco ISE pxGrid Subscriber Connectivity and Topic Health
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.33.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.33.json)
<a id='uc-17-1-34'></a>
- **UC-17.1.34** — pxGrid Topic Throughput Anomaly and Subscriber Lag Detection
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.34.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.34.json)
<a id='uc-17-1-36'></a>
- **UC-17.1.36** — Cisco TrustSec / SGT Assignment Mismatch and SXP Listener Health
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.36.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.36.json)
<a id='uc-17-1-37'></a>
- **UC-17.1.37** — ISE-Cisco ACI / Cisco Secure Workload SGT Binding Synchronisation
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.37.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.37.json)
<a id='uc-17-1-38'></a>
- **UC-17.1.38** — EAP-TLS Client Certificate Failure and Trust-Chain Validation
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.38.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.38.json)
<a id='uc-17-1-40'></a>
- **UC-17.1.40** — RADIUS Authentication Latency SLO and Slow PSN Detection
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.40.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.40.json)
<a id='uc-17-1-41'></a>
- **UC-17.1.41** — Threat-Centric NAC (TC-NAC) — STIX/TAXII Feed and Auto-Quarantine Effectiveness
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.41.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.41.json)
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
<a id='uc-17-1-45'></a>
- **UC-17.1.45** — Cisco ISE PassiveID — WMI / AD Agent / Syslog Provider Health
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.45.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.45.json)
<a id='uc-17-1-46'></a>
- **UC-17.1.46** — Cisco Identity Intelligence (CII) Risk-Score Drift and Adaptive-Auth Triggering
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.46.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.46.json)
<a id='uc-17-1-47'></a>
- **UC-17.1.47** — Cisco ISE Backup Job Success and Operational-Data Backup Validation
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.47.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.47.json)
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
<a id='uc-17-1-50'></a>
- **UC-17.1.50** — Cisco ISE — MDM/UEM Connector Health and Compliance Drift
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.50.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.50.json)
<a id='uc-17-1-51'></a>
- **UC-17.1.51** — ISE Sponsor Portal — Sponsor Approval Latency and Approval-Pattern Anomalies
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.51.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.51.json)
<a id='uc-17-1-52'></a>
- **UC-17.1.52** — Self-Registration Portal Storm Detection and Bot-Onboarding Defense
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.52.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.52.json)
<a id='uc-17-1-53'></a>
- **UC-17.1.53** — Posture Remediation Funnel — Detection-to-Compliant Conversion Rate
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.53.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.53.json)
<a id='uc-17-1-55'></a>
- **UC-17.1.55** — Cisco ISE Profiler Probe Quality and Endpoint-Classification Coverage
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.55.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.55.json)
<a id='uc-17-1-56'></a>
- **UC-17.1.56** — ISE RADIUS Change-of-Authorization (CoA) Failure Detection
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.56.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.56.json)
<a id='uc-17-1-57'></a>
- **UC-17.1.57** — ISE ERS / OpenAPI Brute-Force, Token Theft, and Anomalous API-Caller Detection
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.57.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.57.json)
<a id='uc-17-1-59'></a>
- **UC-17.1.59** — Cisco ISE Logs through Splunk Edge Processor — Pipeline Health and Routing
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.59.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.59.json)
<a id='uc-17-1-61'></a>
- **UC-17.1.61** — ISE Multi-Site Topology — Cross-Site Replication Lag and WAN Loss Impact
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.61.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.61.json)
<a id='uc-17-1-66'></a>
- **UC-17.1.66** — Cisco AI Endpoint Analytics — IoT/OT Classification Confidence and New-Profile Discovery
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.66.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.66.json)
<a id='uc-17-1-67'></a>
- **UC-17.1.67** — Cisco AI Endpoint Behavioural (AEB) Profile-Drift and Behaviour-Anomaly Detection
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.67.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.67.json)
<a id='uc-17-1-68'></a>
- **UC-17.1.68** — ISE IoT/OT Device Onboarding — Profile Match and SGT Assignment Validation
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.68.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.68.json)
<a id='uc-17-1-70'></a>
- **UC-17.1.70** — OCSP Responder and CRL Repository Reachability and Latency Monitoring
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.70.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.70.json)
<a id='uc-17-1-73'></a>
- **UC-17.1.73** — Cisco WLC + ISE Wireless Authentication Funnel — Association → Auth → DHCP → Posture
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.73.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.73.json)
<a id='uc-17-1-77'></a>
- **UC-17.1.77** — Cisco ISE PSN Authentication-Per-Second (TPS) SLO and Capacity Headroom
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.77.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.77.json)
<a id='uc-17-1-80'></a>
- **UC-17.1.80** — ISE ANC Closed-Loop Effectiveness — Quarantine-to-Compromise-Stop Time
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-17-network-security-zero-trust/UC-17.1.80.json`](../../content/cat-17-network-security-zero-trust/UC-17.1.80.json)
<a id='uc-22-2-1'></a>
- **UC-22.2.1** — NIS2 Art.23(4)(a) — 24-Hour Early-Warning Notification Readiness
  - Control family: `ir-drill-evidence`
  - Owner: `Head of IR`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.1.json`](../../content/cat-22-regulatory-compliance/UC-22.2.1.json)
<a id='uc-22-2-10'></a>
- **UC-22.2.10** — NIS2 Cyber Hygiene and Training Compliance
  - Control family: `training-effectiveness`
  - Owner: `HR`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.10.json`](../../content/cat-22-regulatory-compliance/UC-22.2.10.json)
<a id='uc-22-2-11'></a>
- **UC-22.2.11** — NIS2 Cryptography and Encryption Policy Monitoring
  - Control family: `ir-drill-evidence`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.11.json`](../../content/cat-22-regulatory-compliance/UC-22.2.11.json)
<a id='uc-22-2-12'></a>
- **UC-22.2.12** — NIS2 Multi-Factor Authentication and Secure Communications
  - Control family: `access-review-cadence`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.12.json`](../../content/cat-22-regulatory-compliance/UC-22.2.12.json)
<a id='uc-22-2-13'></a>
- **UC-22.2.13** — NIS2 Asset Management and Configuration Baseline
  - Control family: `access-review-cadence`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.13.json`](../../content/cat-22-regulatory-compliance/UC-22.2.13.json)
<a id='uc-22-2-14'></a>
- **UC-22.2.14** — NIS2 Human Resources Security — Joiner/Mover/Leaver Process
  - Control family: `access-review-cadence`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.14.json`](../../content/cat-22-regulatory-compliance/UC-22.2.14.json)
<a id='uc-22-2-15'></a>
- **UC-22.2.15** — NIS2 Secure System Acquisition and Development Lifecycle
  - Control family: `evidence-continuity`
  - Owner: `Board / Audit Committee`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.15.json`](../../content/cat-22-regulatory-compliance/UC-22.2.15.json)
<a id='uc-22-2-17'></a>
- **UC-22.2.17** — NIS2 Backup Management and Disaster Recovery Verification
  - Control family: `backup-restore-evidence`
  - Owner: `Head of IT Operations`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.17.json`](../../content/cat-22-regulatory-compliance/UC-22.2.17.json)
<a id='uc-22-2-18'></a>
- **UC-22.2.18** — NIS2 Network Security Monitoring and Anomaly Detection
  - Control family: `log-source-completeness`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.18.json`](../../content/cat-22-regulatory-compliance/UC-22.2.18.json)
<a id='uc-22-2-20'></a>
- **UC-22.2.20** — NIS2 Management Body Accountability and Governance Evidence
  - Control family: `board-exec-reporting`
  - Owner: `Board / Audit Committee`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.20.json`](../../content/cat-22-regulatory-compliance/UC-22.2.20.json)
<a id='uc-22-2-21'></a>
- **UC-22.2.21** — NIS2 Risk Analysis Evidence for Essential Entities
  - Control family: `log-source-completeness`
  - Owner: `Board / Audit Committee`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.21.json`](../../content/cat-22-regulatory-compliance/UC-22.2.21.json)
<a id='uc-22-2-22'></a>
- **UC-22.2.22** — NIS2 Risk Analysis Evidence for Important Entities
  - Control family: `backup-restore-evidence`
  - Owner: `Head of IT Operations`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.22.json`](../../content/cat-22-regulatory-compliance/UC-22.2.22.json)
<a id='uc-22-2-26'></a>
- **UC-22.2.26** — NIS2 Network Security Monitoring Coverage by Segment
  - Control family: `regulation-specific`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.26.json`](../../content/cat-22-regulatory-compliance/UC-22.2.26.json)
<a id='uc-22-2-27'></a>
- **UC-22.2.27** — NIS2 Vulnerability Disclosure Policy Operational Signals
  - Control family: `ir-drill-evidence`
  - Owner: `Head of IR`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.27.json`](../../content/cat-22-regulatory-compliance/UC-22.2.27.json)
<a id='uc-22-2-28'></a>
- **UC-22.2.28** — NIS2 Cyber Hygiene Practices — Baseline Control Compliance
  - Control family: `break-glass-access`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.28.json`](../../content/cat-22-regulatory-compliance/UC-22.2.28.json)
<a id='uc-22-2-29'></a>
- **UC-22.2.29** — NIS2 Cryptography Policy Compliance — TLS and Certificate Posture
  - Control family: `crypto-drift`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.29.json`](../../content/cat-22-regulatory-compliance/UC-22.2.29.json)
<a id='uc-22-2-3'></a>
- **UC-22.2.3** — NIS2 Vulnerability Disclosure and Patch Management Tracking
  - Control family: `policy-to-control-traceability`
  - Owner: `Board / Audit Committee`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.3.json`](../../content/cat-22-regulatory-compliance/UC-22.2.3.json)
<a id='uc-22-2-30'></a>
- **UC-22.2.30** — NIS2 Human Resources Security Measures Evidence
  - Control family: `training-effectiveness`
  - Owner: `HR`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.30.json`](../../content/cat-22-regulatory-compliance/UC-22.2.30.json)
<a id='uc-22-2-32'></a>
- **UC-22.2.32** — NIS2 Proportional Security Measure Verification by Tier
  - Control family: `evidence-continuity`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.32.json`](../../content/cat-22-regulatory-compliance/UC-22.2.32.json)
<a id='uc-22-2-33'></a>
- **UC-22.2.33** — NIS2 Art.23 — Reporting Timeline Compliance Roll-Up (24h / 72h / 1-Month)
  - Control family: `ir-drill-evidence`
  - Owner: `Head of IR`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.33.json`](../../content/cat-22-regulatory-compliance/UC-22.2.33.json)
<a id='uc-22-2-35'></a>
- **UC-22.2.35** — NIS2 Supervisory Compliance Evidence Pack Readiness
  - Control family: `training-effectiveness`
  - Owner: `HR`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.35.json`](../../content/cat-22-regulatory-compliance/UC-22.2.35.json)
<a id='uc-22-2-36'></a>
- **UC-22.2.36** — NIS2 OT Network Segmentation Validation
  - Control family: `policy-to-control-traceability`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.36.json`](../../content/cat-22-regulatory-compliance/UC-22.2.36.json)
<a id='uc-22-2-37'></a>
- **UC-22.2.37** — NIS2 SCADA System Access Monitoring
  - Control family: `access-review-cadence`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.37.json`](../../content/cat-22-regulatory-compliance/UC-22.2.37.json)
<a id='uc-22-2-38'></a>
- **UC-22.2.38** — NIS2 Industrial Control System Patching and Change Evidence
  - Control family: `evidence-continuity`
  - Owner: `Board / Audit Committee`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.38.json`](../../content/cat-22-regulatory-compliance/UC-22.2.38.json)
<a id='uc-22-2-39'></a>
- **UC-22.2.39** — NIS2 OT Incident Detection — Process and Protocol Anomalies
  - Control family: `ir-drill-evidence`
  - Owner: `Head of IR`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.39.json`](../../content/cat-22-regulatory-compliance/UC-22.2.39.json)
<a id='uc-22-2-41'></a>
- **UC-22.2.41** — NIS2 Management Body Cybersecurity Training Evidence
  - Control family: `training-effectiveness`
  - Owner: `HR`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.41.json`](../../content/cat-22-regulatory-compliance/UC-22.2.41.json)
<a id='uc-22-2-42'></a>
- **UC-22.2.42** — NIS2 Board-Level Cyber Risk Reporting Distribution Audit
  - Control family: `board-exec-reporting`
  - Owner: `Head of IR`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.42.json`](../../content/cat-22-regulatory-compliance/UC-22.2.42.json)
<a id='uc-22-2-43'></a>
- **UC-22.2.43** — NIS2 Annual Security Assessment Completion Tracking
  - Control family: `ir-drill-evidence`
  - Owner: `Head of IR`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.43.json`](../../content/cat-22-regulatory-compliance/UC-22.2.43.json)
<a id='uc-22-2-45'></a>
- **UC-22.2.45** — NIS2 Art.23 — CSIRT Notification Channel Health and Delivery Confirmation
  - Control family: `ir-drill-evidence`
  - Owner: `Head of IR`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.45.json`](../../content/cat-22-regulatory-compliance/UC-22.2.45.json)
<a id='uc-22-2-46'></a>
- **UC-22.2.46** — NIS2 Art.21(2)(j) — Secure emergency communication channel verification
  - Control family: `break-glass-access`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.46.json`](../../content/cat-22-regulatory-compliance/UC-22.2.46.json)
<a id='uc-22-2-47'></a>
- **UC-22.2.47** — NIS2 Art.2/3/26/27 — Entity scope, registry and jurisdiction evidence
  - Control family: `policy-to-control-traceability`
  - Owner: `Legal`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.47.json`](../../content/cat-22-regulatory-compliance/UC-22.2.47.json)
<a id='uc-22-2-48'></a>
- **UC-22.2.48** — NIS2 Art.20/21 governance — Board approval, management training and risk acceptance evidence
  - Control family: `board-exec-reporting`
  - Owner: `Board / Audit Committee`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.48.json`](../../content/cat-22-regulatory-compliance/UC-22.2.48.json)
<a id='uc-22-2-49'></a>
- **UC-22.2.49** — NIS2 Art.23 — Significant Incident Reporting Package Completeness and Timeline Control
  - Control family: `ir-drill-evidence`
  - Owner: `Head of IR`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.49.json`](../../content/cat-22-regulatory-compliance/UC-22.2.49.json)
<a id='uc-22-2-5'></a>
- **UC-22.2.5** — NIS2 Network and Information Systems Access Control Audit
  - Control family: `access-review-cadence`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.5.json`](../../content/cat-22-regulatory-compliance/UC-22.2.5.json)
<a id='uc-22-2-50'></a>
- **UC-22.2.50** — NIS2 Art.21/22 — Critical supplier risk, SBOM exposure and vendor access monitoring
  - Control family: `third-party-activity`
  - Owner: `Procurement`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.50.json`](../../content/cat-22-regulatory-compliance/UC-22.2.50.json)
<a id='uc-22-2-51'></a>
- **UC-22.2.51** — NIS2 Art.12/21 secure development and vulnerability disclosure evidence
  - Control family: `policy-to-control-traceability`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.51.json`](../../content/cat-22-regulatory-compliance/UC-22.2.51.json)
<a id='uc-22-2-52'></a>
- **UC-22.2.52** — NIS2 Art.21 access, HR security, privileged accounts, MFA and secure communications evidence
  - Control family: `access-review-cadence`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.52.json`](../../content/cat-22-regulatory-compliance/UC-22.2.52.json)
<a id='uc-22-2-54'></a>
- **UC-22.2.54** — NIS2 Art.31-35 supervision, enforcement, fine exposure and GDPR<sup class="ref">[<a href="#ref-3">3</a>]</sup> coordination evidence
  - Control family: `evidence-continuity`
  - Owner: `Legal`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.54.json`](../../content/cat-22-regulatory-compliance/UC-22.2.54.json)
<a id='uc-22-2-55'></a>
- **UC-22.2.55** — NIS2 Art.28-30 domain registration, DNS integrity and information-sharing evidence
  - Control family: `log-source-completeness`
  - Owner: `Head of Platform`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.55.json`](../../content/cat-22-regulatory-compliance/UC-22.2.55.json)
<a id='uc-22-2-56'></a>
- **UC-22.2.56** — NIS2 evidence integrity, certification and standards crosswalk control
  - Control family: `evidence-continuity`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.56.json`](../../content/cat-22-regulatory-compliance/UC-22.2.56.json)
<a id='uc-22-2-57'></a>
- **UC-22.2.57** — NIS2 crawl/walk/run maturity and next-best-control benchmark dashboard
  - Control family: `policy-to-control-traceability`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.57.json`](../../content/cat-22-regulatory-compliance/UC-22.2.57.json)
<a id='uc-22-2-6'></a>
- **UC-22.2.6** — NIS2 Risk Analysis and Information System Security Policy Evidence
  - Control family: `policy-to-control-traceability`
  - Owner: `Board / Audit Committee`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.6.json`](../../content/cat-22-regulatory-compliance/UC-22.2.6.json)
<a id='uc-22-2-7'></a>
- **UC-22.2.7** — NIS2 Art.23(4)(b) — 72-Hour Incident Notification Readiness
  - Control family: `ir-drill-evidence`
  - Owner: `Head of IR`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.7.json`](../../content/cat-22-regulatory-compliance/UC-22.2.7.json)
<a id='uc-22-2-8'></a>
- **UC-22.2.8** — NIS2 Art.23(4)(d) — One-Month Final Incident Report Tracking
  - Control family: `ir-drill-evidence`
  - Owner: `Head of IR`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.8.json`](../../content/cat-22-regulatory-compliance/UC-22.2.8.json)
<a id='uc-22-2-9'></a>
- **UC-22.2.9** — NIS2 Effectiveness Assessment of Cybersecurity Measures
  - Control family: `training-effectiveness`
  - Owner: `HR`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.2.9.json`](../../content/cat-22-regulatory-compliance/UC-22.2.9.json)
<a id='uc-22-3-44'></a>
- **UC-22.3.44** — DORA<sup class="ref">[<a href="#ref-4">4</a>]</sup> Art.17 — ICT incident classification timeliness: major-incident clock evidence
  - Control family: `ir-drill-evidence`
  - Owner: `Head of IR`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.3.44.json`](../../content/cat-22-regulatory-compliance/UC-22.3.44.json)
<a id='uc-22-39-1'></a>
- **UC-22.39.1** — Multi-regulator breach-notification SLA tracker (24h NIS2 / 72h GDPR / 72h HIPAA<sup class="ref">[<a href="#ref-13">13</a>]</sup>)
  - Control family: `ir-drill-evidence`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.39.1.json`](../../content/cat-22-regulatory-compliance/UC-22.39.1.json)
<a id='uc-22-39-2'></a>
- **UC-22.39.2** — Regulator-portal submission evidence — one-way API acknowledgement audit
  - Control family: `ir-drill-evidence`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.39.2.json`](../../content/cat-22-regulatory-compliance/UC-22.39.2.json)
<a id='uc-22-41-2'></a>
- **UC-22.41.2** — Certificate / TLS posture — weak cipher and expired-cert detection
  - Control family: `crypto-drift`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.41.2.json`](../../content/cat-22-regulatory-compliance/UC-22.41.2.json)
<a id='uc-22-46-1'></a>
- **UC-22.46.1** — Mandatory security training — completion SLA by role
  - Control family: `training-effectiveness`
  - Owner: `HR`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.46.1.json`](../../content/cat-22-regulatory-compliance/UC-22.46.1.json)
<a id='uc-22-46-2'></a>
- **UC-22.46.2** — Phishing simulation efficacy — click-rate trend and repeat-clicker detection
  - Control family: `training-effectiveness`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.46.2.json`](../../content/cat-22-regulatory-compliance/UC-22.46.2.json)
<a id='uc-22-9-4'></a>
- **UC-22.9.4** — Regulatory Incident Response Time Trending
  - Control family: `regulation-specific`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.9.4.json`](../../content/cat-22-regulatory-compliance/UC-22.9.4.json)

## 5. Evidence collection

### 5.1 Common evidence sources

Auditors typically request the following records when examining this regulation:

- Risk-management framework documentation (policies, procedures, risk register)
- Incident-ticketing system output with severity classification and timelines
- Network-monitoring and EDR alert streams
- Business-continuity and disaster-recovery test records
- Supplier-risk-assessment records and ICT supply-chain attestations
- Security-awareness training records
- Governance-committee minutes with cybersecurity standing item
- Cryptographic policy and implementation evidence

### 5.2 Retention requirements

| Artifact | Retention | Legal basis |
|---|---|---|
| Incident-report records (Art.23) | 5 years minimum post-incident | NIS2 Art.23(3) + national implementing laws |
| Risk-management evidence (Art.21) | Duration of operation + 3 years | National implementing laws (e.g. Germany BSIG, Italy Decreto Legislativo 138/2024) |
| Governance-body records (Art.20 management oversight) | Duration of operation + 3 years | National implementing laws |
| Supply-chain security records (Art.21(2)(d)) | Duration of supplier relationship + 3 years | ENISA supply-chain guidance |
| Training evidence (Art.21(2)(g)) | Duration of employment + 3 years | National implementing laws |
| Incident-notification communications to CSIRT/competent authority | Minimum 5 years | NIS2 Art.23(4) early-warning / 24h, incident-notification / 72h, final-report / 1-month |

> Retention figures above are the legal minimums or regulator-stated expectations. Organisation-specific retention schedules may be longer where business, tax, litigation-hold, or contractual obligations apply. Where a figure conflicts with local data-protection law (e.g. GDPR Art.5(1)(e) storage-limitation principle), the shorter conformant period governs for personal-data content; the evidence-of-compliance retention retains the longer period for audit purposes, scrubbed of excess personal data.

### 5.3 Evidence integrity expectations

Regulators increasingly cite **evidence-integrity failures** as aggravating factors in enforcement actions. Cross-regulation baseline expectations:

- Time-stamped, tamper-evident storage (WORM, cryptographic chaining, or append-only indexes).
- Chain-of-custody for any evidence removed from the SIEM / production system for audit or legal purposes.
- Synchronised clocks (NTP stratum ≤ 3 or equivalent) across all in-scope sources so timeline reconstruction is defensible.
- Documented retention enforcement — not just retention policy — so that deletion is auditable.

See cat-22.35 "Evidence continuity and log integrity" for UCs that implement these controls.

## 6. Control testing procedures

National competent authorities conduct risk-based supervision: essential entities face ex-ante supervision (proactive audits, inspections, security scans), important entities face ex-post supervision (investigation after indicators of non-compliance). Inspections can include on-site security audits, penetration testing, compliance evidence reviews, and technical-control testing. Member states have defined administrative-penalty regimes following the harmonised minimum fines in Art.34. The expanded Splunk implementation adds a no-gap matrix test: each directive, implementing-regulation, ENISA evidence, national-guidance, and sector-overlay row must have a source URL, coverage decision, evidence artifact, owner, assurance rationale, and legal boundary. High-value searches should be tested with positive and negative fixtures before assurance is upgraded.

**Reporting cadence.** Incident reporting on a 24h/72h/1-month cadence; annual cybersecurity-risk-management reports to competent authority in many jurisdictions (national implementation varies). Registration and contact-point updates within 3 months of any material change.

## 7. Roles and responsibilities

| Role | Responsibility |
|---|---|
| **Management Bodies (Board / Executive)** | Art.20: must approve risk-management measures and oversee implementation; can be personally liable for systematic non-compliance. |
| **Competent Authority (CA)** | National body designated per member-state law; receives incident reports, imposes sanctions, conducts inspections. |
| **Computer Security Incident Response Team (CSIRT)** | National-level operational body; receives incident early-warnings and notifications. |
| **Single Point of Contact (SPoC)** | Each member state designates a SPoC to coordinate between CAs, CSIRTs, and cross-border cooperation under the Cooperation Group. |
| **ENISA** | EU Agency for Cybersecurity; maintains guidance, coordinates CSIRTs Network, develops European cybersecurity certification. |
| **European Commission** | Issues implementing acts (e.g. cybersecurity-incident notification thresholds under Art.23(11)). |

## 8. Authoritative guidance

- **Directive (EU) 2022/2555<sup class="ref">[<a href="#ref-1">1</a>]</sup> (NIS2)** — EU Council + Parliament — [https://eur-lex.europa.eu/eli/dir/2022/2555/oj](https://eur-lex.europa.eu/eli/dir/2022/2555/oj)
- **ENISA NIS2 Implementation Guidance** — ENISA — [https://www.enisa.europa.eu/topics/networks-and-information-systems-nis-directive](https://www.enisa.europa.eu/topics/networks-and-information-systems-nis-directive)
- **Commission Implementing Regulation 2024/2690 on technical and methodological requirements** — European Commission — [https://eur-lex.europa.eu/eli/reg_impl/2024/2690/oj](https://eur-lex.europa.eu/eli/reg_impl/2024/2690/oj)
- **National transposition trackers (e.g. Germany BSIG-E, Ireland NIS2 Bill 2024)** — Member state governments — [https://www.enisa.europa.eu/topics/networks-and-information-systems-nis-directive](https://www.enisa.europa.eu/topics/networks-and-information-systems-nis-directive)
- **ENISA NIS2 Technical Implementation Guidance** — ENISA — [https://www.enisa.europa.eu/publications/nis2-technical-implementation-guidance](https://www.enisa.europa.eu/publications/nis2-technical-implementation-guidance)
- **Ireland NCSC draft NIS2 Risk Management Measures Guidance** — Ireland NCSC — [https://www.ncsc.gov.ie/pdfs/NIS2_Risk_Management_Measures_Guidance.pdf](https://www.ncsc.gov.ie/pdfs/NIS2_Risk_Management_Measures_Guidance.pdf)

## 9. Common audit deficiencies

Findings frequently cited by regulators, certification bodies, and external auditors for this regulation. These should be pre-tested as part of readiness reviews.

- Scope misclassification — entity claims to be out of scope but operates in one of the Annex I/II sectors.
- Risk-management framework does not address all 10 domains of Art.21(2).
- Incident-notification timelines (24h, 72h, 1-month) are not demonstrable in tooling; evidence is reconstructed after the fact.
- Management-body oversight is delegated informally; no formal evidence of board-level approval of risk-management measures (Art.20(2) explicitly prohibits this).
- Supply-chain risk-assessments cover large suppliers only; SME suppliers with access to critical functions are excluded.
- Registration with national competent authority is incomplete or contact-point details are stale.

## 10. Enforcement and penalties

Art.34 minimum harmonised administrative fines: up to EUR 10 million or 2 % of worldwide annual turnover (whichever higher) for essential entities; up to EUR 7 million or 1.4 % for important entities. Additional corrective measures: binding instructions, orders to implement specific measures, temporary suspension of certification/authorisation, temporary prohibition from managerial functions (Art.32). Member states may impose stricter measures.

## 11. Pack gaps and remediation backlog

All clauses tracked in `data/regulations.json` for this regulation version are covered by at least one UC. **100 % common-clause coverage**. Remaining work is assurance-upgrade (for example, moving `contributing` entries to `partial` or `full` via explicit control tests) rather than new clause authoring.

## 12. Questions an auditor should ask

These are the questions a regulator, certification body, or external auditor is likely to ask. The pack helps preparers stage evidence and pre-test responses before the review opens.

- Demonstrate the designation decision: is the entity categorised as essential (EE) or important (IE)? What sector and sub-sector?
- Produce the risk-management framework per Art.21(2); show that it covers all 10 required domains (risk policy, incident handling, business continuity, supply chain, network security, vulnerability handling, effectiveness, cyber hygiene, cryptography, access-control and asset management).
- For the last 12 months of incidents, produce the Art.23 early-warning (24h), incident-notification (72h), and final-report (1-month) communications.
- Demonstrate management-body oversight per Art.20; produce evidence of management approval of risk-management measures.
- Produce the registration evidence with the competent authority (typical data: entity details, contact points, services in scope).
- Show supply-chain risk-management evidence per Art.21(2)(d); how are ICT suppliers categorised and monitored?
- For cross-border operations, identify the main-establishment member state and how jurisdictional responsibilities are allocated (Art.26).

## 13. Machine-readable twin

The machine-readable companion of this pack lives at [`api/v1/evidence-packs/nis2.json`](../../api/v1/evidence-packs/nis2.json). It contains the same clause-level coverage, retention guidance, role matrix, and gap list in JSON form, and is regenerated in lockstep with this markdown pack so content stays in sync. Consumers integrating the pack into GRC tools, audit-request portals, or evidence pipelines should consume the JSON document; human readers should consume this markdown.

Related API surfaces (all under [`api/v1/`](../../api/README.md)):

- [`api/v1/compliance/regulations/nis2.json`](../../api/v1/compliance/regulations/nis2.json) — regulation metadata and per-version coverage metrics
- [`api/v1/compliance/ucs/`](../../api/v1/compliance/ucs/index.json) — individual UC sidecars
- [`api/v1/compliance/coverage.json`](../../api/v1/compliance/coverage.json) — global coverage snapshot
- [`api/v1/compliance/gaps.json`](../../api/v1/compliance/gaps.json) — global gap report

## 14. Provenance and regeneration

This pack is **generated**, not hand-authored. Re-running the generator produces byte-identical output (deterministic sort, stable serialisation, no free-form timestamps outside the block below). CI enforces regeneration drift via `--check` mode.

**Inputs to this pack**

- [`data/regulations.json`](../../data/regulations.json) — commonClauses, priority weights, authoritative URLs
- [`data/evidence-pack-extras.json`](../../data/evidence-pack-extras.json) — retention, roles, authoritative guidance, penalty, testing approach
- [`content/cat-*/UC-*.json`](../../content) — UC sidecars containing compliance[] entries, controlFamily, owner, evidence fields
- [`api/v1/compliance/regulations/nis2@*.json`](../../api/v1/compliance/regulations/) — pre-computed coverage metrics (when present)

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

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Primary sources

<a id="ref-1"></a>**[1]** European Parliament and Council of the European Union. (2022, December). *Directive (EU) 2022/2555 — NIS2 Directive on cybersecurity*. Official Journal of the European Union, L 333. ELI: dir/2022/2555. https://eur-lex.europa.eu/eli/dir/2022/2555/oj

### Supporting sources

<a id="ref-2"></a>**[2]** Cisco Systems, Inc. (2026). *Cisco Identity Services Engine (ISE) Documentation*. Retrieved May 11, 2026, from https://www.cisco.com/c/en/us/support/security/identity-services-engine/series.html

<a id="ref-3"></a>**[3]** European Parliament and Council of the European Union. (2016, April). *Regulation (EU) 2016/679 — General Data Protection Regulation*. Official Journal of the European Union, L 119. ELI: reg/2016/679. https://eur-lex.europa.eu/eli/reg/2016/679/oj

<a id="ref-4"></a>**[4]** European Parliament and Council of the European Union. (2022, December). *Regulation (EU) 2022/2554 — Digital Operational Resilience Act (DORA)*. Official Journal of the European Union, L 333. ELI: reg/2022/2554. https://eur-lex.europa.eu/eli/reg/2022/2554/oj

<a id="ref-5"></a>**[5]** Gerhards, R. (2009, March). *The Syslog Protocol*. Internet Engineering Task Force. RFC 5424. https://www.rfc-editor.org/rfc/rfc5424

<a id="ref-6"></a>**[6]** International Electrotechnical Commission. (2018). *IEC 62443 — Industrial communication networks — Network and system security*. IEC. https://webstore.iec.ch/en/publication/7029

<a id="ref-7"></a>**[7]** International Organization for Standardization. (2022). *ISO/IEC 27001:2022 — Information security, cybersecurity and privacy protection — Information security management systems — Requirements*. ISO/IEC. ISO/IEC 27001:2022. https://www.iso.org/standard/27001

<a id="ref-8"></a>**[8]** MITRE Corporation. (2026). *MITRE ATT&CK Knowledge Base*. MITRE Engenuity. https://attack.mitre.org/

<a id="ref-9"></a>**[9]** National Institute of Standards and Technology. (2024). *Cybersecurity Framework (CSF) 2.0* (2.0). U.S. Department of Commerce. NIST CSWP 29. https://www.nist.gov/cyberframework

<a id="ref-10"></a>**[10]** Splunk Inc. (2026). *Splunk Enterprise Security Administration Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ES

<a id="ref-11"></a>**[11]** Splunk Inc. (2026). *Splunk IT Service Intelligence Administration Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ITSI

<a id="ref-12"></a>**[12]** U.S. Department of Health & Human Services. (2002). *HIPAA Privacy Rule (45 CFR Parts 160 and 164, Subparts A and E)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/privacy/index.html

<a id="ref-13"></a>**[13]** U.S. Department of Health & Human Services. (2013). *HIPAA Security Rule (45 CFR Parts 160 and 164, Subparts A and C)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/security/index.html

<details>
<summary>Additional online sources cited in the document body (4)</summary>

<a id="ref-14"></a>**[14]** enisa.europa.eu. *enisa.europa.eu: Networks And Information Systems Nis Directive*. Retrieved May 11, 2026, from https://www.enisa.europa.eu/topics/networks-and-information-systems-nis-directive

<a id="ref-15"></a>**[15]** eur-lex.europa.eu. *EUR-Lex: Oj*. Retrieved May 11, 2026, from https://eur-lex.europa.eu/eli/reg_impl/2024/2690/oj

<a id="ref-16"></a>**[16]** enisa.europa.eu. *enisa.europa.eu: Nis2 Technical Implementation Guidance*. Retrieved May 11, 2026, from https://www.enisa.europa.eu/publications/nis2-technical-implementation-guidance

<a id="ref-17"></a>**[17]** ncsc.gov.ie. *ncsc.gov.ie: Nis2 Risk Management Measures Guidance.Pdf*. Retrieved May 11, 2026, from https://www.ncsc.gov.ie/pdfs/NIS2_Risk_Management_Measures_Guidance.pdf

</details>

### Cited by

- [`docs/nis2-external-review-pack.md`](../nis2-external-review-pack.md)
- [`docs/nis2-maturity-benchmark.md`](../nis2-maturity-benchmark.md)
- [`docs/nis2-monitoring-methodology.md`](../nis2-monitoring-methodology.md)
- [`docs/research/nis2-source-map.md`](../research/nis2-source-map.md)

<!-- END-AUTOGENERATED-SOURCES -->
