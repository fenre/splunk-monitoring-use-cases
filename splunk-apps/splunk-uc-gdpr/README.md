# Splunk Use Cases — GDPR compliance

App ID: `splunk-uc-gdpr`  
App version: **7.1.0**  
Generated: `2026-04-22T11:55:17Z`  
Upstream catalogue: [fenre/splunk-monitoring-use-cases](https://github.com/fenre/splunk-monitoring-use-cases)


This app packages **99 use cases** from the upstream catalogue that cite General Data Protection Regulation (`gdpr`), together with the macros, eventtypes, tags, and lookup needed to operate them.  Every saved search is shipped **disabled by default** so an operator can review the SPL and tune indexes before enabling.

* Regulation tier: **1**
* Jurisdictions: EU, EEA
* Versions covered: 2016/679
* UCs by criticality: critical = 22, high = 71, medium = 6


## Most-referenced clauses

| Clause | UCs tagging this clause |
|--------|-------------------------|
| `Art.7` | 16 |
| `Art.32` | 8 |
| `Art.44` | 7 |
| `Art.45` | 7 |
| `Art.46` | 7 |
| `Art.6` | 6 |
| `Art.33` | 5 |
| `Art.17` | 4 |

## Installation

1. **Review the SPL.**  Every saved search under `default/savedsearches.conf` ships disabled.  Before enabling, replace placeholder `index=` patterns with your site's indexes and macros.
2. **Install.**  Copy this directory into `$SPLUNK_HOME/etc/apps/` or package it with `tar czf splunk-uc-gdpr.spl splunk-uc-gdpr/` and deploy via the Splunk app manager.
3. **Open the compliance posture dashboard.**  The navigation lands on `gdpr_compliance_posture` — a Simple XML dashboard that reads the shipped `uc_compliance_mappings` lookup and works before any saved search is scheduled.  Use it to brief auditors, track clause coverage, and spot mappings with thin assurance.
4. **Enable selectively.**  In *Settings → Searches, reports, and alerts*, enable and schedule the stanzas your team is ready to operate.
5. **Audit trail.**  Every saved search carries the UC id, the regulation version, and the full clause list on its `action.uc_compliance.param.*` attributes.  These are auditor-friendly and survive Splunk's saved-search lifecycle (no lookup required).


## Compliance posture dashboard

The app ships a Simple XML dashboard at `default/data/ui/views/gdpr_compliance_posture.xml` that reads the per-app `uc_compliance_mappings` lookup.  The dashboard needs zero saved searches to render — install the app, open the dashboard, brief your auditor.

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
| UC-9.3.12 | Consent Grant Abuse | critical | Art.7 |
| UC-10.3.89 | Disable Defender Submit Samples Consent Feature | high | Art.32 |
| UC-10.4.24 | Azure AD Block User Consent For Risky Apps Disabled | high | Art.7 |
| UC-10.4.39 | O365 Admin Consent Bypassed by Service Principal | high | Art.7 |
| UC-10.4.45 | O365 Block User Consent For Risky Apps Disabled | high | Art.7 |
| UC-10.4.75 | O365 File Permissioned Application Consent Granted by User | high | Art.6 |
| UC-10.4.79 | O365 Mail Permissioned Application Consent Granted by User | high | Art.6 |
| UC-10.4.111 | O365 Tenant Wide Admin Consent Granted | high | Art.7 |
| UC-10.4.114 | O365 User Consent Blocked for Risky Application | high | Art.7 |
| UC-10.4.115 | O365 User Consent Denied for OAuth Application | high | Art.7 |
| UC-10.7.137 | Azure AD Admin Consent Bypassed by Service Principal | high | Art.7 |
| UC-10.7.154 | Azure AD OAuth Application Consent Granted By User | high | Art.6 |
| UC-10.7.166 | Azure AD Tenant Wide Admin Consent Granted | high | Art.7 |
| UC-10.7.167 | Azure AD User Consent Blocked for Risky Application | high | Art.7 |
| UC-10.7.168 | Azure AD User Consent Denied for OAuth Application | high | Art.7 |
| UC-10.11.62 | Zscaler Data Protection Policy Effectiveness | high | Art.32 |
| UC-11.3.11 | Collaboration App Permission and Consent Audit | high | Art.6 |
| UC-22.1.1 | GDPR PII Detection in Application Log Data | critical | Art.5, Art.6 |
| UC-22.1.2 | GDPR Data Subject Access Request Fulfillment Tracking | critical | Art.15, Art.16, Art.17… |
| UC-22.1.3 | GDPR Breach Notification Timeline Monitoring | critical | Art.33, Art.72 |
| UC-22.1.4 | GDPR Data Retention Policy Enforcement | high | Art.5(1)(e) |
| UC-22.1.5 | GDPR Consent Management Audit Trail | high | Art.7 |
| UC-22.1.6 | GDPR Cross-Border Data Transfer Monitoring | critical | Art.44, Art.45, Art.46… |
| UC-22.1.7 | GDPR Security of Processing — Encryption and Pseudonymisation Coverage | critical | Art.32 |
| UC-22.1.8 | GDPR Records of Processing Activities Completeness | high | Art.30 |
| UC-22.1.9 | GDPR Data Protection by Design — Data Minimisation Validation | high | Art.25 |
| UC-22.1.10 | GDPR Privileged Access to Personal Data Stores | critical | Art.32, Art.5(1)(f) |
| UC-22.1.11 | GDPR Right to Erasure Verification | critical | Art.17 |
| UC-22.1.12 | GDPR Breach Scope and Affected Data Subject Quantification | critical | Art.33(3) |
| UC-22.1.13 | GDPR High-Risk Breach Communication to Data Subjects | critical | Art.34 |
| UC-22.1.14 | GDPR Data Protection Impact Assessment Coverage | high | Art.35 |
| UC-22.1.15 | GDPR Third-Party Processor Compliance Monitoring | high | Art.28 |
| UC-22.1.16 | GDPR Consent Withdrawal Processing Enforcement | high | Art.18, Art.7(3) |
| UC-22.1.17 | GDPR Audit Log Integrity and Tamper Protection | high | Art.5(2) |
| UC-22.1.18 | GDPR Automated Decision-Making and Profiling Transparency | high | Art.22 |
| UC-22.1.19 | GDPR Data Subject Rights Response SLA Dashboard | high | Art.12 |
| UC-22.1.20 | GDPR Legitimate Interest Balancing Test Evidence | high | Art.6(1)(f) |
| UC-22.1.21 | GDPR Encryption at Rest Audit Evidence | high | Art.32(1)(a) |
| UC-22.1.22 | GDPR Access Control Review and Privileged Access Evidence | high | Art.32(1)(b) |
| UC-22.1.23 | GDPR Pseudonymisation Validation in Pipelines and Logs | high | Art.32(1)(a) |
| UC-22.1.24 | GDPR Security Testing Evidence Aggregation (Pen Test / Red Team) | high | Art.32(1)(d) |
| UC-22.1.25 | GDPR Security Incident Tracking Linked to Personal Data Impact | critical | Art.32(1)(c) |
| UC-22.1.26 | GDPR Resilience and Availability Monitoring for Personal-Data Services | high | Art.32(1)(b)(c) |
| UC-22.1.27 | GDPR Processor Compliance Attestation Tracking | high | Art.28(3) |
| UC-22.1.28 | GDPR Sub-Processor Change Monitoring | high | Art.28(2), Art.28(4) |
| UC-22.1.29 | GDPR Processor Personal Data Breach Notification SLA | critical | Art.28(3)(f), Art.33 |
| UC-22.1.30 | GDPR Data Processing Agreement Obligation Control Matrix | high | Art.28(3) |
| UC-22.1.31 | GDPR Processor Audit Evidence — Right to Audit and Inspection Logs | high | Art.28(3)(h) |
| UC-22.1.32 | GDPR DPIA Completion Tracking Against High-Risk Processing | high | Art.35(7) |
| UC-22.1.33 | GDPR DPIA Residual Risk Scoring and Escalation | high | Art.35(7)(b) |
| UC-22.1.34 | GDPR DPIA Supervisory Authority Consultation Tracking | high | Art.36 |
| UC-22.1.35 | GDPR DPIA Remediation Monitoring and Mitigation Closure | high | Art.35(7)(d) |
| UC-22.1.36 | GDPR Transfer Impact Assessment (TIA) Status for Third-Country Transfers | high | Art.44, Art.45, Art.46 |
| UC-22.1.37 | GDPR Standard Contractual Clauses (SCCs) Compliance Tracking | high | Art.46(2)(c) |
| UC-22.1.38 | GDPR Data Localization Enforcement for Restricted Processing | critical | Art.44, Art.45, Art.46… |
| UC-22.1.39 | GDPR Adequacy Decision and Legal Basis Change Monitoring | high | Art.45 |
| UC-22.1.40 | GDPR Binding Corporate Rules (BCR) Evidence and Intra-Group Transfer Monitoring | high | Art.47 |
| UC-22.1.41 | GDPR Unauthorized Cloud Service Detection (Shadow SaaS) | high | Art.32, Art.5(2) |
| UC-22.1.42 | GDPR Shadow IT Personal Data Processing Indicators | high | Art.5(2) |
| UC-22.1.43 | GDPR Personal Data in Non-Approved Systems (ROPA Drift Detection) | high | Art.30, Art.5(2) |
| UC-22.1.44 | GDPR Cross-Border Personal Data Flow Anomaly Detection | high | Art.44, Art.45, Art.46… |
| UC-22.1.45 | GDPR Privacy Settings Default Validation (Privacy by Design / Default) | high | Art.25(2) |
| UC-22.1.46 | GDPR Consent Mechanism Audit (Lawful Basis Alignment) | high | Art.21, Art.25(1), Art.7 |
| UC-22.1.47 | GDPR Data Minimisation Compliance in Logs and APIs | high | Art.25(2), Art.5(1)(c) |
| UC-22.1.48 | GDPR Purpose Limitation Enforcement Across Systems | high | Art.25(1), Art.5(1)(b) |
| UC-22.1.49 | GDPR Storage Limitation Automation Evidence | high | Art.25(2), Art.5(1)(e) |
| UC-22.1.50 | GDPR Transparency Notice Completeness and Version Alignment | high | Art.12, Art.13, Art.14… |
| UC-22.8.39 | SOC 2 P1.1 — Privacy notice: consent-record freshness for privacy-notice version changes | medium | Art.7 |
| UC-22.9.4 | Regulatory Incident Response Time Trending | medium | Art.33 |
| UC-22.35.1 | Audit-log continuity: detect indexing gap indicating lost evidence | critical | Art.32(1)(b) |
| UC-22.35.2 | Log tamper detection via write-once-read-many chain-of-custody | critical | Art.32 |
| UC-22.35.3 | Indexer replication lag exposing evidence to single-point failure | high | Art.32 |
| UC-22.35.4 | Log signing chain integrity — cryptographic signature drift on evidence archive | critical | Art.32(1)(b) |
| UC-22.36.1 | DSAR fulfillment SLA tracker with verification evidence trail | high | Art.12, Art.15 |
| UC-22.36.2 | Right-to-erasure propagation completeness across downstream systems | critical | Art.17, Art.17(2) |
| UC-22.36.3 | Portability export integrity — signed manifest verification | medium | Art.20 |
| UC-22.36.4 | DSAR identity-verification friction — failed-verification anomaly | high | Art.12(6) |
| UC-22.36.5 | DSAR request-type mix anomaly — zero-deletion skew indicating broken workflow | medium | Art.12(2) |
| UC-22.37.1 | Consent capture evidence freshness — stale-consent alerting | high | Art.6, Art.7 |
| UC-22.37.2 | Consent withdrawal propagation SLA — downstream stop-processing evidence | critical | Art.7 |
| UC-22.37.4 | Purpose-limitation enforcement — processing not matching declared purpose | high | Art.5(1)(b) |
| UC-22.37.5 | IAB TCF consent string mutation without user interaction | high | Art.7(1) |
| UC-22.38.1 | Cross-border personal-data flow anomaly — egress to unsanctioned jurisdictions | critical | Art.44, Art.46 |
| UC-22.38.2 | SCC / adequacy decision reference freshness — stale-safeguard detector | medium | Art.45, Art.46 |
| UC-22.38.3 | Data localization enforcement — regulated-data must-stay-in-region | high | Art.44 |
| UC-22.38.4 | Transfer Impact Assessment currency — stale Schrems II assessments | medium | Art.46 |
| UC-22.38.5 | Bulk regulated-data export targeting non-adequate jurisdiction | critical | Art.44, Art.45 |
| UC-22.39.1 | Multi-regulator breach-notification SLA tracker (24h NIS2 / 72h GDPR / 72h HIPAA) | critical | Art.33 |
| UC-22.39.2 | Regulator-portal submission evidence — one-way API acknowledgement audit | high | Art.33 |
| UC-22.39.3 | Data-subject breach communication timeline tracker (Art.34 / §164.404) | high | Art.34 |
| UC-22.39.4 | Cross-regulator consistency — divergent material facts across submissions | high | Art.33(3) |
| UC-22.39.5 | Regulator-portal authentication failure during submission window | high | Art.33(1) |
| UC-22.41.1 | Encryption-at-rest coverage gap — unencrypted storage with regulated data | critical | Art.32 |
| UC-22.44.2 | Subprocessor inventory change — notification SLA to data controllers | high | Art.28 |
| UC-22.46.5 | Developer data-handling training — prod-access engineers lacking training | high | Art.32(4) |
| UC-22.49.1 | Retention execution evidence — records past retention still present | high | Art.5 |
| UC-22.49.2 | Disposal workflow completion — failed disposals requiring manual review | high | Art.5 |
| UC-22.49.4 | Retention policy drift — system config vs policy catalogue | high | Art.5(1)(e) |
| UC-22.49.5 | Cryptographic erasure attestation — per-asset destruction evidence | high | Art.17 |

---

_This app is generated; edits in place will be overwritten.  File bug reports and content requests at https://github.com/fenre/splunk-monitoring-use-cases/issues._
