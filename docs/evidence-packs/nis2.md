# Evidence Pack — NIS2

> **Tier**: Tier 1 &nbsp;·&nbsp; **Jurisdiction**: EU &nbsp;·&nbsp; **Version**: `Directive (EU) 2022/2555`
>
> **Full name**: EU NIS2 Directive
> **Authoritative source**: [https://eur-lex.europa.eu/eli/dir/2022/2555/oj](https://eur-lex.europa.eu/eli/dir/2022/2555/oj)
> **Effective from**: 2024-10-17

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

Network and Information Security Directive 2 (NIS2) is the EU cybersecurity directive that harmonises cybersecurity requirements for 'essential' and 'important' entities across 18 sectors (energy, transport, banking, healthcare, digital infrastructure, public administration, manufacturing, food, etc.). Member states had to transpose NIS2 into national law by 17 October 2024. Replaces NIS1 (Directive 2016/1148) with significantly expanded scope, stricter incident-reporting, management accountability, and harmonised fines.

## 2. Scope and applicability

Essential entities (EE) and important entities (IE) as defined in Annex I and Annex II of the directive. Scope is generally based on size (≥ medium enterprise under EU Recommendation 2003/361/EC) and sector. Non-medium or non-sector entities may still be in scope where member states designate them.

**Territorial scope.** EU member states; extraterritorial reach via Art.26 for third-country entities providing services into the EU.

## 3. Catalogue coverage at a glance

- **Clauses tracked**: 12
- **Clauses covered by at least one UC**: 12 / 12 (100.0%)
- **Priority-weighted coverage**: 100.0%
- **Contributing UCs**: 45

Coverage methodology is documented in [`docs/coverage-methodology.md`](../coverage-methodology.md). Priority weights come from `data/regulations.json` commonClauses entries (see [`data/regulations.json`](../../data/regulations.json) priorityWeightRubric).

## 4. Clause-by-clause coverage

Clauses are listed in the order defined by `data/regulations.json commonClauses` for this regulation version. A clause is considered covered when at least one UC sidecar has a `compliance[]` entry matching `(regulation, version, clause)`. Assurance is the maximum across contributing UCs.

| Clause | Topic | Priority | Assurance | UCs |
|---|---|---|---|---|
| [`Art.20`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.20) | Governance | 1.0 | `contributing` | [UC-22.2.20](#uc-22-2-20), [UC-22.2.41](#uc-22-2-41), [UC-22.2.42](#uc-22-2-42) |
| [`Art.21(2)(a)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.21(2)(a)) | Risk analysis and information-system security policies | 1.0 | `contributing` | [UC-22.2.18](#uc-22-2-18), [UC-22.2.26](#uc-22-2-26), [UC-22.2.36](#uc-22-2-36), [UC-22.2.37](#uc-22-2-37), [UC-22.2.6](#uc-22-2-6) |
| [`Art.21(2)(b)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.21(2)(b)) | Incident handling | 1.0 | `contributing` | [UC-22.2.23](#uc-22-2-23) |
| [`Art.21(2)(c)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.21(2)(c)) | Business continuity and crisis management | 1.0 | `contributing` | [UC-22.2.17](#uc-22-2-17), [UC-22.2.24](#uc-22-2-24), [UC-22.2.4](#uc-22-2-4), [UC-22.2.40](#uc-22-2-40) |
| [`Art.21(2)(d)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.21(2)(d)) | Supply-chain security | 1.0 | `full` | [UC-22.2.16](#uc-22-2-16), [UC-22.2.2](#uc-22-2-2), [UC-22.2.25](#uc-22-2-25), [UC-22.3.42](#uc-22-3-42), [UC-22.44.1](#uc-22-44-1) |
| [`Art.21(2)(e)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.21(2)(e)) | Security in acquisition, development and maintenance | 1.0 | `partial` | [UC-22.2.15](#uc-22-2-15), [UC-22.2.27](#uc-22-2-27), [UC-22.2.3](#uc-22-2-3), [UC-22.2.38](#uc-22-2-38), [UC-22.43.1](#uc-22-43-1) |
| [`Art.21(2)(f)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.21(2)(f)) | Policies and procedures effectiveness | 0.7 | `contributing` | [UC-22.2.39](#uc-22-2-39), [UC-22.2.43](#uc-22-2-43), [UC-22.2.9](#uc-22-2-9) |
| [`Art.21(2)(g)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.21(2)(g)) | Cyber-hygiene and training | 0.7 | `full` | [UC-22.2.10](#uc-22-2-10), [UC-22.2.28](#uc-22-2-28), [UC-22.46.1](#uc-22-46-1), [UC-22.46.2](#uc-22-46-2) |
| [`Art.21(2)(h)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.21(2)(h)) | Cryptography and encryption | 1.0 | `full` | [UC-22.2.11](#uc-22-2-11), [UC-22.2.29](#uc-22-2-29), [UC-22.41.2](#uc-22-41-2) |
| [`Art.21(2)(i)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.21(2)(i)) | Human resources and access control | 1.0 | `contributing` | [UC-22.2.13](#uc-22-2-13), [UC-22.2.14](#uc-22-2-14), [UC-22.2.30](#uc-22-2-30), [UC-22.2.5](#uc-22-2-5) |
| [`Art.21(2)(j)`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.21(2)(j)) | MFA and secure communications | 1.0 | `contributing` | [UC-22.2.12](#uc-22-2-12) |
| [`Art.23`](https://eur-lex.europa.eu/eli/dir/2022/2555/oj#Art.23) | Reporting obligations | 1.0 | `full` | [UC-22.2.1](#uc-22-2-1), [UC-22.2.33](#uc-22-2-33), [UC-22.2.45](#uc-22-2-45), [UC-22.3.44](#uc-22-3-44), [UC-22.39.1](#uc-22-39-1), [UC-22.39.2](#uc-22-39-2) (+1 more) |

### 4.1 Contributing UC detail

<a id='uc-22-2-1'></a>
- **UC-22.2.1** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-10'></a>
- **UC-22.2.10** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-11'></a>
- **UC-22.2.11** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-12'></a>
- **UC-22.2.12** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-13'></a>
- **UC-22.2.13** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-14'></a>
- **UC-22.2.14** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-15'></a>
- **UC-22.2.15** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-16'></a>
- **UC-22.2.16** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-17'></a>
- **UC-22.2.17** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-18'></a>
- **UC-22.2.18** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-2'></a>
- **UC-22.2.2** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-20'></a>
- **UC-22.2.20** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-23'></a>
- **UC-22.2.23** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-24'></a>
- **UC-22.2.24** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-25'></a>
- **UC-22.2.25** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-26'></a>
- **UC-22.2.26** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-27'></a>
- **UC-22.2.27** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-28'></a>
- **UC-22.2.28** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-29'></a>
- **UC-22.2.29** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-3'></a>
- **UC-22.2.3** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-30'></a>
- **UC-22.2.30** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-33'></a>
- **UC-22.2.33** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-36'></a>
- **UC-22.2.36** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-37'></a>
- **UC-22.2.37** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-38'></a>
- **UC-22.2.38** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-39'></a>
- **UC-22.2.39** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-4'></a>
- **UC-22.2.4** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-40'></a>
- **UC-22.2.40** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-41'></a>
- **UC-22.2.41** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-42'></a>
- **UC-22.2.42** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-43'></a>
- **UC-22.2.43** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-45'></a>
- **UC-22.2.45** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-5'></a>
- **UC-22.2.5** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-6'></a>
- **UC-22.2.6** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-2-9'></a>
- **UC-22.2.9** —
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
<a id='uc-22-3-44'></a>
- **UC-22.3.44** —
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
<a id='uc-22-39-2'></a>
- **UC-22.39.2** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-41-2'></a>
- **UC-22.41.2** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-43-1'></a>
- **UC-22.43.1** —
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
<a id='uc-22-46-1'></a>
- **UC-22.46.1** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-46-2'></a>
- **UC-22.46.2** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-9-4'></a>
- **UC-22.9.4** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)

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

National competent authorities conduct risk-based supervision: essential entities face ex-ante supervision (proactive audits, inspections, security scans), important entities face ex-post supervision (investigation after indicators of non-compliance). Inspections can include on-site security audits, penetration testing, compliance evidence reviews, and technical-control testing. Member states have defined administrative-penalty regimes following the harmonised minimum fines in Art.34.

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

- **Directive (EU) 2022/2555 (NIS2)** — EU Council + Parliament — [https://eur-lex.europa.eu/eli/dir/2022/2555/oj](https://eur-lex.europa.eu/eli/dir/2022/2555/oj)
- **ENISA NIS2 Implementation Guidance** — ENISA — [https://www.enisa.europa.eu/topics/networks-and-information-systems-nis-directive](https://www.enisa.europa.eu/topics/networks-and-information-systems-nis-directive)
- **Commission Implementing Regulation 2024/2690 on technical and methodological requirements** — European Commission — [https://eur-lex.europa.eu/eli/reg_impl/2024/2690/oj](https://eur-lex.europa.eu/eli/reg_impl/2024/2690/oj)
- **National transposition trackers (e.g. Germany BSIG-E, Ireland NIS2 Bill 2024)** — Member state governments — [https://www.enisa.europa.eu/topics/networks-and-information-systems-nis-directive](https://www.enisa.europa.eu/topics/networks-and-information-systems-nis-directive)

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
- [`use-cases/cat-*/uc-*.json`](../../use-cases) — UC sidecars containing compliance[] entries, controlFamily, owner, evidence fields
- [`api/v1/compliance/regulations/nis2@*.json`](../../api/v1/compliance/regulations/) — pre-computed coverage metrics (when present)

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
