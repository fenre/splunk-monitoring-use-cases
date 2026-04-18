# Splunk Use Cases — SOC 2 compliance

App ID: `splunk-uc-soc-2`  
App version: **6.1.0**  
Generated: `2026-04-18T08:01:30Z`  
Upstream catalogue: [fenre/splunk-monitoring-use-cases](https://github.com/fenre/splunk-monitoring-use-cases)


This app packages **75 use cases** from the upstream catalogue that cite SOC 2 Trust Services Criteria (`soc-2`), together with the macros, eventtypes, tags, and lookup needed to operate them.  Every saved search is shipped **disabled by default** so an operator can review the SPL and tune indexes before enabling.

* Regulation tier: **1**
* Jurisdictions: US, GLOBAL
* Versions covered: 2017 TSC
* UCs by criticality: critical = 21, high = 40, medium = 14


## Most-referenced clauses

| Clause | UCs tagging this clause |
|--------|-------------------------|
| `unspecified` | 22 |
| `CC8.1` | 9 |
| `CC7.1` | 5 |
| `CC7.2` | 4 |
| `CC6.3` | 3 |
| `A1.2` | 2 |
| `C1.1` | 2 |
| `CC4.1` | 2 |

## Installation

1. **Review the SPL.**  Every saved search under `default/savedsearches.conf` ships disabled.  Before enabling, replace placeholder `index=` patterns with your site's indexes and macros.
2. **Install.**  Copy this directory into `$SPLUNK_HOME/etc/apps/` or package it with `tar czf splunk-uc-soc-2.spl splunk-uc-soc-2/` and deploy via the Splunk app manager.
3. **Open the compliance posture dashboard.**  The navigation lands on `soc_2_compliance_posture` — a Simple XML dashboard that reads the shipped `uc_compliance_mappings` lookup and works before any saved search is scheduled.  Use it to brief auditors, track clause coverage, and spot mappings with thin assurance.
4. **Enable selectively.**  In *Settings → Searches, reports, and alerts*, enable and schedule the stanzas your team is ready to operate.
5. **Audit trail.**  Every saved search carries the UC id, the regulation version, and the full clause list on its `action.uc_compliance.param.*` attributes.  These are auditor-friendly and survive Splunk's saved-search lifecycle (no lookup required).


## Compliance posture dashboard

The app ships a Simple XML dashboard at `default/data/ui/views/soc_2_compliance_posture.xml` that reads the per-app `uc_compliance_mappings` lookup.  The dashboard needs zero saved searches to render — install the app, open the dashboard, brief your auditor.

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
| UC-22.6.49 | ISO/IEC 27001:2022 Clause 9.1 — Monitoring programme coverage: KPI telemetry uptime | high | CC7.1 |
| UC-22.6.50 | ISO/IEC 27001:2022 Clause 9.2 — Internal audit coverage: control sample rotation | medium | CC4.1 |
| UC-22.6.52 | ISO/IEC 27001:2022 Annex A.5.25 — Event classification decisions: SIEM-to-incident triage traceability | high | CC7.3 |
| UC-22.6.54 | ISO/IEC 27001:2022 Clause 7.5 — Documented information control: policy register approval trail | medium | CC1.4 |
| UC-22.6.55 | ISO/IEC 27001:2022 Clause 8.1 — Operational planning: change advisory board (CAB) approval evidence | medium | CC8.1 |
| UC-22.8.1 | SOC 2 Trust Services Criteria Continuous Control Monitoring | critical | CC6-CC8 |
| UC-22.8.2 | SOC 2 System Availability and Incident Response Evidence Collection | critical | A1 |
| UC-22.8.3 | SOC 2 Confidentiality Classification and DLP Event Audit | high | C1 |
| UC-22.8.4 | SOC 2 Control Environment and Board-Level Attestation Workflow | medium | CC1.2, CC2.1 |
| UC-22.8.5 | SOC 2 Risk Assessment — Change-Induced Emergency Pattern Monitoring | high | CC3.2, CC3.3 |
| UC-22.8.6 | SOC 2 Processing Integrity — Financial Batch Job Reconciliation Exceptions | critical | PI1.3 |
| UC-22.8.7 | SOC 2 Privacy — Consent Log Integrity and Downstream Propagation Checks | high | P4.2, P4.3 |
| UC-22.8.8 | SOC 2 Fraud Risk and Anomalous Privileged Activity Correlation | critical | CC9.2 |
| UC-22.8.9 | SOC 2 CC1 — Board and Committee ICT Oversight Evidence Trail | high | unspecified |
| UC-22.8.10 | SOC 2 CC2 — Ethical Conduct and Acceptable-Use Violation Monitoring | medium | unspecified |
| UC-22.8.11 | SOC 2 CC2 — Organizational Structure and Segregation-of-Duties Validation | high | unspecified |
| UC-22.8.12 | SOC 2 CC3 — Management Accountability for Control Deficiency Remediation SLAs | high | unspecified |
| UC-22.8.13 | SOC 2 CC4 — Enterprise Risk Register Ingestion and Coverage Gaps | high | unspecified |
| UC-22.8.14 | SOC 2 CC4 — Fraud Risk Scenario Testing Evidence from Anomaly Correlation | critical | unspecified |
| UC-22.8.15 | SOC 2 CC5 — Change Impact Analysis Completeness for Production Releases | high | unspecified |
| UC-22.8.16 | SOC 2 CC6 — Credential Lifecycle — Orphan and Contractor Account Detection | high | unspecified |
| UC-22.8.17 | SOC 2 CC6 — Physical Access Review Exception Tracking for Sensitive Facilities | high | unspecified |
| UC-22.8.18 | SOC 2 CC6 — Encryption in Transit Policy Enforcement for Admin and API Paths | critical | unspecified |
| UC-22.8.19 | SOC 2 CC6 — Timeliness of Access Removal After HR Termination Events | critical | unspecified |
| UC-22.8.20 | SOC 2 CC7 — Unauthorized Production Configuration Change Detection | critical | unspecified |
| UC-22.8.21 | SOC 2 CC7 — Incident Classification Consistency and Severity Drift Audit | high | unspecified |
| UC-22.8.22 | SOC 2 CC7 — Operational Anomaly Detection on Critical Batch and API SLOs | high | unspecified |
| UC-22.8.23 | SOC 2 CC7 — Vulnerability Management SLA and Exception Expiry Tracking | high | unspecified |
| UC-22.8.24 | SOC 2 CC8 — Infrastructure-as-Code Drift vs Approved Terraform Modules | high | unspecified |
| UC-22.8.25 | SOC 2 CC8 — Software Development Lifecycle Control Gates from CI/CD Telemetry | high | unspecified |
| UC-22.8.26 | SOC 2 CC9 — Change Authorization Dual-Control on Privileged Cloud Roles | critical | unspecified |
| UC-22.8.27 | SOC 2 A1 — Capacity Planning Signals for In-Scope Production Services | medium | unspecified |
| UC-22.8.28 | SOC 2 A1 — Disaster Recovery Test Execution and Evidence Timestamps | high | unspecified |
| UC-22.8.29 | SOC 2 C1 — Confidential Information Disposal and Secure Destruction Evidence | high | unspecified |
| UC-22.8.30 | SOC 2 PI1 — Processing Completeness Validation Across Multi-Stage Pipelines | high | unspecified |
| UC-22.8.31 | SOC 2 CC6.6 — Encryption-in-transit validation: cleartext protocols crossing the trust boundary | high | CC6.6 |
| UC-22.8.32 | SOC 2 CC6.7 — System boundary & data-transmission control: unapproved egress destinations | high | CC6.7 |
| UC-22.8.33 | SOC 2 CC7.1 — System-operations monitoring: uptime attestation and alert-noise governance | high | CC7.1 |
| UC-22.8.34 | SOC 2 CC7.3 — Evaluated events: threshold breaches without documented rationale | medium | CC7.3 |
| UC-22.8.35 | SOC 2 CC7.4 — Incident response: post-incident review completion SLA | high | CC7.4 |
| UC-22.8.36 | SOC 2 CC1.1 — Integrity and ethical values: code-of-conduct acknowledgement trail | medium | CC1.1 |
| UC-22.8.37 | SOC 2 CC9.1 — Risk-mitigation activity: vendor-risk action closure SLA | medium | CC9.1 |
| UC-22.8.38 | SOC 2 C1.1 — Confidentiality: sensitive-data exposure at the egress boundary | high | C1.1 |
| UC-22.8.39 | SOC 2 P1.1 — Privacy notice: consent-record freshness for privacy-notice version changes | medium | P1.1 |
| UC-22.11.91 | PCI-DSS 1.3 — CDE network boundary: unauthorised flows between CDE and untrusted networks | critical | CC6.6 |
| UC-22.11.92 | PCI-DSS 2.2 — Secure configuration baseline: drift from approved hardening template | high | CC8.1 |
| UC-22.11.93 | PCI-DSS 3.3 — Sensitive authentication data: cleartext PAN/CVV detection in logs | critical | C1.1 |
| UC-22.11.95 | PCI-DSS 6.2 — Bespoke-software SDLC: code-review + SAST completion before CDE deploy | high | CC8.1 |
| UC-22.11.96 | PCI-DSS 8.3 — Strong authentication: password-only logins against privileged accounts | critical | CC6.1 |
| UC-22.11.99 | PCI-DSS 10.3 — Audit log integrity: tampering/deletion detection on CDE log source | critical | CC7.2 |
| UC-22.11.101 | PCI-DSS 10.6 — Log review: daily-review evidence for CDE data sources | high | CC7.1 |
| UC-22.11.104 | PCI-DSS 11.4 — Intrusion detection: IDS signature/health attestation + untuned alert monitoring | high | CC7.1 |
| UC-22.11.105 | PCI-DSS 12.10 — Incident response: IR readiness — playbook exercise evidence | high | CC7.4 |
| UC-22.12.36 | SOX-ITGC AccessMgmt.Provisioning — Financial-system user provisioning SLA & workflow adherence | high | CC6.2 |
| UC-22.12.37 | SOX-ITGC AccessMgmt.Termination — Deprovisioning SLA after HR termination event | critical | CC6.3 |
| UC-22.12.38 | SOX-ITGC ChangeMgmt.Testing — Financial-system change test-evidence completeness | high | CC8.1 |
| UC-22.12.39 | SOX-ITGC ChangeMgmt.Approval — Segregation of duties in financial-system change approval | critical | CC8.1 |
| UC-22.12.40 | SOX-ITGC Operations.JobSchedule — Batch-schedule monitoring: financial-job exception visibility | medium | CC7.1 |
| UC-22.35.1 | Audit-log continuity: detect indexing gap indicating lost evidence | critical | CC7.2 |
| UC-22.35.2 | Log tamper detection via write-once-read-many chain-of-custody | critical | CC7.2 |
| UC-22.35.3 | Indexer replication lag exposing evidence to single-point failure | high | A1.2 |
| UC-22.35.5 | Search-head audit-trail completeness — deleted or rewritten search jobs | high | CC7.2 |
| UC-22.40.1 | Privileged session recording — missing recordings for elevated sessions | critical | CC6.1 |
| UC-22.42.1 | Unauthorized production change — no approved CR matches the observed change | critical | CC8.1 |
| UC-22.42.3 | Change rollback execution evidence — declared rollback vs actual | medium | CC8.1 |
| UC-22.42.4 | CAB approval bypass — change pushed before scheduled window | high | CC8.1 |
| UC-22.42.5 | Infrastructure-as-code drift — applied state diverges from merged plan | high | CC8.1 |
| UC-22.45.1 | Backup restore test evidence — RPO/RTO SLA compliance per tier | critical | A1.2 |
| UC-22.47.1 | Control test freshness — evidence older than policy cadence | medium | CC5.1 |
| UC-22.47.2 | Repeat audit findings — same control deficiency across consecutive audit cycles | high | CC3.1 |
| UC-22.47.3 | Control owner attestation freshness | medium | CC1.3 |
| UC-22.47.4 | Evidence-pack drift — auditor-facing vs pre-production evidence | high | CC1.5 |
| UC-22.47.5 | Continuous control monitoring anomaly — failure-rate trending up | high | CC4.1 |
| UC-22.48.3 | Developer-to-production SoD — same developer submits AND approves merge | high | CC6.3 |
| UC-22.48.4 | Financial SoD — same identity posts AND approves a journal entry | critical | CC6.3 |

---

_This app is generated; edits in place will be overwritten.  File bug reports and content requests at https://github.com/fenre/splunk-monitoring-use-cases/issues._
