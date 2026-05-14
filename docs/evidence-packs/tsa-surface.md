# Evidence Pack — TSA Surface Cybersecurity Security Directives

> **Tier**: Tier 1 &nbsp;·&nbsp; **Jurisdiction**: US &nbsp;·&nbsp; **Version**: `2024-consolidated-pipeline-rail`
>
> **Full name**: Transportation Security Administration Security Directives — SD-Pipeline-2021-02C (gas/hazardous-liquid pipeline), SD-1580-2022-01 (freight rail), SD-1582-2022-01 (passenger rail), SD-1542/1544/1582-21-02 (aviation airport + airline)
> **Authoritative source**: [https://www.tsa.gov/for-industry/surface-transportation-cybersecurity](https://www.tsa.gov/for-industry/surface-transportation-cybersecurity)
> **Effective from**: 2021-07-20 (Pipeline SD-1); subsequent SDs through 2024 amendments
>
> This evidence pack is the auditor-facing view of the Splunk monitoring catalogue's coverage of the TSA Surface SD family across all four regulated modes (pipeline, freight rail, passenger rail, aviation). Every clause coverage claim is traceable to a specific UC sidecar JSON file (`content/cat-22-regulatory-compliance/UC-22.56.*.json`); every retention figure cites its legal basis; every URL resolves to an official TSA or DHS source. The pack does **not** assert legal conclusions — it tabulates what the catalogue covers, names the authoritative source, and flags gaps. Interpretation stays with counsel and the Cybersecurity Coordinator.

> **Live views.** [Buyer narrative (`compliance-story.html?reg=tsa-surface`)](../../compliance-story.html?reg=tsa-surface) · [Auditor clause navigator (`clause-navigator.html#reg=tsa-surface`)](../../clause-navigator.html#reg=tsa-surface) · [JSON twin (`api/v1/compliance/story/tsa-surface.json`)](../../api/v1/compliance/story/tsa-surface.json)

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
11. [Questions a TSA inspector should ask](#11-questions-a-tsa-inspector-should-ask)
12. [Machine-readable twin](#12-machine-readable-twin)
13. [Provenance and regeneration](#13-provenance-and-regeneration)

## 1. Purpose of this evidence pack

In response to the May 2021 Colonial Pipeline ransomware incident and the broader threat landscape against US surface transportation infrastructure, the Transportation Security Administration issued a cascade of Security Directives requiring designated owners and operators of critical pipeline, freight rail, passenger rail, and aviation infrastructure to implement specific cybersecurity controls and report cyber incidents to CISA within 24 hours. The SD framework operates outside the standard Notice and Comment Rulemaking process under TSA's expedited authority (49 U.S.C. § 114(l)(2)(A)) but a Final Rule is in preparation and is expected in late 2026. Until the Final Rule lands, the SD-based regime governs; for Pipeline operators it has been re-issued several times (SD-Pipeline-2021-01, -02A, -02B, -02C) and a parallel SD-Pipeline-2021-02D update is in interim form. Freight Rail and Passenger Rail (SD-1580/82-2022-01) and Aviation Airport/Airline (SD-1542/44/82-21-02) follow similar 24-hour reporting + four CIP control families architecture. Public transit operators are NPRM-scoped only, and SD-relevant FTA grantees may elect early voluntary alignment under the proposed Public Transportation Cybersecurity Rule.

## 2. Scope and applicability

Applies to TSA-designated owners and operators of:

- **Pipeline (SD-Pipeline-2021-02C)**: ~100 major operators of TSA-regulated gas and hazardous-liquid pipelines. Includes interstate pipelines, intrastate pipelines feeding interstate, and pipelines designated by TSA. Examples: Colonial, Kinder Morgan, Williams Companies, Energy Transfer, Enterprise Products Partners, Plains All American.
- **Freight Rail (SD-1580-2022-01)**: Class I freight railroads (BNSF, Union Pacific, CSX, Norfolk Southern, Canadian National, Canadian Pacific Kansas City) plus selected Class II railroads with TSA designation.
- **Passenger Rail (SD-1582-2022-01)**: Amtrak and TSA-designated commuter and intercity passenger rail (typically PTC-equipped operations). Some metropolitan transit systems are scoped under the related directives.
- **Aviation (SD-1542/44/82-21-02)**: TSA-regulated airports and airlines, primarily passenger-carrier operators and Category X / Category I airports with cyber-impacting flight operations or sensitive operational areas.

Excludes: smaller pipeline operators below TSA designation threshold; non-Class-I freight rail not specifically designated; non-PTC rail operations; small commercial airports below Category III. Public transit operators remain NPRM-scoped until the Public Transportation Cybersecurity Rule (proposed 2024) is finalised.

**Territorial scope.** Continental United States and territories. Foreign-headquartered operators are reached through their US operations (e.g. Canadian Pacific Kansas City through its US trackage; Canadian National through its US freight lanes). Cross-border data flows for Canadian Pacific and Canadian National route through the TSA SD framework via TSA-CCCS coordination.

## 3. Catalogue coverage at a glance

- **Clauses tracked**: 28
- **Clauses covered by at least one UC**: 28 / 28 (100.0%)
- **Priority-weighted coverage**: 100.0%
- **Contributing UCs**: 28 (UC-22.56.1 through UC-22.56.28)

Coverage methodology is documented in [`docs/coverage-methodology.md`](../coverage-methodology.md). Priority weights come from `data/regulations.json` commonClauses entries (see [`data/regulations.json`](../../data/regulations.json) priorityWeightRubric).

## 4. Clause-by-clause coverage

Clauses are listed in the order defined by `data/regulations.json commonClauses` for this regulation version. A clause is considered covered when at least one UC sidecar has a `compliance[]` entry matching `(regulation, version, clause)`. Assurance is the maximum across contributing UCs.

| Clause | Topic | Priority | Assurance | UCs |
|---|---|---|---|---|
| `TSA-SD-P-2021-02C-s1.A` | Cybersecurity Coordinator + Alternate designation | 1.0 | `full` | UC-22.56.2 |
| `TSA-SD-P-2021-02C-s1.B` | Cybersecurity Coordinator availability (24x7) and SSI-eligibility | 1.0 | `full` | UC-22.56.2 |
| `TSA-SD-P-2021-02C-s2` | 24-hour CISA cyber-incident reporting | 1.0 | `full` | UC-22.56.1 |
| `TSA-SD-P-2021-02C-s3.1` | CIP Control Family 1 — Network Segmentation Policies | 1.0 | `full` | UC-22.56.3 |
| `TSA-SD-P-2021-02C-s3.2` | CIP Control Family 2 — Access Control + MFA | 1.0 | `full` | UC-22.56.4 |
| `TSA-SD-P-2021-02C-s3.3` | CIP Control Family 3 — Continuous Monitoring + Threat Detection | 1.0 | `full` | UC-22.56.5 |
| `TSA-SD-P-2021-02C-s3.4` | CIP Control Family 4 — Risk-Based Patch Management | 1.0 | `full` | UC-22.56.6 |
| `TSA-SD-P-2021-02C-s4` | Cybersecurity Incident Response Plan + annual exercise | 1.0 | `full` | UC-22.56.7 |
| `TSA-SD-P-2021-02C-s5` | Cybersecurity Assessment Programme (CAP) annual self-assessment | 1.0 | `full` | UC-22.56.8 |
| `TSA-SD-1580-2022-01-s2-freight` | Freight rail 24-hour CISA + FRA parallel-notification | 1.0 | `full` | UC-22.56.9 |
| `TSA-SD-1582-2022-01-s2-passenger` | Passenger rail 24-hour CISA + FTA/FRA parallel-notification | 1.0 | `full` | UC-22.56.10 |
| `TSA-SD-1542-21-02-s2-aviation` | Aviation airport+airline 24-hour CISA + FAA parallel-notification | 1.0 | `full` | UC-22.56.11 |
| `TSA-SD-1542-21-02-s3.1-aviation` | Aviation CIP Control Family 1 — DCS/BHS/AOC segmentation | 1.0 | `full` | UC-22.56.12 |
| `TSA-SD-1542-21-02-s3.2-aviation` | Aviation CIP Control Family 2 — Access Control + MFA | 1.0 | `full` | UC-22.56.13 |
| `TSA-SD-1542-21-02-s3.3-aviation` | Aviation CIP Control Family 3 — Continuous Monitoring | 1.0 | `full` | UC-22.56.14 |
| `TSA-SD-1542-21-02-s3.4-aviation` | Aviation CIP Control Family 4 — Patch + Vulnerability Mgmt | 1.0 | `full` | UC-22.56.15 |
| `TSA-SD-cross-modal-third-party` | Multi-modal third-party / vendor remote-access surveillance | 1.0 | `full` | UC-22.56.16 |
| `TSA-SD-public-transit-NPRM` | Public Transit + FTA-grantee NPRM-aligned reporting scaffold | 0.7 | `partial` | UC-22.56.17 |
| `TSA-SD-cip-version-control` | CIP versioning + amendment audit trail | 1.0 | `full` | UC-22.56.18 |
| `TSA-SD-backup-rto` | Multi-modal backup integrity + RTO surveillance | 1.0 | `full` | UC-22.56.19 |
| `TSA-SD-log-retention` | Multi-modal log-retention + audit_evidence retention | 1.0 | `full` | UC-22.56.20 |
| `TSA-SD-personnel-security` | Multi-modal personnel-security + insider-threat detection | 0.7 | `full` | UC-22.56.21 |
| `TSA-SD-sbom-supply-chain` | Multi-modal SBOM ingest + supply-chain risk-score monitoring | 1.0 | `full` | UC-22.56.22 |
| `TSA-SD-threat-sharing` | Multi-modal CISA AIS / E-ISAC / ST-ISAC threat-sharing | 1.0 | `full` | UC-22.56.23 |
| `TSA-SD-phishing-credentials` | Multi-modal phishing + credential-harvesting surveillance | 1.0 | `full` | UC-22.56.24 |
| `TSA-SD-change-control` | Multi-modal change-control + privileged-change audit trail | 1.0 | `full` | UC-22.56.25 |
| `TSA-SD-PHMSA-dual-clock` | Pipeline TSA-PHMSA dual-clock coordination | 1.0 | `full` | UC-22.56.26 |
| `TSA-SD-soc-attestation` | Multi-modal SOC/CSOC tier coverage + on-call attestation | 0.7 | `full` | UC-22.56.27 |
| `TSA-SD-master-rollup` | Multi-modal master compliance scorecard + executive attestation | 1.0 | `full` | UC-22.56.28 |

## 5. Evidence collection

### 5.1 Common evidence sources

Auditors typically request the following records when examining this regulation:

- ServiceNow Security Incident Response (`snow:sir`) for incident tickets, classification, owner assignment, supplemental-report log.
- ServiceNow GRC for the CIP attestation register, Cybersecurity Coordinator roster, CAP submission tracker, CIRP exercise calendar.
- CISA Cyber Incident Reporting Portal submission receipts ingested via HEC (`hec:cisa:submission`).
- TSA / PHMSA / FRA / FTA / FAA parallel-notification correspondence (KV Store + email-to-HEC ingest).
- Cisco Cyber Vision, Claroty CTD, Nozomi Guardian, Dragos Platform, Armis Centrix for OT/ICS asset and detection visibility (pipeline SCADA, rail PTC, aviation DCS/BHS/AOC).
- Tenable.io / Tenable.ot scans against IT and OT (`tenable:io`, `tenable:ot`).
- CISA Known Exploited Vulnerabilities Catalog (`ta_cisa_kev:kev`) feed.
- CyberArk PAM session records for privileged-access incident context.
- Microsoft 365 / Azure AD audit logs (`o365:management`, `azuread:audit`, `azure:activity`).
- AWS CloudTrail / Microsoft Defender / CrowdStrike Falcon Data Replicator / Palo Alto Networks firewall.
- E-ISAC, ST-ISAC, A-ISAC threat-sharing feeds and CISA AIS bidirectional flow.
- DocuSign / Adobe Sign signed CIP amendment trail.

### 5.2 Retention requirements

| Artifact | Retention | Legal basis |
|---|---|---|
| 24-hour CISA cyber-incident report (Form 1 + Form 2) | Minimum 7 years from submission | TSA SD-Pipeline-2021-02C §2; CIRCIA NPRM § 226.18 alignment |
| CIP control-family attestation evidence (4 families) | Minimum 7 years rolling | TSA SD-Pipeline-2021-02C §3; CIP self-assessment guidance |
| CAP (Cybersecurity Assessment Programme) annual report | Minimum 7 years | TSA SD-Pipeline-2021-02C §5 |
| CIRP annual exercise after-action report | Minimum 5 years | TSA SD-Pipeline-2021-02C §4; ANSI N42.18-style retention |
| TSA SD amendment / CIP version-control trail (signed) | Lifetime of operations | TSA inspection authority under 49 U.S.C. § 114(l) |
| Cybersecurity Coordinator + Alternate roster + SSI eligibility | Duration of roster + 5 years | TSA SD-Pipeline-2021-02C §1; 49 CFR Part 1520 (SSI) |
| Backup integrity + RTO test evidence | Minimum 5 years rolling | TSA CIP best practice; CISA Pathway alignment |
| Personnel-security + insider-threat investigation records | Minimum 7 years from event close | TSA CIP §3 + EEOC/HR records governance |
| SBOM + supply-chain risk-score history | Minimum 5 years rolling | NIST SP 800-161 + TSA SD CIP §3 (supply chain) |
| Threat-sharing inbound/outbound (CISA AIS, E-ISAC, ST-ISAC, A-ISAC) | Minimum 5 years rolling | TSA CIP §3 + CISA threat-sharing guidance |
| Phishing + credential-harvesting investigation records | Minimum 3 years rolling | TSA SD-CIP §3 |
| Change-control records for SCADA/OT/NOTAM-relevant systems | Minimum 7 years | TSA CIP §3 + PHMSA dual-clock alignment (pipeline) |
| TSA-PHMSA dual-clock coordination records (pipeline) | Minimum 7 years | PHMSA 49 CFR Part 195 + TSA SD |
| SOC/CSOC on-call attestation records | Duration of roster + 3 years | TSA SD §3 + internal governance |
| Master compliance scorecard archived snapshots | Daily snapshot, 5-year rolling retention | Internal evidence-of-compliance governance |

> Retention figures above are the legal minimums or regulator-stated expectations. SSI-classified material (most CIP attestation evidence) must be handled per 49 CFR Part 1520. Pipeline operators must additionally align with PHMSA 49 CFR Part 195 for incident records that have safety-impacting elements. Aviation operators must align with FAA recordkeeping requirements for cyber-incidents that affect Part 121 / Part 135 operations.

### 5.3 Evidence integrity expectations

All TSA SD evidence must be tamper-evident. The Splunk catalogue archives every UC-22.56.x result row to the `audit_evidence` summary index with a stable marker (`uc=22.56.X,reg=TSA-Surface,clause=...`). The recommended pattern is RFC 3161 time-stamping via Adobe Sign / DigiCert Timestamp Authority, supplemented by ServiceNow GRC immutable-audit-log mode. Cybersecurity Coordinator's manual annotation should reside in ServiceNow GRC with author + timestamp + system-of-record link.

## 6. Control testing procedures

### 6.1 Inspector-style testing

A TSA Inspector typically tests the following on-site or remote:

- **24-hour clock**: artificially trigger a high-impact incident scenario (NDA-restricted), verify that the CC team activates the workflow and the CISA Portal submission is queued within 4 hours, executed within 24 hours, and the receipt is stored in `audit_evidence`.
- **CC availability**: pick a random weekend/holiday timestamp; verify that the on-call roster, the SMS/Webex alert, and the named Alternate were all reachable within 60 minutes.
- **CIP attestation**: ask the operator to demonstrate each of the four CIP control families with a specific named system (e.g. the Colonial Linden Junction control centre, the BNSF Network Operations Center PTC dispatch). Verify continuous monitoring evidence rather than annual snapshots.
- **CIRP exercise**: ask for the most recent exercise's after-action report and the resulting corrective-action ledger; confirm closure of all open actions.
- **Vendor remote-access**: pick a named third-party vendor (e.g. ABB, Honeywell, GE, Siemens, Rockwell for ICS/SCADA); verify just-in-time access grant, session-recording, and break-glass justification.

### 6.2 Internal Cybersecurity Coordinator testing

The CC team should run a quarterly self-test:

1. Trigger a synthetic incident in a Splunk dev environment matching UC-22.56.1's positive scenario.
2. Confirm the 24-hour clock is initiated correctly with the right markers.
3. Confirm the CISA Portal submission is queued and would have been transmitted.
4. Pause before submission and document the rehearsal in `audit_evidence` with `tsa_exercise_id=Q...`.
5. Replay any negative scenarios surfaced by UC-22.56.7's CIRP coordination.

## 7. Roles and responsibilities

- **Cybersecurity Coordinator (CC)** — Designated under SD §1.A, 24x7 reachable, holds personal liability for SD compliance and CIP attestation accuracy. Must be SSI-eligible.
- **Alternate Cybersecurity Coordinator (Alt CC)** — Same SSI eligibility, ready to take over the CC role within 60 minutes.
- **Chief Information Security Officer (CISO)** — Oversees CIP control families implementation; sign-off on CAP self-assessment annually.
- **Chief Information Officer / VP of IT** — Owns IT control implementation and Multi-Factor Authentication, segmentation infrastructure.
- **OT Security Lead** — Owns OT-specific CIP implementation (SCADA, PTC, DCS, BHS, AOC depending on mode).
- **VP of Operations** — Pipeline / Rail / Aviation operations leadership; co-approves CIRP exercise scope.
- **Government Affairs / Regulatory Counsel** — Manages TSA correspondence, PHMSA / FRA / FTA / FAA parallel-notifications, and Final-Rule monitoring.
- **VP of Procurement** — Owns the SBOM register and vendor cybersecurity attestations.
- **Internal Audit** — Conducts the CAP self-assessment and prepares the TSA Inspector ride-along.
- **Board Risk Committee** — Receives quarterly TSA SD compliance scorecard from UC-22.56.28.

## 8. Authoritative guidance

- TSA SD-Pipeline-2021-02C: [https://www.tsa.gov/sites/default/files/sd-pipeline-2021-02c.pdf](https://www.tsa.gov/sites/default/files/sd-pipeline-2021-02c.pdf)
- TSA SD-1580-2022-01 (Freight Rail): [https://www.tsa.gov/sites/default/files/sd-1580-2022-01.pdf](https://www.tsa.gov/sites/default/files/sd-1580-2022-01.pdf)
- TSA SD-1582-2022-01 (Passenger Rail): [https://www.tsa.gov/sites/default/files/sd-1582-2022-01.pdf](https://www.tsa.gov/sites/default/files/sd-1582-2022-01.pdf)
- TSA Aviation SDs (SD-1542/44/82-21-02): [https://www.tsa.gov/for-industry/aviation-cybersecurity](https://www.tsa.gov/for-industry/aviation-cybersecurity)
- CIRCIA + 6 USC § 681b: [https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia)
- CISA Pathway for Pipeline Cybersecurity: [https://www.cisa.gov/topics/critical-infrastructure-security-and-resilience/critical-infrastructure-sectors/transportation-systems-sector](https://www.cisa.gov/topics/critical-infrastructure-security-and-resilience/critical-infrastructure-sectors/transportation-systems-sector)
- NIST SP 800-82 Rev 3 (ICS security): [https://csrc.nist.gov/pubs/sp/800/82/r3/final](https://csrc.nist.gov/pubs/sp/800/82/r3/final)
- 49 CFR Part 1520 (SSI handling): [https://www.ecfr.gov/current/title-49/subtitle-B/chapter-XII/subchapter-A/part-1520](https://www.ecfr.gov/current/title-49/subtitle-B/chapter-XII/subchapter-A/part-1520)
- PHMSA 49 CFR Part 195 (Hazardous Liquid Pipelines): [https://www.ecfr.gov/current/title-49/subtitle-B/chapter-I/subchapter-D/part-195](https://www.ecfr.gov/current/title-49/subtitle-B/chapter-I/subchapter-D/part-195)

## 9. Common audit deficiencies

1. **CC availability lapses** — On-call roster drift, especially after personnel changes; the most-cited TSA inspection finding. Mitigated by UC-22.56.2.
2. **CIP attestation as annual snapshot** — Operators frequently present a one-day audit-readiness snapshot rather than continuous evidence. Mitigated by UC-22.56.3 through UC-22.56.6.
3. **24-hour clock fired late** — Most frequently because classification-as-reportable was deferred. Mitigated by UC-22.56.1 conservative classification trigger.
4. **CAP self-assessment as checklist** — TSA expects substantive narrative + remediation evidence, not just checkboxes. Mitigated by UC-22.56.8.
5. **CIRP exercise scope too narrow** — Operators frequently run a single-vector tabletop and call it sufficient. Mitigated by UC-22.56.7 multi-vector requirement.
6. **Vendor remote-access without break-glass** — JIT access without recorded justification. Mitigated by UC-22.56.16.
7. **TSA-PHMSA dual-clock mismatch** — Pipeline operators sometimes report to PHMSA without parallel CISA reporting, or vice versa. Mitigated by UC-22.56.26.
8. **CIP versioning gaps** — Operators amend the CIP without signed trail. Mitigated by UC-22.56.18.
9. **Backup RTO claim without test** — Backup vault claimed compliant but RTO not exercised. Mitigated by UC-22.56.19.

## 10. Enforcement and penalties

Civil penalties under 49 U.S.C. § 114(l)(2) plus 49 CFR § 1503 may reach $14,950 per violation per day (2024 inflation-adjusted). For criminal violations involving SSI mishandling, penalties may include imprisonment. TSA may also issue compliance orders that, in severe cases, can affect operating authority (rare but precedent exists from the post-Colonial regime). Civil enforcement is via the TSA Office of Chief Counsel; criminal referrals go to DOJ.

## 11. Questions a TSA inspector should ask

- Show me the current Cybersecurity Coordinator roster with phone numbers, SSI eligibility dates, and the on-call rotation for the next 90 days.
- Walk me through the most recent CISA Form 1 submission you sent. Include the timestamps, the staff member who submitted, and the receipt.
- Pick a pipeline / freight rail / passenger rail / aviation operationally-critical system. Demonstrate continuous monitoring of all four CIP control families for that system this morning.
- Show me the after-action report from the most recent CIRP annual exercise and the closure status of every corrective action.
- Pick a third-party vendor with current remote access. Demonstrate the JIT grant, the session record, and the break-glass justification.
- Walk me through the CIP version-control trail since the last amendment.
- Demonstrate a successful backup-recovery exercise within RTO for an operationally-critical system in the last 90 days.

## 12. Machine-readable twin

- API endpoint: `api/v1/compliance/story/tsa-surface.json`
- Raw clause data: `data/regulations.json` (id=`tsa-surface`)
- Per-UC sidecar files: `content/cat-22-regulatory-compliance/UC-22.56.*.json`
- Coverage methodology: `docs/coverage-methodology.md`

## 13. Provenance and regeneration

This evidence pack is regenerated as part of the catalogue build. Manual narrative sections (purpose, scope, common deficiencies, inspector questions) are authored; clause coverage tables are computed from UC sidecar `compliance[]` arrays. Last reviewed: 2026-05-13.
