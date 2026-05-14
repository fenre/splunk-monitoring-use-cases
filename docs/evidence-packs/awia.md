# Evidence Pack — AWIA

> **Tier**: Tier 1 &nbsp;·&nbsp; **Jurisdiction**: US &nbsp;·&nbsp; **Version**: `2018-amended-SDWA-1433`
>
> **Full name**: America's Water Infrastructure Act of 2018 (Section 2013 amendments to SDWA s 1433)
> **Authoritative source**: [https://www.epa.gov/waterresilience/awia-section-2013](https://www.epa.gov/waterresilience/awia-section-2013)
> **Effective from**: 2018-10-23

> This evidence pack is the auditor-facing view of the Splunk monitoring catalogue's coverage of the regulation. Every clause coverage claim is traceable to a specific UC sidecar JSON file (`content/cat-*/UC-*.json`); every retention figure cites its legal basis; every URL resolves to an official regulator or standards-body source. The pack does **not** assert legal conclusions — it tabulates what the catalogue covers, names the authoritative source, and flags gaps. Interpretation stays with counsel.

> **Live views.** [Buyer narrative (`compliance-story.html?reg=awia`)](../../compliance-story.html?reg=awia) · [Auditor clause navigator (`clause-navigator.html#reg=awia`)](../../clause-navigator.html#reg=awia) · [JSON twin (`api/v1/compliance/story/awia.json`)](../../api/v1/compliance/story/awia.json)

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

Section 2013 of America's Water Infrastructure Act of 2018 (Pub.L. 115-270) amended Section 1433 of the Safe Drinking Water Act (42 U.S.C. § 300i-2) to require every community water system (CWS) serving more than 3,300 persons to conduct a Risk and Resilience Assessment (RRA) of malevolent acts, natural hazards, electronic / automated systems, monitoring practices, chemicals, financial infrastructure, and operations and maintenance, and to prepare or revise an Emergency Response Plan (ERP) within 6 months thereafter. The CWS must certify both to EPA, retain the underlying RRA / ERP for 5 years, and revise both at least every 5 years and after material change. EPA does not retain the RRA / ERP — only the certification. The cyber subset of AWIA scope is amplified by EPA / CISA's Top Cyber Actions for Water Utilities and the CISA Pathway to Cybersecurity for the Water and Wastewater Sector. Where a state has voluntarily adopted EPA's July 2024 Cybersecurity Action Plan, cyber is also evaluated during PWS sanitary surveys.

## 2. Scope and applicability

Applies to community water systems (CWS) within the meaning of the Safe Drinking Water Act 42 U.S.C. § 300f, serving more than 3,300 persons. Three statutory population tiers drive the original RRA / ERP submission deadlines: Tier 1 (>=100,000 persons) — RRA certification by 31 March 2020, ERP by 30 September 2020; Tier 2 (50,000-99,999) — RRA by 31 December 2020, ERP by 30 June 2021; Tier 3 (3,301-49,999) — RRA by 30 June 2021, ERP by 31 December 2021. All systems must recertify at least every 5 years. Wastewater utilities are not statutorily in scope of s1433 but are covered by EPA's parallel wastewater resilience programme and increasingly subject to similar expectations under EPA's water-sector cybersecurity portfolio.

**Territorial scope.** United States and territories. All 50 states plus the District of Columbia, Puerto Rico, U.S. Virgin Islands, Guam, American Samoa, and the Northern Mariana Islands. Sovereign tribal nations are covered where the CWS is operated by or for a tribal community served by an EPA Region. SDWA primacy is held by every state and territory except Wyoming and the District of Columbia where EPA is the direct primacy authority; primacy agencies enforce SDWA more broadly but AWIA certification is to EPA.

## 3. Catalogue coverage at a glance

- **Clauses tracked**: 28
- **Clauses covered by at least one UC**: 0 / 28 (0.0%)
- **Priority-weighted coverage**: 0.0%
- **Contributing UCs**: 0

Coverage methodology is documented in [`docs/coverage-methodology.md`](../coverage-methodology.md). Priority weights come from `data/regulations.json` commonClauses entries (see [`data/regulations.json`](../../data/regulations.json) priorityWeightRubric).

## 4. Clause-by-clause coverage

Clauses are listed in the order defined by `data/regulations.json commonClauses` for this regulation version. A clause is considered covered when at least one UC sidecar has a `compliance[]` entry matching `(regulation, version, clause)`. Assurance is the maximum across contributing UCs.

| Clause | Topic | Priority | Assurance | UCs |
|---|---|---|---|---|
| [`AWIA-s1433a`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-s1433a) | Risk and Resilience Assessment (RRA) — duty and scope | 1.0 | `—` | _not yet covered_ |
| [`AWIA-s1433a(1)`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-s1433a(1)) | RRA submission deadlines by system size | 1.0 | `—` | _not yet covered_ |
| [`AWIA-s1433b`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-s1433b) | Emergency Response Plan (ERP) — duty and content | 1.0 | `—` | _not yet covered_ |
| [`AWIA-s1433c`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-s1433c) | ERP coordination with state, local, tribal, and territorial partners | 0.7 | `—` | _not yet covered_ |
| [`AWIA-s1433g`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-s1433g) | Certification — RRA and ERP | 1.0 | `—` | _not yet covered_ |
| [`AWIA-RRA-malevolent-acts`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-RRA-malevolent-acts) | Baseline Information on Malevolent Acts — EPA-defined cyber and physical threat set | 1.0 | `—` | _not yet covered_ |
| [`AWIA-RRA-natural-hazards`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-RRA-natural-hazards) | Natural hazards in the RRA — flood, drought, wildfire, seismic, severe weather | 0.7 | `—` | _not yet covered_ |
| [`AWIA-RRA-electronic-systems`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-RRA-electronic-systems) | RRA — electronic, computer, and automated systems (cyber scope) | 1.0 | `—` | _not yet covered_ |
| [`AWIA-RRA-monitoring-practices`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-RRA-monitoring-practices) | RRA — monitoring practices (continuous data quality and integrity) | 1.0 | `—` | _not yet covered_ |
| [`AWIA-RRA-chemicals`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-RRA-chemicals) | RRA — chemical storage, handling, and dosing | 1.0 | `—` | _not yet covered_ |
| [`AWIA-RRA-financial`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-RRA-financial) | RRA — financial infrastructure | 0.7 | `—` | _not yet covered_ |
| [`AWIA-ERP-strategies-actions`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-ERP-strategies-actions) | ERP — strategies, resources, and actions to mitigate identified risks | 1.0 | `—` | _not yet covered_ |
| [`AWIA-ERP-detection`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-ERP-detection) | ERP — detection strategies for malevolent acts and natural hazards | 1.0 | `—` | _not yet covered_ |
| [`AWIA-ERP-cyber-incident-response`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-ERP-cyber-incident-response) | ERP — cyber-incident response procedures | 1.0 | `—` | _not yet covered_ |
| [`AWIA-ERP-mutual-aid`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-ERP-mutual-aid) | ERP — mutual-aid coordination (WARN networks and local partners) | 0.7 | `—` | _not yet covered_ |
| [`AWIA-ERP-review`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-ERP-review) | ERP — review and revision every 5 years (and after material change) | 0.7 | `—` | _not yet covered_ |
| [`AWIA-EPA-cwc-reporting`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-EPA-cwc-reporting) | Cyber-incident reporting — WaterISAC and EPA Region pathway | 1.0 | `—` | _not yet covered_ |
| [`AWIA-EPA-sanitary-survey`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-EPA-sanitary-survey) | EPA Cybersecurity Action Plan — voluntary cyber-incorporation into sanitary surveys | 0.7 | `—` | _not yet covered_ |
| [`AWIA-EPA-aware-checklist`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-EPA-aware-checklist) | EPA / CISA Top Cyber Actions for Water Utilities (Top 8 / 9 / Pathway) | 1.0 | `—` | _not yet covered_ |
| [`AWIA-EPA-vsat-j100`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-EPA-vsat-j100) | Use of recognised RRA methodology — J100-21 / AWWA M19 / VSAT-Web | 0.7 | `—` | _not yet covered_ |
| [`AWIA-EPA-asset-inventory`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-EPA-asset-inventory) | OT/IT asset inventory (cyber baseline) | 1.0 | `—` | _not yet covered_ |
| [`AWIA-EPA-mfa-remote-access`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-EPA-mfa-remote-access) | Multi-factor authentication on all remote access | 1.0 | `—` | _not yet covered_ |
| [`AWIA-EPA-network-segmentation`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-EPA-network-segmentation) | Network segmentation between IT and OT | 1.0 | `—` | _not yet covered_ |
| [`AWIA-EPA-backup-recovery`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-EPA-backup-recovery) | System and data backup and tested recovery | 0.7 | `—` | _not yet covered_ |
| [`AWIA-EPA-default-creds`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-EPA-default-creds) | Change default passwords on all OT and IT devices | 1.0 | `—` | _not yet covered_ |
| [`AWIA-EPA-training`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-EPA-training) | Cybersecurity awareness training | 0.7 | `—` | _not yet covered_ |
| [`AWIA-EPA-vuln-mgmt`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-EPA-vuln-mgmt) | Reduce exposure to vulnerabilities — patching and configuration | 1.0 | `—` | _not yet covered_ |
| [`AWIA-EPA-records-retention`](https://www.epa.gov/waterresilience/awia-section-2013#AWIA-EPA-records-retention) | RRA / ERP / certification records retention | 0.7 | `—` | _not yet covered_ |

## 5. Evidence collection

### 5.1 Common evidence sources

Auditors typically request the following records when examining this regulation:

- ServiceNow GRC — RRA module, ERP module, certification ledger, partner registry, exercise calendar, top-actions register, methodology register, records-retention register.
- ServiceNow CMDB — financial-system class, asset inventory, lifecycle status, owner assignment.
- Dragos OT visibility / Claroty CTD or xDome / Nozomi Networks Guardian / Armis Centrix — OT asset inventory, default-credential signature detection, OT vulnerability tracking.
- Tenable / Rapid7 / Qualys — IT vulnerability scanning with CISA KEV alignment.
- OSIsoft / AVEVA PI System and Wonderware / AVEVA System Platform — SCADA historian, setpoint stream, work-permit log, alarm-shelve audit.
- Rockwell FactoryTalk / Siemens TIA Portal / Schneider EcoStruxure engineering-workstation logs — PLC program-download audit (a CISA-cited attack vector).
- Cisco AnyConnect / Palo Alto GlobalProtect / Fortinet FortiGate<sup class="ref">[<a href="#ref-3">3</a>]</sup> / Pulse Secure VPN — MFA enforcement audit.
- Okta<sup class="ref">[<a href="#ref-5">5</a>]</sup> / Microsoft Entra ID<sup class="ref">[<a href="#ref-4">4</a>]</sup> / Duo — IdP / MFA enforcement audit.
- Teleport / BeyondTrust PRA / CyberArk PSM — jump-host audit for vendor and operator engineering access.
- Palo Alto / Fortinet OT / Cisco Industrial Ethernet firewalls — IT/OT segmentation enforcement and east-west OT flow logging; Splunk Stream / Zeek for wire-data corroboration.
- Veeam / Commvault / Rubrik / Cohesity — backup-job evidence with offline / immutable copy and restore-test records.
- Cornerstone OnDemand / Workday Learning / KnowBe4 / SANS Security Awareness — training LMS records.
- CISA KEV feed, ICS-CERT advisories, WaterISAC threat intelligence, EPA water-sector cybersecurity portal.
- Microsoft Purview Records Management with retention labels in SharePoint Online / OneDrive — RRA / ERP retention metadata.
- Microsoft Defender for Cloud Apps (MDCAS) / Mimecast / Proofpoint / Forcepoint DLP — monitoring of AWIA Confidential Business Information leakage.
- External attack-surface management (Bishop Fox / Censys / Shodan API) — internet-exposure scanning of SCADA / HMI / engineering workstations.
- Splunk Enterprise Security<sup class="ref">[<a href="#ref-6">6</a>]</sup> correlation searches and Splunk SOAR<sup class="ref">[<a href="#ref-7">7</a>]</sup> playbooks aligned to the UCs in subcategory 22.53.

### 5.2 Retention requirements

| Artifact | Retention | Legal basis |
|---|---|---|
| Risk and Resilience Assessment (RRA) document | Minimum 5 years from certification (one full review cycle) | SDWA 1433(g); EPA AWIA Compliance Manual |
| Emergency Response Plan (ERP) document | Minimum 5 years from certification | SDWA 1433(g); EPA AWIA Compliance Manual |
| EPA AWIA portal certification receipts (RRA + ERP) | Minimum 5 years from submission | SDWA 1433(g) |
| ERP partner coordination minutes (LEPC, state EOC, EPA Regional WPC, FBI WCC, WARN) | 5 years from each coordination event | SDWA 1433(c); AWWA M19 retention guidance |
| Cyber-incident response exercise after-action reports | 5 years from exercise | SDWA 1433(b)(2); EPA AWIA Compliance Manual |
| EPA / CISA Top Cyber Actions evidence (MFA, segmentation, patching, backup, default-credential rotation, training) | 5 years — aligned to AWIA RRA cycle | EPA Cybersecurity Action Plan (July 2024); CISA water-sector guidance |
| WaterISAC and EPA Regional WPC cyber-incident reports | 5 years from each report | EPA water-sector cybersecurity guidance |
| CIRCIA covered-cyber-incident reports to CISA (once final rule in force) | Minimum 2 years from submission; align with AWIA 5-year for the underlying incident record | CIRCIA proposed rule § 226.18; CISA |
| AWIA Baseline Malevolent Acts coverage / RRA threat-coverage records | 5 years — aligned to RRA cycle | EPA Baseline Information on Malevolent Acts (2019, refreshed 2022) |
| Sanitary-survey cyber-readiness evidence (where state has adopted Cybersecurity Action Plan) | Per state primacy agency requirements; commonly 5 years | EPA July 2024 Cybersecurity Action Plan; state primacy regulations |
| Chemical-dosing change-control records (setpoint changes, dual-authorisation evidence) | 5 years from change | AWIA RRA chemicals scope; AWWA G430 / M19 |
| Backup and restore-test records for SCADA / PLC / historian / WQ / business systems | Most recent test plus 5 years | EPA / CISA Top Actions — Backup and Recovery |

> Retention figures above are the legal minimums or regulator-stated expectations. Organisation-specific retention schedules may be longer where business, tax, litigation-hold, or contractual obligations apply. Where a figure conflicts with local data-protection law (e.g. GDPR<sup class="ref">[<a href="#ref-2">2</a>]</sup> Art.5(1)(e) storage-limitation principle), the shorter conformant period governs for personal-data content; the evidence-of-compliance retention retains the longer period for audit purposes, scrubbed of excess personal data.

### 5.3 Evidence integrity expectations

Regulators increasingly cite **evidence-integrity failures** as aggravating factors in enforcement actions. Cross-regulation baseline expectations:

- Time-stamped, tamper-evident storage (WORM, cryptographic chaining, or append-only indexes).
- Chain-of-custody for any evidence removed from the SIEM / production system for audit or legal purposes.
- Synchronised clocks (NTP stratum ≤ 3 or equivalent) across all in-scope sources so timeline reconstruction is defensible.
- Documented retention enforcement — not just retention policy — so that deletion is auditable.

See cat-22.35 "Evidence continuity and log integrity" for UCs that implement these controls.

## 6. Control testing procedures

AWIA is administered by EPA Office of Water (Office of Water Resilience). Inspections are typically conducted in two ways: (a) AWIA compliance reviews triggered by certification anomalies, missed deadlines, or post-incident enquiry; and (b) routine PWS sanitary surveys, which in states that have voluntarily adopted EPA's July 2024 Cybersecurity Action Plan now include a cybersecurity component aligned to EPA Top Actions. Sector-wide cyber maturity is also assessed under EPA's Cybersecurity Self-Assessment process and through CISA Cyber Hygiene services (free vulnerability scanning available to every CWS). External assurance: many medium and large utilities engage an AWWA-affiliated consultancy for the RRA refresh and an MS-ISAC or specialist consultancy for cyber. Penetration testing of SCADA is encouraged under strict change-control; CISA offers cybersecurity advisor (CSA) engagements and water-specific tabletop exercises. Continuous Splunk-based evidence collection through the UCs in this catalogue is the practical model for inspection-readiness between certification cycles.

**Reporting cadence.** RRA certification — by statutory population-tier deadline and every 5 years thereafter. ERP certification — within 6 months of RRA certification and every 5 years thereafter. Cyber-incident reporting — WaterISAC and EPA Regional WPC as soon as practicable after detection; CIRCIA covered-cyber-incident reporting to CISA within 72 hours once the final rule is in force. Annual exercising of cyber-IR procedures. Annual review of ERP partner registry, WARN annual roster, and EPA / CISA Top Actions. Daily refresh of CISA KEV against asset inventory. Continuous monitoring of monitoring-integrity, chemical-dosing integrity, MFA, segmentation, and default-credential signatures. Sanitary-survey-driven cyber readiness in states that have adopted the EPA Cybersecurity Action Plan typically on a 3-year cycle.

## 7. Roles and responsibilities

| Role | Responsibility |
|---|---|
| **General Manager / CEO / Mayor (municipal utilities)** | Senior officer signing the AWIA RRA and ERP certifications; ultimately accountable for AWIA compliance and the certification ledger. |
| **Compliance Officer** | Day-to-day AWIA accountability; re-keys EPA portal receipts; maintains the certification ledger; chairs the 5-year cycle programme. |
| **Information Manager / Records Manager** | Maintains 5-year retention metadata for RRA / ERP / certifications; coordinates EPA inspection production; owns Microsoft Purview retention-label policy. |
| **OT Cybersecurity Lead** | Owns the cyber subset of the RRA, AWIA Baseline coverage, electronic-systems scope, monitoring integrity, chemical-dosing integrity, MFA, segmentation, default credentials, vulnerability management, backup, and the cyber-IR exercise programme. |
| **RRA author** | Authors and curates the RRA against J100-21 / M19 / VSAT-Web; updates threat coverage on every refresh; documents methodology and version per UC-22.53.20. |
| **Resilience Planner** | Sources natural-hazard data from USGS / NOAA / FEMA / EPA CREAT; integrates climate-shift overlays; owns UC-22.53.7. |
| **Plant Manager (per plant)** | Owns plant-floor implementation of ERP strategies; co-authorises chemical-dosing setpoint changes; participates in annual cyber-IR exercises; owns plant-level UC-22.53.10. |
| **Treatment Operations Lead** | Operations leader for treatment-chemical handling, dosing-controller authority, and manual-operation fallback drills; signs ERP strategy ownership for treatment risks. |
| **Emergency Management Coordinator** | Owns the ERP partner registry, WARN annual roster signing, LEPC / state-EOC coordination, mutual-aid invocation; owns UC-22.53.4 and UC-22.53.15. |
| **Incident Response Lead** | Owns cyber-incident response procedure, after-action reports, WaterISAC / EPA / CIRCIA reporting workflows; owns UC-22.53.14 and UC-22.53.17. |
| **Vulnerability Manager** | Tracks CISA KEV / ICS-CERT against the asset inventory and the OT safety-validation process; owns UC-22.53.26. |
| **Infrastructure Manager** | Owns backup and recovery, including offline / immutable copy and the annual restore-test programme; owns UC-22.53.23. |
| **Network Lead** | Owns IT/OT segmentation, industrial firewall configuration, and external-attack-surface monitoring; owns UC-22.53.22. |
| **IAM Lead** | Owns MFA enforcement, IdP integration, vendor / contractor remote-access governance; owns UC-22.53.21. |
| **HR / Learning & Development** | Owns the cybersecurity-awareness training programme and roster; owns UC-22.53.25. |
| **CFO** | Owns financial-infrastructure resilience (billing, customer payment portal, vendor payment) and continuity tests; signs the financial-system scope of UC-22.53.11. |
| **Board / Council (or governing body)** | Receives the AWIA programme status as a fiduciary governance item; approves residual-risk acceptances; oversees CISO appointment; reviews any EPA / WaterISAC / CIRCIA enforcement correspondence. |
| **US Environmental Protection Agency (EPA) — Office of Water Resilience** | Federal regulator; receives AWIA certifications via the EPA AWIA portal; conducts AWIA compliance reviews; coordinates with state primacy agencies; publishes Top Actions and Cybersecurity Action Plan guidance. |
| **EPA Regional Water Protection Coordinator (Regions 1-10)** | Primary EPA-side coordination contact for CWS; receives sector-wide cyber-incident reports; approves alternative-methodology concurrences. |
| **Cybersecurity and Infrastructure Security Agency (CISA)** | Receives CIRCIA covered-cyber-incident reports (once final rule in force); publishes KEV catalogue and water-sector advisories (e.g. AA23-335A); offers free Cyber Hygiene services to CWS. |
| **WaterISAC** | Sector ISAC; receives sector-wide cyber-incident reports; provides threat intelligence and the Cyber Hygiene 15 Fundamental Practices guidance. |
| **State primacy agency (SDWA)** | State / DC / territorial primacy authority for SDWA; conducts PWS sanitary surveys (with cybersecurity component in states that have adopted the EPA Cybersecurity Action Plan); may issue parallel state-level enforcement. |

## 8. Authoritative guidance

- **Safe Drinking Water Act 42 U.S.C. § 300i-2 (SDWA s 1433, as amended by AWIA s 2013)** — U.S. EPA — [https://www.epa.gov/waterresilience/awia-section-2013](https://www.epa.gov/waterresilience/awia-section-2013)
- **EPA AWIA Compliance Manual and Online Tools** — U.S. EPA — [https://www.epa.gov/waterresilience/awia-online-tools](https://www.epa.gov/waterresilience/awia-online-tools)
- **EPA Baseline Information on Malevolent Acts of Relevance to Community Water Systems (2019, refreshed 2022)** — U.S. EPA — [https://www.epa.gov/waterresilience/baseline-information-malevolent-acts-community-water-systems](https://www.epa.gov/waterresilience/baseline-information-malevolent-acts-community-water-systems)
- **EPA July 2024 Cybersecurity Action Plan (replaces vacated March 2023 sanitary-survey memorandum)** — U.S. EPA — [https://www.epa.gov/waterresilience/forms/water-sector-cybersecurity](https://www.epa.gov/waterresilience/forms/water-sector-cybersecurity)
- **EPA Top Actions for Securing Water Systems** — U.S. EPA — [https://www.epa.gov/waterresilience/forms/water-sector-cybersecurity](https://www.epa.gov/waterresilience/forms/water-sector-cybersecurity)
- **CISA Pathway to Cybersecurity for the Water and Wastewater Sector** — U.S. CISA — [https://www.cisa.gov/water](https://www.cisa.gov/water)
- **CISA Known Exploited Vulnerabilities Catalog<sup class="ref">[<a href="#ref-1">1</a>]</sup>** — U.S. CISA — [https://www.cisa.gov/known-exploited-vulnerabilities-catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
- **CISA Ransomware Guide** — U.S. CISA — [https://www.cisa.gov/stopransomware/ransomware-guide](https://www.cisa.gov/stopransomware/ransomware-guide)
- **ICS-CERT Cybersecurity Advisories (Water and Wastewater Systems)** — U.S. CISA — [https://www.cisa.gov/news-events/cybersecurity-advisories](https://www.cisa.gov/news-events/cybersecurity-advisories)
- **CIRCIA Cyber Incident Reporting for Critical Infrastructure Act — Proposed Rule (April 2024)** — U.S. CISA — [https://www.federalregister.gov/documents/2024/04/04/2024-06526/cyber-incident-reporting-for-critical-infrastructure-act-circia-reporting-requirements](https://www.federalregister.gov/documents/2024/04/04/2024-06526/cyber-incident-reporting-for-critical-infrastructure-act-circia-reporting-requirements)
- **ANSI/AWWA/ASCE-ASME-AWWA J100-21 Risk and Resilience Management of Water and Wastewater Systems** — AWWA — [https://www.awwa.org/Resources-Tools/Resource-Topics/Risk-Resilience](https://www.awwa.org/Resources-Tools/Resource-Topics/Risk-Resilience)
- **AWWA Manual M19 Emergency Planning for Water and Wastewater Utilities** — AWWA — [https://www.awwa.org/Store/Product-Details/productId/56906415](https://www.awwa.org/Store/Product-Details/productId/56906415)
- **EPA Vulnerability Self Assessment Tool web edition (VSAT-Web)** — U.S. EPA — [https://www.epa.gov/waterresilience/vulnerability-self-assessment-tool-vsat](https://www.epa.gov/waterresilience/vulnerability-self-assessment-tool-vsat)
- **EPA Climate Resilience Evaluation and Awareness Tool (CREAT)** — U.S. EPA — [https://www.epa.gov/crwu/creat-risk-assessment-application-water-utilities](https://www.epa.gov/crwu/creat-risk-assessment-application-water-utilities)
- **FEMA National Risk Index** — FEMA — [https://hazards.fema.gov/nri/](https://hazards.fema.gov/nri/)
- **WaterISAC — Information Sharing and Analysis Center for the water sector** — WaterISAC — [https://www.waterisac.org/](https://www.waterisac.org/)
- **WARN — Water and Wastewater Agency Response Network** — AWWA / state WARN networks — [https://www.awwa.org/Resources-Tools/Resource-Topics/Risk-Resilience/Mutual-Aid-WARN](https://www.awwa.org/Resources-Tools/Resource-Topics/Risk-Resilience/Mutual-Aid-WARN)
- **CISA Advisory AA23-335A: Iranian-Affiliated Cyber Actors Compromised U.S. Water-Sector PLCs (Nov 2023)** — U.S. CISA — [https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-335a](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-335a)
- **CISA: Compromise of a U.S. Water Treatment Facility (Feb 2021 Florida advisory)** — U.S. CISA — [https://www.cisa.gov/news-events/news/compromise-us-water-treatment-facility](https://www.cisa.gov/news-events/news/compromise-us-water-treatment-facility)

## 9. Common audit deficiencies

Findings frequently cited by regulators, certification bodies, and external auditors for this regulation. These should be pre-tested as part of readiness reviews.

- EPA AWIA portal receipt id not captured in the certification ledger; certification 'submitted' but inspection-evidence is a screenshot rather than the portal receipt (UC-22.53.5).
- RRA submission deadlines missed in a population-tier-boundary year because the population census shifted the tier without a programmatic re-evaluation (UC-22.53.2).
- ERP completed but not certified to EPA within 6 months of RRA certification — the most common AWIA finding in published enforcement actions (UC-22.53.3 / UC-22.53.5).
- EPA Baseline Malevolent Acts threats added in the 2022 refresh not yet folded into the RRA (UC-22.53.6).
- RRA natural-hazard data sourced from non-authoritative providers (hobbyist sites, vendor datasheets) rather than USGS / NOAA / FEMA / EPA CREAT (UC-22.53.7).
- RRA electronic-systems coverage incomplete: remote lift-station PLCs over cellular not inventoried; vendor-managed engineering workstations not in scope (UC-22.53.8).
- Online residual-chlorine analyser stuck for >4 hours with no operator acknowledgement and no maintenance work-permit (UC-22.53.9).
- Chemical-dosing setpoint change executed with single-operator authorisation rather than dual-authorisation (UC-22.53.10).
- Financial-system continuity plan exists but the last restore-test is older than 12 months (UC-22.53.11).
- ERP strategy maps a RRA risk to a role that is currently vacant; named individual was not refreshed after a recent personnel change (UC-22.53.12).
- ERP detection channel (e.g. video analytics or public tipline) is configured but emits zero signals over 24 hours and no smoke-test is recent (UC-22.53.13).
- Annual cyber-IR exercise scheduled but the after-action report omits the CIRCIA-72h notification practice (UC-22.53.14 / UC-22.53.17).
- WARN annual-roster signature expired; LEPC contact is older than 12 months (UC-22.53.15).
- ERP 5-year review missed in the year after a major infrastructure change (post-incident lessons or new plant); change-management did not trigger ERP refresh (UC-22.53.16).
- Sanitary-survey cyber-readiness in a state that has adopted the EPA Cybersecurity Action Plan: backup-test evidence URL or MFA evidence URL missing within 90 days of survey (UC-22.53.18).
- EPA / CISA Top Cyber Actions: 'change default passwords' or 'reduce internet exposure' shown as 'partial' for over 12 months without a remediation plan (UC-22.53.19 / UC-22.53.22 / UC-22.53.24).
- RRA methodology field set to in-house unstructured rather than J100-21 / M19 / VSAT-Web (UC-22.53.20).
- Single-factor VPN or jump-host login detected with no MFA factor type; this is the most common CISA-cited initial-access vector for water utilities (UC-22.53.21).
- Direct corporate-IT-to-OT TCP/502 (Modbus) or TCP/44818 (EtherNet/IP) flow without a documented allow-list row; or internet-exposed Unitronics / Allen-Bradley HMI surface (UC-22.53.22 — mirrors CISA AA23-335A).
- PLC program backup retained but offline / immutable copy not separately retained; ransomware-recoverable position not validated (UC-22.53.23).
- Vendor default credential signature detected on a Hikvision / Dahua / Unitronics device that was 'commissioned' months ago (UC-22.53.24).
- Cybersecurity awareness training roster shows contractors as untrained; AWIA scope includes contractors (UC-22.53.25).
- CISA KEV-listed CVE on a PLC older than the 7-day KEV remediation SLA, with no compensating control and no documented safety-validation deferral (UC-22.53.26).
- Asset inventory: a new remote lift-station PLC discovered via passive OT visibility but not registered in CMDB within 5 business days (UC-22.53.27).
- RRA / ERP retained in SharePoint without a retention label; documents editable by anyone with access (UC-22.53.28).

## 10. Enforcement and penalties

AWIA s1433(h) authorises civil penalties for non-compliance under 42 U.S.C. § 300g-3(b) (SDWA enforcement) and 40 CFR Part 19 (Adjustment of Civil Monetary Penalties), with the federal civil penalty adjusted annually for inflation (currently up to $25,000+ per day per violation as adjusted by the EPA Civil Monetary Penalty Inflation Adjustment Rule). Distinct violations include failure to conduct or revise the RRA, failure to prepare or revise the ERP, failure to certify within the statutory deadline, and failure to retain underlying records for the 5-year window. EPA may also issue compliance orders under SDWA s 1414 and refer matters to the Department of Justice for civil enforcement. Reputational consequences are significant: water-sector cyber-incidents are routinely the subject of public CISA advisories (e.g. AA23-335A, the February 2021 Florida incident); a covered CWS that suffers a cyber incident traceable to a documented AWIA finding can expect press, ratepayer, and municipal-governance consequences. Where personal data was exposed (e.g. customer-payment data), state breach-notification laws and PCI-DSS contractual penalties also apply on top of AWIA.

## 11. Pack gaps and remediation backlog

Clauses tracked in `data/regulations.json` that are **not yet covered** by any UC in this catalogue are listed below. These are the backlog items for the next release. Priority order follows priorityWeight.

| Clause | Topic | Priority |
|---|---|---|
| `AWIA-EPA-asset-inventory` | OT/IT asset inventory (cyber baseline) | 1.0 |
| `AWIA-EPA-aware-checklist` | EPA / CISA Top Cyber Actions for Water Utilities (Top 8 / 9 / Pathway) | 1.0 |
| `AWIA-EPA-cwc-reporting` | Cyber-incident reporting — WaterISAC and EPA Region pathway | 1.0 |
| `AWIA-EPA-default-creds` | Change default passwords on all OT and IT devices | 1.0 |
| `AWIA-EPA-mfa-remote-access` | Multi-factor authentication on all remote access | 1.0 |
| `AWIA-EPA-network-segmentation` | Network segmentation between IT and OT | 1.0 |
| `AWIA-EPA-vuln-mgmt` | Reduce exposure to vulnerabilities — patching and configuration | 1.0 |
| `AWIA-ERP-cyber-incident-response` | ERP — cyber-incident response procedures | 1.0 |
| `AWIA-ERP-detection` | ERP — detection strategies for malevolent acts and natural hazards | 1.0 |
| `AWIA-ERP-strategies-actions` | ERP — strategies, resources, and actions to mitigate identified risks | 1.0 |
| `AWIA-RRA-chemicals` | RRA — chemical storage, handling, and dosing | 1.0 |
| `AWIA-RRA-electronic-systems` | RRA — electronic, computer, and automated systems (cyber scope) | 1.0 |
| `AWIA-RRA-malevolent-acts` | Baseline Information on Malevolent Acts — EPA-defined cyber and physical threat set | 1.0 |
| `AWIA-RRA-monitoring-practices` | RRA — monitoring practices (continuous data quality and integrity) | 1.0 |
| `AWIA-s1433a` | Risk and Resilience Assessment (RRA) — duty and scope | 1.0 |
| `AWIA-s1433a(1)` | RRA submission deadlines by system size | 1.0 |
| `AWIA-s1433b` | Emergency Response Plan (ERP) — duty and content | 1.0 |
| `AWIA-s1433g` | Certification — RRA and ERP | 1.0 |
| `AWIA-EPA-backup-recovery` | System and data backup and tested recovery | 0.7 |
| `AWIA-EPA-records-retention` | RRA / ERP / certification records retention | 0.7 |
| `AWIA-EPA-sanitary-survey` | EPA Cybersecurity Action Plan — voluntary cyber-incorporation into sanitary surveys | 0.7 |
| `AWIA-EPA-training` | Cybersecurity awareness training | 0.7 |
| `AWIA-EPA-vsat-j100` | Use of recognised RRA methodology — J100-21 / AWWA M19 / VSAT-Web | 0.7 |
| `AWIA-ERP-mutual-aid` | ERP — mutual-aid coordination (WARN networks and local partners) | 0.7 |
| `AWIA-ERP-review` | ERP — review and revision every 5 years (and after material change) | 0.7 |
| `AWIA-RRA-financial` | RRA — financial infrastructure | 0.7 |
| `AWIA-RRA-natural-hazards` | Natural hazards in the RRA — flood, drought, wildfire, seismic, severe weather | 0.7 |
| `AWIA-s1433c` | ERP coordination with state, local, tribal, and territorial partners | 0.7 |

## 12. Questions an auditor should ask

These are the questions a regulator, certification body, or external auditor is likely to ask. The pack helps preparers stage evidence and pre-test responses before the review opens.

- Has the CWS certified the RRA to EPA on the statutory deadline applicable to its population tier? Produce the EPA portal receipt id or accepted paper-exception letter.
- Has the CWS certified the ERP to EPA within 6 months of RRA certification? Produce the EPA portal receipt id.
- Is the RRA current under the 5-year review cycle? Produce the most recent RRA certification and the next-due date.
- Does the RRA cover every threat in EPA's Baseline Information on Malevolent Acts of Relevance to Community Water Systems (2019, refreshed 2022)? Produce the per-threat coverage matrix.
- Does the RRA cover natural hazards (flood, drought, wildfire, seismic, severe weather, climate-shift) using data from authoritative providers (USGS, NOAA, FEMA, EPA CREAT)? Produce the data-vintage attestation.
- Does the RRA inventory enterprise IT, SCADA, PLC / RTU at every plant and remote site, network infrastructure, billing systems, and remote-access pathways? Produce the inventory cross-reference.
- Does the RRA address monitoring integrity (online analysers, distribution pressure / flow / chlorine residual sensors)? Produce evidence of stuck-value / alarm-suppression detection.
- Does the RRA address chemical handling (chlorine, sodium hypochlorite, fluoride, polymers, coagulants, lime, sodium hydroxide, hydrofluosilicic acid) and dosing automation? Produce the dual-authorisation evidence.
- Does the RRA address financial infrastructure (billing, customer payment portal, vendor payment) with continuity controls? Produce the continuity-test record.
- Does the ERP map every material RRA risk to a strategy with a named owner, listed resources, and explicit actions? Produce the traceability matrix.
- Does the ERP describe detection strategies (SCADA alarms, WQ monitoring, perimeter intrusion, video, tipline, WaterISAC / EPA / CISA feeds)? Produce evidence the channels are operational with smoke-tests.
- Does the ERP describe cyber-incident response procedures (triage, isolation, manual fallback, notification to CIRCIA / EPA Region / state primacy / WaterISAC, recovery, lessons learned) and is the procedure exercised annually? Produce the latest after-action report.
- Is the ERP coordinated with LEPC, state / local / tribal / territorial emergency response and homeland-security officials, EPA Regional Water Protection Coordinator, FBI WCC for cyber, state primacy agency, and WARN? Produce the partner registry and the latest coordination minutes.
- Is the asset inventory continuously maintained for OT and IT including SCADA, PLCs, HMIs, RTUs at remote sites, network infrastructure, internet-exposed services, and remote-access endpoints? Produce the inventory dashboard.
- Is MFA enforced on every remote-access pathway (VPN, jump host, vendor engineering, SCADA cloud, management UIs)? Produce non-MFA login evidence from the last 24 hours (expected zero).
- Is corporate IT segmented from OT with documented allow-list flows and no internet exposure of SCADA / HMI / engineering workstations? Produce the segmentation diagram and the live exposure report.
- Are vendor default credentials detected and replaced on every OT and IT device, with documented rotation evidence? Produce the latest default-credential signature scan.
- Are backups for SCADA / PLC / historian / WQ / business systems retained offline / immutable and restore-tested at least annually? Produce the latest restore-test report.
- Is cybersecurity awareness training delivered annually to all employees with system access, contractors, and board members, covering phishing, MFA hygiene, removable-media risk, OT-specific physical-tampering recognition, and incident-reporting workflow? Produce the LMS roster.
- Are CISA KEV / vendor / ICS-CERT vulnerabilities tracked and remediated or compensated within SLA, with safety validation for OT patches? Produce the latest KEV remediation report.
- Is the RRA / ERP / certification retained for 5 years with immutability and producible on EPA request? Produce the retention metadata.
- Where the state has adopted EPA's July 2024 Cybersecurity Action Plan, is sanitary-survey cyber-readiness evidence (segmentation, MFA, patching, backup, IR, training) maintained? Produce the readiness matrix.
- When was the RRA methodology last reviewed against J100-21 / AWWA M19 / VSAT-Web? Produce the methodology attestation.

## 13. Machine-readable twin

The machine-readable companion of this pack lives at [`api/v1/evidence-packs/awia.json`](../../api/v1/evidence-packs/awia.json). It contains the same clause-level coverage, retention guidance, role matrix, and gap list in JSON form, and is regenerated in lockstep with this markdown pack so content stays in sync. Consumers integrating the pack into GRC tools, audit-request portals, or evidence pipelines should consume the JSON document; human readers should consume this markdown.

Related API surfaces (all under [`api/v1/`](../../api/README.md)):

- [`api/v1/compliance/regulations/awia.json`](../../api/v1/compliance/regulations/awia.json) — regulation metadata and per-version coverage metrics
- [`api/v1/compliance/ucs/`](../../api/v1/compliance/ucs/index.json) — individual UC sidecars
- [`api/v1/compliance/coverage.json`](../../api/v1/compliance/coverage.json) — global coverage snapshot
- [`api/v1/compliance/gaps.json`](../../api/v1/compliance/gaps.json) — global gap report

## 14. Provenance and regeneration

This pack is **generated**, not hand-authored. Re-running the generator produces byte-identical output (deterministic sort, stable serialisation, no free-form timestamps outside the block below). CI enforces regeneration drift via `--check` mode.

**Inputs to this pack**

- [`data/regulations.json`](../../data/regulations.json) — commonClauses, priority weights, authoritative URLs
- [`data/evidence-pack-extras.json`](../../data/evidence-pack-extras.json) — retention, roles, authoritative guidance, penalty, testing approach
- [`content/cat-*/UC-*.json`](../../content) — UC sidecars containing compliance[] entries, controlFamily, owner, evidence fields
- [`api/v1/compliance/regulations/awia@*.json`](../../api/v1/compliance/regulations/) — pre-computed coverage metrics (when present)

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

<a id="ref-1"></a>**[1]** Cybersecurity and Infrastructure Security Agency. (2026). *CISA Known Exploited Vulnerabilities Catalog*. U.S. Department of Homeland Security. Retrieved May 11, 2026, from https://www.cisa.gov/known-exploited-vulnerabilities-catalog

<a id="ref-2"></a>**[2]** European Parliament and Council of the European Union. (2016, April). *Regulation (EU) 2016/679 — General Data Protection Regulation*. Official Journal of the European Union, L 119. ELI: reg/2016/679. https://eur-lex.europa.eu/eli/reg/2016/679/oj

<a id="ref-3"></a>**[3]** Fortinet, Inc. (2026). *Fortinet FortiOS Documentation*. Retrieved May 11, 2026, from https://docs.fortinet.com/product/fortigate

<a id="ref-4"></a>**[4]** Microsoft Corporation. (2026). *Microsoft Entra ID Documentation*. Retrieved May 11, 2026, from https://learn.microsoft.com/en-us/entra/identity/

<a id="ref-5"></a>**[5]** Okta, Inc. (2026). *Okta Documentation*. Retrieved May 11, 2026, from https://developer.okta.com/docs/

<a id="ref-6"></a>**[6]** Splunk Inc. (2026). *Splunk Enterprise Security Administration Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ES

<a id="ref-7"></a>**[7]** Splunk Inc. (2026). *Splunk SOAR (Cloud) Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/SOARonprem

<details>
<summary>Additional online sources cited in the document body (44)</summary>

<a id="ref-8"></a>**[8]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013

<a id="ref-9"></a>**[9]** epa.gov. *epa.gov: Awia Online Tools*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-online-tools

<a id="ref-10"></a>**[10]** epa.gov. *epa.gov: Baseline Information Malevolent Acts Community Water Systems*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/baseline-information-malevolent-acts-community-water-systems

<a id="ref-11"></a>**[11]** epa.gov. *epa.gov: Water Sector Cybersecurity*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/forms/water-sector-cybersecurity

<a id="ref-12"></a>**[12]** cisa.gov. *CISA: Water*. Retrieved May 11, 2026, from https://www.cisa.gov/water

<a id="ref-13"></a>**[13]** cisa.gov. *CISA: Ransomware Guide*. Retrieved May 11, 2026, from https://www.cisa.gov/stopransomware/ransomware-guide

<a id="ref-14"></a>**[14]** cisa.gov. *CISA: Cybersecurity Advisories*. Retrieved May 11, 2026, from https://www.cisa.gov/news-events/cybersecurity-advisories

<a id="ref-15"></a>**[15]** federalregister.gov. *federalregister.gov: Cyber Incident Reporting For Critical Infrastructure Act Circia Reporting Requirements*. Retrieved May 11, 2026, from https://www.federalregister.gov/documents/2024/04/04/2024-06526/cyber-incident-reporting-for-critical-infrastructure-act-circia-reporting-requirements

<a id="ref-16"></a>**[16]** awwa.org. *awwa.org: Risk Resilience*. Retrieved May 11, 2026, from https://www.awwa.org/Resources-Tools/Resource-Topics/Risk-Resilience

<a id="ref-17"></a>**[17]** awwa.org. *awwa.org: 56906415*. Retrieved May 11, 2026, from https://www.awwa.org/Store/Product-Details/productId/56906415

<a id="ref-18"></a>**[18]** epa.gov. *epa.gov: Vulnerability Self Assessment Tool Vsat*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/vulnerability-self-assessment-tool-vsat

<a id="ref-19"></a>**[19]** epa.gov. *epa.gov: Creat Risk Assessment Application Water Utilities*. Retrieved May 11, 2026, from https://www.epa.gov/crwu/creat-risk-assessment-application-water-utilities

<a id="ref-20"></a>**[20]** hazards.fema.gov. *hazards.fema.gov: Nri*. Retrieved May 11, 2026, from https://hazards.fema.gov/nri/

<a id="ref-21"></a>**[21]** waterisac.org. *waterisac.org*. Retrieved May 11, 2026, from https://www.waterisac.org/

<a id="ref-22"></a>**[22]** awwa.org. *awwa.org: Mutual Aid Warn*. Retrieved May 11, 2026, from https://www.awwa.org/Resources-Tools/Resource-Topics/Risk-Resilience/Mutual-Aid-WARN

<a id="ref-23"></a>**[23]** cisa.gov. *CISA: Aa23 335A*. Retrieved May 11, 2026, from https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-335a

<a id="ref-24"></a>**[24]** cisa.gov. *CISA: Compromise Us Water Treatment Facility*. Retrieved May 11, 2026, from https://www.cisa.gov/news-events/news/compromise-us-water-treatment-facility

<a id="ref-25"></a>**[25]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-s1433a

<a id="ref-26"></a>**[26]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-s1433b

<a id="ref-27"></a>**[27]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-s1433c

<a id="ref-28"></a>**[28]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-s1433g

<a id="ref-29"></a>**[29]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-RRA-malevolent-acts

<a id="ref-30"></a>**[30]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-RRA-natural-hazards

<a id="ref-31"></a>**[31]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-RRA-electronic-systems

<a id="ref-32"></a>**[32]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-RRA-monitoring-practices

<a id="ref-33"></a>**[33]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-RRA-chemicals

<a id="ref-34"></a>**[34]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-RRA-financial

<a id="ref-35"></a>**[35]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-ERP-strategies-actions

<a id="ref-36"></a>**[36]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-ERP-detection

<a id="ref-37"></a>**[37]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-ERP-cyber-incident-response

<a id="ref-38"></a>**[38]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-ERP-mutual-aid

<a id="ref-39"></a>**[39]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-ERP-review

<a id="ref-40"></a>**[40]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-EPA-cwc-reporting

<a id="ref-41"></a>**[41]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-EPA-sanitary-survey

<a id="ref-42"></a>**[42]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-EPA-aware-checklist

<a id="ref-43"></a>**[43]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-EPA-vsat-j100

<a id="ref-44"></a>**[44]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-EPA-asset-inventory

<a id="ref-45"></a>**[45]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-EPA-mfa-remote-access

<a id="ref-46"></a>**[46]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-EPA-network-segmentation

<a id="ref-47"></a>**[47]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-EPA-backup-recovery

<a id="ref-48"></a>**[48]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-EPA-default-creds

<a id="ref-49"></a>**[49]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-EPA-training

<a id="ref-50"></a>**[50]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-EPA-vuln-mgmt

<a id="ref-51"></a>**[51]** epa.gov. *epa.gov: Awia Section 2013*. Retrieved May 11, 2026, from https://www.epa.gov/waterresilience/awia-section-2013#AWIA-EPA-records-retention

</details>

<!-- END-AUTOGENERATED-SOURCES -->
