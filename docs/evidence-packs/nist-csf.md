# Evidence Pack — NIST CSF

> **Tier**: Tier 1 &nbsp;·&nbsp; **Jurisdiction**: US, GLOBAL &nbsp;·&nbsp; **Version**: `2.0`
>
> **Full name**: NIST Cybersecurity Framework
> **Authoritative source**: [https://www.nist.gov/cyberframework](https://www.nist.gov/cyberframework)
> **Effective from**: 2024-02-26

> This evidence pack is the auditor-facing view of the Splunk monitoring catalogue's coverage of the regulation. Every clause coverage claim is traceable to a specific UC sidecar JSON file (`use-cases/cat-*/uc-*.json`); every retention figure cites its legal basis; every URL resolves to an official regulator or standards-body source. The pack does **not** assert legal conclusions — it tabulates what the catalogue covers, names the authoritative source, and flags gaps. Interpretation stays with counsel.

> **Live views.** [Buyer narrative (`compliance-story.html?reg=nist-csf`)](../../compliance-story.html?reg=nist-csf) · [Auditor clause navigator (`clause-navigator.html#reg=nist-csf`)](../../clause-navigator.html#reg=nist-csf) · [JSON twin (`api/v1/compliance/story/nist-csf.json`)](../../api/v1/compliance/story/nist-csf.json)

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

NIST Cybersecurity Framework 2.0 (released 26 February 2024) is a voluntary framework of cybersecurity outcomes organised into six Functions (Govern, Identify, Protect, Detect, Respond, Recover), 22 Categories, and 106 Subcategories. Version 2.0 adds the Govern function to emphasise enterprise risk-management context. Framework Profiles map outcomes to an organisation's business requirements; Implementation Tiers characterise maturity (Partial → Adaptive). Widely adopted across US federal, state, critical-infrastructure, and international private-sector organisations.

## 2. Scope and applicability

Any organisation seeking a structured, outcome-focused approach to cybersecurity. Not a certification. Often used as a baseline for gap analysis against sector-specific regulations (e.g. HIPAA, NYDFS 23 NYCRR 500).

**Territorial scope.** Global adoption (US origin); frequently translated into national variants (Japan's J-CSIP profile, Italy's Framework Nazionale).

## 3. Catalogue coverage at a glance

- **Clauses tracked**: 17
- **Clauses covered by at least one UC**: 17 / 17 (100.0%)
- **Priority-weighted coverage**: 100.0%
- **Contributing UCs**: 18

Coverage methodology is documented in [`docs/coverage-methodology.md`](../coverage-methodology.md). Priority weights come from `data/regulations.json` commonClauses entries (see [`data/regulations.json`](../../data/regulations.json) priorityWeightRubric).

## 4. Clause-by-clause coverage

Clauses are listed in the order defined by `data/regulations.json commonClauses` for this regulation version. A clause is considered covered when at least one UC sidecar has a `compliance[]` entry matching `(regulation, version, clause)`. Assurance is the maximum across contributing UCs.

| Clause | Topic | Priority | Assurance | UCs |
|---|---|---|---|---|
| [`GV.OC-01`](https://csrc.nist.gov/pubs/cswp/29/final#GV.OC-01) | Organisational context | 0.7 | `contributing` | [UC-22.7.8](#uc-22-7-8) |
| [`GV.RM-01`](https://csrc.nist.gov/pubs/cswp/29/final#GV.RM-01) | Risk management strategy | 1.0 | `contributing` | [UC-22.7.10](#uc-22-7-10) |
| [`GV.RR-01`](https://csrc.nist.gov/pubs/cswp/29/final#GV.RR-01) | Organisational leadership | 0.7 | `contributing` | [UC-22.7.11](#uc-22-7-11) |
| [`ID.AM-01`](https://csrc.nist.gov/pubs/cswp/29/final#ID.AM-01) | Asset inventory | 1.0 | `contributing` | [UC-22.7.1](#uc-22-7-1), [UC-22.7.16](#uc-22-7-16) |
| [`ID.RA-01`](https://csrc.nist.gov/pubs/cswp/29/final#ID.RA-01) | Risk assessment | 1.0 | `contributing` | [UC-22.7.19](#uc-22-7-19) |
| [`PR.AA-01`](https://csrc.nist.gov/pubs/cswp/29/final#PR.AA-01) | Authentication | 1.0 | `contributing` | [UC-22.7.23](#uc-22-7-23) |
| [`PR.AA-05`](https://csrc.nist.gov/pubs/cswp/29/final#PR.AA-05) | Access permissions | 1.0 | `full` | [UC-22.7.4](#uc-22-7-4) |
| [`PR.DS-01`](https://csrc.nist.gov/pubs/cswp/29/final#PR.DS-01) | Data-at-rest protection | 1.0 | `contributing` | [UC-22.7.26](#uc-22-7-26) |
| [`PR.DS-02`](https://csrc.nist.gov/pubs/cswp/29/final#PR.DS-02) | Data-in-transit protection | 1.0 | `contributing` | [UC-22.7.27](#uc-22-7-27) |
| [`PR.PS-04`](https://csrc.nist.gov/pubs/cswp/29/final#PR.PS-04) | Log generation | 1.0 | `partial` | [UC-22.7.32](#uc-22-7-32) |
| [`DE.AE-02`](https://csrc.nist.gov/pubs/cswp/29/final#DE.AE-02) | Anomalies and events analysis | 1.0 | `contributing` | [UC-22.7.37](#uc-22-7-37) |
| [`DE.CM-01`](https://csrc.nist.gov/pubs/cswp/29/final#DE.CM-01) | Network monitoring | 1.0 | `contributing` | [UC-22.7.31](#uc-22-7-31) |
| [`DE.CM-03`](https://csrc.nist.gov/pubs/cswp/29/final#DE.CM-03) | Personnel activity monitoring | 1.0 | `contributing` | [UC-22.7.33](#uc-22-7-33) |
| [`DE.CM-09`](https://csrc.nist.gov/pubs/cswp/29/final#DE.CM-09) | Environment monitoring | 0.7 | `partial` | [UC-22.7.5](#uc-22-7-5) |
| [`RS.MA-01`](https://csrc.nist.gov/pubs/cswp/29/final#RS.MA-01) | Incident management | 1.0 | `contributing` | [UC-22.7.39](#uc-22-7-39) |
| [`RS.AN-03`](https://csrc.nist.gov/pubs/cswp/29/final#RS.AN-03) | Incident analysis | 1.0 | `full` | [UC-22.7.6](#uc-22-7-6) |
| [`RC.RP-01`](https://csrc.nist.gov/pubs/cswp/29/final#RC.RP-01) | Recovery plan execution | 1.0 | `contributing` | [UC-22.7.46](#uc-22-7-46) |

### 4.1 Contributing UC detail

<a id='uc-22-7-1'></a>
- **UC-22.7.1** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-7-10'></a>
- **UC-22.7.10** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-7-11'></a>
- **UC-22.7.11** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-7-16'></a>
- **UC-22.7.16** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-7-19'></a>
- **UC-22.7.19** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-7-23'></a>
- **UC-22.7.23** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-7-26'></a>
- **UC-22.7.26** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-7-27'></a>
- **UC-22.7.27** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-7-31'></a>
- **UC-22.7.31** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-7-32'></a>
- **UC-22.7.32** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-7-33'></a>
- **UC-22.7.33** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-7-37'></a>
- **UC-22.7.37** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-7-39'></a>
- **UC-22.7.39** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-7-4'></a>
- **UC-22.7.4** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-7-46'></a>
- **UC-22.7.46** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-7-5'></a>
- **UC-22.7.5** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-7-6'></a>
- **UC-22.7.6** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-7-8'></a>
- **UC-22.7.8** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)

## 5. Evidence collection

### 5.1 Common evidence sources

Auditors typically request the following records when examining this regulation:

- Risk register with CSF Subcategory tags
- SIEM / SOAR alert-to-incident pipelines (Detect + Respond functions)
- Asset inventory with criticality ratings (Identify function)
- Vulnerability-management tooling (Protect function)
- Backup and recovery test records (Recover function)
- Third-party/supplier risk-assessment records (GV.SC)
- Board/ERM committee materials referencing Framework outcomes

### 5.2 Retention requirements

| Artifact | Retention | Legal basis |
|---|---|---|
| Framework Profile (Current + Target) | Indefinite — core enterprise artefact | NIST CSF 2.0 Framework Core section |
| Risk-assessment results per Identify function | 3-7 years depending on sector regulation | NIST SP 800-30, SP 800-39 |
| Detect-function evidence (SIEM/EDR alerts with triage outcome) | 12 months minimum; 3-7 years for regulated industries | NIST SP 800-92 |
| Respond-function evidence (incident tickets, after-action reviews) | 3-7 years depending on sector | NIST SP 800-61 |
| Improvement actions tied to Subcategory gaps | 3 years rolling | NIST CSF 2.0 guidance |

> Retention figures above are the legal minimums or regulator-stated expectations. Organisation-specific retention schedules may be longer where business, tax, litigation-hold, or contractual obligations apply. Where a figure conflicts with local data-protection law (e.g. GDPR Art.5(1)(e) storage-limitation principle), the shorter conformant period governs for personal-data content; the evidence-of-compliance retention retains the longer period for audit purposes, scrubbed of excess personal data.

### 5.3 Evidence integrity expectations

Regulators increasingly cite **evidence-integrity failures** as aggravating factors in enforcement actions. Cross-regulation baseline expectations:

- Time-stamped, tamper-evident storage (WORM, cryptographic chaining, or append-only indexes).
- Chain-of-custody for any evidence removed from the SIEM / production system for audit or legal purposes.
- Synchronised clocks (NTP stratum ≤ 3 or equivalent) across all in-scope sources so timeline reconstruction is defensible.
- Documented retention enforcement — not just retention policy — so that deletion is auditable.

See cat-22.35 "Evidence continuity and log integrity" for UCs that implement these controls.

## 6. Control testing procedures

Self-assessment is the default; organisations typically use a maturity-model approach to rate each Subcategory against Implementation Tiers (Partial, Risk-Informed, Repeatable, Adaptive). External assessments are optional but increasingly common for procurement-driven demonstrations (e.g. CMMC-aligned contracts). Gap analysis between Current and Target Profile drives investment decisions.

**Reporting cadence.** No mandated cadence. Most organisations re-baseline profiles annually, with quarterly improvement-backlog reviews. Some sectors (e.g. TSA surface-transport 2021/2022 Security Directives) reference CSF outcomes with defined reporting cycles.

## 7. Roles and responsibilities

| Role | Responsibility |
|---|---|
| **Chief Executive Officer (CEO) / Senior Leader** | Accountability for the Govern function; cybersecurity is treated as an enterprise-risk discipline, not IT-only. |
| **Chief Information Security Officer (CISO)** | Owns Framework implementation, Profile maintenance, and improvement-backlog execution. |
| **Chief Risk Officer (CRO)** | Integrates cybersecurity risk into the enterprise-risk-management (ERM) framework (Govern function). |
| **Board of Directors / Audit Committee** | Oversees cybersecurity risk-appetite decisions; reviews Profile and material incidents. |
| **Sector-Specific ISAC / ISAO** | Provides sector informative references and threat intelligence that inform CSF Subcategory implementation. |
| **NIST** | Maintains the framework; publishes Informative References Catalog and Community Profiles. |

## 8. Authoritative guidance

- **NIST Cybersecurity Framework 2.0** — NIST — [https://www.nist.gov/cyberframework](https://www.nist.gov/cyberframework)
- **NIST CSF 2.0 Reference Tool** — NIST — [https://csrc.nist.gov/Projects/cybersecurity-framework/Filters](https://csrc.nist.gov/Projects/cybersecurity-framework/Filters)
- **NIST CSF 2.0 Implementation Examples** — NIST — [https://www.nist.gov/cyberframework/implementation](https://www.nist.gov/cyberframework/implementation)
- **NIST SP 800-221A Information and Communications Technology (ICT) Risk Outcomes** — NIST — [https://csrc.nist.gov/publications/detail/sp/800-221A/final](https://csrc.nist.gov/publications/detail/sp/800-221A/final)
- **Community Profiles (e.g. Manufacturing, Maritime, SMB)** — NIST — [https://www.nist.gov/cyberframework/community-profiles](https://www.nist.gov/cyberframework/community-profiles)

## 9. Common audit deficiencies

Findings frequently cited by regulators, certification bodies, and external auditors for this regulation. These should be pre-tested as part of readiness reviews.

- Framework Profile exists but is not integrated with risk register or compliance controls; treated as a separate artefact.
- Govern function is under-invested — board-level cybersecurity reporting does not cite Framework outcomes.
- Subcategories in Detect and Respond are implemented technically but do not have documented metrics or tier targets.
- Supply-chain subcategories (GV.SC) are paper-only; third-party risk-management does not produce tangible evidence of control operation.
- Implementation Tier is self-asserted with no independent validation.
- New Govern Function controls (introduced in 2.0) are not yet addressed; transition from 1.1 profile is incomplete.

## 10. Enforcement and penalties

No direct statutory penalty. However, CSF is frequently cited by regulators (SEC cybersecurity disclosure rules, NYDFS 23 NYCRR 500, HHS 405(d) recognised security practices under HITECH) as evidence of 'reasonable security'. Failure to implement may not directly trigger penalty but may increase penalty severity in downstream regulatory actions.

## 11. Pack gaps and remediation backlog

All clauses tracked in `data/regulations.json` for this regulation version are covered by at least one UC. **100 % common-clause coverage**. Remaining work is assurance-upgrade (for example, moving `contributing` entries to `partial` or `full` via explicit control tests) rather than new clause authoring.

## 12. Questions an auditor should ask

These are the questions a regulator, certification body, or external auditor is likely to ask. The pack helps preparers stage evidence and pre-test responses before the review opens.

- Produce your Framework Current Profile and Target Profile; demonstrate the last gap-analysis and improvement backlog.
- For each of the six Functions (Govern, Identify, Protect, Detect, Respond, Recover), show evidence of at least one Subcategory operating in the last quarter.
- Demonstrate how NIST CSF outcomes feed into the organisation's enterprise-risk-management register (Govern function).
- Produce the Organizational Profile that lists informative references (NIST SP 800-53, ISO 27001, CIS Controls) used for implementation.
- For Respond and Recover, produce the last incident the organisation experienced and trace it through the framework outcomes.
- Show evidence that supply-chain cybersecurity (GV.SC, ID.SC) is addressed, including third-party risk-assessments.
- Demonstrate how Implementation Tier has changed over the last 12-24 months (maturity progression).

## 13. Machine-readable twin

The machine-readable companion of this pack lives at [`api/v1/evidence-packs/nist-csf.json`](../../api/v1/evidence-packs/nist-csf.json). It contains the same clause-level coverage, retention guidance, role matrix, and gap list in JSON form, and is regenerated in lockstep with this markdown pack so content stays in sync. Consumers integrating the pack into GRC tools, audit-request portals, or evidence pipelines should consume the JSON document; human readers should consume this markdown.

Related API surfaces (all under [`api/v1/`](../../api/README.md)):

- [`api/v1/compliance/regulations/nist-csf.json`](../../api/v1/compliance/regulations/nist-csf.json) — regulation metadata and per-version coverage metrics
- [`api/v1/compliance/ucs/`](../../api/v1/compliance/ucs/index.json) — individual UC sidecars
- [`api/v1/compliance/coverage.json`](../../api/v1/compliance/coverage.json) — global coverage snapshot
- [`api/v1/compliance/gaps.json`](../../api/v1/compliance/gaps.json) — global gap report

## 14. Provenance and regeneration

This pack is **generated**, not hand-authored. Re-running the generator produces byte-identical output (deterministic sort, stable serialisation, no free-form timestamps outside the block below). CI enforces regeneration drift via `--check` mode.

**Inputs to this pack**

- [`data/regulations.json`](../../data/regulations.json) — commonClauses, priority weights, authoritative URLs
- [`data/evidence-pack-extras.json`](../../data/evidence-pack-extras.json) — retention, roles, authoritative guidance, penalty, testing approach
- [`use-cases/cat-*/uc-*.json`](../../use-cases) — UC sidecars containing compliance[] entries, controlFamily, owner, evidence fields
- [`api/v1/compliance/regulations/nist-csf@*.json`](../../api/v1/compliance/regulations/) — pre-computed coverage metrics (when present)

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
