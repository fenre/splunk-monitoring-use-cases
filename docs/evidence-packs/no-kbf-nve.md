# Evidence Pack — NO KBF

> **Tier**: Tier 2 &nbsp;·&nbsp; **Jurisdiction**: NO &nbsp;·&nbsp; **Version**: `2012 as amended`
>
> **Full name**: Norwegian Kraftberedskapsforskriften (NVE Power-sector emergency preparedness regulation)
> **Authoritative source**: [https://lovdata.no/dokument/SF/forskrift/2012-12-07-1157](https://lovdata.no/dokument/SF/forskrift/2012-12-07-1157)
> **Effective from**: 2013-01-01

> This evidence pack is the auditor-facing view of the Splunk monitoring catalogue's coverage of the regulation. Every clause coverage claim is traceable to a specific UC sidecar JSON file (`content/cat-*/UC-*.json`); every retention figure cites its legal basis; every URL resolves to an official regulator or standards-body source. The pack does **not** assert legal conclusions — it tabulates what the catalogue covers, names the authoritative source, and flags gaps. Interpretation stays with counsel.

> **Live views.** [Buyer narrative (`compliance-story.html?reg=no-kbf-nve`)](../../compliance-story.html?reg=no-kbf-nve) · [Auditor clause navigator (`clause-navigator.html#reg=no-kbf-nve`)](../../clause-navigator.html#reg=no-kbf-nve) · [JSON twin (`api/v1/compliance/story/no-kbf-nve.json`)](../../api/v1/compliance/story/no-kbf-nve.json)

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

Forskrift om sikkerhet og beredskap i kraftforsyningen (kraftberedskapsforskriften) regulates security and emergency preparedness for Norway's power supply. NVE (Norges vassdrags- og energidirektorat) is beredskapsmyndigheten. KBO-enheter must maintain beredskapsorganisasjon, risk assessments, reporting, exercises, information security for kraftsensitiv informasjon, and protection of driftskontrollsystem (DCS/SCADA). Amendment SF/forskrift/2026-05-04-717 (effective 2026-07-01) strengthens §4-1 reparasjonsberedskap for simultaneous sabotage scenarios.

## 2. Scope and applicability

Applies to KBO-enheter in the Norwegian power supply chain: production, transmission, distribution, and system operators designated under energiloven. Scope includes informasjonssikkerhet (kap. 6), driftskontrollsystem (kap. 7), beredskap (kap. 2), and reparasjonsberedskap (kap. 4). Physical security of classified facilities (kap. 5) is primarily organisational and physical — Splunk evidence is supplementary.

**Territorial scope.** Norway. KBO-enheter operating cross-border interconnectors must also satisfy bilateral and NIS2-derived obligations where applicable; this pack covers KBF only.

## 3. Catalogue coverage at a glance

- **Clauses tracked**: 18
- **Clauses covered by at least one UC**: 18 / 18 (100.0%)
- **Priority-weighted coverage**: 100.0%
- **Contributing UCs**: 18

Coverage methodology is documented in [`docs/coverage-methodology.md`](../coverage-methodology.md). Priority weights come from `data/regulations.json` commonClauses entries (see [`data/regulations.json`](../../data/regulations.json) priorityWeightRubric).

## 4. Clause-by-clause coverage

Clauses are listed in the order defined by `data/regulations.json commonClauses` for this regulation version. A clause is considered covered when at least one UC sidecar has a `compliance[]` entry matching `(regulation, version, clause)`. Assurance is the maximum across contributing UCs.

| Clause | Topic | Priority | Assurance | UCs |
|---|---|---|---|---|
| [`§2-3`](https://veiledere.nve.no/kraftberedskapsforskriften/) | Risikovurdering | 1.0 | `partial` | [UC-22.26.21](#uc-22-26-21) |
| [`§2-5`](https://veiledere.nve.no/kraftberedskapsforskriften/) | Varsling | 1.0 | `partial` | [UC-22.26.22](#uc-22-26-22) |
| [`§2-6`](https://veiledere.nve.no/kraftberedskapsforskriften/) | Rapportering til NVE | 1.0 | `partial` | [UC-22.26.9](#uc-22-26-9) |
| [`§2-7`](https://veiledere.nve.no/kraftberedskapsforskriften/) | Kriseøvelser | 0.7 | `partial` | [UC-22.26.8](#uc-22-26-8) |
| [`§2-10`](https://veiledere.nve.no/kraftberedskapsforskriften/) | Internkontrollsystem | 0.7 | `contributing` | [UC-22.26.23](#uc-22-26-23) |
| [`§4-1`](https://veiledere.nve.no/kraftberedskapsforskriften/) | Reparasjonsberedskap | 1.0 | `partial` | [UC-22.26.24](#uc-22-26-24) |
| [`§4-3`](https://veiledere.nve.no/kraftberedskapsforskriften/) | Gjenoppretting av funksjon | 1.0 | `partial` | [UC-22.26.10](#uc-22-26-10) |
| [`§6-1`](https://veiledere.nve.no/kraftberedskapsforskriften/) | Identifisering av kraftsensitiv informasjon og rettmessige brukere | 1.0 | `partial` | [UC-22.26.25](#uc-22-26-25) |
| [`§6-3`](https://veiledere.nve.no/kraftberedskapsforskriften/) | Beskyttelse, avskjerming og tilgangskontroll | 1.0 | `contributing` | [UC-22.26.7](#uc-22-26-7) |
| [`§6-5`](https://veiledere.nve.no/kraftberedskapsforskriften/) | Anskaffelser og sikkerhetsavtaler | 0.7 | `partial` | [UC-22.26.26](#uc-22-26-26) |
| [`§6-7`](https://veiledere.nve.no/kraftberedskapsforskriften/) | Personkontroll | 0.7 | `partial` | [UC-22.26.27](#uc-22-26-27) |
| [`§6-8`](https://veiledere.nve.no/kraftberedskapsforskriften/) | Sikkerhetskopier | 1.0 | `partial` | [UC-22.26.28](#uc-22-26-28) |
| [`§6-9`](https://veiledere.nve.no/kraftberedskapsforskriften/) | Digitale informasjonssystemer | 1.0 | `contributing` | [UC-14.2.11](#uc-14-2-11) |
| [`§7-1`](https://veiledere.nve.no/kraftberedskapsforskriften/) | Generell plikt til å beskytte driftskontrollsystemet | 1.0 | `partial` | [UC-14.2.11](#uc-14-2-11) |
| [`§7-4`](https://veiledere.nve.no/kraftberedskapsforskriften/) | Kontroll med brukertilgang | 1.0 | `partial` | [UC-14.9.14](#uc-14-9-14), [UC-22.26.6](#uc-22-26-6), [UC-22.26.7](#uc-22-26-7) |
| [`§7-5`](https://veiledere.nve.no/kraftberedskapsforskriften/) | Kontroll ved endringer i driftskontrollsystemet | 1.0 | `partial` | [UC-14.2.9](#uc-14-2-9), [UC-14.6.6](#uc-14-6-6) |
| [`§7-7`](https://veiledere.nve.no/kraftberedskapsforskriften/) | Feil, sårbarheter og sikkerhetsbrudd | 1.0 | `contributing` | [UC-14.9.14](#uc-14-9-14) |
| [`§7-10`](https://veiledere.nve.no/kraftberedskapsforskriften/) | Ekstern tilkobling til driftskontrollsystem | 1.0 | `partial` | [UC-14.2.4](#uc-14-2-4) |

### 4.1 Contributing UC detail

<a id='uc-14-2-11'></a>
- **UC-14.2.11** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-14-2-4'></a>
- **UC-14.2.4** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-14-2-9'></a>
- **UC-14.2.9** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-14-6-6'></a>
- **UC-14.6.6** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-14-9-14'></a>
- **UC-14.9.14** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-26-10'></a>
- **UC-22.26.10** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-26-21'></a>
- **UC-22.26.21** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-26-22'></a>
- **UC-22.26.22** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-26-23'></a>
- **UC-22.26.23** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-26-24'></a>
- **UC-22.26.24** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-26-25'></a>
- **UC-22.26.25** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-26-26'></a>
- **UC-22.26.26** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-26-27'></a>
- **UC-22.26.27** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-26-28'></a>
- **UC-22.26.28** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-26-6'></a>
- **UC-22.26.6** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-26-7'></a>
- **UC-22.26.7** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-26-8'></a>
- **UC-22.26.8** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)
<a id='uc-22-26-9'></a>
- **UC-22.26.9** —
  - Control family: `—`
  - Owner: `—`
  - Evidence fields declared in sidecar: 0
  - Source: [``](../../)

## 5. Evidence collection

### 5.1 Common evidence sources

Auditors typically request the following records when examining this regulation:


### 5.2 Retention requirements

| Artifact | Retention | Legal basis |
|---|---|---|
| Beredskapsplan and risikovurdering revisions (§2-3, §2-4) | Current version + prior versions for audit cycle (typically 5-7 years) | Kraftberedskapsforskriften §2-3; NVE veileder |
| NVE rapportering and varsling records (§2-5, §2-6) | Minimum 5 years; align with NVE reporting cycle | Kraftberedskapsforskriften §2-6; NVE veileder |
| Kriseøvelse evidence (§2-7) | Minimum 3 years per exercise | Kraftberedskapsforskriften §2-7; NVE veileder |
| OT/SCADA security event logs and access reviews (§7-4, §7-7) | Minimum 12 months online + 5 years archive for audit | Kraftberedskapsforskriften kap. 7; IEC 62443-aligned practice |
| Splunk audit_evidence exports for KBF-tagged controls | 7 years default for tier-2 compliance evidence in this catalogue | Catalogue convention; verify against longest-applicable KBO retention policy |

> Retention figures above are the legal minimums or regulator-stated expectations. Organisation-specific retention schedules may be longer where business, tax, litigation-hold, or contractual obligations apply. Where a figure conflicts with local data-protection law (e.g. GDPR<sup class="ref">[<a href="#ref-1">1</a>]</sup> Art.5(1)(e) storage-limitation principle), the shorter conformant period governs for personal-data content; the evidence-of-compliance retention retains the longer period for audit purposes, scrubbed of excess personal data.

### 5.3 Evidence integrity expectations

Regulators increasingly cite **evidence-integrity failures** as aggravating factors in enforcement actions. Cross-regulation baseline expectations:

- Time-stamped, tamper-evident storage (WORM, cryptographic chaining, or append-only indexes).
- Chain-of-custody for any evidence removed from the SIEM / production system for audit or legal purposes.
- Synchronised clocks (NTP stratum ≤ 3 or equivalent) across all in-scope sources so timeline reconstruction is defensible.
- Documented retention enforcement — not just retention policy — so that deletion is auditable.

See cat-22.35 "Evidence continuity and log integrity" for UCs that implement these controls.

## 6. Control testing procedures

NVE tilsyn reviews beredskapsplan, risikovurdering, øvelser, and OT security controls. Splunk evidence supports continuous monitoring of DCS access, change control, segmentation, drill timelines, and reporting-channel integrity — not replacement of NVE documentation.

**Reporting cadence.** NVE reporting per §2-6 event triggers; annual exercise minimum §2-7; continuous SIEM for kap. 7 controls.

## 7. Roles and responsibilities

| Role | Responsibility |
|---|---|

## 8. Authoritative guidance

- **Kraftberedskapsforskriften (Lovdata)** — None — [https://lovdata.no/dokument/SF/forskrift/2012-12-07-1157](https://lovdata.no/dokument/SF/forskrift/2012-12-07-1157)
- **NVE digital veileder til kraftberedskapsforskriften** — None — [https://veiledere.nve.no/kraftberedskapsforskriften/](https://veiledere.nve.no/kraftberedskapsforskriften/)
- **Endring §4-1 reparasjonsberedskap (2026-07-01)** — None — [https://lovdata.no/dokument/SF/forskrift/2026-05-04-717](https://lovdata.no/dokument/SF/forskrift/2026-05-04-717)

## 9. Common audit deficiencies

Findings frequently cited by regulators, certification bodies, and external auditors for this regulation. These should be pre-tested as part of readiness reviews.

- All KBF UCs mapped to §6-1 regardless of SPL semantics — corrected in Phase 1 expansion.
- Missing cross-mapping from existing OT UCs (cat-14) to kap. 7 DCS controls.
- No evidence of annual kriseøvelse ack timelines (§2-7).
- Unapproved NVE/Altinn reporting paths (§2-6).
- IT-to-OT SCADA access without segmentation allowlist (§7-4, §7-10).
- Reparasjonsberedskap not dimensioned for simultaneous sabotage post-2026 amendment (§4-1).

## 10. Enforcement and penalties

Overtredelsesgebyr and tvangsmulkt under kap. 8; straff etter energiloven §8-6 for gross violations. NVE can issue pålegg and dispensasjoner.

## 11. Pack gaps and remediation backlog

All clauses tracked in `data/regulations.json` for this regulation version are covered by at least one UC. **100 % common-clause coverage**. Remaining work is assurance-upgrade (for example, moving `contributing` entries to `partial` or `full` via explicit control tests) rather than new clause authoring.

## 12. Questions an auditor should ask

These are the questions a regulator, certification body, or external auditor is likely to ask. The pack helps preparers stage evidence and pre-test responses before the review opens.


## 13. Machine-readable twin

The machine-readable companion of this pack lives at [`api/v1/evidence-packs/no-kbf-nve.json`](../../api/v1/evidence-packs/no-kbf-nve.json). It contains the same clause-level coverage, retention guidance, role matrix, and gap list in JSON form, and is regenerated in lockstep with this markdown pack so content stays in sync. Consumers integrating the pack into GRC tools, audit-request portals, or evidence pipelines should consume the JSON document; human readers should consume this markdown.

Related API surfaces (all under [`api/v1/`](../../api/README.md)):

- [`api/v1/compliance/regulations/no-kbf-nve.json`](../../api/v1/compliance/regulations/no-kbf-nve.json) — regulation metadata and per-version coverage metrics
- [`api/v1/compliance/ucs/`](../../api/v1/compliance/ucs/index.json) — individual UC sidecars
- [`api/v1/compliance/coverage.json`](../../api/v1/compliance/coverage.json) — global coverage snapshot
- [`api/v1/compliance/gaps.json`](../../api/v1/compliance/gaps.json) — global gap report

## 14. Provenance and regeneration

This pack is **generated**, not hand-authored. Re-running the generator produces byte-identical output (deterministic sort, stable serialisation, no free-form timestamps outside the block below). CI enforces regeneration drift via `--check` mode.

**Inputs to this pack**

- [`data/regulations.json`](../../data/regulations.json) — commonClauses, priority weights, authoritative URLs
- [`data/evidence-pack-extras.json`](../../data/evidence-pack-extras.json) — retention, roles, authoritative guidance, penalty, testing approach
- [`content/cat-*/UC-*.json`](../../content) — UC sidecars containing compliance[] entries, controlFamily, owner, evidence fields
- [`api/v1/compliance/regulations/no-kbf-nve@*.json`](../../api/v1/compliance/regulations/) — pre-computed coverage metrics (when present)

- Generator: [`scripts/generate_evidence_packs.py`](../../scripts/generate_evidence_packs.py)
- Evidence-pack directory index: [`docs/evidence-packs/README.md`](README.md)

**Generation metadata**

```
catalogue_version: 8.25.0
generator_script:  scripts/generate_evidence_packs.py
inputs_sha256:     bce068831a1e77eefefbb021a1055a7fe8f4908c82c4f7a1534d90b90e431a86
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

<a id="ref-1"></a>**[1]** European Parliament and Council of the European Union. (2016, April). *Regulation (EU) 2016/679 — General Data Protection Regulation*. Official Journal of the European Union, L 119. ELI: reg/2016/679. https://eur-lex.europa.eu/eli/reg/2016/679/oj

<a id="ref-2"></a>**[2]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

<details>
<summary>Additional online sources cited in the document body (3)</summary>

<a id="ref-3"></a>**[3]** lovdata.no. *lovdata.no: 2012 12 07 1157*. Retrieved May 11, 2026, from https://lovdata.no/dokument/SF/forskrift/2012-12-07-1157

<a id="ref-4"></a>**[4]** veiledere.nve.no. *veiledere.nve.no: Kraftberedskapsforskriften*. Retrieved May 11, 2026, from https://veiledere.nve.no/kraftberedskapsforskriften/

<a id="ref-5"></a>**[5]** lovdata.no. *lovdata.no: 2026 05 04 717*. Retrieved May 11, 2026, from https://lovdata.no/dokument/SF/forskrift/2026-05-04-717

</details>

<!-- END-AUTOGENERATED-SOURCES -->
