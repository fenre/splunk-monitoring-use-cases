# Splunk Use Cases — HIPAA Security compliance

App ID: `splunk-uc-hipaa-security`  
App version: **6.1.0**  
Generated: `2026-04-18T17:28:10Z`  
Upstream catalogue: [fenre/splunk-monitoring-use-cases](https://github.com/fenre/splunk-monitoring-use-cases)


This app packages **76 use cases** from the upstream catalogue that cite HIPAA Security Rule (`hipaa-security`), together with the macros, eventtypes, tags, and lookup needed to operate them.  Every saved search is shipped **disabled by default** so an operator can review the SPL and tune indexes before enabling.

* Regulation tier: **1**
* Jurisdictions: US
* Versions covered: 2013-final
* UCs by criticality: critical = 36, high = 36, medium = 4


## Most-referenced clauses

| Clause | UCs tagging this clause |
|--------|-------------------------|
| `§164.312(e)(1)` | 8 |
| `§164.308(a)(1)` | 4 |
| `§164.308(a)(5)` | 4 |
| `§164.312(b)` | 4 |
| `§164.312(c)(1)` | 4 |
| `§164.502(b)` | 4 |
| `§164.502(e)` | 4 |
| `§164.310(d)(1)` | 3 |

## Installation

1. **Review the SPL.**  Every saved search under `default/savedsearches.conf` ships disabled.  Before enabling, replace placeholder `index=` patterns with your site's indexes and macros.
2. **Install.**  Copy this directory into `$SPLUNK_HOME/etc/apps/` or package it with `tar czf splunk-uc-hipaa-security.spl splunk-uc-hipaa-security/` and deploy via the Splunk app manager.
3. **Open the compliance posture dashboard.**  The navigation lands on `hipaa_security_compliance_posture` — a Simple XML dashboard that reads the shipped `uc_compliance_mappings` lookup and works before any saved search is scheduled.  Use it to brief auditors, track clause coverage, and spot mappings with thin assurance.
4. **Enable selectively.**  In *Settings → Searches, reports, and alerts*, enable and schedule the stanzas your team is ready to operate.
5. **Audit trail.**  Every saved search carries the UC id, the regulation version, and the full clause list on its `action.uc_compliance.param.*` attributes.  These are auditor-friendly and survive Splunk's saved-search lifecycle (no lookup required).


## Compliance posture dashboard

The app ships a Simple XML dashboard at `default/data/ui/views/hipaa_security_compliance_posture.xml` that reads the per-app `uc_compliance_mappings` lookup.  The dashboard needs zero saved searches to render — install the app, open the dashboard, brief your auditor.

Panels:

1. **Total UCs packaged** — single value.
2. **Critical-tier UCs** — single value, review-first cohort.
3. **Distinct clauses tagged** — single value.
4. **UCs by criticality** — column chart.
5. **Most-referenced clauses (top 15)** — bar chart.
6. **Mappings by assurance bucket** — column chart (full / partial / contributing / unspecified).
7. **UC inventory** — full catalogue table with source-path references back to the upstream catalogue.


## AppInspect / Splunk Cloud readiness

The generator targets AppInspect's baseline checks:

* `app.manifest` version 2.0.0 with the full `info` block.
* `default/app.conf` carries `[install]`, `[ui]`, `[launcher]`, and `[package]` sections.
* `metadata/default.meta` keeps `savedsearches` private, exports macros / eventtypes / tags / transforms / lookups at `system` scope, and the generated dashboard at `app` scope.
* The posture dashboard uses Simple XML 1.1 with CDATA-wrapped queries that rely exclusively on `inputlookup` — no external data, no custom visualisations, no scripted inputs.
* No custom search commands or `local/` overrides are shipped.
* MIT licence file committed at the app root.

The per-regulation app still depends on your site's CIM / Enterprise Security installation for `\`notable\`` and `\`summariesonly\`` macros when saved searches are enabled; see the upstream `scripts/audit_splunk_cloud_compat.py` report.


## Covered use cases

| UC | Title | Criticality | Clauses |
|----|-------|-------------|---------|
| UC-22.6.53 | ISO/IEC 27001:2022 Clause 7.2 — Competence evidence: role-based training completion | medium | §164.308(a)(5) |
| UC-22.8.31 | SOC 2 CC6.6 — Encryption-in-transit validation: cleartext protocols crossing the trust boundary | high | §164.312(e)(1) |
| UC-22.8.38 | SOC 2 C1.1 — Confidentiality: sensitive-data exposure at the egress boundary | high | §164.312(e)(1) |
| UC-22.10.1 | HIPAA Risk Analysis Evidence — Asset & ePHI System Inventory | critical | §164.308(a)(1) |
| UC-22.10.2 | HIPAA Risk Management — Control Deficiency Tracking | critical | §164.308(a)(1) |
| UC-22.10.3 | Information System Activity Review — Cross-Source ePHI Access Summary | critical | §164.308(a)(1)(ii)(D) |
| UC-22.10.4 | Workforce Clearance — HR Hire vs AD Account Creation | high | §164.308(a)(3) |
| UC-22.10.5 | Termination — Access Revocation Within Policy Window | critical | §164.308(a)(3)(ii)(C) |
| UC-22.10.6 | Security Awareness & Training — Phish Simulation Failure to ePHI Risk | high | §164.308(a)(5) |
| UC-22.10.7 | Login Monitoring & Security Incident Procedures — Brute Force to Clinical SSO | critical | §164.308(a)(6) |
| UC-22.10.8 | Contingency Plan — Backup Job Success for ePHI Databases | critical | §164.308(a)(7) |
| UC-22.10.9 | Periodic Evaluation — Control Test Evidence Ingest | high | §164.308(a)(8) |
| UC-22.10.10 | Business Associate Contracts — BAA Coverage for Connected Systems | high | §164.308(a)(1)(ii)(B) |
| UC-22.10.11 | Business Associate Agreements — Expiry & Auto-Renewal Monitoring | high | §164.308(b)(1) |
| UC-22.10.12 | Sanction Policy — Privileged Abuse on EHR Audit Logs | critical | §164.308(a)(1)(ii)(C) |
| UC-22.10.13 | Unique User Identification — Shared or Generic EHR Accounts | critical | §164.312(a)(2)(i) |
| UC-22.10.14 | Emergency Access Procedure — Downtime / Break-Glass Account Usage | critical | §164.312(a)(2)(ii) |
| UC-22.10.15 | Automatic Logoff — Stale Clinical Workstation Sessions | high | §164.312(a)(2)(iii) |
| UC-22.10.16 | Encryption of ePHI at Rest — TDE / BitLocker Status for Clinical Datastores | critical | §164.312(a)(2)(iv) |
| UC-22.10.17 | Audit Controls — High-Volume ePHI Read Baseline & Anomaly | critical | §164.312(b) |
| UC-22.10.18 | Integrity — Unexpected UPDATE/DELETE on PHI Tables (Clarity/Caboodle) | critical | §164.312(c)(1) |
| UC-22.10.19 | Entity Authentication — Smart Card / Certificate Logon Failures | high | §164.312(d) |
| UC-22.10.20 | Transmission Security — TLS 1.0/1.1 Deprecation for EHR Integrations | high | §164.312(e)(1) |
| UC-22.10.21 | Access Control — Role-Based Violations (Coder Accessing Medication Admin) | critical | §164.308(a)(4), §164.312(a)(1) |
| UC-22.10.22 | Remote ePHI Access — MFA Gap for VPN + O365 Clinical Mail | critical | §164.308(a)(1), §164.312(e)(1) |
| UC-22.10.23 | FHIR / SMART on FHIR App Access to ePHI Scopes | high | §164.312(d) |
| UC-22.10.24 | Medical Device Integration — Unapproved HL7 Feeds to EMPI | high | §164.312(a)(1) |
| UC-22.10.25 | Endpoint Controls — ePHI Clipboard/Print from VDI | high | §164.312(a)(1) |
| UC-22.10.26 | Transmission Security — Unencrypted SMTP with PHI Patterns | critical | §164.312(e)(1) |
| UC-22.10.27 | Integrity — Caboodle / Clarity ETL Job Failures & Partial Loads | high | §164.312(c)(1) |
| UC-22.10.28 | Workstation Security — Unattended Unlocked Sessions in Clinical Pods | high | §164.310(b) |
| UC-22.10.29 | Device & Media Controls — USB Mass Storage on ePHI Workstations | critical | §164.310(d)(1) |
| UC-22.10.30 | Media Controls — Large PHI Print Jobs to Non-Secure Printers | high | §164.310(d)(2) |
| UC-22.10.31 | Facility vs Logical Access — Badge-In Without VPN/SSO for Remote Roles | high | §164.310(a)(1) |
| UC-22.10.32 | Workstation Use — After-Hours Login from Non-Clinical IP Space | high | §164.310(b), §164.310(c) |
| UC-22.10.33 | Minimum Necessary — Access Outside Active Care Team | critical | §164.502(b), §164.514(d) |
| UC-22.10.34 | Break-Glass — Emergency Access Reason Codes & Post-Review | critical | §164.502(a)(2)(ii) |
| UC-22.10.35 | Non-Treating Provider — Specialty Mismatch Chart Access | high | §164.502(a)(1) |
| UC-22.10.36 | Bulk ePHI Export — Clarity SQL / Caboodle Extract Volume Spike | critical | §164.312(b), §164.502(b) |
| UC-22.10.37 | After-Hours ePHI Access — Billing Users on Inpatient Charts | high | §164.502(b) |
| UC-22.10.38 | Deceased Patient Records — Access After Death Date | high | §164.502(f) |
| UC-22.10.39 | VIP / High-Profile Patient — Elevated Access Monitoring | critical | §164.502(a) |
| UC-22.10.40 | Research Access — Chart Views Without Active IRB Consent Flag | critical | §164.502(a)(1), §164.512(i) |
| UC-22.10.41 | Accounting of Disclosures — Registry vs EHR-Logged Disclosures | high | §164.528 |
| UC-22.10.42 | Patient Portal — Suspicious MyChart Password Reset & MFA Changes | critical | §164.312(d), §164.530(c) |
| UC-22.10.43 | Breach Discovery — Time-to-Detect from First PHI Indicator | critical | §164.404 |
| UC-22.10.44 | Breach Risk Assessment — Four-Factor Documentation Tracking | critical | §164.402, §164.404 |
| UC-22.10.45 | Individual Notification — Letter Generation & Mailing Evidence | critical | §164.404(b) |
| UC-22.10.46 | HHS Secretary Notification — 500+ Individuals Threshold Watch | critical | §164.408 |
| UC-22.10.47 | Media Notification — Large-State Resident Threshold Tracking | critical | §164.406(c) |
| UC-22.10.48 | Breach Log / Incident Register — Immutable Chronological Record | high | §164.402 |
| UC-22.10.49 | Breach Remediation — Control Implementation Evidence Post-Incident | high | §164.308(a)(1)(ii)(A) |
| UC-22.10.50 | Annual Breach Reporting — Trend of Affected Individuals & Root Cause | high | §164.408 |
| UC-22.10.51 | Business Associate Access — VPN/SSO Sessions Originating from BA Address Space | high | §164.308(b), §164.502(e) |
| UC-22.10.52 | BAA Compliance Evidence — Control Attestations vs Technical Telemetry | high | §164.308(b)(3), §164.502(e) |
| UC-22.10.53 | Subcontractor Access — Downstream API Keys Touching ePHI Interfaces | critical | §164.502(e) |
| UC-22.10.54 | Third-Party Data Sharing — O365 Sharing Links to External Domains on PHI Libraries | critical | §164.502(b), §164.514(e) |
| UC-22.10.55 | Cloud Service Provider — ePHI Hosting Admin Actions in AWS or Azure Audit | critical | §164.308(a)(1), §164.502(e) |
| UC-22.35.1 | Audit-log continuity: detect indexing gap indicating lost evidence | critical | §164.312(b) |
| UC-22.35.2 | Log tamper detection via write-once-read-many chain-of-custody | critical | §164.312(c)(1) |
| UC-22.35.4 | Log signing chain integrity — cryptographic signature drift on evidence archive | critical | §164.312(c)(1) |
| UC-22.35.5 | Search-head audit-trail completeness — deleted or rewritten search jobs | high | §164.312(b) |
| UC-22.39.1 | Multi-regulator breach-notification SLA tracker (24h NIS2 / 72h GDPR / 72h HIPAA) | critical | §164.308(a)(6) |
| UC-22.39.3 | Data-subject breach communication timeline tracker (Art.34 / §164.404) | high | §164.404 |
| UC-22.41.1 | Encryption-at-rest coverage gap — unencrypted storage with regulated data | critical | §164.312(a)(2)(iv) |
| UC-22.41.2 | Certificate / TLS posture — weak cipher and expired-cert detection | high | §164.312(e)(1) |
| UC-22.41.4 | TLS downgrade / legacy-cipher handshake spike | high | §164.312(e)(1) |
| UC-22.45.2 | Backup encryption and air-gap integrity — tamper detection on immutable storage | critical | §164.308(a)(7) |
| UC-22.45.4 | Backup repository TLS posture — aged or weak-cipher endpoints | medium | §164.312(e)(1) |
| UC-22.46.1 | Mandatory security training — completion SLA by role | medium | §164.308(a)(5) |
| UC-22.46.3 | Privileged-role specialist training — admins lacking annual deep-training | medium | §164.308(a)(5)(ii)(A) |
| UC-22.46.5 | Developer data-handling training — prod-access engineers lacking training | high | §164.308(a)(5) |
| UC-22.49.1 | Retention execution evidence — records past retention still present | high | §164.310(d)(1) |
| UC-22.49.2 | Disposal workflow completion — failed disposals requiring manual review | high | §164.310(d)(1) |
| UC-22.49.4 | Retention policy drift — system config vs policy catalogue | high | §164.316(b)(2) |
| UC-22.49.5 | Cryptographic erasure attestation — per-asset destruction evidence | high | §164.310(d)(2)(i) |

---

_This app is generated; edits in place will be overwritten.  File bug reports and content requests at https://github.com/fenre/splunk-monitoring-use-cases/issues._
