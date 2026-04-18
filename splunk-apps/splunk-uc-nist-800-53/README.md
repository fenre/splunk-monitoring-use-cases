# Splunk Use Cases — NIST 800-53 compliance

App ID: `splunk-uc-nist-800-53`  
App version: **6.1.0**  
Generated: `2026-04-18T08:01:30Z`  
Upstream catalogue: [fenre/splunk-monitoring-use-cases](https://github.com/fenre/splunk-monitoring-use-cases)


This app packages **138 use cases** from the upstream catalogue that cite NIST SP 800-53 Rev. 5 (`nist-800-53`), together with the macros, eventtypes, tags, and lookup needed to operate them.  Every saved search is shipped **disabled by default** so an operator can review the SPL and tune indexes before enabling.

* Regulation tier: **1**
* Jurisdictions: US
* Versions covered: Rev. 5
* UCs by criticality: critical = 43, high = 76, medium = 18, unspecified = 1


## Most-referenced clauses

| Clause | UCs tagging this clause |
|--------|-------------------------|
| `RA-5` | 6 |
| `CM-3` | 4 |
| `CM-6` | 4 |
| `CP-9` | 4 |
| `AC-6` | 3 |
| `CA-2` | 3 |
| `CA-7` | 3 |
| `IA-2` | 3 |

## Installation

1. **Review the SPL.**  Every saved search under `default/savedsearches.conf` ships disabled.  Before enabling, replace placeholder `index=` patterns with your site's indexes and macros.
2. **Install.**  Copy this directory into `$SPLUNK_HOME/etc/apps/` or package it with `tar czf splunk-uc-nist-800-53.spl splunk-uc-nist-800-53/` and deploy via the Splunk app manager.
3. **Open the compliance posture dashboard.**  The navigation lands on `nist_800_53_compliance_posture` — a Simple XML dashboard that reads the shipped `uc_compliance_mappings` lookup and works before any saved search is scheduled.  Use it to brief auditors, track clause coverage, and spot mappings with thin assurance.
4. **Enable selectively.**  In *Settings → Searches, reports, and alerts*, enable and schedule the stanzas your team is ready to operate.
5. **Audit trail.**  Every saved search carries the UC id, the regulation version, and the full clause list on its `action.uc_compliance.param.*` attributes.  These are auditor-friendly and survive Splunk's saved-search lifecycle (no lookup required).


## Compliance posture dashboard

The app ships a Simple XML dashboard at `default/data/ui/views/nist_800_53_compliance_posture.xml` that reads the per-app `uc_compliance_mappings` lookup.  The dashboard needs zero saved searches to render — install the app, open the dashboard, brief your auditor.

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
| UC-9.1.3 | Privileged Group Membership Changes |  | AC-2(7) |
| UC-22.1.48 | GDPR Purpose Limitation Enforcement Across Systems | high | PT-3 |
| UC-22.3.41 | DORA Art.6 — ICT risk-management framework evidence: control catalogue drift detection | high | PM-9 |
| UC-22.3.43 | DORA Art.8 — ICT risk identification: newly discovered high-severity exposure on critical financial services | critical | RA-5 |
| UC-22.3.45 | DORA Art.24 — Digital operational-resilience testing: test-plan execution attestation | high | CA-8 |
| UC-22.6.46 | ISO/IEC 27001:2022 Clause 6.1 — Risk-assessment evidence: live risk register decay | high | PM-9 |
| UC-22.6.47 | ISO/IEC 27001:2022 Clause 6.2 — Information-security objectives: measurable-target attainment | medium | PM-6 |
| UC-22.6.48 | ISO/IEC 27001:2022 Clause 8.2 — Operational risk-assessment: per-change risk-score recalculation | high | RA-3 |
| UC-22.6.49 | ISO/IEC 27001:2022 Clause 9.1 — Monitoring programme coverage: KPI telemetry uptime | high | CA-7 |
| UC-22.6.50 | ISO/IEC 27001:2022 Clause 9.2 — Internal audit coverage: control sample rotation | medium | CA-2 |
| UC-22.6.51 | ISO/IEC 27001:2022 Annex A.5.24 — Incident-management planning: runbook currency attestation | medium | IR-4 |
| UC-22.6.52 | ISO/IEC 27001:2022 Annex A.5.25 — Event classification decisions: SIEM-to-incident triage traceability | high | IR-4 |
| UC-22.6.54 | ISO/IEC 27001:2022 Clause 7.5 — Documented information control: policy register approval trail | medium | PL-2 |
| UC-22.8.33 | SOC 2 CC7.1 — System-operations monitoring: uptime attestation and alert-noise governance | high | SI-4 |
| UC-22.10.5 | Termination — Access Revocation Within Policy Window | critical | PS-4 |
| UC-22.11.92 | PCI-DSS 2.2 — Secure configuration baseline: drift from approved hardening template | high | CM-6 |
| UC-22.11.94 | PCI-DSS 5.2 — Anti-malware: EDR coverage + detection-queue attestation | high | SI-3 |
| UC-22.11.96 | PCI-DSS 8.3 — Strong authentication: password-only logins against privileged accounts | critical | IA-2 |
| UC-22.11.97 | PCI-DSS 8.4 — MFA coverage: administrative access to CDE without MFA | critical | IA-2(1) |
| UC-22.11.98 | PCI-DSS 8.6 — Application and system accounts: interactive use of a service account | high | IA-2 |
| UC-22.11.100 | PCI-DSS 10.4 — Time synchronisation: NTP drift on CDE hosts | high | AU-8 |
| UC-22.11.102 | PCI-DSS 10.7 — Log retention: CDE data-source retention + immutability attestation | high | AU-11 |
| UC-22.11.103 | PCI-DSS 11.3 — Vulnerability programme: overdue scan cadence and unremediated high-severity | high | RA-5 |
| UC-22.14.1 | Centralized Audit Event Logging Policy Coverage | critical | AU-2 |
| UC-22.14.2 | Audit Record Content Completeness for Privileged Actions | critical | AU-3 |
| UC-22.14.3 | Audit Storage Capacity and Index Growth Guardrails | high | AU-4 |
| UC-22.14.4 | Response to Audit Logging Failures and Forwarder Gaps | critical | AU-5 |
| UC-22.14.5 | Audit Review, Analysis, and Reporting for Privileged Users | critical | AU-6 |
| UC-22.14.6 | Audit Reduction and Report Generation Integrity | high | AU-7 |
| UC-22.14.7 | Time Synchronization and Clock Skew for Audit Timestamps | high | AU-8 |
| UC-22.14.8 | Protection of Audit Information — Tamper Detection on Audit Indexes | critical | AU-9 |
| UC-22.14.9 | Non-Repudiation Evidence for Sensitive Transactions | high | AU-10 |
| UC-22.14.10 | Audit Record Retention Compliance vs Policy | high | AU-11 |
| UC-22.14.11 | Audit Generation Coverage for Critical Network Controls | critical | AU-12 |
| UC-22.14.12 | Monitoring for Information Disclosure via DLP and Web Exfil Patterns | high | AU-13 |
| UC-22.14.13 | Session Audit for Privileged Interactive Access | high | AU-14 |
| UC-22.14.14 | Alternate Audit Capability During Control Outages | high | AU-15 |
| UC-22.14.15 | Cross-Organizational Audit Forwarding Health to SIEM | high | AU-16 |
| UC-22.14.16 | Account Management — Orphan and Stale Privileged Accounts | critical | AC-2 |
| UC-22.14.17 | Access Enforcement — Unauthorized Access Attempts to Sensitive Shares | critical | AC-3 |
| UC-22.14.18 | Separation of Duties Violations in Change Tickets | high | AC-5 |
| UC-22.14.19 | Least Privilege — Excessive Cloud IAM Permissions | critical | AC-6 |
| UC-22.14.20 | Unsuccessful Logon Attempts and Account Lockout Patterns | high | AC-7 |
| UC-22.14.21 | System Use Notification Banner Acceptance in SSH Sessions | high | AC-8 |
| UC-22.14.22 | Session Lock Events for Workstation Inactivity Policy | high | AC-11 |
| UC-22.14.23 | Session Termination on Logoff and VPN Disconnect | high | AC-12 |
| UC-22.14.24 | Remote Access Anomalies — Geo-Velocity and Off-Hours VPN | critical | AC-17 |
| UC-22.14.25 | Use of External Systems — Unmanaged SaaS OAuth Grants | high | AC-20 |
| UC-22.14.26 | Multifactor Authentication Gaps for Interactive Sign-Ins | critical | IA-2 |
| UC-22.14.27 | Device Identification for Corporate-Managed Endpoints | high | IA-3 |
| UC-22.14.28 | Identifier Management — Non-Human Service Account Sprawl | high | IA-4 |
| UC-22.14.29 | Authenticator Management — Password Age and Rotation Anomalies | high | IA-5 |
| UC-22.14.30 | Authentication Feedback — Credential Stuffing via Login Failures | medium | IA-6 |
| UC-22.14.31 | Identification of Non-Organization Users in Collaboration Tools | high | IA-8 |
| UC-22.14.32 | Re-Authentication for Sensitive Application Roles | high | IA-11 |
| UC-22.14.33 | Identity Proofing Evidence for HR Onboarding Events | high | IA-12 |
| UC-22.14.34 | Flaw Remediation SLA Tracking from Vulnerability Scans | critical | SI-2 |
| UC-22.14.35 | Malicious Code Protection — EDR / AV Detections Volume and Gaps | critical | SI-3 |
| UC-22.14.36 | System Monitoring — Host Instrumentation Coverage vs Inventory | critical | SI-4 |
| UC-22.14.37 | Security Alerts Ingestion Health from Vendor Feeds | high | SI-5 |
| UC-22.14.38 | Security Function Verification — Forwarder Config Change Auditing | high | SI-6 |
| UC-22.14.39 | Software and Firmware Integrity — Unexpected Driver Loads | critical | SI-7 |
| UC-22.14.40 | Information Input Validation — Web Parameter Anomalies | high | SI-10 |
| UC-22.14.41 | Error Handling — Application Stack Traces Exposing Internals | medium | SI-11 |
| UC-22.14.42 | Information Management — Sensitive Fields in Unapproved Indexes | high | SI-12 |
| UC-22.14.43 | Memory Protection Signals — Exploitation Primitives in EDR Telemetry | critical | SI-16 |
| UC-22.14.44 | Incident Response Training Completion Tracking | medium | IR-2 |
| UC-22.14.45 | Incident Handling Stage Timestamps from Case Management | critical | IR-4 |
| UC-22.14.46 | Incident Monitoring — SOC Queue Depth and Severity Mix | high | IR-5 |
| UC-22.14.47 | Incident Reporting to Authorities — Regulatory Timer Watch | critical | IR-6 |
| UC-22.14.48 | Incident Response Assistance — External IR Firm Access Auditing | high | IR-7 |
| UC-22.14.49 | Incident Response Plan Test Evidence from Scheduled Tabletop Tags | medium | IR-8 |
| UC-22.14.50 | Information Spillage — DLP High-Severity Exfil Indicators | critical | IR-9 |
| UC-22.14.51 | Integrated Information Security Analysis Team Handoffs | high | IR-10 |
| UC-22.14.52 | Baseline Configuration Drift vs Gold Build | high | CM-2 |
| UC-22.14.53 | Configuration Change Control — Unauthorized Firewall Rule Adds | critical | CM-3 |
| UC-22.14.54 | Security Impact Analysis Signals for Emergency Changes | high | CM-4 |
| UC-22.14.55 | Access Restrictions for Change — Privileged Route Changes | high | CM-5 |
| UC-22.14.56 | Configuration Settings Compliance — CIS Benchmark Control Checks | high | CM-6 |
| UC-22.14.57 | Least Functionality — Unexpected Listening Ports | high | CM-7 |
| UC-22.14.58 | System Component Inventory vs Observed Network Assets | high | CM-8 |
| UC-22.14.59 | User-Installed Software Detections on Corporate Images | medium | CM-11 |
| UC-22.14.60 | Control Assessment Findings Ingest and Aging | high | CA-2 |
| UC-22.14.61 | Information Exchange Agreements — Data Share Volume Anomalies | high | CA-3 |
| UC-22.14.62 | Plan of Action and Milestones Open Items Past Due | high | CA-5 |
| UC-22.14.63 | Continuous Monitoring Control Health Scores | critical | CA-7 |
| UC-22.14.64 | Penetration Test Windows and Detected Activities | high | CA-8 |
| UC-22.14.65 | Internal System Connections — East-West New Service Relationships | high | CA-9 |
| UC-22.14.66 | Residual Information in Shared Cloud Object Stores | high | SC-4 |
| UC-22.14.67 | Boundary Protection — Firewall Deny Burst to Sensitive Segments | critical | SC-7 |
| UC-22.14.68 | Transmission Confidentiality and Integrity — TLS Policy Downgrades | critical | SC-8 |
| UC-22.14.69 | Network Disconnect for Inactive Sessions on Admin Services | high | SC-10 |
| UC-22.14.70 | Cryptographic Key Management Events from Cloud KMS | critical | SC-12 |
| UC-22.14.71 | Cryptographic Protection — BitLocker or Disk Encryption Status Drops | high | SC-13 |
| UC-22.14.72 | Session Authenticity — Token Replay Across Geographies | critical | SC-23 |
| UC-22.14.73 | Protection of Information at Rest — Storage Encryption Misconfigurations | critical | SC-28 |
| UC-22.14.74 | Risk Assessment Inputs — Control Deficiency Hotspots | high | RA-3 |
| UC-22.14.75 | Vulnerability Monitoring — Exploitable in the Wild Prioritization | critical | RA-5 |
| UC-22.14.76 | Risk Response Effectiveness After Control Changes | medium | RA-7 |
| UC-22.14.77 | Threat Hunting Outcomes Logged for Repeatable Hunts | high | RA-10 |
| UC-22.14.78 | Contingency Plan Tabletop and Activation Logging | medium | CP-2 |
| UC-22.14.79 | System Backup Success and RPO Violations | critical | CP-9 |
| UC-22.14.80 | System Recovery Time Objective Tracking from DR Drills | critical | CP-10 |
| UC-22.35.3 | Indexer replication lag exposing evidence to single-point failure | high | AU-9 |
| UC-22.40.1 | Privileged session recording — missing recordings for elevated sessions | critical | AC-6 |
| UC-22.40.2 | Break-glass account usage review with mandatory post-use approval | critical | AC-6 |
| UC-22.40.3 | Periodic access review SLA — stale certifications by control owner | high | AC-2 |
| UC-22.40.4 | Standing-privilege credential vaulting drift — admin accounts outside PAM | critical | AC-5 |
| UC-22.40.5 | High-risk privileged-session command without JIT approval | critical | AC-6(9) |
| UC-22.41.1 | Encryption-at-rest coverage gap — unencrypted storage with regulated data | critical | SC-13 |
| UC-22.41.2 | Certificate / TLS posture — weak cipher and expired-cert detection | high | SC-8 |
| UC-22.41.3 | Key rotation attestation — KMS/HSM rotation SLA tracker | high | SC-13 |
| UC-22.41.4 | TLS downgrade / legacy-cipher handshake spike | high | SC-8 |
| UC-22.41.5 | Key custodian SoD — same identity creates AND approves a key | high | SC-12 |
| UC-22.42.1 | Unauthorized production change — no approved CR matches the observed change | critical | CM-3 |
| UC-22.42.2 | Configuration baseline drift — regulated hosts deviating from CIS benchmark | high | CM-2, CM-6 |
| UC-22.42.3 | Change rollback execution evidence — declared rollback vs actual | medium | CM-3 |
| UC-22.42.4 | CAB approval bypass — change pushed before scheduled window | high | CM-3 |
| UC-22.42.5 | Infrastructure-as-code drift — applied state diverges from merged plan | high | CM-6 |
| UC-22.43.1 | Critical vulnerability SLA tracker — unpatched 30+ days with exploited-in-the-wild indicator | critical | RA-5 |
| UC-22.43.2 | Vulnerability rediscovery after patch — regressed exposures | high | RA-5 |
| UC-22.43.3 | Internet-facing asset × unpatched critical CVE | critical | RA-5 |
| UC-22.43.4 | Scanner coverage gap — regulated hosts without a recent scan | high | RA-5(2) |
| UC-22.43.5 | SBOM vendor-component CVE exposure | high | SR-11 |
| UC-22.44.1 | Supplier attestation currency — stale SOC 2 / ISO 27001 reports for critical vendors | high | SR-3 |
| UC-22.44.4 | Vendor access telemetry — principals active outside contracted hours/geos | high | SR-6 |
| UC-22.44.5 | SBOM attestation completeness — critical vendors without signed SBOM | high | SR-11(1) |
| UC-22.45.1 | Backup restore test evidence — RPO/RTO SLA compliance per tier | critical | CP-9 |
| UC-22.45.2 | Backup encryption and air-gap integrity — tamper detection on immutable storage | critical | CP-9 |
| UC-22.45.3 | Backup completeness — unprotected workloads with regulated data | high | CP-9 |
| UC-22.45.4 | Backup repository TLS posture — aged or weak-cipher endpoints | medium | CP-9(3) |
| UC-22.45.5 | Business-continuity rehearsal evidence — BCP/DR exercise execution logged | medium | CP-4 |
| UC-22.46.3 | Privileged-role specialist training — admins lacking annual deep-training | medium | AT-3 |
| UC-22.46.4 | Tabletop rehearsal evidence — IR plan exercise frequency | medium | IR-3 |
| UC-22.47.1 | Control test freshness — evidence older than policy cadence | medium | PM-1 |
| UC-22.47.3 | Control owner attestation freshness | medium | CA-2 |
| UC-22.47.5 | Continuous control monitoring anomaly — failure-rate trending up | high | CA-7 |
| UC-22.49.5 | Cryptographic erasure attestation — per-asset destruction evidence | high | MP-6 |

---

_This app is generated; edits in place will be overwritten.  File bug reports and content requests at https://github.com/fenre/splunk-monitoring-use-cases/issues._
