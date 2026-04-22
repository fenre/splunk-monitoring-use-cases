# Evidence Pack — UK GDPR

> **Tier**: Tier 2 &nbsp;·&nbsp; **Jurisdiction**: UK &nbsp;·&nbsp; **Version**: `post-Brexit`
>
> **Full name**: UK General Data Protection Regulation
> **Authoritative source**: [https://www.legislation.gov.uk/eur/2016/679/contents](https://www.legislation.gov.uk/eur/2016/679/contents)
> **Effective from**: 2021-01-01
> **Derived from**: `gdpr` (`identity` inheritance) — see Phase 3.3

> This evidence pack is the auditor-facing view of the Splunk monitoring catalogue's coverage of the regulation. Every clause coverage claim is traceable to a specific UC sidecar JSON file (`use-cases/cat-*/uc-*.json`); every retention figure cites its legal basis; every URL resolves to an official regulator or standards-body source. The pack does **not** assert legal conclusions — it tabulates what the catalogue covers, names the authoritative source, and flags gaps. Interpretation stays with counsel.

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

UK GDPR is the United Kingdom's onshored version of Regulation (EU) 2016/679, adopted into domestic law under the European Union (Withdrawal) Act 2018 and amended by the Data Protection, Privacy and Electronic Communications (Amendments etc.) (EU Exit) Regulations 2019. It preserves the GDPR substantive regime intact while substituting UK bodies (ICO, UK government) for EU institutions. Sits alongside the Data Protection Act 2018 which provides the UK's detailed implementation framework.

## 2. Scope and applicability

Applies to controllers and processors established in the UK and to those outside the UK who offer goods/services to UK residents or monitor their behaviour within the UK. The DPA 2018 Part 3 governs law enforcement processing; Part 4 governs intelligence-services processing.

**Territorial scope.** UK territorial scope plus extraterritorial reach under Art.3 of the retained Regulation.

## 3. Catalogue coverage at a glance

- **Clauses tracked**: 1
- **Clauses covered by at least one UC**: 1 / 1 (100.0%)
- **Priority-weighted coverage**: 100.0%
- **Assurance-adjusted coverage**: 25.0%
- **Contributing UCs**: 1
- **Derived via `derivesFrom`**: parent `gdpr` (mode `identity`). The UK GDPR `commonClauses` in `data/regulations.json` currently tracks only `Art.32` (security of processing) as the priority clause for independent coverage. Parent GDPR UCs provide broader evidence for inherited clauses but are not counted in this pack's native coverage. Native hand-authored mappings take precedence. Known divergences are listed in `data/regulations.json derivesFrom[].divergences`.

Coverage methodology is documented in [`docs/coverage-methodology.md`](../coverage-methodology.md). Priority weights come from `data/regulations.json` commonClauses entries (see [`data/regulations.json`](../../data/regulations.json) priorityWeightRubric).

## 4. Clause-by-clause coverage

The UK GDPR `commonClauses` in `data/regulations.json` currently tracks `Art.32` (security of processing) as the priority clause for independent coverage. Broader GDPR clauses are covered via the parent `gdpr` identity inheritance but are not counted in this pack's native coverage metric. A clause is considered covered when at least one UC sidecar has a `compliance[]` entry matching `(regulation, version, clause)`. Assurance is the maximum across contributing UCs.

| Clause | Topic | Priority | Assurance | UCs |
|---|---|---|---|---|
| [`Art.32`](https://www.legislation.gov.uk/eur/2016/679/article/Art.32) | Security of processing | 1.0 | `contributing` | UC-22.1.1 and inherited GDPR UCs |

**Note on inherited coverage:** The remaining GDPR clauses (Art.5, Art.6, Art.7, Art.15--Art.22, Art.25, Art.28, Art.30, Art.33--Art.35, Art.44--Art.46) are covered through parent GDPR UCs via the `derivesFrom` identity relationship. Consult the [GDPR evidence pack](gdpr.md) for full clause-level detail on those inherited mappings.

## 5. Evidence collection

### 5.1 Common evidence sources

Auditors typically request the following records when examining this regulation:

- Same as GDPR, plus UK-specific entries:
- PECR (Privacy and Electronic Communications Regulations) direct-marketing consent logs
- ICO self-assessment tool outputs (ICO publishes structured self-assessment workbooks)
- UK Cyber Essentials / Cyber Essentials Plus certification evidence (often bundled with UK GDPR assurance)
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

ICO exercises enforcement primarily through monetary-penalty notices (up to GBP 17.5 million or 4 % of worldwide turnover), enforcement notices, and assessment notices. External auditors typically align UK GDPR testing with ISO 27001, Cyber Essentials Plus, or ISAE 3000 assurance engagements. Unlike GDPR, UK regulators have been explicit that contemporaneous evidence of the detection-to-notification timeline will be scrutinised in any Art.33 enforcement review.

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
| `Art.15` | Right of access | 1.0 |
| `Art.17` | Right to erasure | 1.0 |
| `Art.25` | Data protection by design and by default | 1.0 |
| `Art.28` | Processor obligations | 1.0 |
| `Art.30` | Records of processing | 1.0 |
| `Art.32` | Security of processing | 1.0 |
| `Art.33` | Breach notification to supervisory authority | 1.0 |
| `Art.34` | Breach communication to data subjects | 1.0 |
| `Art.44` | International transfers — general principle | 1.0 |
| `Art.5` | Principles of processing | 1.0 |
| `Art.6` | Lawful basis | 1.0 |
| `Art.16` | Right to rectification | 0.7 |
| `Art.18` | Right to restrict processing | 0.7 |
| `Art.20` | Right to data portability | 0.7 |
| `Art.21` | Right to object | 0.7 |
| `Art.22` | Automated decision making | 0.7 |
| `Art.35` | DPIA | 0.7 |
| `Art.45` | Transfers via adequacy decision | 0.7 |
| `Art.46` | Transfers subject to safeguards | 0.7 |
| `Art.7` | Conditions for consent | 0.7 |

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
- [`use-cases/cat-*/uc-*.json`](../../use-cases) — UC sidecars containing compliance[] entries, controlFamily, owner, evidence fields
- [`api/v1/compliance/regulations/uk-gdpr@*.json`](../../api/v1/compliance/regulations/) — pre-computed coverage metrics (when present)

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
