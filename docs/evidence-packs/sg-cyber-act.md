# Evidence Pack — Singapore Cybersecurity Act 2018 (with 2024 Amendment)

> **Tier**: Tier 1 &nbsp;·&nbsp; **Jurisdiction**: Singapore &nbsp;·&nbsp; **Version**: `2024-amendment`
>
> **Full name**: Cybersecurity Act 2018 (Act 9 of 2018) as amended by the Cybersecurity (Amendment) Act 2024 + Cybersecurity Code of Practice (CCoP) 2.0
> **Authoritative source**: [https://sso.agc.gov.sg/Act/CA2018](https://sso.agc.gov.sg/Act/CA2018)
> **Effective from**: 2018-08-31 (CSA Act); 2024-amendment effective 2024-12 (CIISP, FDI, ESCI provisions)
>
> This evidence pack is the auditor-facing view of the Splunk monitoring catalogue's coverage of the Singapore Cybersecurity Act. Every clause coverage claim is traceable to a specific UC sidecar JSON file (`content/cat-22-regulatory-compliance/UC-22.57.*.json`); every retention figure cites its legal basis; every URL resolves to an official Cyber Security Agency of Singapore (CSA) or AGC source. Interpretation stays with the Cybersecurity Officer (CO) and the Commissioner of Cybersecurity.

> **Live views.** [Buyer narrative (`compliance-story.html?reg=sg-cyber-act`)](../../compliance-story.html?reg=sg-cyber-act) · [Auditor clause navigator (`clause-navigator.html#reg=sg-cyber-act`)](../../clause-navigator.html#reg=sg-cyber-act) · [JSON twin (`api/v1/compliance/story/sg-cyber-act.json`)](../../api/v1/compliance/story/sg-cyber-act.json)

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
11. [Questions a CSA inspector should ask](#11-questions-a-csa-inspector-should-ask)
12. [Machine-readable twin](#12-machine-readable-twin)
13. [Provenance and regeneration](#13-provenance-and-regeneration)

## 1. Purpose of this evidence pack

Singapore's Cybersecurity Act 2018 (Act 9 of 2018) is the primary statute administered by the Cyber Security Agency of Singapore (CSA). It establishes a regime for the designation, designation-change, and protection of Critical Information Infrastructure (CII) supporting essential services in Singapore. The Cybersecurity Code of Practice (CCoP 2.0), issued under §11 of the Act, specifies mandatory technical and organisational controls. The 2024 Cybersecurity (Amendment) Act extends the regime to Critical Information Infrastructure Service Providers (CIISPs), Foundational Digital Infrastructure (FDI), and Entities of Special Cybersecurity Interest (ESCI), and tightens DNS / TLD obligations through IDA / SGNIC. CII owners must register the asset with the Commissioner of Cybersecurity, designate a Cybersecurity Officer (CO) and Alternate, report cyber incidents within 2 hours (initial) and 14 days (detailed) to the National Cyber Incident Response Centre (NCIRC), undergo a bi-annual CSA-approved independent cybersecurity audit, conduct an annual risk assessment, participate in Exercise Cyber Star, and submit to mandatory penetration testing.

## 2. Scope and applicability

Applies to:

- **CII Owners** designated by the Commissioner of Cybersecurity under §7 of the Act across 11 essential-services sectors: Banking & Finance, Energy, Water, Healthcare, Transport (Land, Maritime, Aviation), InfoComm, Security & Emergency Services, Aviation, Maritime, Government, and Media.
- **CIISP** (Critical Information Infrastructure Service Providers) — third-party providers who serve CII owners with cybersecurity functions; designated under §16D of the amended Act.
- **FDI** (Foundational Digital Infrastructure) — public cloud, data centres, exchanges; designated under §16D.
- **ESCI** (Entities of Special Cybersecurity Interest) — entities with strategic cyber significance; designated under §16D.
- **IDA / SGNIC Domain Name Registrar/Registry** — Internet infrastructure obligations.

Excludes: non-Singapore-designated entities; entities below CSA designation threshold; entities under sector-specific cybersecurity regimes not bridged through the Cybersecurity Act.

**Territorial scope.** Singapore. Foreign-headquartered entities reached through their Singapore subsidiaries / branches. PDPA cyber-overlay reaches data-breach obligations beyond CII scope but is co-regulated through the PDPC.

## 3. Catalogue coverage at a glance

- **Clauses tracked**: 15
- **Clauses covered by at least one UC**: 15 / 15 (100.0%)
- **Priority-weighted coverage**: 100.0%
- **Contributing UCs**: 15 (UC-22.57.1 through UC-22.57.15)

Coverage methodology is documented in [`docs/coverage-methodology.md`](../coverage-methodology.md). Priority weights come from `data/regulations.json` commonClauses entries.

## 4. Clause-by-clause coverage

Clauses are listed in the order defined by `data/regulations.json commonClauses` for this regulation version. A clause is considered covered when at least one UC sidecar has a `compliance[]` entry matching `(regulation, version, clause)`. Assurance is the maximum across contributing UCs.

| Clause | Topic | Priority | Assurance | UCs |
|---|---|---|---|---|
| `CSA-s7` | CII designation + scope-change notification to CSA within 2 hours | 1.0 | `full` | UC-22.57.1 |
| `CSA-s14` | 2-hour initial + 14-day detailed CII incident reporting to NCIRC | 1.0 | `full` | UC-22.57.2 |
| `CSA-CCoP-2.0` | CCoP 2.0 compliance scorecard | 1.0 | `full` | UC-22.57.3 |
| `CSA-s15-risk-assessment` | Annual cybersecurity risk assessment + Commissioner submission | 1.0 | `full` | UC-22.57.4 |
| `CSA-s15-audit` | Bi-annual CSA-approved independent cybersecurity audit | 1.0 | `full` | UC-22.57.5 |
| `CSA-Exercise-Cyber-Star` | Annual cybersecurity exercise + Exercise Cyber Star participation | 1.0 | `full` | UC-22.57.6 |
| `CSA-s15-pentest` | Mandatory penetration test scheduling + remediation closure | 1.0 | `full` | UC-22.57.7 |
| `CSA-s16D-CIISP` | CIISP register + obligations tracker (2024 amendment) | 0.7 | `full` | UC-22.57.8 |
| `CSA-s16D-FDI` | Foundational Digital Infrastructure provider obligations (2024) | 0.7 | `full` | UC-22.57.9 |
| `CSA-s16D-ESCI` | Entities of Special Cybersecurity Interest (2024) — 2-hr reporting | 1.0 | `full` | UC-22.57.10 |
| `CSA-DNS-SGNIC` | IDA / SGNIC Domain Name Registrar/Registry obligations + DNSSEC | 0.7 | `full` | UC-22.57.11 |
| `CSA-CTSP-AISP` | CII Threat-Sharing Programme + AISP integration health | 0.7 | `full` | UC-22.57.12 |
| `CSA-PDPA-overlay` | CSA + PDPA cyber-overlay — data-breach correlation | 0.7 | `full` | UC-22.57.13 |
| `CSA-CCoP-CRY` | CCoP §CRY — cryptographic key management + HSM attestation | 0.7 | `partial` | UC-22.57.14 |
| `CSA-master-rollup` | Master CSA compliance dashboard + Commissioner attestation | 1.0 | `full` | UC-22.57.15 |

## 5. Evidence collection

### 5.1 Common evidence sources

- ServiceNow Security Incident Response (`snow:sir`) for incident tickets, classification, owner assignment.
- ServiceNow GRC for the CII registration, CO + Alternate roster, audit register, exercise participation register, pentest schedule.
- CSA Form A and Form B submission receipts ingested via HEC (`hec:csa:submission`).
- CSA-approved auditor evidence packs (typically signed XLSX + PDF).
- Microsoft 365 / Azure AD audit logs.
- AWS CloudTrail<sup class="ref">[<a href="#ref-2">2</a>]</sup> and GuardDuty.
- Palo Alto Networks firewall + Prisma Cloud.
- CrowdStrike Falcon<sup class="ref">[<a href="#ref-3">3</a>]</sup> Data Replicator.
- Microsoft Defender for Endpoint.
- CyberArk PAM session records.
- Tenable Nessus + Tenable.ot scans.
- CSA Cybersecurity-Notice (CSN) and IOC distribution feed (`csa:csn:feed`).
- Singapore National Cyber Threat Sensor Network (NCTSN) bulletins.
- HSM audit (Thales Luna, AWS KMS, Azure Key Vault).
- PDPC (Personal Data Protection Commission) data-breach notification correspondence for PDPA cyber-overlay.

### 5.2 Retention requirements

| Artifact | Retention | Legal basis |
|---|---|---|
| CSA Form A (initial 2-hour CII incident report) | Minimum 10 years from submission | Cybersecurity Act §14; 10-year statute-of-limitations for CII offences |
| CSA Form B (14-day detailed report) | Minimum 10 years from submission | Cybersecurity Act §14 |
| Bi-annual CSA-approved independent audit report | Minimum 10 years rolling | Cybersecurity Act §15(2); CCoP Audit Annex |
| Annual cybersecurity risk assessment | Minimum 7 years rolling | Cybersecurity Act §15(1) |
| Exercise Cyber Star participation record + after-action | Minimum 7 years | CSA Exercise Cyber Star Programme |
| Penetration test report + remediation closure | Minimum 7 years rolling | CCoP §IS; pentest cycle |
| CII registration + scope-change notifications | Lifetime of CII designation + 7 years | Cybersecurity Act §7 |
| Cybersecurity Officer + Alternate roster | Duration of roster + 5 years | Cybersecurity Act §10 |
| CCoP attestation evidence (per control family) | Minimum 5 years rolling | CCoP 2.0 Annex |
| CIISP / FDI / ESCI compliance records (2024 amendment) | Minimum 7 years rolling | Cybersecurity (Amendment) Act 2024 §16D |
| DNSSEC / DNS infrastructure logs | Minimum 5 years rolling | IDA / SGNIC obligations |
| CTSP / AISP threat-sharing records | Minimum 3 years rolling | CSA Threat-Sharing Programme |
| PDPA data-breach notification (cyber-overlay) | Minimum 5 years | PDPA §26B + CSA correlation |
| HSM attestation + key rotation records | Lifetime of key + 5 years | CCoP §CRY + FIPS 140-3 |
| Master compliance scorecard snapshots | Daily snapshot, 5-year rolling retention | Internal governance + CSA inspection |

> Retention figures above are minimums. PDPA personal-data content scrubbing applies where personal data appears in evidence packets. The 10-year statute-of-limitations for CII offences under the Cybersecurity Act drives the longer retention period for CSA Forms.

### 5.3 Evidence integrity expectations

All CSA evidence must be tamper-evident. The Splunk catalogue archives every UC-22.57.x result row to the `audit_evidence` summary index with a stable marker (`uc=22.57.X,reg=SG-Cyber-Act,clause=...`). Recommended pattern: RFC 3161 time-stamping + ServiceNow GRC immutable-audit-log mode. CO's manual annotation in ServiceNow GRC with author + timestamp.

## 6. Control testing procedures

### 6.1 Inspector-style testing

A CSA inspector typically tests:

- **2-hour clock**: synthetic incident scenario; verify CO activates workflow, Form A submission queued within 30 minutes, executed within 2 hours.
- **CO availability**: random pick; verify 24x7 reachability, Alternate readiness.
- **CCoP attestation**: pick a named CCoP control family; demonstrate evidence with continuous monitoring, not snapshot.
- **Risk assessment cadence**: ask for the most recent risk assessment; check Commissioner submission receipt and corrective-action progress.
- **Audit cadence**: ask for the most recent CSA-approved audit; verify remediation closure.
- **Exercise Cyber Star**: ask for participation evidence; check after-action report and closure status.

### 6.2 Internal Cybersecurity Officer testing

Quarterly self-test:

1. Trigger a synthetic incident in dev environment matching UC-22.57.2.
2. Confirm the 2-hour clock fires correctly.
3. Confirm Form A submission would have been queued and transmitted.
4. Pause before submission; document in `audit_evidence` with `csa_exercise_id=Q...`.

## 7. Roles and responsibilities

- **Cybersecurity Officer (CO)** — Designated under §10, 24x7 reachable, holds personal liability for CSA compliance.
- **Alternate Cybersecurity Officer (Alt CO)** — Same designation, ready to take over.
- **Chief Information Security Officer (CISO)** — Oversees CCoP control families.
- **Commissioner of Cybersecurity** — CSA leadership; receives Forms A/B, audit reports, risk assessments.
- **CSA-approved auditor** — Independent third-party (e.g. PwC, Deloitte, EY, KPMG with CSA accreditation).
- **PDPC liaison** — Personal Data Protection Commission contact for cyber-overlay.
- **CIISP / FDI / ESCI representative** — Where applicable, the designated contact under the 2024 amendment.

## 8. Authoritative guidance

- Cybersecurity Act 2018 + 2024 amendment: [https://sso.agc.gov.sg/Act/CA2018](https://sso.agc.gov.sg/Act/CA2018)
- Cybersecurity Code of Practice (CCoP) 2.0: [https://www.csa.gov.sg/legislation/code-of-practice](https://www.csa.gov.sg/legislation/code-of-practice)
- Cybersecurity Code of Practice for CII (technical detail): [https://www.csa.gov.sg/legislation/critical-information-infrastructure](https://www.csa.gov.sg/legislation/critical-information-infrastructure)
- CSA National Cyber Incident Response Centre: [https://www.csa.gov.sg/our-programmes/Cyber-Security-Agency-of-Singapore/national-cyber-incident-response-centre](https://www.csa.gov.sg/our-programmes/Cyber-Security-Agency-of-Singapore/national-cyber-incident-response-centre)
- Exercise Cyber Star: [https://www.csa.gov.sg/our-programmes/cyber-readiness/exercise-cyber-star](https://www.csa.gov.sg/our-programmes/cyber-readiness/exercise-cyber-star)
- Personal Data Protection Act 2012: [https://sso.agc.gov.sg/Act/PDPA2012](https://sso.agc.gov.sg/Act/PDPA2012)
- IDA / SGNIC DNSSEC requirements: [https://www.sgnic.sg/](https://www.sgnic.sg/)

## 9. Common audit deficiencies

1. **CO availability lapses** — On-call drift; mitigated by UC-22.57.1's CO roster surveillance.
2. **2-hour clock fired late** — Classification deferred; mitigated by UC-22.57.2 conservative trigger.
3. **CCoP attestation snapshot** — Annual checklist rather than continuous evidence; mitigated by UC-22.57.3.
4. **Risk assessment as desktop exercise** — Inadequate validation; mitigated by UC-22.57.4.
5. **Audit findings carry over multiple cycles** — Remediation not closed; mitigated by UC-22.57.5.
6. **Pentest as compliance checkbox** — Findings not remediated; mitigated by UC-22.57.7.
7. **CIISP / FDI / ESCI scope misclassification** — Failure to recognise 2024-amendment scope; mitigated by UC-22.57.8/9/10.
8. **DNSSEC partial deployment** — Some .sg zones unprotected; mitigated by UC-22.57.11.
9. **PDPA / CSA reporting mismatch** — Single incident reported under only one regime; mitigated by UC-22.57.13.
10. **HSM rotation lag** — Cryptographic keys exceed rotation window; mitigated by UC-22.57.14.

## 10. Enforcement and penalties

Civil and criminal penalties under §17–§21 of the Cybersecurity Act:

- **§17 — Failure to comply with CSA direction**: fine up to S$100,000 (organisation) or S$25,000 (individual) or imprisonment up to 2 years.
- **§19 — Failure to report CII incident**: fine up to S$25,000.
- **§24 — CII-related offence**: fine up to S$100,000 + statutory imprisonment.

10-year statute-of-limitations applies to CII offences. Commissioner of Cybersecurity has investigative authority including subpoena power under §15.

## 11. Questions a CSA inspector should ask

- Show me the current Cybersecurity Officer roster with NRIC / FIN, phone numbers, and on-call rotation for the next 90 days.
- Walk me through the most recent CSA Form A submission. Include timestamps, the staff member who submitted, and the NCIRC receipt.
- Pick a CCoP control family. Demonstrate continuous monitoring of that family for the named CII this morning.
- Show me the most recent CSA-approved audit report and the closure status of every finding.
- Show me Exercise Cyber Star participation evidence and after-action report.
- Walk me through the most recent risk assessment and the Commissioner submission.
- Show me the most recent penetration test report and remediation closure trail.
- For CIISP / FDI / ESCI entities (post-2024 amendment): demonstrate the relevant designated obligations and parallel reporting.

## 12. Machine-readable twin

- API endpoint: `api/v1/compliance/story/sg-cyber-act.json`
- Raw clause data: `data/regulations.json` (id=`sg-cyber-act`)
- Per-UC sidecar files: `content/cat-22-regulatory-compliance/UC-22.57.*.json`
- Coverage methodology: `docs/coverage-methodology.md`

## 13. Provenance and regeneration

This evidence pack is regenerated as part of the catalogue build. Manual narrative sections (purpose, scope, common deficiencies, inspector questions) are authored; clause coverage tables are computed from UC sidecar `compliance[]` arrays. Last reviewed: 2026-05-13.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** Amazon Web Services, Inc. (2026). *Amazon GuardDuty User Guide*. Retrieved May 11, 2026, from https://docs.aws.amazon.com/guardduty/latest/ug/what-is-guardduty.html

<a id="ref-2"></a>**[2]** Amazon Web Services, Inc. (2026). *AWS CloudTrail User Guide*. Retrieved May 11, 2026, from https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-user-guide.html

<a id="ref-3"></a>**[3]** CrowdStrike Holdings, Inc. (2026). *CrowdStrike Falcon Documentation*. CrowdStrike. Retrieved May 11, 2026, from https://falcon.crowdstrike.com/documentation

<a id="ref-4"></a>**[4]** Microsoft Corporation. (2026). *Microsoft Entra ID Documentation*. Retrieved May 11, 2026, from https://learn.microsoft.com/en-us/entra/identity/

<a id="ref-5"></a>**[5]** Palo Alto Networks, Inc. (2026). *Palo Alto Networks PAN-OS Documentation*. Retrieved May 11, 2026, from https://docs.paloaltonetworks.com/pan-os

<details>
<summary>Additional online sources cited in the document body (7)</summary>

<a id="ref-6"></a>**[6]** sso.agc.gov.sg. *sso.agc.gov.sg: Ca2018*. Retrieved May 11, 2026, from https://sso.agc.gov.sg/Act/CA2018

<a id="ref-7"></a>**[7]** csa.gov.sg. *csa.gov.sg: Code Of Practice*. Retrieved May 11, 2026, from https://www.csa.gov.sg/legislation/code-of-practice

<a id="ref-8"></a>**[8]** csa.gov.sg. *csa.gov.sg: Critical Information Infrastructure*. Retrieved May 11, 2026, from https://www.csa.gov.sg/legislation/critical-information-infrastructure

<a id="ref-9"></a>**[9]** csa.gov.sg. *csa.gov.sg: National Cyber Incident Response Centre*. Retrieved May 11, 2026, from https://www.csa.gov.sg/our-programmes/Cyber-Security-Agency-of-Singapore/national-cyber-incident-response-centre

<a id="ref-10"></a>**[10]** csa.gov.sg. *csa.gov.sg: Exercise Cyber Star*. Retrieved May 11, 2026, from https://www.csa.gov.sg/our-programmes/cyber-readiness/exercise-cyber-star

<a id="ref-11"></a>**[11]** sso.agc.gov.sg. *sso.agc.gov.sg: Pdpa2012*. Retrieved May 11, 2026, from https://sso.agc.gov.sg/Act/PDPA2012

<a id="ref-12"></a>**[12]** sgnic.sg. *sgnic.sg*. Retrieved May 11, 2026, from https://www.sgnic.sg/

</details>

<!-- END-AUTOGENERATED-SOURCES -->
