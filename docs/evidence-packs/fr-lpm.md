# Evidence Pack — France LPM OIV Regime

> **Tier**: Tier 1 &nbsp;·&nbsp; **Jurisdiction**: France &nbsp;·&nbsp; **Version**: `2024-NIS2-transposition-decret-2024-405`
>
> **Full name**: Loi de Programmation Militaire (LPM 2013, updated 2018, 2024) + Code de la défense Art. R.1332-41-1 à R.1332-41-22 + Décret n° 2024-405 du 8 mai 2024 (NIS2<sup class="ref">[<a href="#ref-2">2</a>]</sup> transposition)
> **Authoritative source**: [https://cyber.gouv.fr/loi-de-programmation-militaire-lpm](https://cyber.gouv.fr/loi-de-programmation-militaire-lpm)
> **Effective from**: 2013-12-18 (Loi n° 2013-1168); 2024-amendment via Décret 2024-405
>
> This evidence pack is the auditor-facing view of the Splunk monitoring catalogue's coverage of the French LPM OIV regime. Every clause coverage claim is traceable to a specific UC sidecar JSON file (`content/cat-22-regulatory-compliance/UC-22.58.*.json`); every retention figure cites its legal basis; every URL resolves to an official ANSSI or Legifrance source. Interpretation stays with the Délégué OIV (statutorily-named representative) and the RSSI (Responsable de la Sécurité des Systèmes d'Information).

