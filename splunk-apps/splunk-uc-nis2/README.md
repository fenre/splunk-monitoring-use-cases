# Splunk Use Cases — NIS2 compliance

App ID: `splunk-uc-nis2`  
App version: **6.1.0**  
Generated: `2026-04-18T17:28:10Z`  
Upstream catalogue: [fenre/splunk-monitoring-use-cases](https://github.com/fenre/splunk-monitoring-use-cases)


This app packages **63 use cases** from the upstream catalogue that cite EU NIS2 Directive (`nis2`), together with the macros, eventtypes, tags, and lookup needed to operate them.  Every saved search is shipped **disabled by default** so an operator can review the SPL and tune indexes before enabling.

* Regulation tier: **1**
* Jurisdictions: EU
* Versions covered: Directive (EU) 2022/2555
* UCs by criticality: critical = 23, high = 34, medium = 6


## Most-referenced clauses

| Clause | UCs tagging this clause |
|--------|-------------------------|
| `Art.21(2)(d)` | 8 |
| `Art.23` | 7 |
| `Art.21(2)(e)` | 6 |
| `Art.21(2)(a)` | 5 |
| `Art.21(2)(c)` | 5 |
| `Art.21(2)(g)` | 4 |
| `Art.21(2)(i)` | 4 |
| `Art.20` | 3 |

## Installation

1. **Review the SPL.**  Every saved search under `default/savedsearches.conf` ships disabled.  Before enabling, replace placeholder `index=` patterns with your site's indexes and macros.
2. **Install.**  Copy this directory into `$SPLUNK_HOME/etc/apps/` or package it with `tar czf splunk-uc-nis2.spl splunk-uc-nis2/` and deploy via the Splunk app manager.
3. **Open the compliance posture dashboard.**  The navigation lands on `nis2_compliance_posture` — a Simple XML dashboard that reads the shipped `uc_compliance_mappings` lookup and works before any saved search is scheduled.  Use it to brief auditors, track clause coverage, and spot mappings with thin assurance.
4. **Enable selectively.**  In *Settings → Searches, reports, and alerts*, enable and schedule the stanzas your team is ready to operate.
5. **Audit trail.**  Every saved search carries the UC id, the regulation version, and the full clause list on its `action.uc_compliance.param.*` attributes.  These are auditor-friendly and survive Splunk's saved-search lifecycle (no lookup required).


## Compliance posture dashboard

The app ships a Simple XML dashboard at `default/data/ui/views/nis2_compliance_posture.xml` that reads the per-app `uc_compliance_mappings` lookup.  The dashboard needs zero saved searches to render — install the app, open the dashboard, brief your auditor.

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
| UC-22.2.1 | NIS2 Incident Detection and 24-Hour Early Warning Reporting | critical | Art.23 |
| UC-22.2.2 | NIS2 Supply Chain Security Monitoring | high | Art.21(2)(d) |
| UC-22.2.3 | NIS2 Vulnerability Disclosure and Patch Management Tracking | critical | Art.21(2)(e) |
| UC-22.2.4 | NIS2 Business Continuity and Crisis Management Monitoring | critical | Art.21(2)(c) |
| UC-22.2.5 | NIS2 Network and Information Systems Access Control Audit | critical | Art.21(2)(i) |
| UC-22.2.6 | NIS2 Risk Analysis and Information System Security Policy Evidence | critical | Art.21(2)(a) |
| UC-22.2.7 | NIS2 72-Hour Incident Notification Readiness | critical | Art.23(2) |
| UC-22.2.8 | NIS2 One-Month Final Incident Report Tracking | high | Art.23(4) |
| UC-22.2.9 | NIS2 Effectiveness Assessment of Cybersecurity Measures | high | Art.21(2)(f) |
| UC-22.2.10 | NIS2 Cyber Hygiene and Training Compliance | medium | Art.21(2)(g) |
| UC-22.2.11 | NIS2 Cryptography and Encryption Policy Monitoring | high | Art.21(2)(h) |
| UC-22.2.12 | NIS2 Multi-Factor Authentication and Secure Communications | critical | Art.21(2)(j) |
| UC-22.2.13 | NIS2 Asset Management and Configuration Baseline | high | Art.21(2)(i) |
| UC-22.2.14 | NIS2 Human Resources Security — Joiner/Mover/Leaver Process | high | Art.21(2)(i) |
| UC-22.2.15 | NIS2 Secure System Acquisition and Development Lifecycle | high | Art.21(2)(e) |
| UC-22.2.16 | NIS2 Supply Chain Third-Party Risk Continuous Monitoring | high | Art.21(2)(d) |
| UC-22.2.17 | NIS2 Backup Management and Disaster Recovery Verification | critical | Art.21(2)(c) |
| UC-22.2.18 | NIS2 Network Security Monitoring and Anomaly Detection | critical | Art.21(2)(a) |
| UC-22.2.19 | NIS2 Cross-Border Incident Impact Assessment | high | Art.23(3) |
| UC-22.2.20 | NIS2 Management Body Accountability and Governance Evidence | high | Art.20 |
| UC-22.2.21 | NIS2 Risk Analysis Evidence for Essential Entities | critical | Art.21(2) |
| UC-22.2.22 | NIS2 Risk Analysis Evidence for Important Entities | high | Art.21(2) |
| UC-22.2.23 | NIS2 Incident Handling Procedure Adherence and Playbook Execution | critical | Art.21(2)(b) |
| UC-22.2.24 | NIS2 Business Continuity and ICT Continuity Evidence | critical | Art.21(2)(c) |
| UC-22.2.25 | NIS2 Supply Chain Security Assessment Coverage | high | Art.21(2)(d) |
| UC-22.2.26 | NIS2 Network Security Monitoring Coverage by Segment | critical | Art.21(2)(a) |
| UC-22.2.27 | NIS2 Vulnerability Disclosure Policy Operational Signals | high | Art.21(2)(e) |
| UC-22.2.28 | NIS2 Cyber Hygiene Practices — Baseline Control Compliance | high | Art.21(2)(g) |
| UC-22.2.29 | NIS2 Cryptography Policy Compliance — TLS and Certificate Posture | high | Art.21(2)(h) |
| UC-22.2.30 | NIS2 Human Resources Security Measures Evidence | high | Art.21(2)(i) |
| UC-22.2.31 | NIS2 Entity Classification Validation (Essential vs Important) | high | Art.2(1) |
| UC-22.2.32 | NIS2 Proportional Security Measure Verification by Tier | high | Art.21(2) |
| UC-22.2.33 | NIS2 Incident Reporting Timeline Compliance (24h Early Warning / 72h Notification) | critical | Art.23 |
| UC-22.2.34 | NIS2 Cross-Border Incident Coordination Task Tracking | high | Art.23(3) |
| UC-22.2.35 | NIS2 Supervisory Compliance Evidence Pack Readiness | high | Art.32, Art.33 |
| UC-22.2.36 | NIS2 OT Network Segmentation Validation | critical | Art.21(2)(a) |
| UC-22.2.37 | NIS2 SCADA System Access Monitoring | critical | Art.21(2)(a) |
| UC-22.2.38 | NIS2 Industrial Control System Patching and Change Evidence | high | Art.21(2)(e) |
| UC-22.2.39 | NIS2 OT Incident Detection — Process and Protocol Anomalies | critical | Art.21(2)(f) |
| UC-22.2.40 | NIS2 Safety System Integrity Monitoring (SIL / SIS Interlocks) | critical | Art.21(2)(c) |
| UC-22.2.41 | NIS2 Management Body Cybersecurity Training Evidence | high | Art.20 |
| UC-22.2.42 | NIS2 Board-Level Cyber Risk Reporting Distribution Audit | high | Art.20 |
| UC-22.2.43 | NIS2 Annual Security Assessment Completion Tracking | high | Art.21(2)(f) |
| UC-22.2.44 | NIS2 Cooperation Group and Sector Information Sharing Participation | high | Art.14 |
| UC-22.2.45 | NIS2 CSIRT Notification Compliance and Channel Health | critical | Art.23 |
| UC-22.3.42 | DORA Art.7 — ICT systems inventory completeness: unmanaged endpoints attached to financial services | high | Art.21(2)(d) |
| UC-22.3.44 | DORA Art.17 — ICT incident classification timeliness: major-incident clock evidence | critical | Art.23 |
| UC-22.9.4 | Regulatory Incident Response Time Trending | medium | Art.23 |
| UC-22.39.1 | Multi-regulator breach-notification SLA tracker (24h NIS2 / 72h GDPR / 72h HIPAA) | critical | Art.23 |
| UC-22.39.2 | Regulator-portal submission evidence — one-way API acknowledgement audit | high | Art.23 |
| UC-22.39.4 | Cross-regulator consistency — divergent material facts across submissions | high | Art.23(4) |
| UC-22.39.5 | Regulator-portal authentication failure during submission window | high | Art.23(1) |
| UC-22.41.2 | Certificate / TLS posture — weak cipher and expired-cert detection | high | Art.21(2)(h) |
| UC-22.43.1 | Critical vulnerability SLA tracker — unpatched 30+ days with exploited-in-the-wild indicator | critical | Art.21(2)(e) |
| UC-22.43.3 | Internet-facing asset × unpatched critical CVE | critical | Art.21(2)(e) |
| UC-22.43.5 | SBOM vendor-component CVE exposure | high | Art.21(2)(d) |
| UC-22.44.1 | Supplier attestation currency — stale SOC 2 / ISO 27001 reports for critical vendors | high | Art.21(2)(d) |
| UC-22.44.4 | Vendor access telemetry — principals active outside contracted hours/geos | high | Art.21(2)(d) |
| UC-22.44.5 | SBOM attestation completeness — critical vendors without signed SBOM | high | Art.21(2)(d) |
| UC-22.45.5 | Business-continuity rehearsal evidence — BCP/DR exercise execution logged | medium | Art.21(2)(c) |
| UC-22.46.1 | Mandatory security training — completion SLA by role | medium | Art.21(2)(g) |
| UC-22.46.2 | Phishing simulation efficacy — click-rate trend and repeat-clicker detection | medium | Art.21(2)(g) |
| UC-22.46.4 | Tabletop rehearsal evidence — IR plan exercise frequency | medium | Art.21(2)(b) |

---

_This app is generated; edits in place will be overwritten.  File bug reports and content requests at https://github.com/fenre/splunk-monitoring-use-cases/issues._
