# Splunk Use Cases — ISO 27001 compliance

App ID: `splunk-uc-iso-27001`  
App version: **7.1.0**  
Generated: `2026-04-22T11:55:17Z`  
Upstream catalogue: [fenre/splunk-monitoring-use-cases](https://github.com/fenre/splunk-monitoring-use-cases)


This app packages **109 use cases** from the upstream catalogue that cite ISO/IEC 27001 — ISMS (`iso-27001`), together with the macros, eventtypes, tags, and lookup needed to operate them.  Every saved search is shipped **disabled by default** so an operator can review the SPL and tune indexes before enabling.

* Regulation tier: **1**
* Jurisdictions: GLOBAL
* Versions covered: 2013, 2022
* UCs by criticality: critical = 16, high = 60, medium = 33


## Most-referenced clauses

| Clause | UCs tagging this clause |
|--------|-------------------------|
| `A.5.36` | 7 |
| `9.1` | 6 |
| `A.8.8` | 5 |
| `8.2` | 3 |
| `A.5.18` | 3 |
| `A.5.24` | 3 |
| `A.5.3` | 3 |
| `A.8.12` | 3 |

## Installation

1. **Review the SPL.**  Every saved search under `default/savedsearches.conf` ships disabled.  Before enabling, replace placeholder `index=` patterns with your site's indexes and macros.
2. **Install.**  Copy this directory into `$SPLUNK_HOME/etc/apps/` or package it with `tar czf splunk-uc-iso-27001.spl splunk-uc-iso-27001/` and deploy via the Splunk app manager.
3. **Open the compliance posture dashboard.**  The navigation lands on `iso_27001_compliance_posture` — a Simple XML dashboard that reads the shipped `uc_compliance_mappings` lookup and works before any saved search is scheduled.  Use it to brief auditors, track clause coverage, and spot mappings with thin assurance.
4. **Enable selectively.**  In *Settings → Searches, reports, and alerts*, enable and schedule the stanzas your team is ready to operate.
5. **Audit trail.**  Every saved search carries the UC id, the regulation version, and the full clause list on its `action.uc_compliance.param.*` attributes.  These are auditor-friendly and survive Splunk's saved-search lifecycle (no lookup required).


## Compliance posture dashboard

The app ships a Simple XML dashboard at `default/data/ui/views/iso_27001_compliance_posture.xml` that reads the per-app `uc_compliance_mappings` lookup.  The dashboard needs zero saved searches to render — install the app, open the dashboard, brief your auditor.

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
| UC-22.3.41 | DORA Art.6 — ICT risk-management framework evidence: control catalogue drift detection | high | A.5.1 |
| UC-22.3.42 | DORA Art.7 — ICT systems inventory completeness: unmanaged endpoints attached to financial services | high | A.5.9 |
| UC-22.3.43 | DORA Art.8 — ICT risk identification: newly discovered high-severity exposure on critical financial services | critical | A.8.8 |
| UC-22.3.44 | DORA Art.17 — ICT incident classification timeliness: major-incident clock evidence | critical | A.5.24 |
| UC-22.3.45 | DORA Art.24 — Digital operational-resilience testing: test-plan execution attestation | high | A.5.29 |
| UC-22.6.1 | ISO 27001 Annex A Control Effectiveness Monitoring | critical | A.8.16 |
| UC-22.6.2 | ISO 27001 Information Security Event Log Review Compliance | high | A.12.4, A.12.4.1 |
| UC-22.6.3 | ISO 27001 Access Rights Review and Recertification | critical | A.9.2.5 |
| UC-22.6.4 | ISO 27001 Information Labelling and Media Handling via DLP | high | A.8.2.3 |
| UC-22.6.5 | ISO 27001 Cryptographic Key and Certificate Lifecycle Monitoring | critical | A.10.1.2 |
| UC-22.6.6 | ISO 27001 Network Security — Segmentation and Firewall Deny Baseline | high | A.13.1.1 |
| UC-22.6.7 | ISO 27001 Supplier IAM and SaaS Integration Change Surveillance | high | A.15.1.2 |
| UC-22.6.8 | ISO 27001 Segregation of Duties — Privileged Splunk Knowledge Object Changes | critical | A.5.3 |
| UC-22.6.9 | ISMS Policy Acknowledgment and Version Drift in Confluence or SharePoint | high | A.5.1 |
| UC-22.6.10 | Security Role Changes vs RACI in ServiceNow CMDB Ownership | medium | A.5.2 |
| UC-22.6.11 | Threat Intelligence Feed Freshness and STIX Object Ingest Gaps | high | A.5.7 |
| UC-22.6.12 | Project Security Gate — Production Deploys Without Security CAB Tag | medium | A.5.8 |
| UC-22.6.13 | Cloud Shared Responsibility Control Coverage Map | high | A.5.23 |
| UC-22.6.14 | Business Continuity — RTO Breach Signals from ITSI Service Degradation | medium | A.5.29 |
| UC-22.6.15 | ICT Readiness for BC — Backup Window Overruns vs RPO | high | A.5.30 |
| UC-22.6.16 | Compliance with Policies — Splunk Search Head Knowledge Object Violations | medium | A.5.36 |
| UC-22.6.17 | Personnel Screening — Contractor Badge Activations Before Background Check Complete | high | A.6.1 |
| UC-22.6.18 | Security Awareness Completion Rate by Department | medium | A.6.3 |
| UC-22.6.19 | Disciplinary Process Triggers — HR Case Codes Correlated with Security Incidents | high | A.6.4 |
| UC-22.6.20 | Remote Working — VPN Split Tunnel and Sensitive App Access | medium | A.6.7 |
| UC-22.6.21 | Physical Perimeter — After-Hours Badge Swipes Without Matching Shift | high | A.7.1 |
| UC-22.6.22 | Physical Security Monitoring — Camera NVR Offline or Disk Full Events | medium | A.7.4 |
| UC-22.6.23 | Removable Storage — USB Mount Events on Engineering Workstations | high | A.7.10 |
| UC-22.6.24 | Secure Disposal — Asset Decommission Wipe Confirmation Before CMDB Retire | medium | A.7.14 |
| UC-22.6.25 | User Endpoint Patch Latency Beyond SLA | high | A.8.1 |
| UC-22.6.26 | Privileged Access — Sudo and RunAs Usage Outside PAM Session | medium | A.12.4.3, A.8.2 |
| UC-22.6.27 | Information Access Restriction — SharePoint Anonymous Link Creation Blocked vs Attempted | high | A.8.3 |
| UC-22.6.28 | Secure Authentication — Password Spray Pattern in Entra Sign-Ins | medium | A.8.5 |
| UC-22.6.29 | Capacity Management — Disk Utilization Forecast Breach in 14 Days | high | A.8.6 |
| UC-22.6.30 | Malware Protection — AV Engine Disabled or Out of Date Events | medium | A.8.7 |
| UC-22.6.31 | Technical Vulnerability Management — Exploitable CVEs with Public PoC on In-Scope Hosts | high | A.8.8 |
| UC-22.6.32 | Configuration Management — Drift on CIS Hardening Parameters for Web Tier | medium | A.8.9 |
| UC-22.6.33 | Information Deletion — S3 Object Delete Storm Outside Retention Workflow | high | A.8.10 |
| UC-22.6.34 | Data Masking — Sampled PII Pattern Hits in Non-Production Test Indexes | medium | A.8.11 |
| UC-22.6.35 | Data Leakage Prevention — High Volume Print to PDF on HR Workstations | high | A.8.12 |
| UC-22.6.36 | Information Backup — Immutable Backup Bucket Policy Change Attempts | medium | A.8.13 |
| UC-22.6.37 | Redundancy of IT — Cluster Node Loss Events for Critical Databases | high | A.8.14 |
| UC-22.6.38 | Logging — Forwarder Stopped or CrashLoop on Security-Relevant Hosts | medium | A.12.4.2, A.8.15 |
| UC-22.6.39 | Monitoring Activities — SOC Queue Depth vs On-Shift Analyst Headcount | high | A.16.1.2, A.8.16 |
| UC-22.6.40 | Clock Synchronization — Kerberos Clock Skew Related Authentication Failures | medium | A.8.17 |
| UC-22.6.41 | Network Security — East-West Firewall Deny Spike on Server VLAN | high | A.8.20 |
| UC-22.6.42 | Web and Email Filtering — Denied High-Risk Categories Toward Young Domains | medium | A.8.21, A.8.23 |
| UC-22.6.43 | Network Segmentation — Cross-VLAN RDP Allowed by Mis-Tuned ACL | high | A.8.22 |
| UC-22.6.44 | Use of Cryptography — Weak Cipher Suites Negotiated on Public Load Balancer | medium | A.8.24 |
| UC-22.6.45 | Secure SDLC, App Security Requirements, and Secure Coding Pipeline Gates | high | A.8.25, A.8.26, A.8.28 |
| UC-22.6.46 | ISO/IEC 27001:2022 Clause 6.1 — Risk-assessment evidence: live risk register decay | high | 6.1 |
| UC-22.6.47 | ISO/IEC 27001:2022 Clause 6.2 — Information-security objectives: measurable-target attainment | medium | 6.2, 9.1 |
| UC-22.6.48 | ISO/IEC 27001:2022 Clause 8.2 — Operational risk-assessment: per-change risk-score recalculation | high | 6.1, 8.2 |
| UC-22.6.49 | ISO/IEC 27001:2022 Clause 9.1 — Monitoring programme coverage: KPI telemetry uptime | high | 9.1 |
| UC-22.6.50 | ISO/IEC 27001:2022 Clause 9.2 — Internal audit coverage: control sample rotation | medium | 9.2 |
| UC-22.6.51 | ISO/IEC 27001:2022 Annex A.5.24 — Incident-management planning: runbook currency attestation | medium | A.5.24 |
| UC-22.6.52 | ISO/IEC 27001:2022 Annex A.5.25 — Event classification decisions: SIEM-to-incident triage traceability | high | A.5.25 |
| UC-22.6.53 | ISO/IEC 27001:2022 Clause 7.2 — Competence evidence: role-based training completion | medium | 7.2 |
| UC-22.6.54 | ISO/IEC 27001:2022 Clause 7.5 — Documented information control: policy register approval trail | medium | 7.5 |
| UC-22.6.55 | ISO/IEC 27001:2022 Clause 8.1 — Operational planning: change advisory board (CAB) approval evidence | medium | 8.1 |
| UC-22.8.31 | SOC 2 CC6.6 — Encryption-in-transit validation: cleartext protocols crossing the trust boundary | high | A.8.24 |
| UC-22.8.32 | SOC 2 CC6.7 — System boundary & data-transmission control: unapproved egress destinations | high | A.8.23 |
| UC-22.8.33 | SOC 2 CC7.1 — System-operations monitoring: uptime attestation and alert-noise governance | high | 8.1 |
| UC-22.8.34 | SOC 2 CC7.3 — Evaluated events: threshold breaches without documented rationale | medium | A.5.25 |
| UC-22.8.35 | SOC 2 CC7.4 — Incident response: post-incident review completion SLA | high | A.5.26 |
| UC-22.8.36 | SOC 2 CC1.1 — Integrity and ethical values: code-of-conduct acknowledgement trail | medium | 6.3 |
| UC-22.8.37 | SOC 2 CC9.1 — Risk-mitigation activity: vendor-risk action closure SLA | medium | A.5.19 |
| UC-22.8.38 | SOC 2 C1.1 — Confidentiality: sensitive-data exposure at the egress boundary | high | A.8.12 |
| UC-22.9.1 | Compliance Posture Score Trending | high | A.5.36 |
| UC-22.9.2 | Audit Finding Closure Rate Trending | high | A.5.36 |
| UC-22.9.3 | Control Effectiveness Trending | high | A.5.36 |
| UC-22.9.5 | Policy Violation Volume Trending | medium | A.5.36 |
| UC-22.9.6 | Compliance Trending — SOC 2 Control Test Pass Rate vs Prior Quarter Baseline | medium | 9.1 |
| UC-22.9.7 | Compliance Trending — ISO 27001 Statement of Applicability Control Exception Burn-Down | high | 8.2, 9.1 |
| UC-22.9.9 | Compliance Trending — Regulatory Change Feed Impact Score on In-Scope Controls | high | 9.1 |
| UC-22.9.10 | Compliance Trending — Weighted Compliance Posture Composite and Driver Attribution | high | 9.1 |
| UC-22.11.91 | PCI-DSS 1.3 — CDE network boundary: unauthorised flows between CDE and untrusted networks | critical | A.8.22 |
| UC-22.11.92 | PCI-DSS 2.2 — Secure configuration baseline: drift from approved hardening template | high | A.8.9 |
| UC-22.11.93 | PCI-DSS 3.3 — Sensitive authentication data: cleartext PAN/CVV detection in logs | critical | A.8.12 |
| UC-22.11.94 | PCI-DSS 5.2 — Anti-malware: EDR coverage + detection-queue attestation | high | A.8.7 |
| UC-22.11.95 | PCI-DSS 6.2 — Bespoke-software SDLC: code-review + SAST completion before CDE deploy | high | A.8.25 |
| UC-22.11.96 | PCI-DSS 8.3 — Strong authentication: password-only logins against privileged accounts | critical | A.8.5 |
| UC-22.11.97 | PCI-DSS 8.4 — MFA coverage: administrative access to CDE without MFA | critical | A.8.5 |
| UC-22.11.98 | PCI-DSS 8.6 — Application and system accounts: interactive use of a service account | high | A.5.16 |
| UC-22.11.99 | PCI-DSS 10.3 — Audit log integrity: tampering/deletion detection on CDE log source | critical | A.8.15 |
| UC-22.11.100 | PCI-DSS 10.4 — Time synchronisation: NTP drift on CDE hosts | high | A.8.17 |
| UC-22.11.101 | PCI-DSS 10.6 — Log review: daily-review evidence for CDE data sources | high | A.5.28 |
| UC-22.11.102 | PCI-DSS 10.7 — Log retention: CDE data-source retention + immutability attestation | high | A.5.33 |
| UC-22.11.103 | PCI-DSS 11.3 — Vulnerability programme: overdue scan cadence and unremediated high-severity | high | A.8.8 |
| UC-22.11.104 | PCI-DSS 11.4 — Intrusion detection: IDS signature/health attestation + untuned alert monitoring | high | A.8.16 |
| UC-22.11.105 | PCI-DSS 12.10 — Incident response: IR readiness — playbook exercise evidence | high | A.5.24 |
| UC-22.11.106 | PCI-DSS 12.3 — Targeted risk analysis: frequency adherence for per-requirement TRAs | medium | 8.2 |
| UC-22.12.36 | SOX-ITGC AccessMgmt.Provisioning — Financial-system user provisioning SLA & workflow adherence | high | A.5.18 |
| UC-22.12.37 | SOX-ITGC AccessMgmt.Termination — Deprovisioning SLA after HR termination event | critical | A.5.18 |
| UC-22.12.38 | SOX-ITGC ChangeMgmt.Testing — Financial-system change test-evidence completeness | high | A.8.32 |
| UC-22.12.39 | SOX-ITGC ChangeMgmt.Approval — Segregation of duties in financial-system change approval | critical | A.5.3 |
| UC-22.12.40 | SOX-ITGC Operations.JobSchedule — Batch-schedule monitoring: financial-job exception visibility | medium | A.8.30 |
| UC-22.40.2 | Break-glass account usage review with mandatory post-use approval | critical | A.5.15 |
| UC-22.40.3 | Periodic access review SLA — stale certifications by control owner | high | A.5.18 |
| UC-22.42.5 | Infrastructure-as-code drift — applied state diverges from merged plan | high | A.8.9 |
| UC-22.43.1 | Critical vulnerability SLA tracker — unpatched 30+ days with exploited-in-the-wild indicator | critical | A.8.8 |
| UC-22.43.4 | Scanner coverage gap — regulated hosts without a recent scan | high | A.8.8 |
| UC-22.46.5 | Developer data-handling training — prod-access engineers lacking training | high | A.6.3 |
| UC-22.47.1 | Control test freshness — evidence older than policy cadence | medium | A.5.36 |
| UC-22.47.3 | Control owner attestation freshness | medium | A.5.35 |
| UC-22.47.5 | Continuous control monitoring anomaly — failure-rate trending up | high | A.5.36 |
| UC-22.48.1 | Segregation of duties — toxic role combinations in IAM | critical | A.5.3 |
| UC-22.48.3 | Developer-to-production SoD — same developer submits AND approves merge | high | A.8.30 |
| UC-22.49.3 | Litigation-hold override audit — holds applied/released without ticket | high | A.5.33 |

---

_This app is generated; edits in place will be overwritten.  File bug reports and content requests at https://github.com/fenre/splunk-monitoring-use-cases/issues._
