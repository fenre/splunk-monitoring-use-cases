# Evidence Pack — UK GDPR

> **Tier**: Tier 2 &nbsp;·&nbsp; **Jurisdiction**: UK &nbsp;·&nbsp; **Version**: `post-Brexit`
>
> **Full name**: UK General Data Protection Regulation<sup class="ref">[<a href="#ref-2">2</a>]</sup>
> **Authoritative source**: [https://www.legislation.gov.uk/eur/2016/679/contents](https://www.legislation.gov.uk/eur/2016/679/contents)
> **Effective from**: 2021-01-01
> **Derived from**: `gdpr` (`identity` inheritance) — see Phase 3.3

> This evidence pack is the auditor-facing view of the Splunk monitoring catalogue's coverage of the regulation. Every clause coverage claim is traceable to a specific UC sidecar JSON file (`content/cat-*/UC-*.json`); every retention figure cites its legal basis; every URL resolves to an official regulator or standards-body source. The pack does **not** assert legal conclusions — it tabulates what the catalogue covers, names the authoritative source, and flags gaps. Interpretation stays with counsel.

> **Live views.** [Buyer narrative (`compliance-story.html?reg=uk-gdpr`)](../../compliance-story.html?reg=uk-gdpr) · [Auditor clause navigator (`clause-navigator.html#reg=uk-gdpr`)](../../clause-navigator.html#reg=uk-gdpr) · [JSON twin (`api/v1/compliance/story/uk-gdpr.json`)](../../api/v1/compliance/story/uk-gdpr.json)

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

UK GDPR is the United Kingdom's onshored version of Regulation (EU) 2016/679, adopted into domestic law under the European Union (Withdrawal) Act 2018 and amended by the Data Protection, Privacy and Electronic Communications (Amendments etc.) (EU Exit) Regulations 2019. It preserves the GDPR substantive regime intact while substituting UK bodies (ICO, UK government) for EU institutions. Sits alongside the Data Protection Act 2018<sup class="ref">[<a href="#ref-1">1</a>]</sup> which provides the UK's detailed implementation framework.

## 2. Scope and applicability

Applies to controllers and processors established in the UK and to those outside the UK who offer goods/services to UK residents or monitor their behaviour within the UK. The DPA 2018 Part 3 governs law enforcement processing; Part 4 governs intelligence-services processing.

**Territorial scope.** UK territorial scope plus extraterritorial reach under Art.3 of the retained Regulation.

## 3. Catalogue coverage at a glance

- **Clauses tracked**: 20
- **Clauses covered by at least one UC**: 15 / 20 (75.0%)
- **Priority-weighted coverage**: 76.3%
- **Contributing UCs**: 24
- **Derived via `derivesFrom`**: parent `gdpr` (mode `identity`). Identity-mode derivatives inherit the parent's full clause set unless explicitly diverged. This pack reports coverage against the **inherited parent clause inventory** so the auditor view is comparable to the parent. Inherited mappings carry assurance degraded one step from the parent and are marked `provenance: derived-from-parent` in the UC sidecar. Native hand-authored mappings take precedence. Known divergences are listed in `data/regulations.json derivesFrom[].divergences`.

Coverage methodology is documented in [`docs/coverage-methodology.md`](../coverage-methodology.md). Priority weights come from `data/regulations.json` commonClauses entries (see [`data/regulations.json`](../../data/regulations.json) priorityWeightRubric).

## 4. Clause-by-clause coverage

Because this regulation derives from `gdpr` with identity inheritance, the clause inventory below merges the parent's commonClauses (from `data/regulations.json`) with any divergent clauses the derivative explicitly redefines. A clause is considered covered when at least one UC sidecar has a `compliance[]` entry matching `(regulation, version, clause)`. Assurance is the maximum across contributing UCs.

| Clause | Topic | Priority | Assurance | UCs |
|---|---|---|---|---|
| [`Art.5`](https://www.legislation.gov.uk/eur/2016/679/article/Art.5) | Principles of processing | 1.0 | `partial` | [UC-22.49.1](#uc-22-49-1), [UC-22.49.2](#uc-22-49-2) |
| [`Art.6`](https://www.legislation.gov.uk/eur/2016/679/article/Art.6) | Lawful basis | 1.0 | `contributing` | [UC-22.37.1](#uc-22-37-1) |
| [`Art.7`](https://www.legislation.gov.uk/eur/2016/679/article/Art.7) | Conditions for consent | 0.7 | `partial` | [UC-22.1.5](#uc-22-1-5), [UC-22.37.1](#uc-22-37-1), [UC-22.37.2](#uc-22-37-2), [UC-22.8.39](#uc-22-8-39) |
| [`Art.15`](https://www.legislation.gov.uk/eur/2016/679/article/Art.15) | Right of access | 1.0 | `partial` | [UC-22.36.1](#uc-22-36-1) |
| [`Art.16`](https://www.legislation.gov.uk/eur/2016/679/article/Art.16) | Right to rectification | 0.7 | `—` | _not yet covered_ |
| [`Art.17`](https://www.legislation.gov.uk/eur/2016/679/article/Art.17) | Right to erasure | 1.0 | `partial` | [UC-22.36.2](#uc-22-36-2), [UC-22.49.5](#uc-22-49-5) |
| [`Art.18`](https://www.legislation.gov.uk/eur/2016/679/article/Art.18) | Right to restrict processing | 0.7 | `contributing` | [UC-22.1.16](#uc-22-1-16) |
| [`Art.20`](https://www.legislation.gov.uk/eur/2016/679/article/Art.20) | Right to data portability | 0.7 | `partial` | [UC-22.36.3](#uc-22-36-3) |
| [`Art.21`](https://www.legislation.gov.uk/eur/2016/679/article/Art.21) | Right to object | 0.7 | `contributing` | [UC-22.1.46](#uc-22-1-46) |
| [`Art.22`](https://www.legislation.gov.uk/eur/2016/679/article/Art.22) | Automated decision making | 0.7 | `—` | _not yet covered_ |
| [`Art.25`](https://www.legislation.gov.uk/eur/2016/679/article/Art.25) | Data protection by design and by default | 1.0 | `—` | _not yet covered_ |
| [`Art.28`](https://www.legislation.gov.uk/eur/2016/679/article/Art.28) | Processor obligations | 1.0 | `partial` | [UC-22.44.2](#uc-22-44-2) |
| [`Art.30`](https://www.legislation.gov.uk/eur/2016/679/article/Art.30) | Records of processing | 1.0 | `—` | _not yet covered_ |
| [`Art.32`](https://www.legislation.gov.uk/eur/2016/679/article/Art.32) | Security of processing | 1.0 | `partial` | [UC-22.35.2](#uc-22-35-2), [UC-22.35.3](#uc-22-35-3), [UC-22.41.1](#uc-22-41-1) |
| [`Art.33`](https://www.legislation.gov.uk/eur/2016/679/article/Art.33) | Breach notification to supervisory authority | 1.0 | `partial` | [UC-22.39.1](#uc-22-39-1), [UC-22.39.2](#uc-22-39-2) |
| [`Art.34`](https://www.legislation.gov.uk/eur/2016/679/article/Art.34) | Breach communication to data subjects | 1.0 | `partial` | [UC-22.39.3](#uc-22-39-3) |
| [`Art.35`](https://www.legislation.gov.uk/eur/2016/679/article/Art.35) | DPIA | 0.7 | `—` | _not yet covered_ |
| [`Art.44`](https://www.legislation.gov.uk/eur/2016/679/article/Art.44) | International transfers — general principle | 1.0 | `partial` | [UC-22.38.1](#uc-22-38-1), [UC-22.38.3](#uc-22-38-3), [UC-22.38.5](#uc-22-38-5) |
| [`Art.45`](https://www.legislation.gov.uk/eur/2016/679/article/Art.45) | Transfers via adequacy decision | 0.7 | `contributing` | [UC-22.38.2](#uc-22-38-2), [UC-22.38.5](#uc-22-38-5) |
| [`Art.46`](https://www.legislation.gov.uk/eur/2016/679/article/Art.46) | Transfers subject to safeguards | 0.7 | `full` | [UC-22.38.1](#uc-22-38-1), [UC-22.38.2](#uc-22-38-2), [UC-22.38.4](#uc-22-38-4) |

### 4.1 Contributing UC detail

<a id='uc-22-1-16'></a>
- **UC-22.1.16** — GDPR Consent Withdrawal Processing Enforcement
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.1.16.json`](../../content/cat-22-regulatory-compliance/UC-22.1.16.json)
<a id='uc-22-1-46'></a>
- **UC-22.1.46** — GDPR Consent Mechanism Audit (Lawful Basis Alignment)
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.1.46.json`](../../content/cat-22-regulatory-compliance/UC-22.1.46.json)
<a id='uc-22-1-5'></a>
- **UC-22.1.5** — GDPR Consent Management Audit Trail
  - Control family: `evidence-continuity`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 0
  - Source: [`content/cat-22-regulatory-compliance/UC-22.1.5.json`](../../content/cat-22-regulatory-compliance/UC-22.1.5.json)
<a id='uc-22-35-2'></a>
- **UC-22.35.2** — Log tamper detection via write-once-read-many chain-of-custody
  - Control family: `evidence-continuity`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.35.2.json`](../../content/cat-22-regulatory-compliance/UC-22.35.2.json)
<a id='uc-22-35-3'></a>
- **UC-22.35.3** — Indexer replication lag exposing evidence to single-point failure
  - Control family: `evidence-continuity`
  - Owner: `Head of Platform`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.35.3.json`](../../content/cat-22-regulatory-compliance/UC-22.35.3.json)
<a id='uc-22-36-1'></a>
- **UC-22.36.1** — DSAR fulfillment SLA tracker with verification evidence trail
  - Control family: `data-subject-request-lifecycle`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.36.1.json`](../../content/cat-22-regulatory-compliance/UC-22.36.1.json)
<a id='uc-22-36-2'></a>
- **UC-22.36.2** — Right-to-erasure propagation completeness across downstream systems
  - Control family: `data-subject-request-lifecycle`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.36.2.json`](../../content/cat-22-regulatory-compliance/UC-22.36.2.json)
<a id='uc-22-36-3'></a>
- **UC-22.36.3** — Portability export integrity — signed manifest verification
  - Control family: `data-subject-request-lifecycle`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.36.3.json`](../../content/cat-22-regulatory-compliance/UC-22.36.3.json)
<a id='uc-22-37-1'></a>
- **UC-22.37.1** — Consent capture evidence freshness — stale-consent alerting
  - Control family: `data-subject-request-lifecycle`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.37.1.json`](../../content/cat-22-regulatory-compliance/UC-22.37.1.json)
<a id='uc-22-37-2'></a>
- **UC-22.37.2** — Consent withdrawal propagation SLA — downstream stop-processing evidence
  - Control family: `data-subject-request-lifecycle`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.37.2.json`](../../content/cat-22-regulatory-compliance/UC-22.37.2.json)
<a id='uc-22-38-1'></a>
- **UC-22.38.1** — Cross-border personal-data flow anomaly — egress to unsanctioned jurisdictions
  - Control family: `data-flow-cross-border`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.38.1.json`](../../content/cat-22-regulatory-compliance/UC-22.38.1.json)
<a id='uc-22-38-2'></a>
- **UC-22.38.2** — SCC / adequacy decision reference freshness — stale-safeguard detector
  - Control family: `data-flow-cross-border`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.38.2.json`](../../content/cat-22-regulatory-compliance/UC-22.38.2.json)
<a id='uc-22-38-3'></a>
- **UC-22.38.3** — Data localization enforcement — regulated-data must-stay-in-region
  - Control family: `data-flow-cross-border`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.38.3.json`](../../content/cat-22-regulatory-compliance/UC-22.38.3.json)
<a id='uc-22-38-4'></a>
- **UC-22.38.4** — Transfer Impact Assessment currency — stale Schrems II assessments
  - Control family: `data-flow-cross-border`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.38.4.json`](../../content/cat-22-regulatory-compliance/UC-22.38.4.json)
<a id='uc-22-38-5'></a>
- **UC-22.38.5** — Bulk regulated-data export targeting non-adequate jurisdiction
  - Control family: `data-flow-cross-border`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.38.5.json`](../../content/cat-22-regulatory-compliance/UC-22.38.5.json)
<a id='uc-22-39-1'></a>
- **UC-22.39.1** — Multi-regulator breach-notification SLA tracker (24h NIS2<sup class="ref">[<a href="#ref-4">4</a>]</sup> / 72h GDPR / 72h HIPAA<sup class="ref">[<a href="#ref-12">12</a>]</sup>)
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
<a id='uc-22-39-3'></a>
- **UC-22.39.3** — Data-subject breach communication timeline tracker (Art.34 / §164.404)
  - Control family: `ir-drill-evidence`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.39.3.json`](../../content/cat-22-regulatory-compliance/UC-22.39.3.json)
<a id='uc-22-41-1'></a>
- **UC-22.41.1** — Encryption-at-rest coverage gap — unencrypted storage with regulated data
  - Control family: `crypto-drift`
  - Owner: `CISO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.41.1.json`](../../content/cat-22-regulatory-compliance/UC-22.41.1.json)
<a id='uc-22-44-2'></a>
- **UC-22.44.2** — Subprocessor inventory change — notification SLA to data controllers
  - Control family: `third-party-activity`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.44.2.json`](../../content/cat-22-regulatory-compliance/UC-22.44.2.json)
<a id='uc-22-49-1'></a>
- **UC-22.49.1** — Retention execution evidence — records past retention still present
  - Control family: `retention-end-enforcement`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.49.1.json`](../../content/cat-22-regulatory-compliance/UC-22.49.1.json)
<a id='uc-22-49-2'></a>
- **UC-22.49.2** — Disposal workflow completion — failed disposals requiring manual review
  - Control family: `retention-end-enforcement`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.49.2.json`](../../content/cat-22-regulatory-compliance/UC-22.49.2.json)
<a id='uc-22-49-5'></a>
- **UC-22.49.5** — Cryptographic erasure attestation — per-asset destruction evidence
  - Control family: `retention-end-enforcement`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.49.5.json`](../../content/cat-22-regulatory-compliance/UC-22.49.5.json)
<a id='uc-22-8-39'></a>
- **UC-22.8.39** — SOC 2<sup class="ref">[<a href="#ref-3">3</a>]</sup> P1.1 — Privacy notice: consent-record freshness for privacy-notice version changes
  - Control family: `data-subject-request-lifecycle`
  - Owner: `DPO`
  - Evidence fields declared in sidecar: 1
  - Source: [`content/cat-22-regulatory-compliance/UC-22.8.39.json`](../../content/cat-22-regulatory-compliance/UC-22.8.39.json)

## 5. Evidence collection

### 5.1 Common evidence sources

Auditors typically request the following records when examining this regulation:

- Same as GDPR, plus UK-specific entries:
- PECR (Privacy and Electronic Communications Regulations) direct-marketing consent logs
- ICO self-assessment tool outputs (ICO publishes structured self-assessment workbooks)
- UK Cyber Essentials<sup class="ref">[<a href="#ref-7">7</a>]</sup> / Cyber Essentials Plus certification evidence (often bundled with UK GDPR assurance)
- NCSC (National Cyber Security Centre) incident-reporting records where a breach involves critical national infrastructure

### 5.2 Retention requirements

| Artifact | Retention | Legal basis |
|---|---|---|
| Article 30 records of processing | Duration of processing + 6 years | ICO Accountability Framework; DPA 2018 s.61 |
| Breach-notification records | 6 years minimum | ICO breach-reporting guidance |
| Data-subject request logs | 6 years post-closure | ICO retention schedule |
| Direct-marketing consent logs | 24 months minimum; 6 years recommended | PECR enforcement notices |
| International-transfer evidence | Duration of transfer + 6 years | ICO International Data Transfer Agreement (IDTA) guidance |
| DPIA documentation | Duration of processing + 6 years | ICO DPIA guidance |

> Retention figures above are the legal minimums or regulator-stated expectations. Organisation-specific retention schedules may be longer where business, tax, litigation-hold, or contractual obligations apply. Where a figure conflicts with local data-protection law (e.g. GDPR Art.5(1)(e) storage-limitation principle), the shorter conformant period governs for personal-data content; the evidence-of-compliance retention retains the longer period for audit purposes, scrubbed of excess personal data.

### 5.3 Evidence integrity expectations

Regulators increasingly cite **evidence-integrity failures** as aggravating factors in enforcement actions. Cross-regulation baseline expectations:

- Time-stamped, tamper-evident storage (WORM, cryptographic chaining, or append-only indexes).
- Chain-of-custody for any evidence removed from the SIEM / production system for audit or legal purposes.
- Synchronised clocks (NTP stratum ≤ 3 or equivalent) across all in-scope sources so timeline reconstruction is defensible.
- Documented retention enforcement — not just retention policy — so that deletion is auditable.

See cat-22.35 "Evidence continuity and log integrity" for UCs that implement these controls.

## 6. Control testing procedures

ICO exercises enforcement primarily through monetary-penalty notices (up to GBP 17.5 million or 4 % of worldwide turnover), enforcement notices, and assessment notices. External auditors typically align UK GDPR testing with ISO 27001<sup class="ref">[<a href="#ref-5">5</a>]</sup>, Cyber Essentials Plus, or ISAE 3000 assurance engagements. Unlike GDPR, UK regulators have been explicit that contemporaneous evidence of the detection-to-notification timeline will be scrutinised in any Art.33 enforcement review.

**Reporting cadence.** No mandatory certification cycle. Most organisations run an annual DPIA review cycle, a quarterly breach-drill, and continuous Article 30 updates. Cyber Essentials Plus re-certification is annual and is a common proxy for UK GDPR Art.32 technical-controls assurance.

## 7. Roles and responsibilities

| Role | Responsibility |
|---|---|
| **Data Controller** | Same as GDPR Art.4(7); accountable under ICO enforcement. |
| **Data Processor** | Same as GDPR Art.4(8); Art.28 agreements required. |
| **Data Protection Officer (DPO)** | Same obligations as GDPR Arts.37-39; ICO registration may be required for certain activities. |
| **Representative in the UK** | Non-UK controllers under Art.3(2) of retained Regulation must appoint a UK representative (Art.27). |
| **Information Commissioner's Office (ICO)** | UK's independent supervisory authority; investigation, enforcement, and adequacy monitoring powers. |

## 8. Authoritative guidance

- **ICO Guide to the UK GDPR** — ICO — [https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/)
- **ICO Accountability Framework** — ICO — [https://ico.org.uk/for-organisations/accountability-framework/](https://ico.org.uk/for-organisations/accountability-framework/)
- **ICO International Data Transfer Agreement (IDTA)** — ICO — [https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/international-data-transfer-agreement-and-guidance/](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/international-data-transfer-agreement-and-guidance/)
- **DCMS UK GDPR reform consultation outcomes** — DCMS — [https://www.gov.uk/government/consultations/data-a-new-direction](https://www.gov.uk/government/consultations/data-a-new-direction)
- **Data (Use and Access) Act 2025 amendments tracker** — UK Government — [https://www.legislation.gov.uk/ukpga/2025](https://www.legislation.gov.uk/ukpga/2025)

## 9. Common audit deficiencies

Findings frequently cited by regulators, certification bodies, and external auditors for this regulation. These should be pre-tested as part of readiness reviews.

- Organisation has retained EU-style SCCs post-21 March 2024 without replacing them with IDTAs or UK Addendums.
- Breach-notification workflow still escalates to an EU SA rather than (or in addition to) ICO.
- PECR and UK GDPR treated as one regime; direct-marketing consent evidence does not meet the stricter PECR standard.
- ICO Accountability Framework gap-assessment is not completed or is stale.
- ROPA has not been updated to reflect ICO determinations or Data (Use and Access) Act 2025 amendments.

## 10. Enforcement and penalties

Same tiered structure as GDPR translated into sterling: up to GBP 8.7 million or 2 % of worldwide annual turnover for lower tier, up to GBP 17.5 million or 4 % for upper tier. ICO has imposed fines exceeding GBP 10 million (British Airways, Marriott, Clearview AI). Civil claims under s.168 DPA 2018 allow compensation for material and non-material damage.

## 11. Pack gaps and remediation backlog

Clauses tracked in `data/regulations.json` that are **not yet covered** by any UC in this catalogue are listed below. These are the backlog items for the next release. Priority order follows priorityWeight.

| Clause | Topic | Priority |
|---|---|---|
| `Art.25` | Data protection by design and by default | 1.0 |
| `Art.30` | Records of processing | 1.0 |
| `Art.16` | Right to rectification | 0.7 |
| `Art.22` | Automated decision making | 0.7 |
| `Art.35` | DPIA | 0.7 |

## 12. Questions an auditor should ask

These are the questions a regulator, certification body, or external auditor is likely to ask. The pack helps preparers stage evidence and pre-test responses before the review opens.

- Does your UK GDPR processing inventory distinguish UK residents from EU residents (since post-Brexit transfers between UK and EU rely on UK adequacy decision 2021/2151)?
- Where are the International Data Transfer Agreements (IDTAs) or UK Addendums to EU SCCs stored, and how do you track re-authorisation?
- Has your Representative in the UK (Art.27 of retained Regulation) been updated since January 2021?
- Does your breach-notification playbook explicitly cite the ICO (not an EU SA) as the primary notification destination?
- Has your organisation subscribed to ICO enforcement-action updates so it tracks newly issued guidance (ICO issues ~6 significant determinations per year)?
- For cross-border processing, does the lead supervisory authority under the one-stop-shop align with current UK GDPR territorial reach?
- Are your data-subject-request response templates citing UK domestic legal exemptions (DPA 2018 Sch.2-4) rather than EU derogations?

## 13. Machine-readable twin

The machine-readable companion of this pack lives at [`api/v1/evidence-packs/uk-gdpr.json`](../../api/v1/evidence-packs/uk-gdpr.json). It contains the same clause-level coverage, retention guidance, role matrix, and gap list in JSON form, and is regenerated in lockstep with this markdown pack so content stays in sync. Consumers integrating the pack into GRC tools, audit-request portals, or evidence pipelines should consume the JSON document; human readers should consume this markdown.

Related API surfaces (all under [`api/v1/`](../../api/README.md)):

- [`api/v1/compliance/regulations/uk-gdpr.json`](../../api/v1/compliance/regulations/uk-gdpr.json) — regulation metadata and per-version coverage metrics
- [`api/v1/compliance/ucs/`](../../api/v1/compliance/ucs/index.json) — individual UC sidecars
- [`api/v1/compliance/coverage.json`](../../api/v1/compliance/coverage.json) — global coverage snapshot
- [`api/v1/compliance/gaps.json`](../../api/v1/compliance/gaps.json) — global gap report

## 14. Provenance and regeneration

This pack is **generated**, not hand-authored. Re-running the generator produces byte-identical output (deterministic sort, stable serialisation, no free-form timestamps outside the block below). CI enforces regeneration drift via `--check` mode.

**Inputs to this pack**

- [`data/regulations.json`](../../data/regulations.json) — commonClauses, priority weights, authoritative URLs
- [`data/evidence-pack-extras.json`](../../data/evidence-pack-extras.json) — retention, roles, authoritative guidance, penalty, testing approach
- [`content/cat-*/UC-*.json`](../../content) — UC sidecars containing compliance[] entries, controlFamily, owner, evidence fields
- [`api/v1/compliance/regulations/uk-gdpr@*.json`](../../api/v1/compliance/regulations/) — pre-computed coverage metrics (when present)

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

### Primary sources

<a id="ref-1"></a>**[1]** United Kingdom Parliament. (2018). *Data Protection Act 2018 (UK GDPR, retained EU law)*. The Stationery Office. 2018 c. 12. https://www.legislation.gov.uk/ukpga/2018/12/contents

<a id="ref-2"></a>**[2]** European Parliament and Council of the European Union. (2016, April). *Regulation (EU) 2016/679 — General Data Protection Regulation*. Official Journal of the European Union, L 119. ELI: reg/2016/679. https://eur-lex.europa.eu/eli/reg/2016/679/oj

### Supporting sources

<a id="ref-3"></a>**[3]** American Institute of Certified Public Accountants. (2017). *Trust Services Criteria (2017) for Security, Availability, Processing Integrity, Confidentiality, and Privacy*. AICPA & CIMA. SOC 2 / TSP Section 100. https://www.aicpa-cima.com/topic/audit-assurance/soc-suite-of-services

<a id="ref-4"></a>**[4]** European Parliament and Council of the European Union. (2022, December). *Directive (EU) 2022/2555 — NIS2 Directive on cybersecurity*. Official Journal of the European Union, L 333. ELI: dir/2022/2555. https://eur-lex.europa.eu/eli/dir/2022/2555/oj

<a id="ref-5"></a>**[5]** International Organization for Standardization. (2022). *ISO/IEC 27001:2022 — Information security, cybersecurity and privacy protection — Information security management systems — Requirements*. ISO/IEC. ISO/IEC 27001:2022. https://www.iso.org/standard/27001

<a id="ref-6"></a>**[6]** International Organization for Standardization. (2019). *ISO/IEC 27701:2019 — Privacy information management*. ISO/IEC. ISO/IEC 27701:2019. https://www.iso.org/standard/71670.html

<a id="ref-7"></a>**[7]** National Cyber Security Centre (UK). (2025). *Cyber Essentials — Montpellier (2025)*. NCSC, IASME Consortium. https://www.ncsc.gov.uk/cyberessentials/overview

<a id="ref-8"></a>**[8]** Splunk Inc. (2026). *Splunk Common Information Model Add-on Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/CIM

<a id="ref-9"></a>**[9]** Splunk Inc. (2026). *Splunk Enterprise Security Administration Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ES

<a id="ref-10"></a>**[10]** Splunk Inc. (2026). *Splunk IT Service Intelligence Administration Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ITSI

<a id="ref-11"></a>**[11]** U.S. Department of Health & Human Services. (2002). *HIPAA Privacy Rule (45 CFR Parts 160 and 164, Subparts A and E)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/privacy/index.html

<a id="ref-12"></a>**[12]** U.S. Department of Health & Human Services. (2013). *HIPAA Security Rule (45 CFR Parts 160 and 164, Subparts A and C)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/security/index.html

<details>
<summary>Additional online sources cited in the document body (26)</summary>

<a id="ref-13"></a>**[13]** legislation.gov.uk. *UK Legislation 2016 c. 679*. Retrieved May 11, 2026, from https://www.legislation.gov.uk/eur/2016/679/contents

<a id="ref-14"></a>**[14]** ico.org.uk. *ico.org.uk: Uk Gdpr Guidance And Resources*. Retrieved May 11, 2026, from https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/

<a id="ref-15"></a>**[15]** ico.org.uk. *ico.org.uk: Accountability Framework*. Retrieved May 11, 2026, from https://ico.org.uk/for-organisations/accountability-framework/

<a id="ref-16"></a>**[16]** ico.org.uk. *ico.org.uk: International Data Transfer Agreement And Guidance*. Retrieved May 11, 2026, from https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/international-data-transfer-agreement-and-guidance/

<a id="ref-17"></a>**[17]** gov.uk. *gov.uk: Data A New Direction*. Retrieved May 11, 2026, from https://www.gov.uk/government/consultations/data-a-new-direction

<a id="ref-18"></a>**[18]** legislation.gov.uk. *UK Legislation: 2025*. Retrieved May 11, 2026, from https://www.legislation.gov.uk/ukpga/2025

<a id="ref-19"></a>**[19]** legislation.gov.uk. *UK Legislation 2016 c. 679*. Retrieved May 11, 2026, from https://www.legislation.gov.uk/eur/2016/679/article/Art.5

<a id="ref-20"></a>**[20]** legislation.gov.uk. *UK Legislation 2016 c. 679*. Retrieved May 11, 2026, from https://www.legislation.gov.uk/eur/2016/679/article/Art.6

<a id="ref-21"></a>**[21]** legislation.gov.uk. *UK Legislation 2016 c. 679*. Retrieved May 11, 2026, from https://www.legislation.gov.uk/eur/2016/679/article/Art.7

<a id="ref-22"></a>**[22]** legislation.gov.uk. *UK Legislation 2016 c. 679*. Retrieved May 11, 2026, from https://www.legislation.gov.uk/eur/2016/679/article/Art.15

<a id="ref-23"></a>**[23]** legislation.gov.uk. *UK Legislation 2016 c. 679*. Retrieved May 11, 2026, from https://www.legislation.gov.uk/eur/2016/679/article/Art.16

<a id="ref-24"></a>**[24]** legislation.gov.uk. *UK Legislation 2016 c. 679*. Retrieved May 11, 2026, from https://www.legislation.gov.uk/eur/2016/679/article/Art.17

<a id="ref-25"></a>**[25]** legislation.gov.uk. *UK Legislation 2016 c. 679*. Retrieved May 11, 2026, from https://www.legislation.gov.uk/eur/2016/679/article/Art.18

<a id="ref-26"></a>**[26]** legislation.gov.uk. *UK Legislation 2016 c. 679*. Retrieved May 11, 2026, from https://www.legislation.gov.uk/eur/2016/679/article/Art.20

<a id="ref-27"></a>**[27]** legislation.gov.uk. *UK Legislation 2016 c. 679*. Retrieved May 11, 2026, from https://www.legislation.gov.uk/eur/2016/679/article/Art.21

<a id="ref-28"></a>**[28]** legislation.gov.uk. *UK Legislation 2016 c. 679*. Retrieved May 11, 2026, from https://www.legislation.gov.uk/eur/2016/679/article/Art.22

<a id="ref-29"></a>**[29]** legislation.gov.uk. *UK Legislation 2016 c. 679*. Retrieved May 11, 2026, from https://www.legislation.gov.uk/eur/2016/679/article/Art.25

<a id="ref-30"></a>**[30]** legislation.gov.uk. *UK Legislation 2016 c. 679*. Retrieved May 11, 2026, from https://www.legislation.gov.uk/eur/2016/679/article/Art.28

<a id="ref-31"></a>**[31]** legislation.gov.uk. *UK Legislation 2016 c. 679*. Retrieved May 11, 2026, from https://www.legislation.gov.uk/eur/2016/679/article/Art.30

<a id="ref-32"></a>**[32]** legislation.gov.uk. *UK Legislation 2016 c. 679*. Retrieved May 11, 2026, from https://www.legislation.gov.uk/eur/2016/679/article/Art.32

<a id="ref-33"></a>**[33]** legislation.gov.uk. *UK Legislation 2016 c. 679*. Retrieved May 11, 2026, from https://www.legislation.gov.uk/eur/2016/679/article/Art.33

<a id="ref-34"></a>**[34]** legislation.gov.uk. *UK Legislation 2016 c. 679*. Retrieved May 11, 2026, from https://www.legislation.gov.uk/eur/2016/679/article/Art.34

<a id="ref-35"></a>**[35]** legislation.gov.uk. *UK Legislation 2016 c. 679*. Retrieved May 11, 2026, from https://www.legislation.gov.uk/eur/2016/679/article/Art.35

<a id="ref-36"></a>**[36]** legislation.gov.uk. *UK Legislation 2016 c. 679*. Retrieved May 11, 2026, from https://www.legislation.gov.uk/eur/2016/679/article/Art.44

<a id="ref-37"></a>**[37]** legislation.gov.uk. *UK Legislation 2016 c. 679*. Retrieved May 11, 2026, from https://www.legislation.gov.uk/eur/2016/679/article/Art.45

<a id="ref-38"></a>**[38]** legislation.gov.uk. *UK Legislation 2016 c. 679*. Retrieved May 11, 2026, from https://www.legislation.gov.uk/eur/2016/679/article/Art.46

</details>

<!-- END-AUTOGENERATED-SOURCES -->
