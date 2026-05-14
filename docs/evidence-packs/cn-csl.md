# Evidence Pack — China CSL / DSL / PIPL / CII Regulations / MLPS 2.0

> **Tier**: Tier 1 &nbsp;·&nbsp; **Jurisdiction**: CN &nbsp;·&nbsp; **Version**: `2017-csl-with-2021-dsl-pipl-and-2022-ciio-cross-border`
>
> **Full name**: People's Republic of China Cybersecurity Law of 2017 (CSL), Data Security Law of 2021 (DSL), Personal Information Protection Law of 2021 (PIPL), Regulations on Security Protection of Critical Information Infrastructure (State Council Order 745, 2021), Cybersecurity Review Measures (2022 revision), Measures for Security Assessment of Cross-Border Data Transfers (CAC, September 2022), and the Multi-Level Protection Scheme 2.0 (MLPS 2.0 — GB/T 22239-2019 + GB/T 22240-2020).
> **Authoritative sources**: [Cyberspace Administration of China (CAC)](http://www.cac.gov.cn/) · [SAC / TC260 standards](http://www.tc260.org.cn/) · [Ministry of Public Security MLPS portal](https://www.mps.gov.cn/)
> **Effective from**: 2017-06-01 (CSL); 2021-09-01 (DSL); 2021-11-01 (PIPL); 2021-09-01 (CII Regulations); 2022-02-15 (CRM revision); 2022-09-01 (CAC Cross-Border Measures binding); 2020-12-01 (GB/T 22239-2019 MLPS 2.0 baseline)
>
> This evidence pack is the auditor-facing view of the Splunk monitoring catalogue's coverage of the consolidated PRC cybersecurity-and-data regime. Every clause coverage claim is traceable to a specific UC sidecar JSON file (`content/cat-22-regulatory-compliance/UC-22.61.*.json`); every retention figure cites its legal basis; every URL resolves to an official CAC, MPS, SAC/TC260, or NIA source. The pack does **not** assert legal conclusions — Chinese law, the CAC, the MPS Public Information Network Security Supervision (PINSS), and where applicable the National Intelligence Agency (NIA) under DSL Art.35 retain final interpretive authority. Interpretation stays with PRC counsel.

> **Live views.** [Buyer narrative (`compliance-story.html?reg=cn-csl`)](../../compliance-story.html?reg=cn-csl) · [Auditor clause navigator (`clause-navigator.html#reg=cn-csl`)](../../clause-navigator.html#reg=cn-csl) · [JSON twin (`api/v1/compliance/story/cn-csl.json`)](../../api/v1/compliance/story/cn-csl.json)

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
11. [Questions a CAC / MPS inspector should ask](#11-questions-a-cac--mps-inspector-should-ask)
12. [Machine-readable twin](#12-machine-readable-twin)
13. [Provenance and regeneration](#13-provenance-and-regeneration)

## 1. Purpose of this evidence pack

The People's Republic of China operates a layered, interlocking cybersecurity-and-data regime. The Cybersecurity Law of 2017 (CSL) is the foundation: it establishes the Multi-Level Protection Scheme (MLPS), grades network operators by their data-classification and impact tier, and imposes baseline cybersecurity duties. The Data Security Law of 2021 (DSL) adds a data-centric obligation layer focused on the lifecycle and classification of data — important data (重要数据), core data (核心数据), and ordinary data. The Personal Information Protection Law of 2021 (PIPL) is the personal-data limb, modelled on but distinct from GDPR, with a unique extraterritorial reach and explicit consent / impact-assessment / cross-border-transfer rules. Critical Information Infrastructure (CII) Regulations (State Council Order 745, 2021) tighten obligations for CII Operators (CIIOs) designated by sectoral regulators (Industry & IT Ministry, Cyberspace Administration of China, People's Bank, et al). The CAC Cybersecurity Review Measures (2022 revision) regulate procurement and IPO activity that may touch national security. The CAC Measures for Security Assessment of Cross-Border Data Transfers (2022) impose the most onerous data-export approval pipeline in any major jurisdiction. The Multi-Level Protection Scheme 2.0 (MLPS 2.0 — GB/T 22239-2019) operationalises CSL Art.21 via five grades; the most common operating grades are L2 (general business systems) and L3 (CIIO, large data processors, government-relevant systems).

The Splunk monitoring catalogue's coverage maps directly into this multi-document regime: the catalogue produces an auditable evidence chain that the Network Operator (or the CIIO, the Significant Data Processor under PIPL Art.58, or the Important-Data Handler under DSL Art.30) can hand to the CAC inspector, the MPS PINSS officer, the Industry & IT Ministry (MIIT) sectoral inspector, or — in core-data and national-security contexts — the National Intelligence Agency liaison.

## 2. Scope and applicability

Applies to:

- **Every network operator (网络运营者)** under CSL Art.21 — broadly any entity operating an information system in the PRC, regardless of nationality of the operating entity.
- **Every CIIO (关键信息基础设施运营者)** designated by a sectoral regulator under CII Regulations Art.10 — energy, finance, telecom, transport, water conservancy, public services, public health, e-government, national defence science & technology industry, and any other sector designated by State Council.
- **Every Important-Data Handler** under DSL Art.30 (operators handling data classified as "important data" — the catalogue tracks this via the data-classification register UC-22.61.6).
- **Every Personal Information Handler** under PIPL Art.4, with extraterritorial reach to non-PRC entities processing the personal information of PRC residents under PIPL Art.3(2).
- **Every Significant Personal Information Handler** under PIPL Art.58 — operators processing the personal information of more than one million natural persons.
- **Network products / services entering CIIO procurement or eyeing IPO with PRC nexus** — under CRM Art.7 (Cybersecurity Review Measures, 2022 revision).

Excludes: state-secret information systems handled under the Law on Guarding State Secrets (separate framework); pure military information systems under MOD-led regulation; offshore-only operations with no PRC residents whose personal-information processing is wholly outside scope of PIPL Art.3(2).

**Territorial scope.** The CSL governs in-country operations only. The DSL and PIPL each have an extraterritorial reach: DSL Art.2 applies to data activity outside the PRC that harms PRC national security or public interest; PIPL Art.3(2) reaches non-PRC entities processing PRC residents' personal information for the purpose of offering products / services or analysing behaviour. Cross-border data transfers out of the PRC are governed by the CAC Cross-Border Data Transfer Measures (2022) under one of three mechanisms: CAC security assessment, CAC-supervised standard contract, or PRC certification body certification.

## 3. Catalogue coverage at a glance

- **Clauses tracked**: 14 (CSL Art.21, Art.24, Art.27, Art.31; DSL Art.27, Art.29, Art.31, Art.32; PIPL Art.38, Art.55, Art.56, Art.58; CIIO Art.10, Art.17, Art.20; MLPS-2-0-L3, MLPS-2-0-annual)
- **Clauses covered by at least one UC**: 14 / 14 (100.0%)
- **Priority-weighted coverage**: 100.0%
- **Contributing UCs**: 12 (UC-22.61.1 through UC-22.61.12)

Coverage methodology is documented in [`docs/coverage-methodology.md`](../coverage-methodology.md). Priority weights come from `data/regulations.json` commonClauses entries.

## 4. Clause-by-clause coverage

Clauses are listed in the order defined by `data/regulations.json commonClauses` for this regulation version. A clause is considered covered when at least one UC sidecar has a `compliance[]` entry matching `(regulation, version, clause)`. Assurance is the maximum across contributing UCs.

| Clause | Topic | Priority | Assurance | UCs |
|---|---|---|---|---|
| `CSL-Art-21` | Tiered Multi-Level Protection of network operations (MLPS basis) | 1.0 | `full` | UC-22.61.1, UC-22.61.11, UC-22.61.12 |
| `CSL-Art-24` | Network operator real-name registration of users | 1.0 | `full` | UC-22.61.2 |
| `CSL-Art-27` | Prohibited cyber-attack-assistance behaviours | 1.0 | `full` | UC-22.61.3 |
| `CSL-Art-31` | CIIO security protection obligations | 1.0 | `full` | UC-22.61.1, UC-22.61.11 |
| `DSL-Art-27` | Data security management system + responsible person | 1.0 | `full` | UC-22.61.6, UC-22.61.7 |
| `DSL-Art-29` | Data security incident emergency response + reporting | 1.0 | `full` | UC-22.61.10, UC-22.61.12 |
| `DSL-Art-31` | Important-data cross-border transfer regulation | 1.0 | `full` | UC-22.61.5 |
| `DSL-Art-32` | Important-data export blocking under foreign-state demand | 1.0 | `full` | UC-22.61.4 |
| `PIPL-Art-38` | Cross-border transfer of personal information | 1.0 | `full` | UC-22.61.5 |
| `PIPL-Art-55` | Personal Information Protection Impact Assessment (PIPIA) | 1.0 | `full` | UC-22.61.8 |
| `PIPL-Art-56` | PIPIA scope — sensitive PI, ADM, cross-border, etc. | 1.0 | `full` | UC-22.61.8, UC-22.61.9 |
| `PIPL-Art-58` | Significant Personal Information Handler obligations | 1.0 | `full` | UC-22.61.8 |
| `CIIO-Reg-Art-10` | CIIO designation and reporting | 1.0 | `full` | UC-22.61.1 |
| `CIIO-Reg-Art-17` | CIIO annual cybersecurity risk assessment | 1.0 | `full` | UC-22.61.11 |
| `CIIO-Reg-Art-20` | CIIO procurement / Cybersecurity Review trigger | 1.0 | `full` | UC-22.61.7 |
| `MLPS-2-0-L3` | MLPS 2.0 Grade 3+ baseline + annual independent assessment | 1.0 | `full` | UC-22.61.11, UC-22.61.12 |
| `MLPS-2-0-annual` | MLPS annual filing + grading review with PINSS | 1.0 | `full` | UC-22.61.11 |

## 5. Evidence collection

### 5.1 Common evidence sources

- **MLPS Filing Register** — KV Store `cn_mlps_register_lookup`. Per-system grade, filing date, certificate number, annual-assessment status.
- **MLPS Findings Register** — KV Store `cn_mlps_findings_lookup`. Open MLPS-graded findings with remediation tracking.
- **MPS Accredited Assessor Catalogue** — KV Store `cn_mps_accredited_assessors_lookup`. Refreshed from MPS PINSS website.
- **CIIO Designation Register** — KV Store `cn_ciio_designation_lookup`. Sectoral-regulator designation letters, sector ID, reporting cadence.
- **Real-Name Registration Register** — KV Store `cn_csl_realname_register_lookup`. CSL Art.24 limb evidence per service.
- **Data-Classification Register** — KV Store `cn_data_classification_lookup`. Important / core / ordinary categorisation with handler responsible-person.
- **Cross-Border Data Transfer Approval Register** — KV Store `cn_cbdt_approval_lookup`. Per-transfer mechanism (CAC assessment / standard contract / certification), expiry, approval reference number.
- **Blocking-Statute Register** — KV Store `cn_blocking_statute_request_lookup`. Tracks every foreign-state data demand received and the legal-review chain.
- **PIPIA Register** — KV Store `cn_pipia_register_lookup`. Per-PIA trigger, scope, completion, finding-closure.
- **ADM (Automated Decision-Making) Notice Register** — KV Store `cn_adm_notice_register_lookup`. PIPL Art.24 / Art.55(2) transparency limb.
- **CSL/DSL Log Retention attestations** — KV Store `cn_csl_log_retention_lookup`. Per-source 6-month retention attestation + integrity-protection mode.
- **Splunk internal retention configuration** — `_internal`, `_audit` indexes; REST API `/services/data/indexes`; `index=_internal source=*splunkd.log component=BucketMover`.
- **Custom HEC integrity-hash freshness** — `hec:integrity:hash:freshness`. Source-aware Merkle-tree freshness for tamper-evidence per CSL Art.21(3).
- **Incident-tracker (ServiceNow SIR)** — `snow:sir` events; classification status; 8-hour and 24-hour clock fields.
- **Bug-bounty + threat-intel ingest** — for CSL Art.27 (prohibited cyber-attack-assistance behaviours) monitoring.

### 5.2 Retention requirements

| Artifact | Retention | Legal basis |
|---|---|---|
| Network operations log (Article 21(3) network log) | Minimum 6 months rolling | CSL Art.21(3) |
| MLPS filing certificate + grading review report | Lifetime of system + 3 years | GB/T 22239-2019; MPS Order 43 |
| MLPS annual independent assessment report (L3+) | Minimum 5 years | GB/T 22239-2019 §8.1 + Cybersecurity Review Measures Art.4 |
| Data-security incident response report (DSL Art.29) | Minimum 5 years | DSL Art.29; CAC Notice on Data Security Incident Reporting (2024) |
| Cross-border data transfer assessment file (CAC) | Minimum 3 years after approval expiry | CAC Cross-Border Measures Art.13 (2022) |
| Standard-contract filing record (CAC SCC) | Minimum 3 years after contract expiry | CAC SCC Measures Art.7 (2023) |
| PIPIA report (PIPL Art.55) | Minimum 3 years | PIPL Art.56 |
| Real-name registration record (CSL Art.24) | Duration of account + 6 months minimum | CSL Art.24; CAC Account Information Real-Name Provisions |
| Important-data handler responsible-person filing | Lifetime of designation + 3 years | DSL Art.27 + sectoral implementing rules |
| CIIO procurement-review filing (CRM Art.7) | Lifetime of contract + 5 years | Cybersecurity Review Measures Art.10 (2022) |
| ADM transparency-notice record (PIPL Art.24) | Lifetime of ADM service + 3 years | PIPL Art.24, Art.55(2) |
| Audit-evidence summary index (catalogue archive) | Daily snapshot, 7-year rolling | Internal evidence-of-compliance governance |

> Retention figures above are minimums or regulator-stated expectations. State-secret data is governed separately by the Law on Guarding State Secrets and has its own retention regime. Cross-border data transfer files for "important data" or for processing >1M individuals' personal information typically have longer effective retention via CAC re-assessment cadence (every 2 years if the approval would otherwise expire and the transfer is ongoing).

### 5.3 Evidence integrity expectations

All CAC / MPS / sectoral-regulator evidence must be tamper-evident. The Splunk catalogue archives every UC-22.61.x result row to the `audit_evidence` summary index with a stable marker (`uc=22.61.X,reg=CSL,clause=...`). Recommended pattern: source-aware Merkle-tree hashing via the custom HEC endpoint `hec:integrity:hash:freshness` (CSL Art.21(3) tamper-evidence limb), plus ServiceNow GRC immutable-audit-log mode for the manual narrative. Records that touch personal information should be encrypted at rest with PRC-approved cryptography (SM4 / SM2 / SM3 for state-relevant systems; AES-256 GCM acceptable for most commercial systems unless the CRM Art.7 cybersecurity review demands otherwise).

## 6. Control testing procedures

### 6.1 Inspector-style testing

A CAC / MPS PINSS / sectoral-regulator inspector typically tests:

- **MLPS grading currency** — pick a named L3+ system; demonstrate the current MLPS filing certificate, the most recent annual assessment, accredited-assessor credentials, and the open-finding remediation status (UC-22.61.11).
- **Network log retention** — pick a random sourcetype; demonstrate at least 6 months rolling retention plus integrity-hash freshness, in an index physically stored within the PRC (UC-22.61.12).
- **Real-name registration** — pick a service; demonstrate the registration check on the account at sign-up and the periodic re-verification (UC-22.61.2).
- **CSL Art.27 prohibited behaviour** — demonstrate the detection logic for offering / disseminating tools enabling cyber-attacks (UC-22.61.3).
- **Important-data export blocking** — synthetic foreign-state-style data demand; demonstrate the blocking-statute workflow with legal-review chain (UC-22.61.4).
- **Cross-border data transfer** — pick a named transfer; demonstrate the active mechanism (CAC assessment letter / standard-contract filing receipt / certification), the data-volume reconciliation, and the bi-annual review (UC-22.61.5).
- **Data classification** — pick a named system; demonstrate the data-class register with responsible-person and breach-impact attestation (UC-22.61.6).
- **CRM-relevant procurement** — pick a named procurement of network products / services touching CIIO scope; demonstrate the Cybersecurity Review Measures filing or the exemption rationale (UC-22.61.7).
- **PIPIA freshness** — pick a named ADM / cross-border / sensitive-PI / Significant-Handler trigger; demonstrate the corresponding PIPIA with current scope (UC-22.61.8).
- **ADM transparency** — pick a named ADM service; demonstrate the user-facing notice + opt-out + algorithmic-explainability (UC-22.61.9).
- **DSL Art.29 incident clock** — synthetic data-security incident; verify the 8-hour Significant-Incident report and the 24-hour Ordinary-Incident report to the relevant CAC / sectoral regulator (UC-22.61.10).

### 6.2 Internal compliance-officer testing

Quarterly self-test (Data Security Officer + DPO led):

1. Trigger a synthetic data-security incident in a dev environment matching UC-22.61.10.
2. Confirm the 8-hour Significant-Incident and 24-hour Ordinary-Incident clocks fire correctly.
3. Pause before submission and document the rehearsal in `audit_evidence` with `cac_exercise_id=Q...`.
4. Run UC-22.61.11 over the past 18 months to verify MLPS annual-assessment continuity.

## 7. Roles and responsibilities

- **Network Security Officer / Data Security Officer (网络安全负责人 / 数据安全负责人)** — Designated under CSL Art.21(2) and DSL Art.27; bears personal liability for the cybersecurity / data-security management system. PRC-resident required.
- **Personal Information Protection Officer (个人信息保护负责人)** — Required for Personal Information Handlers under PIPL Art.52, mandatory and named under PIPL Art.58 for Significant Personal Information Handlers (>1M individuals). PRC-resident required.
- **CIIO Security Director** — Required for CIIOs under CII Regulations Art.14; chairs the cybersecurity review for procurement of network products / services that may affect national security (CRM Art.7).
- **Legal Counsel (PRC-qualified)** — Owns the blocking-statute review under DSL Art.32 (and the parallel Anti-Foreign-Sanctions Law / Foreign Investment Information Reporting interface).
- **CAC liaison (designated)** — The single point of contact for the local CAC office; named on the MLPS filing, the CIIO designation, and the cross-border-transfer approval files.
- **Algorithmic Recommendation / ADM Officer** — Designated for ADM services under the Internet Information Service Algorithmic Recommendation Management Provisions (CAC, 2022); maintains the ADM filing register.
- **Board / General Manager** — Counter-signs MLPS L3+ annual attestation and the DSL Art.27 data-security management system.

## 8. Authoritative guidance

- Cyberspace Administration of China (CAC) — primary regulator portal: http://www.cac.gov.cn/
- Ministry of Public Security MLPS portal: https://www.mps.gov.cn/
- TC260 (SAC TC260) cybersecurity standards: http://www.tc260.org.cn/
- GB/T 22239-2019 — MLPS 2.0 baseline requirements: http://openstd.samr.gov.cn/bzgk/gb/newGbInfo?hcno=BAFB6A65EF26CF02EE5B5D7A57AE12A4
- GB/T 22240-2020 — MLPS 2.0 system classification guide: http://openstd.samr.gov.cn/
- CAC Measures for Security Assessment of Cross-Border Data Transfers (2022): http://www.cac.gov.cn/2022-07/07/c_1658811536396503.htm
- CAC Standard Contract for Cross-Border Transfer of Personal Information (2023): http://www.cac.gov.cn/2023-02/24/c_1678884830036813.htm
- CAC Cybersecurity Review Measures (2022 revision): http://www.cac.gov.cn/2021-12/28/c_1642023987080927.htm
- State Council Order 745 — Critical Information Infrastructure Regulations: http://www.gov.cn/zhengce/content/2021-08/17/content_5631671.htm
- CAC Internet Information Service Algorithmic Recommendation Management Provisions (2022): http://www.cac.gov.cn/2022-01/04/c_1642894606364259.htm

## 9. Common audit deficiencies

1. **MLPS L3+ annual assessment lapse** — Most-cited CAC / MPS inspection finding. Mitigated by UC-22.61.11.
2. **Network log <6 months** — Frequent retention misconfiguration where indexes are sized for IT-ops not regulatory retention. Mitigated by UC-22.61.12.
3. **Cross-border transfer without mechanism** — Operators frequently transfer data abroad without an active CAC assessment / standard contract / certification. Mitigated by UC-22.61.5.
4. **PIPIA missing for ADM / sensitive-PI / >1M individuals** — PIPIA gap is one of the highest-frequency PIPL findings. Mitigated by UC-22.61.8.
5. **ADM transparency notice missing** — Algorithmic Recommendation services lack the PIPL Art.24 user-facing notice + opt-out. Mitigated by UC-22.61.9.
6. **Important-data foreign demand not blocked** — Operators respond to foreign discovery demands without DSL Art.32 governmental approval. Mitigated by UC-22.61.4.
7. **CIIO designation not surfaced internally** — Operators receive a CIIO designation letter from a sectoral regulator and fail to operationalise CII Regulations Art.14-20 internally. Mitigated by UC-22.61.1.
8. **Data classification register stale** — Inadequate maintenance of important-data / core-data classification. Mitigated by UC-22.61.6.
9. **Real-name registration not periodically re-verified** — Initial registration captured but no periodic re-verification. Mitigated by UC-22.61.2.
10. **DSL Art.29 incident clock late** — Operators frequently classify incidents conservatively and miss the 8-hour Significant-Incident clock. Mitigated by UC-22.61.10.

## 10. Enforcement and penalties

- **CSL** — administrative fines up to RMB 1,000,000 (Art.59); senior-management personal liability up to RMB 100,000 (Art.59); business suspension; operating-license revocation; criminal referral for severe cases.
- **DSL** — administrative fines up to RMB 10,000,000 (Art.45); senior-management personal liability up to RMB 1,000,000; cessation of business; license revocation. Failures involving "core data" (Art.45) attract substantially heavier penalties.
- **PIPL** — administrative fines up to 5% of preceding-year revenue or RMB 50,000,000 (Art.66); senior-management personal liability up to RMB 1,000,000; cessation of business; license revocation; entry on the national credit-default blacklist.
- **CRM Art.10** — failure to undergo a required cybersecurity review attracts the higher of CSL / DSL / PIPL penalties depending on the underlying data-classification scope.
- **MLPS** — failure to file or to complete the L3+ annual assessment is enforced through PINSS via warning letter, escalated administrative fine, and (in extreme cases) network-service suspension.

## 11. Questions a CAC / MPS inspector should ask

- Show me the current MLPS filing certificate for every L3+ system, and the most recent annual assessment with the accredited-assessor credential.
- Pick a network-log sourcetype at random — demonstrate at least 6 months rolling retention and tamper-evidence within a PRC index.
- Show me the cross-border data transfer mechanism active for every named outbound personal-information flow, including the CAC approval reference or standard-contract filing receipt.
- Demonstrate that every Significant Personal Information Handler trigger (>1M individuals) has a current PIPIA and a PRC-resident PIPO.
- Walk me through a recent foreign-state data demand and the DSL Art.32 / blocking-statute legal-review chain.
- Pick a named ADM service — demonstrate the user-facing transparency notice + opt-out, and the algorithmic-recommendation filing with CAC.
- Demonstrate a recent CRM Art.7 procurement filing or the exemption rationale for procurement of network products / services touching CIIO scope.

## 12. Machine-readable twin

- API endpoint: `api/v1/compliance/story/cn-csl.json`
- Raw clause data: `data/regulations.json` (id=`cn-csl`)
- Per-UC sidecar files: `content/cat-22-regulatory-compliance/UC-22.61.*.json`
- Coverage methodology: `docs/coverage-methodology.md`

## 13. Provenance and regeneration

This evidence pack is regenerated as part of the catalogue build. Manual narrative sections (purpose, scope, common deficiencies, inspector questions) are authored; clause coverage tables are computed from UC sidecar `compliance[]` arrays. Last reviewed: 2026-05-14.
