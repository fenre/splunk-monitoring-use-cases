# Evidence Pack — CERT-In Directions 2022 + DPDP Act 2023 (India)

> **Tier**: Tier 1 &nbsp;·&nbsp; **Jurisdiction**: IN &nbsp;·&nbsp; **Version**: `2022-04-28-cert-in-directions-with-2023-dpdp`
>
> **Full name**: Indian Computer Emergency Response Team (CERT-In) Directions No. 20(3)/2022-CERT-In issued 28 April 2022 under Section 70B(6) of the Information Technology Act 2000, together with the Digital Personal Data Protection Act 2023 ("DPDP") and the Data Protection Board of India.
> **Authoritative sources**: [Indian Computer Emergency Response Team (CERT-In)](https://www.cert-in.org.in/) · [Ministry of Electronics and IT (MeitY)](https://www.meity.gov.in/) · [Data Protection Board of India](https://www.dpb.gov.in/) (once operational)
> **Effective from**: 2022-06-27 (CERT-In Directions binding date); 2023-08-12 (DPDP Act assent); DPDP rules notified by Union Notification dated 2025 (rolling implementation through 2026)
>
> This evidence pack is the auditor-facing view of the Splunk monitoring catalogue's coverage of CERT-In Directions 2022 and the DPDP Act 2023 + Data Protection Board of India regime. Every clause coverage claim is traceable to a specific UC sidecar JSON file (`content/cat-22-regulatory-compliance/UC-22.62.*.json`); every retention figure cites its legal basis; every URL resolves to an official CERT-In, MeitY, or DPB-India source. The pack does **not** assert legal conclusions — Indian law, CERT-In, MeitY, and the Data Protection Board of India retain final interpretive authority. Interpretation stays with India-qualified counsel and the Data Protection Officer (DPO).

> **Live views.** [Buyer narrative (`compliance-story.html?reg=cert-in`)](../../compliance-story.html?reg=cert-in) · [Auditor clause navigator (`clause-navigator.html#reg=cert-in`)](../../clause-navigator.html#reg=cert-in) · [JSON twin (`api/v1/compliance/story/cert-in.json`)](../../api/v1/compliance/story/cert-in.json)

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
11. [Questions a CERT-In / DPB-India inspector should ask](#11-questions-a-cert-in--dpb-india-inspector-should-ask)
12. [Machine-readable twin](#12-machine-readable-twin)
13. [Provenance and regeneration](#13-provenance-and-regeneration)

## 1. Purpose of this evidence pack

On 28 April 2022, the Indian Computer Emergency Response Team (CERT-In) issued binding Directions under Section 70B(6) of the Information Technology Act 2000 covering every body corporate, intermediary, data centre, virtual private server (VPS) provider, cloud-service provider, government organisation, and virtual asset service provider (VASP / crypto exchange) operating in or providing services to users in India. The Directions create a stringent and short-clock cyber-incident reporting regime that diverges materially from comparable regimes in other jurisdictions:

- **Direction (ii)** — every regulated entity must report cybersecurity incidents falling within 20 enumerated categories to CERT-In within 6 hours of noticing them (the shortest such clock in any major jurisdiction).
- **Direction (iii)** — every regulated entity must synchronise all ICT systems clocks with NTP servers traceable to NIC (National Informatics Centre) or NPL (National Physical Laboratory).
- **Direction (iv)** — every regulated entity must retain ICT logs for a rolling 180 days within Indian jurisdiction.
- **Direction (v)** — VPN, VPS, and cloud-service providers must maintain customer KYC for 5 years and IP-address allocation records for 5 years.
- **Direction (vi)** — every regulated entity must designate a Point-of-Contact (POC) for CERT-In communications and notify any change within 7 days; the POC must be reachable 24x7.
- **Direction (vii)** — virtual asset service providers (crypto exchanges, custodial wallets) must maintain customer KYC + transaction records for 5 years.

In parallel, the Digital Personal Data Protection Act 2023 (DPDP) entered the statute book on 12 August 2023, with rolling rule-notification through 2025-2026. DPDP creates obligations on Data Fiduciaries (controllers in GDPR parlance) and a heavier-handed sub-class — Significant Data Fiduciaries (SDFs) — designated by the Central Government under DPDP Section 10. SDF obligations include: India-based Data Protection Officer (DPO), periodic Data Protection Impact Assessment (DPIA), annual independent data audit, and 72-hour breach notification to the Data Protection Board of India.

The Splunk monitoring catalogue's coverage maps directly into this multi-document regime: the catalogue produces an auditable evidence chain that the regulated entity can hand to a CERT-In Director, a sectoral CERT (CERT-Fin, CERT-Telecom, CERT-Power) inspector, a MeitY auditor, or a Data Protection Board of India inspection officer.

## 2. Scope and applicability

Applies to:

- **Every body corporate** in India processing or handling Sensitive Personal Data or Information (SPDI) under IT Act Section 43A — practical scope is broad, covering most operating businesses with personal-data systems.
- **Every intermediary** under IT Act Section 79 — internet intermediaries, telecom intermediaries, payment intermediaries, social-media platforms (Significant Social Media Intermediaries face additional duties under the IT Rules 2021).
- **Every data centre, VPS provider, cloud-service provider** offering services in India — including foreign-headquartered cloud providers with Indian customers or Indian data residency.
- **Every government organisation** at central, state, or municipal level operating ICT systems.
- **Every Virtual Asset Service Provider (VASP)** — Indian crypto exchanges, custodial wallets, NFT marketplaces, and similar. Indian residents may not transact via offshore VASPs without the offshore VASP complying with CERT-In Direction (vii) — a frequently-litigated extraterritoriality point.
- **Every Data Fiduciary (controller equivalent)** processing personal data of Data Principals (data subjects) in India under DPDP Act.
- **Every Significant Data Fiduciary (SDF)** designated by the Central Government under DPDP Section 10 — typical SDF triggers: volume of personal data, sensitivity of personal data, risk to rights of Data Principals, sovereignty / national-security factors.

Excludes: pure offline operations with no ICT system handling personal data and no incident-eligible scope under CERT-In Directions; certain limited-scope household-use data processing (DPDP); state-secret communications under the Official Secrets Act 1923 (separate framework).

**Territorial scope.** CERT-In Directions reach every entity offering services to users in India, regardless of nationality of the operating entity — a foreign-headquartered VPN provider serving Indian subscribers is fully in-scope. DPDP Act has extraterritorial reach under DPDP Section 3(b) to data processing outside India that is in connection with offering goods or services to Data Principals in India.

## 3. Catalogue coverage at a glance

- **Clauses tracked**: 11 (CERT-In-Dir-2 through Dir-7; IT-Act-Sec-70B; IT-Act-Sec-43A; DPDP-Sec-8; DPDP-Sec-10; DPDP-Sched-A)
- **Clauses covered by at least one UC**: 11 / 11 (100.0%)
- **Priority-weighted coverage**: 100.0%
- **Contributing UCs**: 8 (UC-22.62.1 through UC-22.62.8)

Coverage methodology is documented in [`docs/coverage-methodology.md`](../coverage-methodology.md). Priority weights come from `data/regulations.json` commonClauses entries.

## 4. Clause-by-clause coverage

Clauses are listed in the order defined by `data/regulations.json commonClauses` for this regulation version. A clause is considered covered when at least one UC sidecar has a `compliance[]` entry matching `(regulation, version, clause)`. Assurance is the maximum across contributing UCs.

| Clause | Topic | Priority | Assurance | UCs |
|---|---|---|---|---|
| `CERT-In-Dir-2` | 6-hour cybersecurity incident reporting to CERT-In | 1.0 | `full` | UC-22.62.1 |
| `CERT-In-Dir-3` | NTP synchronisation to NIC / NPL traceable sources | 1.0 | `full` | UC-22.62.2 |
| `CERT-In-Dir-4` | Designated Point-of-Contact + 24x7 availability + 7-day change notification | 1.0 | `full` | UC-22.62.3 |
| `CERT-In-Dir-5` | 180-day rolling ICT log retention within Indian jurisdiction | 1.0 | `full` | UC-22.62.4 |
| `CERT-In-Dir-5-1` | VPN / VPS / cloud-provider subscriber KYC + 5-year retention | 1.0 | `full` | UC-22.62.5 |
| `CERT-In-Dir-6` | VASP / crypto-exchange KYC + 5-year transaction-record retention | 1.0 | `full` | UC-22.62.6 |
| `CERT-In-Dir-7` | Body-corporate KYC supervision under sectoral regulators | 1.0 | `partial` | UC-22.62.6 |
| `IT-Act-Sec-70B` | CERT-In authority + IT Act Section 70B(6) Directions | 1.0 | `full` | UC-22.62.1 |
| `IT-Act-Sec-43A` | Reasonable Security Practices for SPDI | 1.0 | `full` | UC-22.62.7, UC-22.62.8 |
| `DPDP-Sec-8` | SDF obligations + 72-hour breach notification | 1.0 | `full` | UC-22.62.7, UC-22.62.8 |

## 5. Evidence collection

### 5.1 Common evidence sources

- **CERT-In Category Taxonomy lookup** — KV Store `cert_in_category_taxonomy_lookup`. The 20-incident-category enumeration with mapping to internal alert sources.
- **ServiceNow SIR** — `snow:sir`. Incident tickets, classification, owner assignment, supplemental-report log.
- **CERT-In Reporting Submission HEC** — `hec:certin:reporting:submission`. The CERT-In Portal acknowledgement and submission timestamps.
- **NTP Authoritative Source Register** — KV Store `cert_in_ntp_authoritative_lookup`. NIC/NPL-traceable NTP servers (samay1.nic.in, samay2.nic.in, time.npl.res.in).
- **NTP Register** — KV Store `cert_in_ntp_register_lookup`. Per-host last-sync time, source, drift, traceability.
- **NTP daemon events** — OS NTP / chronyd / w32time events ingested via Splunk Add-ons for Unix/Linux and Windows.
- **POC Register** — KV Store `cert_in_poc_register_lookup`. Designated CERT-In Point-of-Contact with on-call coverage, 7-day-change-window tracking, and HRIS integration.
- **POC Contactability-Test Register** — KV Store `cert_in_poc_contactability_test_lookup`. Synthetic tests of POC reachability.
- **Splunk REST API** — `/services/data/indexes` for `frozenTimePeriodInSecs`; `| dbinspect` for oldest indexed event per source.
- **Log Register** — KV Store `cert_in_log_register_lookup`. Per-source jurisdiction attestation (Indian-hosted) and 180-day retention attestation.
- **Subscriber KYC Register** — KV Store `cert_in_subscriber_kyc_lookup`. Per-customer KYC limbs (validated name, contact, IP, period of hire, owner identity, purpose, pattern of ownership change).
- **VPN/VPS IP Allocation Register** — KV Store `cert_in_ip_allocation_lookup`. Per-customer IP lease records for 5 years.
- **VASP Customer KYC Register** — KV Store `vasp_customer_kyc_lookup`. Per-customer crypto-exchange KYC limbs.
- **VASP Transaction Retention Attestation** — KV Store `vasp_transaction_retention_attestation_lookup`. Per-customer transaction-record retention per CERT-In Dir-6.
- **SDF Register** — KV Store `dpdp_sdf_register_lookup`. DPDP Section 10 SDF designation with DPO (Indian-resident), DPIA cadence, audit-cadence tracking.
- **DPIA Register** — KV Store `dpdp_dpia_register_lookup`. DPDP Section 8(d) DPIA scope, completion, finding-closure.
- **Independent Audit Register** — KV Store `dpdp_independent_audit_register_lookup`. DPDP Section 10(2)(c) annual data-audit by independent auditor.
- **SPDI Taxonomy Lookup** — KV Store `dpdp_spdi_taxonomy_lookup`. Sensitive Personal Data or Information categories per IT Rules 2011.
- **Data Principal Notification Register** — KV Store `dpdp_data_principal_notification_lookup`. The 72-hour data-principal-notification limb under DPDP Section 8(6).
- **DPB-India Reporting Submission HEC** — `hec:dpb:reporting:submission`. Data Protection Board of India Portal acknowledgement and submission timestamps.

### 5.2 Retention requirements

| Artifact | Retention | Legal basis |
|---|---|---|
| Cybersecurity incident report to CERT-In (Direction (ii)) | Minimum 5 years | CERT-In Directions 2022 §(iv) — log retention; IT Act Section 70B(6) record-keeping |
| ICT system logs (Direction (iv)) | Minimum 180 days rolling, within Indian jurisdiction | CERT-In Directions 2022 §(iv) |
| VPN/VPS/cloud-provider subscriber KYC + IP allocation records | Minimum 5 years post-deregistration | CERT-In Directions 2022 §(v) |
| VASP customer KYC + transaction records | Minimum 5 years | CERT-In Directions 2022 §(vi) + RBI / FIU-IND PMLA requirements |
| POC designation file + change-history | Lifetime of POC + 5 years | CERT-In Directions 2022 §(vii) |
| NTP audit-evidence | Minimum 180 days rolling | CERT-In Directions 2022 §(iii) |
| SPDI handling records under IT Act Section 43A | Minimum 3 years post-data-deletion | IT Act Section 43A + Reasonable Security Practices Rules 2011 |
| DPDP SDF DPIA report | Minimum 3 years from completion | DPDP Section 8(d) + DPDP Rules (notified 2024-2026) |
| DPDP SDF annual independent audit report | Minimum 5 years from completion | DPDP Section 10(2)(c) |
| DPDP 72-hour breach-notification report | Minimum 5 years | DPDP Section 8(6) |
| Audit-evidence summary index (catalogue archive) | Daily snapshot, 7-year rolling | Internal evidence-of-compliance governance |

> Retention figures above are minimums or regulator-stated expectations. Cross-sectoral overlays may impose longer retention — for example, RBI prudential supervision retention for banks (10 years on customer information), SEBI for capital markets intermediaries (8 years for inter-account-flow records), and IRDAI for insurance entities (7 years on policy-related records).

### 5.3 Evidence integrity expectations

All CERT-In / MeitY / DPB-India evidence must be tamper-evident and produced in English (Hindi or relevant regional language acceptable for state-level submissions). The Splunk catalogue archives every UC-22.62.x result row to the `audit_evidence` summary index with a stable marker (`uc=22.62.X,reg=CERT-In,clause=...`). Recommended pattern: RFC 3161 time-stamping via emSigner / eMudhra / Capricorn (India-licensed Certifying Authorities under IT Act Section 24); ServiceNow GRC immutable-audit-log mode; CERT-In Portal submission receipt cryptographic chain. POC designations and DPO appointments should be physically counter-signed by a Director / Partner on company letterhead.

## 6. Control testing procedures

### 6.1 Inspector-style testing

A CERT-In Director / sectoral-CERT inspector / DPB-India inspection officer typically tests:

- **6-hour incident clock** — pick a synthetic incident in a dev environment matching UC-22.62.1; verify the SOAR-automated CERT-In submission is queued within 1 hour, executed within 6 hours, and the receipt is stored in `audit_evidence` (UC-22.62.1).
- **NTP traceability** — pick a random ICT host; verify the NTP source is NIC/NPL-traceable and the last-sync drift is within tolerance (UC-22.62.2).
- **POC reachability** — pick a random weekend/holiday timestamp; verify the POC, the synthetic contactability-test record, and the on-call-roster freshness (UC-22.62.3).
- **180-day log retention** — pick a random sourcetype; verify the index `frozenTimePeriodInSecs` is at least 15,552,000 (180 days), the oldest event timestamp is at least 180 days old, and the index is physically hosted in India (UC-22.62.4).
- **VPN/VPS/cloud subscriber KYC** — pick a random customer of a VPN/VPS/cloud product; demonstrate the seven KYC limbs (validated name, contact, IP, period of hire, owner identity, purpose, pattern of ownership change) plus the 5-year retention (UC-22.62.5).
- **VASP KYC + transaction retention** — pick a random VASP customer; demonstrate the KYC limbs and the 5-year transaction-record retention (UC-22.62.6).
- **DPDP SDF DPIA + independent audit** — pick a designated SDF; demonstrate the Indian-resident DPO, the current DPIA, and the most recent independent audit (UC-22.62.7).
- **DPDP 72-hour breach notification** — synthetic SPDI-touching breach; verify the DPB-India submission within 72 hours and the parallel Data Principal notification (UC-22.62.8).

### 6.2 Internal DPO / Compliance Officer testing

Quarterly self-test (DPO / Compliance Officer led):

1. Trigger a synthetic incident in dev environment matching UC-22.62.1 (CERT-In 6-hour clock) and UC-22.62.8 (DPB-India 72-hour clock).
2. Confirm both clocks fire correctly with the right markers.
3. Confirm the CERT-In Portal and DPB-India Portal submissions are queued.
4. Pause before submission and document the rehearsal in `audit_evidence` with `cert_in_exercise_id=Q...`.
5. Run UC-22.62.4 over the past 200 days to verify 180-day log-retention continuity.

## 7. Roles and responsibilities

- **Designated CERT-In Point of Contact (POC)** — Required under Direction (vii); single 24x7 contact for CERT-In; 7-day change notification.
- **Data Protection Officer (DPO)** — Required for Significant Data Fiduciaries under DPDP Section 10(2)(a); must be India-resident; reports to the Board.
- **Chief Information Security Officer (CISO)** — Owns CERT-In Direction technical-control implementation; sign-off on the annual ICT log-retention attestation.
- **Privacy / Legal Counsel (India-qualified)** — Owns DPDP / IT Act Section 43A interpretation; manages cross-border data-flow questions and the IT Rules 2021 interface.
- **Sectoral CISO liaison** — For regulated industries: CERT-Fin for finance, CERT-Telecom for telecom (under DoT), CERT-Power for power, NCIIPC for CII assets, FIU-IND for VASP and PMLA-relevant entities.
- **VASP Compliance Officer (Director-level)** — Required for Virtual Asset Service Providers; bears KYC + AML + transaction-retention liability.
- **Board / Designated Director** — Counter-signs SDF attestation and CERT-In annual compliance attestation; bears personal liability under Section 70B(7) of the IT Act for material non-compliance.

## 8. Authoritative guidance

- CERT-In Directions No. 20(3)/2022-CERT-In (28 April 2022): https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf
- CERT-In Directions FAQ: https://www.cert-in.org.in/PDF/FAQ_CERT-In_Directions.pdf
- IT Act 2000 (consolidated): https://www.meity.gov.in/writereaddata/files/itact2000/itbill2000.pdf
- IT Rules (Reasonable Security Practices for SPDI) 2011: https://www.meity.gov.in/writereaddata/files/GSR313E_10511(1)_0.pdf
- Digital Personal Data Protection Act 2023: https://www.meity.gov.in/writereaddata/files/Digital%20Personal%20Data%20Protection%20Act%202023.pdf
- DPDP Rules (notified 2024-2026): https://www.meity.gov.in/data-protection-framework
- RBI Master Direction — Information Technology Governance (2023): https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12549
- SEBI Cybersecurity and Cyber Resilience Framework (CSCRF, 2024): https://www.sebi.gov.in/legal/circulars/aug-2024/cybersecurity-and-cyber-resilience-framework-cscrf-for-sebi-regulated-entities-res-_85964.html
- IRDAI Information & Cybersecurity Guidelines (2023): https://www.irdai.gov.in/

## 9. Common audit deficiencies

1. **6-hour clock fired late** — Most-cited CERT-In finding; classification-as-reportable is deferred while the team investigates. Mitigated by UC-22.62.1.
2. **NTP source non-traceable** — Hosts default to public NTP pools (pool.ntp.org) instead of NIC/NPL. Mitigated by UC-22.62.2.
3. **POC change without 7-day notification** — HR onboards/offboards the POC role without CERT-In notification. Mitigated by UC-22.62.3.
4. **Log retention < 180 days** — Indexes sized for cost not for regulatory retention. Mitigated by UC-22.62.4.
5. **Cross-border log storage** — Logs persisted to non-Indian regions of public cloud providers without an India region designation. Mitigated by UC-22.62.4.
6. **VPN subscriber KYC incomplete** — VPN providers often capture only name + email; the 7-limb KYC is rare. Mitigated by UC-22.62.5.
7. **VASP transaction records missing** — Crypto-exchange transaction-record retention is frequently incomplete; the 5-year retention is rarely enforced internally. Mitigated by UC-22.62.6.
8. **SDF DPO not India-resident** — SDFs frequently appoint a parent-company DPO offshore. Mitigated by UC-22.62.7.
9. **DPDP 72-hour clock missed** — DPDP breach notification overlaps but does not align with the CERT-In 6-hour clock; teams report once and forget the parallel clock. Mitigated by UC-22.62.8.

## 10. Enforcement and penalties

- **CERT-In Directions** — non-compliance is punishable under IT Act Section 70B(7) by imprisonment up to 1 year or a fine up to INR 100,000 or both. Sectoral regulators (RBI, SEBI, IRDAI, TRAI) impose parallel administrative penalties on their regulated entities for material non-compliance.
- **IT Act Section 43A** — civil compensation to affected Data Principals where reasonable security practices have been wilfully or negligently not followed; no statutory cap on compensation.
- **DPDP Act** — administrative penalties up to INR 250 crore (~ USD 30 million) per breach class under DPDP Schedule (failure to take reasonable security safeguards); senior-management personal liability for SDFs.
- **PMLA (for VASPs)** — fine up to INR 1 crore + imprisonment up to 7 years for serious offences.
- **Sectoral overlays** — RBI Cyber Security Framework / SEBI CSCRF / IRDAI Info-Sec Guidelines impose additional penalties on regulated entities.

## 11. Questions a CERT-In / DPB-India inspector should ask

- Show me the most recent CERT-In incident submission and the timestamps from notice to submission. Was the 6-hour clock met?
- Pick a random ICT host — demonstrate the NTP source is NIC/NPL-traceable and the last-sync drift is within tolerance.
- Show me the current POC designation and the synthetic contactability test from this quarter.
- Pick a random sourcetype — demonstrate at least 180 days rolling retention in an Indian-jurisdiction index.
- For a VPN/VPS/cloud customer — demonstrate the seven KYC limbs and the 5-year retention attestation.
- For a VASP customer — demonstrate the KYC limbs and the 5-year transaction-record retention.
- If you are an SDF — demonstrate the India-resident DPO, the most recent DPIA, and the most recent annual independent audit.
- Walk me through the most recent DPDP 72-hour breach notification to the Data Protection Board of India.

## 12. Machine-readable twin

- API endpoint: `api/v1/compliance/story/cert-in.json`
- Raw clause data: `data/regulations.json` (id=`cert-in`)
- Per-UC sidecar files: `content/cat-22-regulatory-compliance/UC-22.62.*.json`
- Coverage methodology: `docs/coverage-methodology.md`

## 13. Provenance and regeneration

This evidence pack is regenerated as part of the catalogue build. Manual narrative sections (purpose, scope, common deficiencies, inspector questions) are authored; clause coverage tables are computed from UC sidecar `compliance[]` arrays. Last reviewed: 2026-05-14.
