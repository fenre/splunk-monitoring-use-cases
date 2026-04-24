# Splunk Use Cases — DORA compliance

App ID: `splunk-uc-dora`  
App version: **7.1.0**  
Generated: `2026-04-22T11:55:17Z`  
Upstream catalogue: [fenre/splunk-monitoring-use-cases](https://github.com/fenre/splunk-monitoring-use-cases)


This app packages **72 use cases** from the upstream catalogue that cite EU Digital Operational Resilience Act (`dora`), together with the macros, eventtypes, tags, and lookup needed to operate them.  Every saved search is shipped **disabled by default** so an operator can review the SPL and tune indexes before enabling.

* Regulation tier: **1**
* Jurisdictions: EU
* Versions covered: Regulation (EU) 2022/2554
* UCs by criticality: critical = 18, high = 42, medium = 12


## Most-referenced clauses

| Clause | UCs tagging this clause |
|--------|-------------------------|
| `Art.5` | 14 |
| `Art.24` | 9 |
| `Art.28` | 9 |
| `Art.17` | 8 |
| `Art.12` | 7 |
| `Art.19` | 5 |
| `Art.6` | 4 |
| `Art.10` | 3 |

## Installation

1. **Review the SPL.**  Every saved search under `default/savedsearches.conf` ships disabled.  Before enabling, replace placeholder `index=` patterns with your site's indexes and macros.
2. **Install.**  Copy this directory into `$SPLUNK_HOME/etc/apps/` or package it with `tar czf splunk-uc-dora.spl splunk-uc-dora/` and deploy via the Splunk app manager.
3. **Open the compliance posture dashboard.**  The navigation lands on `dora_compliance_posture` — a Simple XML dashboard that reads the shipped `uc_compliance_mappings` lookup and works before any saved search is scheduled.  Use it to brief auditors, track clause coverage, and spot mappings with thin assurance.
4. **Enable selectively.**  In *Settings → Searches, reports, and alerts*, enable and schedule the stanzas your team is ready to operate.
5. **Audit trail.**  Every saved search carries the UC id, the regulation version, and the full clause list on its `action.uc_compliance.param.*` attributes.  These are auditor-friendly and survive Splunk's saved-search lifecycle (no lookup required).


## Compliance posture dashboard

The app ships a Simple XML dashboard at `default/data/ui/views/dora_compliance_posture.xml` that reads the per-app `uc_compliance_mappings` lookup.  The dashboard needs zero saved searches to render — install the app, open the dashboard, brief your auditor.

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
| UC-22.3.1 | DORA ICT Risk Management Dashboard | critical | Art.10, Art.11, Art.12… |
| UC-22.3.2 | DORA ICT Incident Classification and Reporting | critical | Art.17, Art.18, Art.19… |
| UC-22.3.3 | DORA Digital Operational Resilience Testing | high | Art.24, Art.25, Art.26… |
| UC-22.3.4 | DORA Third-Party ICT Provider Concentration Risk | high | Art.28, Art.29, Art.30… |
| UC-22.3.5 | DORA Cross-Region Disaster Recovery Compliance | critical | Art.11, Art.12 |
| UC-22.3.6 | DORA ICT Change Management and Patch Compliance | critical | Art.9(4)(e) |
| UC-22.3.7 | DORA ICT Anomaly Detection Capabilities | critical | Art.10 |
| UC-22.3.8 | DORA ICT Incident Response and Recovery Time Tracking | critical | Art.11 |
| UC-22.3.9 | DORA Backup Completeness and Restoration Testing | critical | Art.12 |
| UC-22.3.10 | DORA Post-Incident Review and Learning | high | Art.13 |
| UC-22.3.11 | DORA Major ICT Incident 7-Criteria Classification | critical | Art.18 |
| UC-22.3.12 | DORA ICT Incident Intermediate and Final Report Tracking | critical | Art.19 |
| UC-22.3.13 | DORA Register of Information for ICT Third-Party Arrangements | high | Art.28(3) |
| UC-22.3.14 | DORA ICT Third-Party SLA Performance Monitoring | high | Art.30 |
| UC-22.3.15 | DORA ICT Access Control and Authentication Monitoring | critical | Art.9(4)(c) |
| UC-22.3.16 | DORA Vulnerability Assessment and Penetration Test Tracking | high | Art.25 |
| UC-22.3.17 | DORA Threat-Led Penetration Testing (TLPT) Lifecycle | high | Art.26 |
| UC-22.3.18 | DORA ICT Third-Party Exit Strategy Readiness | high | Art.28(8) |
| UC-22.3.19 | DORA Management Body ICT Governance and Oversight | high | Art.5 |
| UC-22.3.20 | DORA ICT Crisis Communication Readiness | high | Art.14 |
| UC-22.3.21 | DORA ICT Concentration — Single-Provider Spend and Workload Share Thresholds | high | Art.5 |
| UC-22.3.22 | DORA ICT Concentration — Critical Service Dependency Fan-In by Provider | critical | Art.5 |
| UC-22.3.23 | DORA ICT Concentration — Regional Provider Outage Correlation Exposure Score | high | Art.17 |
| UC-22.3.24 | DORA ICT Concentration — Substitutability and Secondary Sourcing Readiness Index | medium | Art.5 |
| UC-22.3.25 | DORA TLPT — Test Planning Milestone and Scope Lock Audit Trail | high | Art.24 |
| UC-22.3.26 | DORA TLPT — Tester Independence and Conflict-of-Interest Attestation Log | high | Art.5 |
| UC-22.3.27 | DORA TLPT — Findings Severity, Remediation Owner, and Due Date Tracking | high | Art.24 |
| UC-22.3.28 | DORA TLPT — Retest and Control Effectiveness Verification Events | high | Art.24 |
| UC-22.3.29 | DORA Information Sharing — FINCERT-Style Submission Timeliness and Acknowledgment Log | high | Art.5 |
| UC-22.3.30 | DORA Information Sharing — Indicator Distribution to Subsidiaries and Branches Coverage | medium | Art.5 |
| UC-22.3.31 | DORA Information Sharing — Anonymized Incident TTP Contribution Quality Metrics | medium | Art.17 |
| UC-22.3.32 | DORA Outsourcing Registers — Sub-Processor Notification Lag vs Contractual Notice Period | high | Art.5 |
| UC-22.3.33 | DORA Outsourcing Registers — Function Mapping Completeness for Each Outsourced Arrangement | high | Art.5 |
| UC-22.3.34 | DORA Outsourcing Registers — Data Localization and Cross-Border Transfer Field Validation | critical | Art.5 |
| UC-22.3.35 | DORA Exit Strategy — Alternative Provider Shortlist Currency and RFP Readiness | high | Art.5 |
| UC-22.3.36 | DORA Exit Strategy — Data Portability Test Evidence and Export Volume Integrity | high | Art.5 |
| UC-22.3.37 | DORA Exit Strategy — Runbook Step Completion and Sign-Off SLA for Critical Providers | high | Art.5 |
| UC-22.3.38 | DORA ICT Third-Party Risk Register — Inherent vs Residual Risk Score Reconciliation | high | Art.19 |
| UC-22.3.39 | DORA ICT Third-Party Risk Register — Control Testing Evidence Freshness by Provider Tier | high | Art.24 |
| UC-22.3.40 | DORA ICT Third-Party Risk Register — Issue Density and Open Finding Trend by Provider | medium | Art.28 |
| UC-22.3.41 | DORA Art.6 — ICT risk-management framework evidence: control catalogue drift detection | high | Art.6 |
| UC-22.3.42 | DORA Art.7 — ICT systems inventory completeness: unmanaged endpoints attached to financial services | high | Art.7 |
| UC-22.3.43 | DORA Art.8 — ICT risk identification: newly discovered high-severity exposure on critical financial services | critical | Art.8 |
| UC-22.3.44 | DORA Art.17 — ICT incident classification timeliness: major-incident clock evidence | critical | Art.17 |
| UC-22.3.45 | DORA Art.24 — Digital operational-resilience testing: test-plan execution attestation | high | Art.24 |
| UC-22.6.46 | ISO/IEC 27001:2022 Clause 6.1 — Risk-assessment evidence: live risk register decay | high | Art.6 |
| UC-22.6.51 | ISO/IEC 27001:2022 Annex A.5.24 — Incident-management planning: runbook currency attestation | medium | Art.17 |
| UC-22.6.52 | ISO/IEC 27001:2022 Annex A.5.25 — Event classification decisions: SIEM-to-incident triage traceability | high | Art.17 |
| UC-22.8.32 | SOC 2 CC6.7 — System boundary & data-transmission control: unapproved egress destinations | high | Art.7 |
| UC-22.8.33 | SOC 2 CC7.1 — System-operations monitoring: uptime attestation and alert-noise governance | high | Art.10 |
| UC-22.8.34 | SOC 2 CC7.3 — Evaluated events: threshold breaches without documented rationale | medium | Art.17 |
| UC-22.8.35 | SOC 2 CC7.4 — Incident response: post-incident review completion SLA | high | Art.17 |
| UC-22.8.37 | SOC 2 CC9.1 — Risk-mitigation activity: vendor-risk action closure SLA | medium | Art.28 |
| UC-22.11.97 | PCI-DSS 8.4 — MFA coverage: administrative access to CDE without MFA | critical | Art.9 |
| UC-22.11.103 | PCI-DSS 11.3 — Vulnerability programme: overdue scan cadence and unremediated high-severity | high | Art.8 |
| UC-22.11.105 | PCI-DSS 12.10 — Incident response: IR readiness — playbook exercise evidence | high | Art.24 |
| UC-22.11.106 | PCI-DSS 12.3 — Targeted risk analysis: frequency adherence for per-requirement TRAs | medium | Art.6 |
| UC-22.35.3 | Indexer replication lag exposing evidence to single-point failure | high | Art.12 |
| UC-22.38.3 | Data localization enforcement — regulated-data must-stay-in-region | high | Art.28 |
| UC-22.38.5 | Bulk regulated-data export targeting non-adequate jurisdiction | critical | Art.28 |
| UC-22.39.1 | Multi-regulator breach-notification SLA tracker (24h NIS2 / 72h GDPR / 72h HIPAA) | critical | Art.19 |
| UC-22.39.4 | Cross-regulator consistency — divergent material facts across submissions | high | Art.19 |
| UC-22.41.3 | Key rotation attestation — KMS/HSM rotation SLA tracker | high | Art.9 |
| UC-22.44.1 | Supplier attestation currency — stale SOC 2 / ISO 27001 reports for critical vendors | high | Art.28 |
| UC-22.44.2 | Subprocessor inventory change — notification SLA to data controllers | high | Art.28 |
| UC-22.44.3 | Fourth-party concentration risk — shared critical dependencies across vendors | medium | Art.28 |
| UC-22.44.4 | Vendor access telemetry — principals active outside contracted hours/geos | high | Art.28 |
| UC-22.45.1 | Backup restore test evidence — RPO/RTO SLA compliance per tier | critical | Art.12 |
| UC-22.45.3 | Backup completeness — unprotected workloads with regulated data | high | Art.12 |
| UC-22.45.4 | Backup repository TLS posture — aged or weak-cipher endpoints | medium | Art.12 |
| UC-22.45.5 | Business-continuity rehearsal evidence — BCP/DR exercise execution logged | medium | Art.24 |
| UC-22.46.4 | Tabletop rehearsal evidence — IR plan exercise frequency | medium | Art.24 |

---

_This app is generated; edits in place will be overwritten.  File bug reports and content requests at https://github.com/fenre/splunk-monitoring-use-cases/issues._
