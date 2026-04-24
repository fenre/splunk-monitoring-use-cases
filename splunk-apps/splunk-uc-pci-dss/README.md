# Splunk Use Cases — PCI DSS compliance

App ID: `splunk-uc-pci-dss`  
App version: **7.1.0**  
Generated: `2026-04-22T11:55:17Z`  
Upstream catalogue: [fenre/splunk-monitoring-use-cases](https://github.com/fenre/splunk-monitoring-use-cases)


This app packages **140 use cases** from the upstream catalogue that cite Payment Card Industry Data Security Standard (`pci-dss`), together with the macros, eventtypes, tags, and lookup needed to operate them.  Every saved search is shipped **disabled by default** so an operator can review the SPL and tune indexes before enabling.

* Regulation tier: **1**
* Jurisdictions: GLOBAL
* Versions covered: v3.2.1, v4.0
* UCs by criticality: critical = 45, high = 71, medium = 24


## Most-referenced clauses

| Clause | UCs tagging this clause |
|--------|-------------------------|
| `10.2.2` | 4 |
| `2.2.4` | 4 |
| `4.2.1` | 4 |
| `12.6` | 3 |
| `3.4.1` | 3 |
| `5.3.1` | 3 |
| `6.3.1` | 3 |
| `6.3.3` | 3 |

## Installation

1. **Review the SPL.**  Every saved search under `default/savedsearches.conf` ships disabled.  Before enabling, replace placeholder `index=` patterns with your site's indexes and macros.
2. **Install.**  Copy this directory into `$SPLUNK_HOME/etc/apps/` or package it with `tar czf splunk-uc-pci-dss.spl splunk-uc-pci-dss/` and deploy via the Splunk app manager.
3. **Open the compliance posture dashboard.**  The navigation lands on `pci_dss_compliance_posture` — a Simple XML dashboard that reads the shipped `uc_compliance_mappings` lookup and works before any saved search is scheduled.  Use it to brief auditors, track clause coverage, and spot mappings with thin assurance.
4. **Enable selectively.**  In *Settings → Searches, reports, and alerts*, enable and schedule the stanzas your team is ready to operate.
5. **Audit trail.**  Every saved search carries the UC id, the regulation version, and the full clause list on its `action.uc_compliance.param.*` attributes.  These are auditor-friendly and survive Splunk's saved-search lifecycle (no lookup required).


## Compliance posture dashboard

The app ships a Simple XML dashboard at `default/data/ui/views/pci_dss_compliance_posture.xml` that reads the per-app `uc_compliance_mappings` lookup.  The dashboard needs zero saved searches to render — install the app, open the dashboard, brief your auditor.

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
| UC-1.4.8 | PCIe Link Width and Speed Degradation | medium | 6.3.3 |
| UC-10.12.7 | PCI DSS Log Review Compliance | high | 10.4.1 |
| UC-10.12.15 | PCI Scope Validation | high | 12.5.2 |
| UC-22.3.43 | DORA Art.8 — ICT risk identification: newly discovered high-severity exposure on critical financial services | critical | 11.3.1 |
| UC-22.6.53 | ISO/IEC 27001:2022 Clause 7.2 — Competence evidence: role-based training completion | medium | 12.6 |
| UC-22.8.31 | SOC 2 CC6.6 — Encryption-in-transit validation: cleartext protocols crossing the trust boundary | high | 4.2.1 |
| UC-22.8.32 | SOC 2 CC6.7 — System boundary & data-transmission control: unapproved egress destinations | high | 1.3.1 |
| UC-22.8.38 | SOC 2 C1.1 — Confidentiality: sensitive-data exposure at the egress boundary | high | 10.6.2 |
| UC-22.11.1 | Scheduled Firewall Rule Review Evidence for CDE NSCs | high | 1.2.8 |
| UC-22.11.2 | NSC Configuration Change Correlation to Change Tickets | critical | 1.2.1 |
| UC-22.11.3 | CDE Boundary Traffic — Unexpected Corporate-to-Payment Flows | critical | 1.3.1 |
| UC-22.11.4 | Denied Inbound Attempts to Payment Application Ports | high | 1.3.2 |
| UC-22.11.5 | DMZ Originated Sessions Hitting CDE Internal Segments | critical | 1.3.7 |
| UC-22.11.6 | Wireless Client Pools Reaching CDE Hosts | high | 2.2.4 |
| UC-22.11.7 | Outbound Service Allow-List Violations from CDE Servers | medium | 1.2.6 |
| UC-22.11.8 | Default and Vendor Account Authentications on In-Scope Systems | critical | 2.2.2 |
| UC-22.11.9 | Configuration Drift vs CIS Hardening Benchmark on Windows CDE Members | high | 2.2.3 |
| UC-22.11.10 | Listening Services and Daemons on Linux Payment Middleware | medium | 2.2.5 |
| UC-22.11.11 | System Component Inventory Reconciliation — New In-Scope Hosts | high | 2.1.2 |
| UC-22.11.12 | Removal of Vendor Default SNMP and Community Strings | high | 2.2.4 |
| UC-22.11.13 | Security Parameter Drift on In-Scope Routers from Gold Config Hash | medium | 2.2.3 |
| UC-22.11.14 | Primary Account Number Pattern Discovery in Application Indexes | critical | 3.4.1 |
| UC-22.11.15 | Key Management Operations from HSM and KMS Audit Trails | critical | 3.6.1 |
| UC-22.11.16 | Data Retention Job Failures for Cardholder Data Stores | high | 3.3.1 |
| UC-22.11.17 | Cryptographic Erasure Verification After Decommission | high | 3.5.1 |
| UC-22.11.18 | PAN Masking Validation in Point-of-Sale and Web Receipt Logs | medium | 3.4, 3.4.1 |
| UC-22.11.19 | Sensitive Authentication Data (SAD) in Auth Broker Logs | critical | 3.2.1 |
| UC-22.11.20 | Hash and Truncation Method Changes on Tokenization Database | high | 3.5.1 |
| UC-22.11.21 | Cryptographic Key Rotation and Custodian Acknowledgement Trail | high | 3.6.4 |
| UC-22.11.22 | TLS 1.2 Minimum Version Violations on Payment APIs | critical | 4.2.1 |
| UC-22.11.23 | Weak Cipher Suites Offered by Internal TLS Terminators | high | 4.2.1 |
| UC-22.11.24 | Certificate Expiry Risk for Public-Facing Payment Hostnames | high | 4.2.1.2 |
| UC-22.11.25 | Cleartext PAN Indicators in HTTP Headers or Query Strings | critical | 3.4.1 |
| UC-22.11.26 | Wireless Link Encryption Downgrade for Store WLAN Carrying Payment Terminals | medium | 2.2.4 |
| UC-22.11.27 | Anti-Malware Agent Coverage Gaps on CDE Windows Servers | critical | 5.3.1 |
| UC-22.11.28 | Malware Definition and Sensor Policy Update Lag | high | 5.3.2 |
| UC-22.11.29 | Scheduled Malware Scan or On-Demand Scan Failures | high | 5.3.2 |
| UC-22.11.30 | Malware Detection Volume Trend by Store and Server Tier | medium | 5.3.1 |
| UC-22.11.31 | Phishing Simulation Click-Through Rates for Users with CDE Access | medium | 12.6.1 |
| UC-22.11.32 | Anti-Malware Tamper and Bypass Attempt Telemetry | critical | 5.3.1 |
| UC-22.11.33 | Critical and High Vulnerabilities on Payment Application Servers | critical | 11.3.1 |
| UC-22.11.34 | Critical CVE Remediation SLA Breach Tracking | critical | 6.3.3 |
| UC-22.11.35 | Web Application Firewall Blocks and Anomalies on Checkout URIs | high | 6.4.2 |
| UC-22.11.36 | Pull-Request and Code Review Evidence for Payment Microservices | medium | 6.3.1 |
| UC-22.11.37 | Change Control Completeness for Production Payment Releases | high | 6.5.2 |
| UC-22.11.38 | DAST and SAST Finding Density Before Payment Service Releases | high | 6.3.2 |
| UC-22.11.39 | Public-Facing Payment Web Tier Patch and Library Drift | high | 6.2.4 |
| UC-22.11.40 | Role-Based Group Membership Drift for Active Directory CDE OU | high | 7.2.2 |
| UC-22.11.41 | Excessive Database Grants on Schemas Storing Tokenized PAN | critical | 7.2.5 |
| UC-22.11.42 | Access Request and Approval Completeness for CDE VPN Accounts | high | 8.2.1 |
| UC-22.11.43 | Least-Privilege Validation — Interactive Logons to Database Tier from Workstations | high | 8.2.1 |
| UC-22.11.44 | Privilege Escalation Chains on CDE Windows Servers | critical | 10.2.2 |
| UC-22.11.45 | Shared and Break-Glass Account Usage on Payment Infrastructure | critical | 8.6.1 |
| UC-22.11.46 | Vendor Remote Access Sessions into CDE Jump Hosts | high | 12.8.1 |
| UC-22.11.47 | MFA Gap Detection for CDE Interactive and Remote Access | critical | 8.4.2 |
| UC-22.11.48 | Domain Password Policy Compliance via Resultant Set of Policy Events | medium | 8.2.3, 8.3.7 |
| UC-22.11.49 | Failed Authentication Burst Detection on Payment Gateway Accounts | high | 10.2.4 |
| UC-22.11.50 | Account Lifecycle — New AD Users with Immediate CDE Group Assignment | high | 8.2.4 |
| UC-22.11.51 | Inactive Human Accounts Still Entitled to CDE Groups | high | 8.2.6 |
| UC-22.11.52 | Generic Account Prohibition — `admin` / `root` Interactive Success on CDE | critical | 2.2.2 |
| UC-22.11.53 | Remote Access MFA Evidence Correlation — VPN Success Without Step-Up Token | critical | 8.5.1 |
| UC-22.11.54 | Service Account Inventory Reconciliation — Unexpected SPN or Delegation Changes | high | 8.6.1 |
| UC-22.11.55 | Session Timeout Enforcement on Payment Web Admin Consoles | medium | 8.2.8 |
| UC-22.11.56 | Physical Badge Access to Data Center Containing Cardholder Systems | high | 9.4.2 |
| UC-22.11.57 | Visitor Log Completeness for Data Center Escorted Access | medium | 9.4.4 |
| UC-22.11.58 | Secure Media Destruction Workflow Completion for Backup Tapes with CHD | high | 3.2.1 |
| UC-22.11.59 | POS Terminal Tamper and Intrusion Switch Alerts | critical | 9.3.2 |
| UC-22.11.60 | Quarterly Physical Access List Review Exception Tracking | medium | 12.1.1 |
| UC-22.11.61 | Audit Log Source Completeness — Missing Windows Security Events per CDE Host | critical | 10.2, 10.3.1 |
| UC-22.11.62 | Log Ingestion Pipeline Lag and Parser Error Rate for PCI Indexes | high | 10.5.1 |
| UC-22.11.63 | Daily Log Review Workflow — PCI Queue Ticket Closure SLA | high | 10.4.1.1, 10.6 |
| UC-22.11.64 | NTP Stratum and Sync Failure Events on Payment Switches and Firewalls | high | 10.6.1.2 |
| UC-22.11.65 | Splunk `_audit` Tamper Indicators — Saved Search Deletes and Role Changes | critical | 10.2.1.2, 10.5 |
| UC-22.11.66 | Critical System Clock Skew Between Database and Application Tier | high | 10.6.1.3 |
| UC-22.11.67 | Comprehensive Audit Trail for Successful CDE Administrator Logons | high | 10.1, 10.2.2 |
| UC-22.11.68 | Log Retention Index Frozen Bucket Age Compliance | high | 10.5.1.2 |
| UC-22.11.69 | Automated Log Review — Correlation of Firewall Deny Bursts with IDS Signatures | high | 11.4.1 |
| UC-22.11.70 | File Integrity Monitoring Alerts on Payment Web Roots | critical | 11.5.1 |
| UC-22.11.71 | Security Event Correlation — Payment API Errors with Concurrent Admin Logons | high | 10.2.2 |
| UC-22.11.72 | Log Source Coverage Gaps — Expected Sourcetypes with Zero Events | high | 12.10.1 |
| UC-22.11.73 | ASV External Scan Failure and Non-Compliant Finding Trend | critical | 11.3.2 |
| UC-22.11.74 | Internal Authenticated Vulnerability Scan Coverage by CDE Subnet | high | 11.3.1.3 |
| UC-22.11.75 | Unauthorized Wireless Access Point Detection by SSID and BSSID | high | 1.2.3 |
| UC-22.11.76 | Penetration Test Finding Severity and Re-test Status | critical | 11.4.5 |
| UC-22.11.77 | IDS and IPS Alert Volume Baseline and Spike Detection | high | 11.4, 11.4.4 |
| UC-22.11.78 | Segmentation Control Validation — Scanner IP Blocked at CDE Border as Expected | medium | 1.3.3 |
| UC-22.11.79 | Quarterly Internal Scan Remediation Aging Buckets | high | 6.3.1 |
| UC-22.11.80 | External Network Scan Job Failures and Timeout Trending | medium | 6.3.1 |
| UC-22.11.81 | Critical Payment Application Binary and Config File Integrity Alerts | critical | 11.5.1.1 |
| UC-22.11.82 | Network Topology Drift — New L3 Adjacency or BGP Peer on CDE Perimeter | high | 1.2.1 |
| UC-22.11.83 | Security Awareness Training Completion for Personnel with CDE Access | medium | 12.6.3 |
| UC-22.11.84 | Incident Response Plan Tabletop and Live Test Execution Logging | high | 12.10.2 |
| UC-22.11.85 | Formal Risk Assessment Evidence and Residual Risk Score Trend | high | 12.3.2 |
| UC-22.11.86 | Third-Party Service Provider Compliance Scorecard Ingest | high | 12.8.2 |
| UC-22.11.87 | Acceptable Use Policy Annual Attestation Completion | medium | 12.6.1 |
| UC-22.11.88 | Security Roles and Responsibilities Assignment Completeness | medium | 12.5.1 |
| UC-22.11.89 | Technology Acceptable Use — USB Mass Storage on CDE Workstations | high | 2.2.4 |
| UC-22.11.90 | Annual Information Security Policy Review and Approval Workflow | medium | 12.1.2 |
| UC-22.11.91 | PCI-DSS 1.3 — CDE network boundary: unauthorised flows between CDE and untrusted networks | critical | 1.3 |
| UC-22.11.92 | PCI-DSS 2.2 — Secure configuration baseline: drift from approved hardening template | high | 2.2 |
| UC-22.11.93 | PCI-DSS 3.3 — Sensitive authentication data: cleartext PAN/CVV detection in logs | critical | 3.3 |
| UC-22.11.94 | PCI-DSS 5.2 — Anti-malware: EDR coverage + detection-queue attestation | high | 5.2 |
| UC-22.11.95 | PCI-DSS 6.2 — Bespoke-software SDLC: code-review + SAST completion before CDE deploy | high | 6.2 |
| UC-22.11.96 | PCI-DSS 8.3 — Strong authentication: password-only logins against privileged accounts | critical | 8.3 |
| UC-22.11.97 | PCI-DSS 8.4 — MFA coverage: administrative access to CDE without MFA | critical | 8.4 |
| UC-22.11.98 | PCI-DSS 8.6 — Application and system accounts: interactive use of a service account | high | 8.6 |
| UC-22.11.99 | PCI-DSS 10.3 — Audit log integrity: tampering/deletion detection on CDE log source | critical | 10.3 |
| UC-22.11.100 | PCI-DSS 10.4 — Time synchronisation: NTP drift on CDE hosts | high | 10.4 |
| UC-22.11.101 | PCI-DSS 10.6 — Log review: daily-review evidence for CDE data sources | high | 10.6 |
| UC-22.11.102 | PCI-DSS 10.7 — Log retention: CDE data-source retention + immutability attestation | high | 10.7 |
| UC-22.11.103 | PCI-DSS 11.3 — Vulnerability programme: overdue scan cadence and unremediated high-severity | high | 11.3 |
| UC-22.11.104 | PCI-DSS 11.4 — Intrusion detection: IDS signature/health attestation + untuned alert monitoring | high | 11.4 |
| UC-22.11.105 | PCI-DSS 12.10 — Incident response: IR readiness — playbook exercise evidence | high | 12.10 |
| UC-22.11.106 | PCI-DSS 12.3 — Targeted risk analysis: frequency adherence for per-requirement TRAs | medium | 12.3 |
| UC-22.12.36 | SOX-ITGC AccessMgmt.Provisioning — Financial-system user provisioning SLA & workflow adherence | high | 8.2.4 |
| UC-22.12.37 | SOX-ITGC AccessMgmt.Termination — Deprovisioning SLA after HR termination event | critical | 8.2.5 |
| UC-22.12.38 | SOX-ITGC ChangeMgmt.Testing — Financial-system change test-evidence completeness | high | 6.4.6 |
| UC-22.12.39 | SOX-ITGC ChangeMgmt.Approval — Segregation of duties in financial-system change approval | critical | 6.4.4 |
| UC-22.35.1 | Audit-log continuity: detect indexing gap indicating lost evidence | critical | 10.2.1 |
| UC-22.35.2 | Log tamper detection via write-once-read-many chain-of-custody | critical | 10.5 |
| UC-22.35.4 | Log signing chain integrity — cryptographic signature drift on evidence archive | critical | 10.3.4 |
| UC-22.35.5 | Search-head audit-trail completeness — deleted or rewritten search jobs | high | 10.3.2 |
| UC-22.40.1 | Privileged session recording — missing recordings for elevated sessions | critical | 10.2 |
| UC-22.40.4 | Standing-privilege credential vaulting drift — admin accounts outside PAM | critical | 7.2.5.1 |
| UC-22.40.5 | High-risk privileged-session command without JIT approval | critical | 10.2.2 |
| UC-22.41.1 | Encryption-at-rest coverage gap — unencrypted storage with regulated data | critical | 3.5 |
| UC-22.41.2 | Certificate / TLS posture — weak cipher and expired-cert detection | high | 4.2 |
| UC-22.41.3 | Key rotation attestation — KMS/HSM rotation SLA tracker | high | 3.6 |
| UC-22.41.4 | TLS downgrade / legacy-cipher handshake spike | high | 4.2.1 |
| UC-22.41.5 | Key custodian SoD — same identity creates AND approves a key | high | 3.6.1 |
| UC-22.42.2 | Configuration baseline drift — regulated hosts deviating from CIS benchmark | high | 1.2 |
| UC-22.43.1 | Critical vulnerability SLA tracker — unpatched 30+ days with exploited-in-the-wild indicator | critical | 6.3 |
| UC-22.43.2 | Vulnerability rediscovery after patch — regressed exposures | high | 6.3 |
| UC-22.43.3 | Internet-facing asset × unpatched critical CVE | critical | 6.3.3 |
| UC-22.43.4 | Scanner coverage gap — regulated hosts without a recent scan | high | 11.3.1.1 |
| UC-22.46.1 | Mandatory security training — completion SLA by role | medium | 12.6 |
| UC-22.46.2 | Phishing simulation efficacy — click-rate trend and repeat-clicker detection | medium | 12.6 |
| UC-22.46.3 | Privileged-role specialist training — admins lacking annual deep-training | medium | 12.6.3 |
| UC-22.48.1 | Segregation of duties — toxic role combinations in IAM | critical | 7.2 |
| UC-22.48.5 | Vendor-master SoD — same identity creates vendor AND approves payment | critical | 7.2.5 |

---

_This app is generated; edits in place will be overwritten.  File bug reports and content requests at https://github.com/fenre/splunk-monitoring-use-cases/issues._