> **Live views.** [Buyer narrative (`compliance-story.html?reg=fr-lpm`)](../../compliance-story.html?reg=fr-lpm) · [Auditor clause navigator (`clause-navigator.html#reg=fr-lpm`)](../../clause-navigator.html#reg=fr-lpm) · [JSON twin (`api/v1/compliance/story/fr-lpm.json`)](../../api/v1/compliance/story/fr-lpm.json)

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
11. [Questions an ANSSI / PASSI inspector should ask](#11-questions-an-anssi--passi-inspector-should-ask)
12. [Machine-readable twin](#12-machine-readable-twin)
13. [Provenance and regeneration](#13-provenance-and-regeneration)

## 1. Purpose of this evidence pack

The French Loi de Programmation Militaire (LPM) — introduced in the 2013 military programming law and consolidated through 2018 and 2024 — establishes a designation regime for Opérateurs d'Importance Vitale (Operators of Vital Importance). The regime is operationalised through Code de la défense Articles R.1332-41-1 to R.1332-41-22 and administered by the Agence Nationale de la Sécurité des Systèmes d'Information (ANSSI). Approximately 240 OIVs are designated by the Prime Minister across 12 secteurs d'activités d'importance vitale (sectors of vital activity). Each OIV must maintain a Système d'Information d'Importance Vitale (SAIV) inventory and notify ANSSI of material modifications, declare cyber incidents to CERT-FR within 72 hours, implement the 20 règles d'hygiène (PSSI-MCAS), undergo periodic PASSI-qualified audit, procure only ANSSI-qualified products (visa de sécurité, CSPN, CC), maintain AIE (Architecture Industrielle d'Échange) zone segmentation, and reconcile LPM obligations with the NIS2 transposition under Décret 2024-405 (REC and REI). The Délégué OIV — a named individual signing all obligation submissions — bears personal liability under the Code de la défense.

## 2. Scope and applicability

Applies to OIVs designated under the LPM regime — approximately 240 organisations across 12 sectors:

- Alimentation (food)
- Communications électroniques + audiovisuel + information
- Énergie (energy)
- Espace + recherche (space + research)
- Finances
- Gestion de l'eau (water management)
- Industrie (industry — civilian segments)
- Judiciaire (judicial)
- Militaire (military — civilian-controlled segments)
- Santé (health)
- Transports (rail, air, maritime, road)
- Activités civiles de l'État (civil State activities)

The 2024 NIS2 transposition under Décret 2024-405 extends to:

- **REC** (Réseau d'Entités Critiques) — Critical Entities Network — a parallel designation for entities not previously OIV
- **REI** (Réseau d'Entités Importantes) — Important Entities Network — a broader population with lighter obligations

Some entities hold dual regime obligations (OIV + REC or OIV + REI).

**Territorial scope.** France métropolitaine + DROM-COM (Départements et Régions d'Outre-Mer + Collectivités d'Outre-Mer). Some sub-sectoral nuances apply for entities in Mayotte, Wallis-et-Futuna, etc. Foreign-headquartered entities reached through their French operations. Cross-border data flows for European subsidiaries route through ANSSI bilateral coordination with BSI (Germany), GCHQ-NCSC (UK), CCN (Spain).

## 3. Catalogue coverage at a glance

- **Clauses tracked**: 8
- **Clauses covered by at least one UC**: 8 / 8 (100.0%)
- **Priority-weighted coverage**: 100.0%
- **Contributing UCs**: 8 (UC-22.58.1 through UC-22.58.8)

Coverage methodology is documented in [`docs/coverage-methodology.md`](../coverage-methodology.md). Priority weights come from `data/regulations.json` commonClauses entries.

## 4. Clause-by-clause coverage

Clauses are listed in the order defined by `data/regulations.json commonClauses` for this regulation version. A clause is considered covered when at least one UC sidecar has a `compliance[]` entry matching `(regulation, version, clause)`. Assurance is the maximum across contributing UCs.

| Clause | Topic | Priority | Assurance | UCs |
|---|---|---|---|---|
| `LPM-Art-R1332-41-1` | OIV designation register + SAIV scope-change notification | 1.0 | `full` | UC-22.58.1 |
| `LPM-Art-R1332-41-10` | 72-hour cyber-incident reporting to ANSSI via CERT-FR | 1.0 | `full` | UC-22.58.2 |
| `LPM-PSSI-MCAS-Art-R1332-41-2` | PSSI-MCAS (20 règles d'hygiène) compliance scorecard | 1.0 | `partial` | UC-22.58.3 |
| `LPM-Art-R1332-41-11` | Mandatory PASSI-qualified audit ledger + remediation closure | 1.0 | `full` | UC-22.58.4 |
| `LPM-Art-R1332-41-13` | ANSSI-qualified product (visa, CSPN, CC) procurement evidence | 1.0 | `partial` | UC-22.58.5 |
| `LPM-AIE-Art-R1332-41-2` | SAIV segmentation + AIE zone-boundary surveillance | 1.0 | `full` | UC-22.58.6 |
| `LPM-NIS2-Decret-2024-405` | LPM/NIS2 transposition tracker — dual-regime reconciliation | 0.7 | `partial` | UC-22.58.7 |
| `LPM-master-rollup` | Master compliance dashboard + Direction Générale attestation | 1.0 | `full` | UC-22.58.8 |

## 5. Evidence collection

### 5.1 Common evidence sources

- ServiceNow Security Incident Response (`snow:sir`) for incident tickets with `lpm_in_scope` flag.
- ServiceNow GRC for the OIV designation register, RSSI roster, PASSI audit register, derogation register.
- CERT-FR submission API (`cert-fr:submission`) — direct submission integration.
- ANSSI visa register (sync from cyber.gouv.fr/produits-services-qualifies).
- Microsoft Defender for Endpoint, CrowdStrike Falcon<sup class="ref">[<a href="#ref-1">1</a>]</sup>, Palo Alto Networks firewall.
- Stormshield SNS (French national champion firewall — qualified for OIV).
- Fortinet FortiGate<sup class="ref">[<a href="#ref-4">4</a>]</sup>, Cisco Secure Firewall FTD.
- Nozomi Guardian / Vantage, Claroty CTD / xDome (for OT-OIV).
- CyberArk PAM session records.
- Tenable Nessus + Tenable.ot scans.
- ANSSI CSPN-qualified product evidence.
- French CERT-FR Cybersecurity-Notice (CSN) feed and IOC distribution.
- PASSI auditor evidence packs (signed PDF + XLSX).

### 5.2 Retention requirements

| Artifact | Retention | Legal basis |
|---|---|---|
| CERT-FR 72-hour incident notification + supplementary updates | Lifetime of SAIV + 5 years | Code de la défense Art. R.1332-41-10; ANSSI guidance |
| PASSI tri-annual audit report (signed by qualified auditor) | Minimum 10 years | Art. R.1332-41-11; ANSSI PASSI référentiel |
| PSSI-MCAS evidence per règle (20 règles) | Minimum 7 years rolling | Art. R.1332-41-2; ANSSI 20-rules guidance |
| OIV designation register + SAIV scope-change | Lifetime of designation + 7 years | Art. R.1332-41-1 |
| Derogation register (ANSSI-approved deviations) | Duration of derogation + 7 years | ANSSI derogation policy |
| ANSSI-qualified product procurement evidence | Lifetime of deployment + 5 years | Art. R.1332-41-13 |
| AIE matrix + zone-assignment register | Lifetime of architecture + 5 years | Art. R.1332-41-2; ANSSI Cartographie guide |
| Délégué OIV monthly attestation | Minimum 7 years | Internal governance + ANSSI inspection authority |
| RSSI roster + qualification records | Duration of role + 5 years | Internal governance |
| LPM/NIS2 reconciliation register | Minimum 7 years rolling | Décret 2024-405; ANSSI guidance |
| Master compliance scorecard archived snapshots | Daily snapshot, 7-year rolling retention | Internal governance |

> Retention figures above are minimums or regulator-stated expectations. Where personal-data content appears in evidence packets, GDPR<sup class="ref">[<a href="#ref-3">3</a>]</sup> Art.5(1)(e) storage-limitation principle drives shorter retention for the personal-data fields, while the evidence-of-compliance retention retains the longer period (anonymised). National-security restrictions under Code de la défense may extend retention for safety-impacting SAIV (rare).

### 5.3 Evidence integrity expectations

All LPM evidence must be tamper-evident and produced in French (linguistic precision matters). The Splunk catalogue archives every UC-22.58.x result row to the `audit_evidence` summary index with a stable marker (`uc=22.58.X,reg=FR-LPM,clause=...`). Recommended pattern: RFC 3161 time-stamping via DocuSign France or DigiCert FR + ServiceNow GRC immutable-audit-log mode. Délégué OIV personally signs the monthly attestation (qualified-electronic-signature equivalent, eIDAS-compliant).

## 6. Control testing procedures

### 6.1 Inspector-style testing

An ANSSI inspector or PASSI auditor typically tests:

- **72-hour clock**: synthetic incident scenario; verify Délégué OIV activates workflow, CERT-FR submission queued within 4 hours, executed within 72 hours.
- **PSSI-MCAS attestation**: pick a named règle (e.g. Règle 6 — administration sécurisée); demonstrate evidence with continuous monitoring, not snapshot.
- **PASSI audit closure**: ask for the most recent PASSI report and the closure status of every finding.
- **AIE conformity**: pick a named zone-pair; demonstrate AIE-matrix conformance with current firewall rule-set audit.
- **ANSSI-visa procurement**: pick a named SAIV-protecting product; demonstrate visa de sécurité currency.
- **LPM/NIS2 dual-regime**: for dual-regime entities, demonstrate parallel obligations without duplicate reporting.

### 6.2 Internal Délégué OIV testing

Quarterly self-test:

1. Trigger a synthetic incident in dev environment matching UC-22.58.2.
2. Confirm the 72-hour clock fires correctly.
3. Confirm CERT-FR submission would have been queued and transmitted.
4. Pause before submission; document in `audit_evidence` with `lpm_exercise_id=Q...`.

## 7. Roles and responsibilities

- **Délégué OIV** — Designated by the OIV legal entity, named to ANSSI, holds personal liability for LPM compliance signatures and CERT-FR submissions.
- **Responsable de la Sécurité des Systèmes d'Information (RSSI)** — Chief Information Security Officer; oversees PSSI-MCAS implementation and SOC operations.
- **DSI (Direction des Systèmes d'Information)** — Chief Information Officer; oversees IT control implementation.
- **Direction Générale** — Executive leadership; receives monthly LPM compliance scorecard.
- **PASSI auditeur agréé** — Independent ANSSI-qualified auditor (e.g. ITrust, Sopra Steria, Atos, Capgemini Sogeti, Almond, Lexsi).
- **ANSSI / CERT-FR liaison** — Regulator interface, including CERT-FR submission and ANSSI inspector relationship.
- **Direction Juridique** — Manages LPM/NIS2 dual-regime obligations and Décret 2024-405 transposition.
- **Procurement Manager** — Owns the ANSSI visa register and qualified-product procurement.

## 8. Authoritative guidance

- Code de la défense Articles R.1332-41-1 à R.1332-41-22: [https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006071307/LEGISCTA000032295434/](https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006071307/LEGISCTA000032295434/)
- Loi n° 2013-1168 du 18 décembre 2013 (LPM 2014-2019): [https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000028338825](https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000028338825)
- ANSSI — Règlement OIV: [https://cyber.gouv.fr/oiv-et-oiv-services-numeriques](https://cyber.gouv.fr/oiv-et-oiv-services-numeriques)
- ANSSI — Loi de Programmation Militaire (LPM): [https://cyber.gouv.fr/loi-de-programmation-militaire-lpm](https://cyber.gouv.fr/loi-de-programmation-militaire-lpm)
- ANSSI — Règles d'hygiène applicable au SAIV (20 règles): [https://cyber.gouv.fr/publications/regles-dhygiene-applicables-aux-saiv](https://cyber.gouv.fr/publications/regles-dhygiene-applicables-aux-saiv)
- ANSSI — Cartographie du système d'information (AIE guidance): [https://cyber.gouv.fr/publications/cartographie-du-systeme-dinformation](https://cyber.gouv.fr/publications/cartographie-du-systeme-dinformation)
- ANSSI — Référentiel PASSI: [https://cyber.gouv.fr/passi](https://cyber.gouv.fr/passi)
- ANSSI — Produits et services qualifiés: [https://cyber.gouv.fr/produits-services-qualifies](https://cyber.gouv.fr/produits-services-qualifies)
- Décret n° 2024-405 du 8 mai 2024 (NIS2 transposition): [https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000049532193](https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000049532193)
- ANSSI — NIS2 / REC / REI: [https://cyber.gouv.fr/nis-2-directive-pour-un-niveau-eleve-commun-de-cybersecurite-dans-lunion](https://cyber.gouv.fr/nis-2-directive-pour-un-niveau-eleve-commun-de-cybersecurite-dans-lunion)
- CERT-FR portal: [https://www.cert.ssi.gouv.fr/](https://www.cert.ssi.gouv.fr/)

## 9. Common audit deficiencies

1. **CERT-FR submission late** — Classification deferred; mitigated by UC-22.58.2 conservative LPM-classification trigger.
2. **PSSI-MCAS as snapshot** — Annual checklist; mitigated by UC-22.58.3.
3. **PASSI audit findings carry over** — Remediation not closed; mitigated by UC-22.58.4.
4. **Non-qualified product on SAIV** — Most-cited PASSI finding; mitigated by UC-22.58.5.
5. **AIE matrix staleness** — Architecture evolves without matrix update; mitigated by UC-22.58.6 continuous flow surveillance.
6. **LPM/NIS2 double reporting** — Single incident reported twice; mitigated by UC-22.58.7 reconciliation matrix.
7. **Délégué OIV personal-liability gap** — Délégué not personally engaged in monthly attestation; mitigated by UC-22.58.8 attestation cadence.
8. **Linguistic imprecision** — Evidence in English-only when French required; remediation: translate at point-of-submission.
9. **Arrêté ministériel update missed** — Sector scope changes; mitigated by UC-22.58.1 annual reconciliation.

## 10. Enforcement and penalties

Civil and criminal penalties under Code pénal + Code de la défense:

- **Art. 1332-7 Code de la défense — Failure to comply with ANSSI direction**: amende up to €750,000 + imprisonment up to 3 years.
- **Art. L1332-6-1 Code de la défense — Failure to declare cyber incident**: amende + imprisonment.
- **Personal liability of Délégué OIV**: civil + criminal under named-officer principle.

ANSSI has investigative authority including inspection-on-demand. Délégué OIV personally signs declarations and bears the legal consequence.

## 11. Questions an ANSSI / PASSI inspector should ask

- Montrez-moi le registre actuel des Délégué OIV avec coordonnées, qualification et la rotation d'astreinte sur 90 jours.
- Présentez la dernière soumission CERT-FR (Form A). Incluez les horodatages, le membre de l'équipe qui a soumis, et le récépissé CERT-FR.
- Choisissez une règle PSSI-MCAS. Démontrez la surveillance en continu pour le SAIV nommé ce matin.
- Présentez le dernier rapport d'audit PASSI et le statut de fermeture de chaque écart.
- Pour un produit déployé sur SAIV, démontrez la validité actuelle du visa ANSSI.
- Présentez le dernier exercice de simulation d'incident LPM et l'après-action.
- Pour une entité à double régime (LPM + NIS2 REC), démontrez la réconciliation et l'absence de doublon de déclaration.
- Présentez la dernière attestation mensuelle signée par le Délégué OIV.

## 12. Machine-readable twin

- API endpoint: `api/v1/compliance/story/fr-lpm.json`
- Raw clause data: `data/regulations.json` (id=`fr-lpm`)
- Per-UC sidecar files: `content/cat-22-regulatory-compliance/UC-22.58.*.json`
- Coverage methodology: `docs/coverage-methodology.md`

## 13. Provenance and regeneration

This evidence pack is regenerated as part of the catalogue build. Manual narrative sections (purpose, scope, common deficiencies, inspector questions) are authored; clause coverage tables are computed from UC sidecar `compliance[]` arrays. Last reviewed: 2026-05-13. Linguistic note: ANSSI / PASSI inspector questions presented in French to match official auditor practice.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** CrowdStrike Holdings, Inc. (2026). *CrowdStrike Falcon Documentation*. CrowdStrike. Retrieved May 11, 2026, from https://falcon.crowdstrike.com/documentation

<a id="ref-2"></a>**[2]** European Parliament and Council of the European Union. (2022, December). *Directive (EU) 2022/2555 — NIS2 Directive on cybersecurity*. Official Journal of the European Union, L 333. ELI: dir/2022/2555. https://eur-lex.europa.eu/eli/dir/2022/2555/oj

<a id="ref-3"></a>**[3]** European Parliament and Council of the European Union. (2016, April). *Regulation (EU) 2016/679 — General Data Protection Regulation*. Official Journal of the European Union, L 119. ELI: reg/2016/679. https://eur-lex.europa.eu/eli/reg/2016/679/oj

<a id="ref-4"></a>**[4]** Fortinet, Inc. (2026). *Fortinet FortiOS Documentation*. Retrieved May 11, 2026, from https://docs.fortinet.com/product/fortigate

<a id="ref-5"></a>**[5]** Palo Alto Networks, Inc. (2026). *Palo Alto Networks PAN-OS Documentation*. Retrieved May 11, 2026, from https://docs.paloaltonetworks.com/pan-os

<details>
<summary>Additional online sources cited in the document body (11)</summary>

<a id="ref-6"></a>**[6]** cyber.gouv.fr. *cyber.gouv.fr: Loi De Programmation Militaire Lpm*. Retrieved May 11, 2026, from https://cyber.gouv.fr/loi-de-programmation-militaire-lpm

<a id="ref-7"></a>**[7]** legifrance.gouv.fr. *legifrance.gouv.fr: Legiscta000032295434*. Retrieved May 11, 2026, from https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006071307/LEGISCTA000032295434/

<a id="ref-8"></a>**[8]** legifrance.gouv.fr. *legifrance.gouv.fr: Jorftext000028338825*. Retrieved May 11, 2026, from https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000028338825

<a id="ref-9"></a>**[9]** cyber.gouv.fr. *cyber.gouv.fr: Oiv Et Oiv Services Numeriques*. Retrieved May 11, 2026, from https://cyber.gouv.fr/oiv-et-oiv-services-numeriques

<a id="ref-10"></a>**[10]** cyber.gouv.fr. *cyber.gouv.fr: Regles Dhygiene Applicables Aux Saiv*. Retrieved May 11, 2026, from https://cyber.gouv.fr/publications/regles-dhygiene-applicables-aux-saiv

<a id="ref-11"></a>**[11]** cyber.gouv.fr. *cyber.gouv.fr: Cartographie Du Systeme Dinformation*. Retrieved May 11, 2026, from https://cyber.gouv.fr/publications/cartographie-du-systeme-dinformation

<a id="ref-12"></a>**[12]** cyber.gouv.fr. *cyber.gouv.fr: Passi*. Retrieved May 11, 2026, from https://cyber.gouv.fr/passi

<a id="ref-13"></a>**[13]** cyber.gouv.fr. *cyber.gouv.fr: Produits Services Qualifies*. Retrieved May 11, 2026, from https://cyber.gouv.fr/produits-services-qualifies

<a id="ref-14"></a>**[14]** legifrance.gouv.fr. *legifrance.gouv.fr: Jorftext000049532193*. Retrieved May 11, 2026, from https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000049532193

<a id="ref-15"></a>**[15]** cyber.gouv.fr. *cyber.gouv.fr: Nis 2 Directive Pour Un Niveau Eleve Commun De Cybersecurite Dans Lunion*. Retrieved May 11, 2026, from https://cyber.gouv.fr/nis-2-directive-pour-un-niveau-eleve-commun-de-cybersecurite-dans-lunion

<a id="ref-16"></a>**[16]** cert.ssi.gouv.fr. *cert.ssi.gouv.fr*. Retrieved May 11, 2026, from https://www.cert.ssi.gouv.fr/

</details>

<!-- END-AUTOGENERATED-SOURCES -->
