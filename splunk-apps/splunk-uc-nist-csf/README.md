# Splunk Use Cases — NIST CSF compliance

App ID: `splunk-uc-nist-csf`  
App version: **6.1.0**  
Generated: `2026-04-18T08:01:30Z`  
Upstream catalogue: [fenre/splunk-monitoring-use-cases](https://github.com/fenre/splunk-monitoring-use-cases)


This app packages **54 use cases** from the upstream catalogue that cite NIST Cybersecurity Framework (`nist-csf`), together with the macros, eventtypes, tags, and lookup needed to operate them.  Every saved search is shipped **disabled by default** so an operator can review the SPL and tune indexes before enabling.

* Regulation tier: **1**
* Jurisdictions: US, GLOBAL
* Versions covered: 1.1, 2.0
* UCs by criticality: critical = 3, high = 31, medium = 20


## Most-referenced clauses

| Clause | UCs tagging this clause |
|--------|-------------------------|
| `GV.PO-02` | 2 |
| `ID.IM-02` | 2 |
| `PR.AC-1` | 2 |
| `DE.AE-01` | 1 |
| `DE.AE-02` | 1 |
| `DE.AE-03` | 1 |
| `DE.AE-3` | 1 |
| `DE.CM-01` | 1 |

## Installation

1. **Review the SPL.**  Every saved search under `default/savedsearches.conf` ships disabled.  Before enabling, replace placeholder `index=` patterns with your site's indexes and macros.
2. **Install.**  Copy this directory into `$SPLUNK_HOME/etc/apps/` or package it with `tar czf splunk-uc-nist-csf.spl splunk-uc-nist-csf/` and deploy via the Splunk app manager.
3. **Open the compliance posture dashboard.**  The navigation lands on `nist_csf_compliance_posture` — a Simple XML dashboard that reads the shipped `uc_compliance_mappings` lookup and works before any saved search is scheduled.  Use it to brief auditors, track clause coverage, and spot mappings with thin assurance.
4. **Enable selectively.**  In *Settings → Searches, reports, and alerts*, enable and schedule the stanzas your team is ready to operate.
5. **Audit trail.**  Every saved search carries the UC id, the regulation version, and the full clause list on its `action.uc_compliance.param.*` attributes.  These are auditor-friendly and survive Splunk's saved-search lifecycle (no lookup required).


## Compliance posture dashboard

The app ships a Simple XML dashboard at `default/data/ui/views/nist_csf_compliance_posture.xml` that reads the per-app `uc_compliance_mappings` lookup.  The dashboard needs zero saved searches to render — install the app, open the dashboard, brief your auditor.

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
| UC-22.7.1 | NIST CSF Maturity Posture Dashboard | high | Id entify/Protect/Detect/Respond/Recover |
| UC-22.7.2 | NIST CSF Detect Function Coverage Gap Analysis | high | DE.AE-3, MITRE ATT&CK |
| UC-22.7.3 | NIST CSF Identify — Asset Inventory Coverage and Shadow SaaS Signals | high | ID.AM-1, ID.AM-2 |
| UC-22.7.4 | NIST CSF Protect — Identity Authentication Hardening and MFA Gaps | critical | PR.AA-05, PR.AC-1 |
| UC-22.7.5 | NIST CSF Detect — Continuous Vulnerability Exposure Drift on Critical Servers | high | DE.CM-09, DE.CM-7 |
| UC-22.7.6 | NIST CSF Respond — Incident Response Playbook Execution and Stage Timestamps | critical | RS.AN-03, RS.RP-1 |
| UC-22.7.7 | NIST CSF Recover — Backup Job Success and RTO Readiness for Critical Databases | critical | RC.RP-1 |
| UC-22.7.8 | Governance Context — Business Critical Services Mapped to IT Assets | high | GV.OC-01 |
| UC-22.7.9 | External Stakeholder Dependencies — Third-Party SaaS in Auth Flows | high | GV.OC-02 |
| UC-22.7.10 | Enterprise Risk Appetite vs Open Critical Vulnerabilities | medium | GV.RM-01 |
| UC-22.7.11 | Security Role Attestation — RBAC Changes vs HR Start Dates | high | GV.RR-01 |
| UC-22.7.12 | Policy Exception Tracking — Conditional Access Exclusion Groups | high | GV.PO-01 |
| UC-22.7.13 | Documented Baseline Drift — Firewall Rule Adds Outside CAB Window | medium | GV.PO-02 |
| UC-22.7.14 | Executive Oversight Dashboard — Mean Time to Acknowledge Critical Alerts | high | GV.OV-01 |
| UC-22.7.15 | Supply Chain — New Package Installs in CI Against Approved Registry | medium | GV.SC-01 |
| UC-22.7.16 | Hardware Asset Coverage — Agents Missing on In-Scope Servers | high | ID.AM-01 |
| UC-22.7.17 | Software Bill of Materials Signals — Container Image Digests | medium | ID.AM-02 |
| UC-22.7.18 | Data Asset Classification — Sensitive Columns in Query Logs | high | ID.AM-03 |
| UC-22.7.19 | Business Process Impact — Incidents by Critical Application | high | ID.RA-01 |
| UC-22.7.20 | Control Weakness Heatmap — Failed CIS Benchmark Checks | medium | ID.RA-02 |
| UC-22.7.21 | Lessons Learned — Post-Incident Analyst Search Activity | high | ID.IM-01 |
| UC-22.7.22 | Process KPI — Median Days to Remediate High and Critical CVEs | medium | ID.IM-02 |
| UC-22.7.23 | Privileged Path — PAM JIT Elevation vs Standing Admin Logons | high | PR.AA-01 |
| UC-22.7.24 | Non-Human Identity — Service Principal Secret and Certificate Adds | medium | PR.AA-02 |
| UC-22.7.25 | Phishing Simulation Clicks vs Security Awareness Completion | high | PR.AT-01 |
| UC-22.7.26 | Encryption in Transit — Deprecated TLS on Internal APIs | medium | PR.DS-01 |
| UC-22.7.27 | DLP — Blocked Exfil to Personal Email Domains | high | PR.DS-02 |
| UC-22.7.28 | Platform Integrity — sudoers or nsswitch Changes on Linux | medium | PR.PS-01 |
| UC-22.7.29 | DNS Resolver Error Rate SLO for Internal Resolvers | high | PR.IR-01 |
| UC-22.7.30 | Storage Path — Cluster Failover or Multipath Events | medium | PR.IR-02 |
| UC-22.7.31 | EDR Heartbeat Gap Beyond Policy SLA | high | DE.CM-01 |
| UC-22.7.32 | Administrative API Logging Volume Drop vs Baseline | medium | DE.CM-02, PR.PS-04 |
| UC-22.7.33 | Proxy Denies Toward Young Threat-Intel Domains | high | DE.CM-03 |
| UC-22.7.34 | Database Connection Storm from Application Service Account | medium | DE.CM-04 |
| UC-22.7.35 | Certificate Transparency — New Public Cert for Corporate Brand | high | DE.CM-05 |
| UC-22.7.36 | Lateral Movement Chain — Auth, RDP, and Process Create Same Src | medium | DE.AE-01 |
| UC-22.7.37 | Anomaly on Outbound Bytes from Database Subnet | high | DE.AE-02 |
| UC-22.7.38 | Risk Index Spike for Privileged Accounts | medium | DE.AE-03 |
| UC-22.7.39 | IR Ticket Stuck in Containment Beyond SLA | high | RS.MA-01 |
| UC-22.7.40 | SOAR Case Backlog Aging by Severity | medium | RS.MA-02 |
| UC-22.7.41 | Root Cause Field Completeness on Closed Incidents | high | RS.AN-01 |
| UC-22.7.42 | Composite Timeline — Notable, AV, and Proxy Same Host One Hour | medium | RS.AN-02 |
| UC-22.7.43 | Executive Paging Lag After Sev-1 Playbook Start | medium | RS.CO-01 |
| UC-22.7.44 | Legal Hold Population — Elevated File Export Activity | high | RS.CO-02 |
| UC-22.7.45 | EDR Host Isolation Action Success Rate | high | RS.MI-01 |
| UC-22.7.46 | Scheduled Restore Test Outcomes vs Policy Frequency | high | RC.RP-01 |
| UC-22.7.47 | AD Forest Recovery Drill — Directory Service Restore Events | medium | RC.RP-02 |
| UC-22.7.48 | Multi-Region Failover — Health-Check Driven DNS Answer Changes | high | RC.RP-03 |
| UC-22.7.49 | Crisis Email Blast Size to All Employees | medium | RC.CO-01 |
| UC-22.7.50 | Status Page Update Cadence During Major Incident | high | RC.CO-02 |
| UC-22.9.1 | Compliance Posture Score Trending | high | GV.OV-03 |
| UC-22.9.2 | Audit Finding Closure Rate Trending | high | GV.OV-02 |
| UC-22.9.3 | Control Effectiveness Trending | high | ID.IM-02 |
| UC-22.9.5 | Policy Violation Volume Trending | medium | GV.PO-02 |

---

_This app is generated; edits in place will be overwritten.  File bug reports and content requests at https://github.com/fenre/splunk-monitoring-use-cases/issues._
