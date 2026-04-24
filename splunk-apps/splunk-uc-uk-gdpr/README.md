# Splunk Use Cases — UK GDPR compliance

App ID: `splunk-uc-uk-gdpr`  
App version: **7.1.0**  
Generated: `2026-04-22T11:55:17Z`  
Upstream catalogue: [fenre/splunk-monitoring-use-cases](https://github.com/fenre/splunk-monitoring-use-cases)


This app packages **31 use cases** from the upstream catalogue that cite UK General Data Protection Regulation (`uk-gdpr`), together with the macros, eventtypes, tags, and lookup needed to operate them.  Every saved search is shipped **disabled by default** so an operator can review the SPL and tune indexes before enabling.

* Regulation tier: **2**
* Jurisdictions: UK
* Versions covered: post-Brexit
* UCs by criticality: critical = 9, high = 18, medium = 4


## Most-referenced clauses

| Clause | UCs tagging this clause |
|--------|-------------------------|
| `Art.46` | 4 |
| `Art.32` | 3 |
| `Art.44` | 3 |
| `Art.7` | 3 |
| `Art.17` | 2 |
| `Art.32(1)(b)` | 2 |
| `Art.33` | 2 |
| `Art.45` | 2 |

## Installation

1. **Review the SPL.**  Every saved search under `default/savedsearches.conf` ships disabled.  Before enabling, replace placeholder `index=` patterns with your site's indexes and macros.
2. **Install.**  Copy this directory into `$SPLUNK_HOME/etc/apps/` or package it with `tar czf splunk-uc-uk-gdpr.spl splunk-uc-uk-gdpr/` and deploy via the Splunk app manager.
3. **Open the compliance posture dashboard.**  The navigation lands on `uk_gdpr_compliance_posture` — a Simple XML dashboard that reads the shipped `uc_compliance_mappings` lookup and works before any saved search is scheduled.  Use it to brief auditors, track clause coverage, and spot mappings with thin assurance.
4. **Enable selectively.**  In *Settings → Searches, reports, and alerts*, enable and schedule the stanzas your team is ready to operate.
5. **Audit trail.**  Every saved search carries the UC id, the regulation version, and the full clause list on its `action.uc_compliance.param.*` attributes.  These are auditor-friendly and survive Splunk's saved-search lifecycle (no lookup required).


## Compliance posture dashboard

The app ships a Simple XML dashboard at `default/data/ui/views/uk_gdpr_compliance_posture.xml` that reads the per-app `uc_compliance_mappings` lookup.  The dashboard needs zero saved searches to render — install the app, open the dashboard, brief your auditor.

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
| UC-22.1.16 | GDPR Consent Withdrawal Processing Enforcement | high | Art.18 |
| UC-22.1.46 | GDPR Consent Mechanism Audit (Lawful Basis Alignment) | high | Art.21 |
| UC-22.8.39 | SOC 2 P1.1 — Privacy notice: consent-record freshness for privacy-notice version changes | medium | Art.7 |
| UC-22.35.1 | Audit-log continuity: detect indexing gap indicating lost evidence | critical | Art.32(1)(b) |
| UC-22.35.2 | Log tamper detection via write-once-read-many chain-of-custody | critical | Art.32 |
| UC-22.35.3 | Indexer replication lag exposing evidence to single-point failure | high | Art.32 |
| UC-22.35.4 | Log signing chain integrity — cryptographic signature drift on evidence archive | critical | Art.32(1)(b) |
| UC-22.36.1 | DSAR fulfillment SLA tracker with verification evidence trail | high | Art.12, Art.15 |
| UC-22.36.2 | Right-to-erasure propagation completeness across downstream systems | critical | Art.17, Art.17(2) |
| UC-22.36.3 | Portability export integrity — signed manifest verification | medium | Art.20 |
| UC-22.36.4 | DSAR identity-verification friction — failed-verification anomaly | high | Art.12(6) |
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
| UC-22.41.1 | Encryption-at-rest coverage gap — unencrypted storage with regulated data | critical | Art.32 |
| UC-22.44.2 | Subprocessor inventory change — notification SLA to data controllers | high | Art.28 |
| UC-22.46.5 | Developer data-handling training — prod-access engineers lacking training | high | Art.32(4) |
| UC-22.49.1 | Retention execution evidence — records past retention still present | high | Art.5 |
| UC-22.49.2 | Disposal workflow completion — failed disposals requiring manual review | high | Art.5 |
| UC-22.49.4 | Retention policy drift — system config vs policy catalogue | high | Art.5(1)(e) |
| UC-22.49.5 | Cryptographic erasure attestation — per-asset destruction evidence | high | Art.17 |

---

_This app is generated; edits in place will be overwritten.  File bug reports and content requests at https://github.com/fenre/splunk-monitoring-use-cases/issues._
