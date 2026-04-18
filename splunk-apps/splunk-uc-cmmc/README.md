# Splunk Use Cases — CMMC compliance

App ID: `splunk-uc-cmmc`  
App version: **6.1.0**  
Generated: `2026-04-18T08:01:30Z`  
Upstream catalogue: [fenre/splunk-monitoring-use-cases](https://github.com/fenre/splunk-monitoring-use-cases)


This app packages **25 use cases** from the upstream catalogue that cite Cybersecurity Maturity Model Certification (`cmmc`), together with the macros, eventtypes, tags, and lookup needed to operate them.  Every saved search is shipped **disabled by default** so an operator can review the SPL and tune indexes before enabling.

* Regulation tier: **1**
* Jurisdictions: US
* Versions covered: 2.0
* UCs by criticality: critical = 7, high = 6, low = 6, medium = 6


## Most-referenced clauses

| Clause | UCs tagging this clause |
|--------|-------------------------|
| `CM MC 2.0 Level 2` | 10 |
| `CM MC` | 5 |
| `CM MC 2.0 Assessment` | 5 |
| `CM MC 2.0 Level 3` | 5 |
| `AC.L2-3.1.1` | 1 |
| `AC.L2-3.1.5` | 1 |
| `AU.L2-3.3.1` | 1 |
| `AU.L2-3.3.2` | 1 |

## Installation

1. **Review the SPL.**  Every saved search under `default/savedsearches.conf` ships disabled.  Before enabling, replace placeholder `index=` patterns with your site's indexes and macros.
2. **Install.**  Copy this directory into `$SPLUNK_HOME/etc/apps/` or package it with `tar czf splunk-uc-cmmc.spl splunk-uc-cmmc/` and deploy via the Splunk app manager.
3. **Open the compliance posture dashboard.**  The navigation lands on `cmmc_compliance_posture` — a Simple XML dashboard that reads the shipped `uc_compliance_mappings` lookup and works before any saved search is scheduled.  Use it to brief auditors, track clause coverage, and spot mappings with thin assurance.
4. **Enable selectively.**  In *Settings → Searches, reports, and alerts*, enable and schedule the stanzas your team is ready to operate.
5. **Audit trail.**  Every saved search carries the UC id, the regulation version, and the full clause list on its `action.uc_compliance.param.*` attributes.  These are auditor-friendly and survive Splunk's saved-search lifecycle (no lookup required).


## Compliance posture dashboard

The app ships a Simple XML dashboard at `default/data/ui/views/cmmc_compliance_posture.xml` that reads the per-app `uc_compliance_mappings` lookup.  The dashboard needs zero saved searches to render — install the app, open the dashboard, brief your auditor.

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
| UC-22.20.1 | CMMC Level 2 practice evidence — CUI control area 1 | high | AC.L2-3.1.1, CM MC 2.0 Level 2 |
| UC-22.20.2 | CMMC Level 2 practice evidence — CUI control area 2 | medium | AC.L2-3.1.5, CM MC 2.0 Level 2 |
| UC-22.20.3 | CMMC Level 2 practice evidence — CUI control area 3 | low | AU.L2-3.3.1, CM MC 2.0 Level 2 |
| UC-22.20.4 | CMMC Level 2 practice evidence — CUI control area 4 | critical | AU.L2-3.3.2, CM MC 2.0 Level 2 |
| UC-22.20.5 | CMMC Level 2 practice evidence — CUI control area 5 | high | AU.L2-3.3.5, CM MC 2.0 Level 2 |
| UC-22.20.6 | CMMC Level 2 practice evidence — CUI control area 6 | medium | CM MC 2.0 Level 2, CM.L2-3.4.1 |
| UC-22.20.7 | CMMC Level 2 practice evidence — CUI control area 7 | low | CM MC 2.0 Level 2, IR.L2-3.6.1 |
| UC-22.20.8 | CMMC Level 2 practice evidence — CUI control area 8 | critical | CM MC 2.0 Level 2, SC.L2-3.13.8 |
| UC-22.20.9 | CMMC Level 2 practice evidence — CUI control area 9 | high | CM MC 2.0 Level 2, SI.L2-3.14.6 |
| UC-22.20.10 | CMMC Level 2 practice evidence — CUI control area 10 | medium | CM MC 2.0 Level 2 |
| UC-22.20.11 | CMMC Level 3 enhanced practice — threat scenario 1 | low | CM MC 2.0 Level 3 |
| UC-22.20.12 | CMMC Level 3 enhanced practice — threat scenario 2 | critical | CM MC 2.0 Level 3 |
| UC-22.20.13 | CMMC Level 3 enhanced practice — threat scenario 3 | high | CM MC 2.0 Level 3 |
| UC-22.20.14 | CMMC Level 3 enhanced practice — threat scenario 4 | medium | CM MC 2.0 Level 3 |
| UC-22.20.15 | CMMC Level 3 enhanced practice — threat scenario 5 | low | CM MC 2.0 Level 3 |
| UC-22.20.16 | CMMC assessment readiness — artifact 1 | critical | CM MC 2.0 Assessment |
| UC-22.20.17 | CMMC assessment readiness — artifact 2 | high | CM MC 2.0 Assessment |
| UC-22.20.18 | CMMC assessment readiness — artifact 3 | medium | CM MC 2.0 Assessment |
| UC-22.20.19 | CMMC assessment readiness — artifact 4 | low | CM MC 2.0 Assessment |
| UC-22.20.20 | CMMC assessment readiness — artifact 5 | critical | CM MC 2.0 Assessment |
| UC-22.32.17 | Controlled unclassified information access control | critical | CM MC |
| UC-22.32.18 | CMMC practice implementation evidence collection | medium | CM MC |
| UC-22.32.19 | CMMC assessment readiness scoring | low | CM MC |
| UC-22.32.20 | CUI incident response evidence | critical | CM MC |
| UC-22.32.21 | Continuous monitoring for CMMC practice families | high | CM MC |

---

_This app is generated; edits in place will be overwritten.  File bug reports and content requests at https://github.com/fenre/splunk-monitoring-use-cases/issues._
