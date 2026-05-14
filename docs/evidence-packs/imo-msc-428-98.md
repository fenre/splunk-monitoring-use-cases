# Evidence Pack — IMO MSC.428(98) Maritime Cyber Risk Management

> **Tier**: Tier 1 &nbsp;·&nbsp; **Jurisdiction**: GLOBAL &nbsp;·&nbsp; **Version**: `2017-msc-428-98-with-2022-circ-3-rev-2-and-2024-iacs-e26-e27`
>
> **Full name**: IMO Resolution MSC.428(98) — Maritime Cyber Risk Management in Safety Management Systems, with MSC-FAL.1/Circ.3 Rev.2 Guidelines on Maritime Cyber Risk Management (2022), IACS UR E26 (cyber resilience of ships, Rev.4 2024) and IACS UR E27 (cyber resilience of on-board systems and equipment, Rev.3 2024), reading alongside the BIMCO *Guidelines on Cyber Security Onboard Ships* (v5, 2025).
> **Authoritative source**: [https://www.imo.org/en/OurWork/Security/Pages/Cyber-security.aspx](https://www.imo.org/en/OurWork/Security/Pages/Cyber-security.aspx)
> **Effective from**: 2021-01-01 (first annual DoC verification after 1 January 2021 for the Resolution; 2024-07-01 for E26/E27 new-build contracts)
>
> This evidence pack is the auditor-facing view of the Splunk monitoring catalogue's coverage of the IMO maritime cyber-risk management regime. Every clause coverage claim is traceable to a specific UC sidecar JSON file (`content/cat-22-regulatory-compliance/UC-22.59.*.json`); every retention figure cites its legal basis; every URL resolves to an official IMO, IACS, BIMCO, or flag-State source. Interpretation stays with the Company Security Officer (CSO), the Designated Person Ashore (DPA) and the vessel's Ship Cyber Security Officer (CySO).

> **Live views.** [Buyer narrative (`compliance-story.html?reg=imo-msc-428-98`)](../../compliance-story.html?reg=imo-msc-428-98) · [Auditor clause navigator (`clause-navigator.html#reg=imo-msc-428-98`)](../../clause-navigator.html#reg=imo-msc-428-98) · [JSON twin (`api/v1/compliance/story/imo-msc-428-98.json`)](../../api/v1/compliance/story/imo-msc-428-98.json)

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
11. [Questions a flag-State / PSC / class-society inspector should ask](#11-questions-a-flag-state--psc--class-society-inspector-should-ask)
12. [Machine-readable twin](#12-machine-readable-twin)
13. [Provenance and regeneration](#13-provenance-and-regeneration)

## 1. Purpose of this evidence pack

The International Maritime Organization (IMO) Resolution MSC.428(98) was adopted by the IMO Maritime Safety Committee in June 2017. It affirms that an approved Safety Management System (SMS) under the International Safety Management (ISM) Code should consider cyber risk management in accordance with the objectives and functional requirements of the ISM Code, with the requirement entering practical force no later than the first annual verification of a company's Document of Compliance (DoC) after 1 January 2021. The Resolution is the headline obligation; its day-to-day operational guidance is set out in **MSC-FAL.1/Circ.3 Rev.2 — Guidelines on Maritime Cyber Risk Management** (2022), which structures cyber risk management around the five NIST CSF functions (Identify, Protect, Detect, Respond, Recover). For new vessels keel-laid on or after 1 July 2024, classification societies enforce **IACS UR E26 (cyber resilience of ships)** and **IACS UR E27 (cyber resilience of on-board systems and equipment)** as unified requirements covered by every IACS member society (DNV, ABS, LR, BV, ClassNK, CCS, KR, RINA, IRS, RS, PRS, CRS). The **BIMCO Guidelines on Cyber Security Onboard Ships** (v5, 2025) is the industry-standard practitioner reference, jointly published with INTERTANKO, ICS, INTERCARGO, OCIMF, IUMI and other industry bodies.

The combined obligation is enforced at three layers: the flag State (via DoC verification under ISM Code §13, sometimes delegated to a Recognised Organisation), the port State (via Port State Control inspection under the Paris, Tokyo, Caribbean, Indian Ocean, Riyadh and Black Sea MoUs, which from 2023 onward run periodic Concentrated Inspection Campaigns on cyber risk management), and the classification society (via E26/E27 surveys and the resulting class notation — e.g. DNV CyberSecure, ABS CyberSafety, LR ShipRight, BV Cyber Resilient, ClassNK Cyber). Non-compliance manifests as either a DoC non-conformity (potentially leading to suspension of the DoC and the Safety Management Certificate), a PSC detention (denial of departure), or loss of class (loss of insurance, charterer rejection).

The Splunk monitoring catalogue's coverage maps directly into this three-layer regime: it produces an auditable evidence chain that the CSO and DPA can hand to the flag-State auditor, PSC inspector, or class surveyor. Coverage is built around the NIST-CSF-shaped clauses of MSC-FAL.1/Circ.3 and the equipment-specific UR E26/E27 attestation registers. The DPA bears personal accountability under the ISM Code.

## 2. Scope and applicability

Applies globally to ships ≥ 500 GT engaged in international voyages and the companies operating them under the ISM Code (SOLAS Chapter IX). Approximately 99,000 ships and approximately 50,000 companies are in scope. The clause coverage in this pack assumes the company is an SMS-holder and operates one or more in-scope vessels.

Specific scope rules:

- **MSC.428(98) (Resolution)** — applies to every company operating an in-scope vessel. Cyber risk management must be addressed in the company SMS at first DoC annual verification after 1 January 2021.
- **MSC-FAL.1/Circ.3 Rev.2 (Guidelines)** — operational guidance; the company's SMS is expected to align with the five NIST CSF functions described in §2.1–§2.5.
- **IACS UR E26 (cyber resilience of ships)** — applies to ships contracted on or after 1 July 2024 under an IACS class society. Existing ships (pre-July 2024 contracts) are grandfathered but may voluntarily adopt.
- **IACS UR E27 (cyber resilience of systems and equipment)** — applies at the equipment level to every E26 in-scope vessel. The owner-operator must obtain attestation per cyber-vulnerable component.
- **Class notation (DNV CyberSecure, ABS CyberSafety, LR ShipRight, BV Cyber Resilient, ClassNK Cyber)** — optional voluntary class notation; mandatory for vessels seeking specific charter contracts that require it.
- **Port State Control (PSC)** — applies at every port of call worldwide. The Paris MoU 2023 cyber CIC was a precedent; further CICs are scheduled across all 9 PSC MoU regimes.
- **BIMCO Guidelines on Cyber Security Onboard Ships** — practitioner reference; not directly enforceable but widely cited as the de-facto industry standard for "ordinary practice of seamen" in cyber risk management.

**Territorial scope.** Global. Every flag State has agreed to the IMO regime through ratification of SOLAS Chapter IX and ISM Code adoption. Most flag States (Panama, Liberia, Marshall Islands, Bahamas, Malta, Singapore, etc.) delegate annual verification to Recognised Organisations (typically the vessel's class society). The US Coast Guard (USCG) enforces a parallel domestic regime via the USCG Cyber Strategic Outlook + 33 CFR 101 maritime security regulations, applied through the National Response Center (NRC) reporting workflow and PSC programme. EU flag States additionally cross-reference NIS2 obligations.

## 3. Catalogue coverage at a glance

- **Clauses tracked**: 17
- **Clauses covered by at least one UC**: 17 / 17 (100.0%)
- **Priority-weighted coverage**: 100.0%
- **Contributing UCs**: 17 (UC-22.59.1 through UC-22.59.17)

Coverage methodology is documented in [`docs/coverage-methodology.md`](../coverage-methodology.md). Priority weights come from `data/regulations.json` commonClauses entries.

## 4. Clause-by-clause coverage

Clauses are listed in the order defined by `data/regulations.json commonClauses` for this regulation version. A clause is considered covered when at least one UC sidecar has a `compliance[]` entry matching `(regulation, version, clause)`. Assurance is the maximum across contributing UCs.

| Clause | Topic | Priority | Assurance | UCs |
|---|---|---|---|---|
| `IMO-MSC-428-98-p1` | Resolution paragraph 1 — cyber risks addressed in SMS | 1.0 | `full` | UC-22.59.1 |
| `IMO-MSC-428-98-p2` | Resolution paragraph 2 — first annual DoC verification after 2021-01-01 | 1.0 | `full` | UC-22.59.1 |
| `IMO-MSC-428-98-p3` | Resolution paragraph 3 — administrations ensure cyber risks addressed in SMS | 1.0 | `full` | UC-22.59.17 |
| `IMO-MSC-FAL-Circ-3-s2-1` | Guidelines §2.1 Identify — cyber risk asset register | 1.0 | `full` | UC-22.59.3 |
| `IMO-MSC-FAL-Circ-3-s2-2` | Guidelines §2.2 Protect — segregation, access controls, hardening | 1.0 | `full` | UC-22.59.4, UC-22.59.7, UC-22.59.10, UC-22.59.11, UC-22.59.12 |
| `IMO-MSC-FAL-Circ-3-s2-3` | Guidelines §2.3 Detect — anomaly + integrity surveillance | 1.0 | `full` | UC-22.59.5, UC-22.59.6, UC-22.59.8, UC-22.59.9 |
| `IMO-MSC-FAL-Circ-3-s2-4` | Guidelines §2.4 Respond — incident response + reporting | 1.0 | `full` | UC-22.59.13 |
| `IMO-MSC-FAL-Circ-3-s2-5` | Guidelines §2.5 Recover — drills + after-action register | 0.9 | `full` | UC-22.59.14 |
| `IMO-MSC-FAL-Circ-3-s3-1` | Guidelines §3.1 Cyber-vulnerable systems enumeration | 1.0 | `full` | UC-22.59.3 |
| `IMO-ISM-Code-s1-4` | ISM Code §1.4 SMS functional requirements | 1.0 | `full` | UC-22.59.1 |
| `IMO-ISM-Code-s8-2` | ISM Code §8.2 emergency preparedness drills | 0.9 | `full` | UC-22.59.13, UC-22.59.14 |
| `IACS-UR-E26-r4` | IACS UR E26 Rev.4 — cyber resilience of ships (new-build ≥2024-07-01) | 1.0 | `full` | UC-22.59.15 |
| `IACS-UR-E27-r3` | IACS UR E27 Rev.3 — cyber resilience of systems and equipment | 1.0 | `full` | UC-22.59.16 |
| `BIMCO-Cyber-bridge-systems` | BIMCO §bridge-systems — IBS / ECDIS / GMDSS / VDR hardening | 0.7 | `full` | UC-22.59.5, UC-22.59.6, UC-22.59.7 |

## 5. Evidence collection

### 5.1 Common evidence sources

- **Fleet Document of Compliance (DoC) register** — KV Store `imo_doc_verification_lookup`. Issuance, annual-verification cadence, and SMS-attestation status for every company-managed vessel.
- **DPA + CySO + Alternate roster** — KV Store `imo_dpa_cyso_roster_lookup`. 24×7 reachability via Iridium / VSAT and shore-side heartbeat.
- **Cyber Risk Asset Register (CRAR)** — KV Store `imo_crar_lookup` and `imo_crar_components_lookup`. The MSC-FAL.1/Circ.3 §3.1 cyber-vulnerable systems enumeration, per vessel.
- **Integrated Bridge System baseline** — KV Store `imo_ibs_baseline_lookup`. Golden image of bridge, INS, GMDSS, ECDIS, AIS, VDR configuration.
- **ECDIS / ENC chart-update integrity** — sourcetype `ecdis:enc:update`. Signature-verification status of every chart update applied on every bridge worldwide.
- **AIS / GMDSS / VDES / GNSS** — sourcetypes `ais:nmea2000`, `ais:nmea0183`, `ais:vdes`, `gmdss:audit`. Continuous monitoring of communication-system integrity for spoofing, jamming, and impossible-track anomalies.
- **VDR voyage data recorder** — sourcetype `vdr:audit`. Integrity events from the black-box equivalent.
- **Propulsion / engine control / PMS telemetry** — `osisoft:pi:archive`, `aveva:pi:audit`. Time-series telemetry from OSIsoft PI / AVEVA PI System per vessel.
- **Dynamic Positioning System** — sourcetype `dps:event`. DP-class-1/2/3 vessel-specific telemetry.
- **Cargo Management System / Tank Monitoring System** — sourcetypes `cms:audit`, `tms:audit`. Cargo handling and tank gauging integrity events.
- **USB / removable-media governance** — Microsoft Defender Device Control sourcetype `mscs:wd:atp:device-control`. Bridge and engineering workstation USB-port governance.
- **Shore-to-ship satcom remote access** — CyberArk PSM sourcetypes `cyberark:session`, `cyberark:audit`. PAM-mediated remote access for shipboard OT changes.
- **OT-discovery sensor feed** — Cisco Cyber Vision, Claroty CTD / xDome, Nozomi Guardian / Vantage, Dragos Platform, Armis Centrix. Sourcetypes `cisco:cybervision:asset`, `claroty:ctd:asset`, `nozomi:guardian:asset`, `dragos:platform:asset`, `armis:centrix:detection`.
- **Authority submission receipts** — HEC tokens `hec:imo:flag:submission`, `hec:uscg:nrc:submission`, `hec:psc:submission`, `hec:ro:submission`. Submission audit for flag-State, USCG NRC, port-State and Recognised Organisation notifications.
- **IACS UR E26 / E27 attestation register** — KV Stores `iacs_ur_e26_attestation_lookup`, `iacs_ur_e27_attestation_lookup`. Ship-level and equipment-level cyber-resilience attestations.
- **Class notation register** — KV Store `class_notation_lookup`. DNV CyberSecure / ABS CyberSafety / LR ShipRight / BV Cyber Resilient / ClassNK Cyber attestation status.
- **Cyber-drill after-action register** — KV Store `imo_cyber_drill_lookup`. Annual cyber-drill and tabletop completion ledger.
- **ServiceNow GRC / CMDB / SIR** — `snow:cmdb_ci`, `snow:risk`, `snow:sir`. Vessel inventory, incident workflow, action-item closure.
- **Audit-evidence summary index** — `audit_evidence`. Consolidated 5-year retention of every UC-22.59.x result row, marker `uc=22.59.X,reg=IMO-MSC-428-98,clause=...`.

### 5.2 Retention requirements

| Artifact | Retention | Legal basis |
|---|---|---|
| DoC + SMC certificates and annual verification records | Lifetime of DoC + 5 years | ISM Code §13; flag-State guidance |
| Cyber Risk Asset Register (CRAR) per vessel | Lifetime of vessel + 5 years | MSC-FAL.1/Circ.3 §3.1 |
| Cyber-incident notification + flag-State / RO / NRC / PSC receipts | Lifetime of vessel + 5 years (often 10 in EU NIS2 overlap) | MSC-FAL.1/Circ.3 §2.4; ISM Code §8.2 |
| Cyber-drill after-action register | Minimum 5 years rolling | ISM Code §8.2; MSC-FAL.1/Circ.3 §2.5 |
| OT-discovery sensor feed (sufficient for E27 forensic re-creation) | Minimum 5 years rolling for class survey; 7 years for incidents | IACS UR E27; class-society guidance |
| ECDIS / ENC chart-update integrity log | Minimum 2 years rolling (full voyage history per VDR rules) | SOLAS Chapter V; IHO S-66 |
| IBS configuration-baseline drift register | Minimum 5 years rolling | IACS UR E26; class-society guidance |
| AIS / GMDSS / GNSS integrity events | Minimum 5 years rolling | SOLAS Chapter IV-V |
| IACS UR E26 ship-level attestation | Lifetime of vessel + 10 years (class survey horizon) | IACS UR E26 |
| IACS UR E27 equipment-level attestation | Lifetime of equipment + 5 years | IACS UR E27 |
| Class notation register (DNV CyberSecure etc.) | Lifetime of notation + 10 years | Class-society rules |
| DPA / CySO roster + qualification records | Duration of role + 5 years | ISM Code §4 |
| Shore-to-ship satcom PAM session records | Minimum 5 years rolling | Internal governance; IACS UR E27 |
| Master compliance scorecard archived snapshots | Daily snapshot, 7-year rolling retention | Internal governance |

> Retention figures above are minimums or regulator-stated expectations. Where personal-data content appears in evidence packets (e.g. crew identifiers), GDPR Art.5(1)(e) storage-limitation principle drives shorter retention for the personal-data fields while the evidence-of-compliance retention retains the longer period (anonymised). National-security restrictions may extend retention for tonnage-tax-relevant or military-sealift vessels.

### 5.3 Evidence integrity expectations

All IMO / IACS / class-society evidence must be tamper-evident and produced in English (the working language of the IMO and class societies). The Splunk catalogue archives every UC-22.59.x result row to the `audit_evidence` summary index with a stable marker (`uc=22.59.X,reg=IMO-MSC-428-98,clause=...`). Recommended pattern: RFC 3161 time-stamping via DigiCert / DocuSign + ServiceNow GRC immutable-audit-log mode. The DPA signs the monthly attestation; the class-society surveyor counter-signs at the annual cyber-survey.

## 6. Control testing procedures

### 6.1 Inspector-style testing

A flag-State auditor, PSC inspector, or class-society cyber surveyor typically tests:

- **DoC cyber-SMS verification** — pick a named vessel; demonstrate continuous-monitoring evidence for §2.1 (Identify), §2.2 (Protect), §2.3 (Detect), §2.4 (Respond) and §2.5 (Recover) from the past 12 months.
- **CRAR completeness** — request the §3.1 seven cyber-vulnerable categories enumeration for a named vessel and the staleness check on the latest update.
- **AIS / GMDSS / GNSS integrity** — present a 30-day rolling spoof / jam / impossible-track event audit for a named vessel and the response actions taken.
- **ECDIS / ENC chart-update signature** — pick a named recent voyage; demonstrate signature-verification status on every chart update applied during the voyage.
- **IBS baseline drift** — pick a named vessel; demonstrate baseline-conformance audit at master takeover.
- **Cyber-incident clock** — synthetic incident; verify the DPA + CySO escalation, flag-State / RO / NRC / PSC submission within the 24-hour window.
- **PSC inspector cyber CIC** — present 12-month rolling evidence packet for a vessel arriving in a Paris MoU port.
- **Class society cyber survey** — pick a named E26 + E27 in-scope vessel; demonstrate attestation currency + firmware-match on the named OT equipment.
- **USB / removable-media governance** — pick a named bridge or engineering workstation; demonstrate enforced policy.
- **Shore-to-ship satcom** — pick a named recent PAM session; demonstrate WYSIWYS, MFA, session recording.
- **Crew BYOD / passenger Wi-Fi segregation** — pick a named vessel; demonstrate isolation from OT/CBS.

### 6.2 Internal DPA testing

Quarterly self-test (DPA-led):

1. Trigger a synthetic incident in dev environment matching UC-22.59.13.
2. Confirm the 24-hour clock fires correctly for each authority.
3. Confirm flag-State + RO + (where applicable) USCG NRC + port-State submissions would have been queued and transmitted.
4. Pause before submission; document in `audit_evidence` with `imo_exercise_id=Q...`.
5. Run UC-22.59.14 over the past 12 months to verify drill-cadence currency.

## 7. Roles and responsibilities

- **Designated Person Ashore (DPA)** — Named to flag State under ISM Code §4; bears personal liability for SMS compliance signatures and emergency-preparedness oversight. The DPA holds the ultimate authority on cyber-incident classification and reporting.
- **Company Security Officer (CSO)** — Owns cyber risk management on behalf of the company; signs the cyber-SMS attestation; liaises with class society and flag-State auditor.
- **Master + Ship Cyber Security Officer (CySO)** — Vessel-level owner; the CySO is a named officer onboard (often the chief engineer, ETO, or first officer in dual-hatted role) who carries the operational cyber-response responsibility at sea.
- **Designated Operational Centre / Fleet-Operations Centre (FOC)** — 24×7 shore-side cybersecurity monitoring centre. May be in-house or SOC-as-a-service.
- **Recognised Organisation (RO) / Class Society surveyor** — Delegates the flag-State annual verification + E26/E27 + class-notation survey. DNV, ABS, LR, BV, ClassNK, CCS, KR, RINA, IRS, RS, PRS, CRS.
- **Flag State Administration** — Issues the DoC + Safety Management Certificate (SMC). Examples: Panama Maritime Authority, Liberian Registry, Marshall Islands Registry, Bahamas Maritime Authority, Malta Maritime Authority, MPA Singapore.
- **Port State Control (PSC) inspector** — Member-state inspector under Paris / Tokyo / Caribbean / Indian Ocean / Riyadh / Black Sea / Abuja / Viña del Mar / Mediterranean MoU.
- **United States Coast Guard (USCG)** — For US-port-visiting vessels, the USCG National Response Center (NRC) reporting channel under 33 CFR 101.
- **Procurement Manager** — Owns the supply-chain workflow that registers every UR E27 component delivery against the attestation register.
- **OT Engineer / Marine Engineer** — Vessel-side engineer responsible for OT-discovery sensor coverage, baseline conformance, and firmware-attestation match.

## 8. Authoritative guidance

- IMO Resolution MSC.428(98): [https://wwwcdn.imo.org/localresources/en/OurWork/Security/Documents/Resolution%20MSC.428(98).pdf](https://wwwcdn.imo.org/localresources/en/OurWork/Security/Documents/Resolution%20MSC.428(98).pdf)
- IMO MSC-FAL.1/Circ.3 Rev.2 (Guidelines on Maritime Cyber Risk Management): [https://wwwcdn.imo.org/localresources/en/OurWork/Security/Documents/MSC-FAL.1-Circ.3-Rev.2.pdf](https://wwwcdn.imo.org/localresources/en/OurWork/Security/Documents/MSC-FAL.1-Circ.3-Rev.2.pdf)
- IMO Maritime Cyber Risk page: [https://www.imo.org/en/OurWork/Security/Pages/Cyber-security.aspx](https://www.imo.org/en/OurWork/Security/Pages/Cyber-security.aspx)
- International Safety Management (ISM) Code: [https://www.imo.org/en/OurWork/HumanElement/Pages/ISMCode.aspx](https://www.imo.org/en/OurWork/HumanElement/Pages/ISMCode.aspx)
- IACS UR E26 (Cyber Resilience of Ships, Rev.4): [https://iacs.org.uk/publications/unified-requirements/](https://iacs.org.uk/publications/unified-requirements/)
- IACS UR E27 (Cyber Resilience of Systems and Equipment, Rev.3): [https://iacs.org.uk/publications/unified-requirements/](https://iacs.org.uk/publications/unified-requirements/)
- BIMCO Guidelines on Cyber Security Onboard Ships (v5, 2025): [https://www.bimco.org/about-us-and-our-members/publications/the-guidelines-on-cyber-security-onboard-ships](https://www.bimco.org/about-us-and-our-members/publications/the-guidelines-on-cyber-security-onboard-ships)
- DNV Maritime Cyber Security: [https://www.dnv.com/maritime/insights/topics/maritime-cyber-security/index.html](https://www.dnv.com/maritime/insights/topics/maritime-cyber-security/index.html)
- ABS Guide for Cybersecurity Implementation for the Marine and Offshore Industries: [https://ww2.eagle.org/en/rules-and-resources/rules-and-guides.html](https://ww2.eagle.org/en/rules-and-resources/rules-and-guides.html)
- Lloyd's Register ShipRight Cyber: [https://www.lr.org/en/services/maritime/maritime-cyber-security/](https://www.lr.org/en/services/maritime/maritime-cyber-security/)
- Bureau Veritas Cyber Resilient: [https://marine-offshore.bureauveritas.com/cybersecurity](https://marine-offshore.bureauveritas.com/cybersecurity)
- Paris MoU Cyber CIC 2023: [https://www.parismou.org/inspections-risk/library-faq/cic](https://www.parismou.org/inspections-risk/library-faq/cic)
- USCG Maritime Cyber Strategic Outlook: [https://www.uscg.mil/maritimecyber/](https://www.uscg.mil/maritimecyber/)
- USCG MSIB 002-23 Reporting Maritime Cyber Incidents: [https://www.uscg.mil/Maritime-Commons/](https://www.uscg.mil/Maritime-Commons/)
- USCG National Response Center: [https://www.nrc.uscg.mil/](https://www.nrc.uscg.mil/)
- IHO S-66 (Facts about electronic charts and carriage requirements): [https://iho.int/](https://iho.int/)

## 9. Common audit deficiencies

1. **Cyber-SMS attestation stale** — DoC verifier finds the cyber-SMS attestation is older than 12 months; mitigated by UC-22.59.1 continuous register surveillance.
2. **DPA / CySO single-point-of-failure** — only one person holds the role with no documented alternate; mitigated by UC-22.59.2 roster check.
3. **CRAR incomplete** — one or more §3.1 cyber-vulnerable categories missing; mitigated by UC-22.59.3 enumeration validation.
4. **IT/OT segregation drift** — administrative LAN traffic reaches OT systems; mitigated by UC-22.59.4 baseline conformance.
5. **ECDIS / ENC chart update signature unverified** — fake or self-signed chart applied; mitigated by UC-22.59.5 signature-verification surveillance.
6. **AIS spoof / jam not detected** — vessel reporting impossible position; mitigated by UC-22.59.6 anomaly detection.
7. **IBS configuration drift** — bridge software updated without baseline refresh; mitigated by UC-22.59.7 drift detection.
8. **Propulsion / DP cyber-anomaly missed** — statistical deviations not tied to cyber-investigation workflow; mitigated by UC-22.59.8.
9. **Cargo system tampering** — tank-gauging or inert-gas anomaly; mitigated by UC-22.59.9.
10. **USB policy not enforced** — engineering workstation tolerates removable media; mitigated by UC-22.59.10.
11. **Satcom remote access without PAM** — shore-to-ship support bypasses PAM and session recording; mitigated by UC-22.59.11.
12. **Passenger Wi-Fi reaches OT** — segregation between guest network and CBS broken; mitigated by UC-22.59.12.
13. **24-hour reporting clock missed** — flag State or USCG NRC notified too late; mitigated by UC-22.59.13.
14. **Annual cyber-drill skipped** — drill register stale; mitigated by UC-22.59.14.
15. **IACS UR E26 / E27 attestation expired** — class survey overdue; mitigated by UC-22.59.15 and UC-22.59.16.
16. **Firmware drifts from attested baseline** — installed software differs from the version attested to UR E27; mitigated by UC-22.59.16.
17. **PSC cyber-CIC evidence retrieval slow** — inspector requests evidence, retrieval takes longer than the inspection window; mitigated by UC-22.59.17 retrieval ledger.

## 10. Enforcement and penalties

Enforcement is exercised at three levels:

- **Flag State (ISM Code §13 + national law)** — non-compliance can lead to a DoC non-conformity (major or minor) at annual verification; a major non-conformity uncorrected within the agreed window leads to DoC suspension and consequently to SMC suspension on every vessel under the DoC. SMC suspension prevents the vessel from sailing under the flag and triggers detention at the next port.
- **Port State Control (Paris / Tokyo / Caribbean / Indian Ocean / Riyadh / Black Sea / Abuja / Viña del Mar / Mediterranean MoU)** — non-compliance at a cyber-CIC inspection can lead to a "30-day rectification" deficiency, a PSC detention, or in extreme cases a ban from the MoU region. The Paris MoU 2023 cyber CIC issued detentions for vessels failing to demonstrate basic cyber-risk-management evidence.
- **Class society (IACS UR E26 / E27 + class notation)** — non-compliance can lead to a class condition, suspension or withdrawal of class. Loss of class triggers loss of insurance under the typical hull and machinery policy, and rejection by major charterers (oil-majors via OCIMF / SIRE 2.0, chemical via CDI, dry-bulk via RightShip).

In addition, the US Coast Guard applies parallel domestic enforcement under 33 CFR 101 and the Maritime Transportation Security Act (MTSA). For vessels engaged in US trade, USCG can issue Captain of the Port Orders, deny port entry, or detain vessels. Civil penalties under MTSA scale to USD 25,000 per violation per day.

The DPA bears personal liability under the ISM Code; in some flag-State jurisdictions (Panama, Liberia, Marshall Islands) this can rise to criminal liability in case of safety-impacting incidents traced to cyber-risk-management failure.

## 11. Questions a flag-State / PSC / class-society inspector should ask

- Show me the current DPA + CySO roster + on-call rotation for the past 90 days, and the heartbeat status today.
- Present the current Cyber Risk Asset Register for vessel <IMO-number>. Walk me through each of the seven cyber-vulnerable categories from MSC-FAL.1/Circ.3 §3.1.
- Demonstrate continuous IT/OT segregation surveillance for vessel <IMO-number> over the past 30 days. What was the worst flow-violation event and what was the response?
- Show me the latest ECDIS / ENC chart-update signature audit on vessel <IMO-number>. Were there any unsigned updates? What was the policy response?
- Show me a 30-day rolling AIS / GMDSS / GNSS integrity audit on vessel <IMO-number>. Pick the worst spoof or impossible-track event and walk me through the response.
- Show me the latest cyber-drill record for vessel <IMO-number>. What scenario was exercised? What action items are still open?
- For vessel <IMO-number> contracted after 1 July 2024 — present the IACS UR E26 attestation, the class notation, and the certifying surveyor.
- For an E27-in-scope component on vessel <IMO-number> — present the attestation, the attested firmware version, and demonstrate that the installed firmware matches.
- Present the most recent cyber-incident notification submitted to my office. Walk me through the 24-hour clock and the multi-authority routing.
- Present the DPA monthly attestation for the past 12 months.
- Demonstrate the audit-evidence retrieval workflow for vessel <IMO-number>. Hand me a PDF / CSV bundle covering UC-22.59.1 to UC-22.59.16 over the past 90 days.

## 12. Machine-readable twin

- API endpoint: `api/v1/compliance/story/imo-msc-428-98.json`
- Raw clause data: `data/regulations.json` (id=`imo-msc-428-98`)
- Per-UC sidecar files: `content/cat-22-regulatory-compliance/UC-22.59.*.json`
- Coverage methodology: `docs/coverage-methodology.md`

## 13. Provenance and regeneration

This evidence pack is regenerated as part of the catalogue build. Manual narrative sections (purpose, scope, common deficiencies, inspector questions) are authored; clause coverage tables are computed from UC sidecar `compliance[]` arrays. Last reviewed: 2026-05-14. Note: this evidence pack is the auditor-facing companion to UC-22.59.1 through UC-22.59.17. The DPA and CSO sign the consolidated attestation; the class society counter-signs at the annual E26/E27 cyber survey.
