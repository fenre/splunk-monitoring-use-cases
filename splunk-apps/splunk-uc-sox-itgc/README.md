# Splunk Use Cases — SOX ITGC compliance

App ID: `splunk-uc-sox-itgc`  
App version: **6.0.0**  
Generated: `2026-04-17T16:48:56Z`  
Upstream catalogue: [fenre/splunk-monitoring-use-cases](https://github.com/fenre/splunk-monitoring-use-cases)


This app packages **71 use cases** from the upstream catalogue that cite SOX — PCAOB AS 2201 ITGCs (`sox-itgc`), together with the macros, eventtypes, tags, and lookup needed to operate them.  Every saved search is shipped **disabled by default** so an operator can review the SPL and tune indexes before enabling.

* Regulation tier: **1**
* Jurisdictions: US
* Versions covered: PCAOB AS 2201
* UCs by criticality: critical = 23, high = 21, low = 9, medium = 12, unspecified = 6


## Most-referenced clauses

| Clause | UCs tagging this clause |
|--------|-------------------------|
| `SOX ITGC` | 8 |
| `SOX §404` | 6 |
| `ITGC.AccessMgmt.Privileged` | 4 |
| `ITGC.ChangeMgmt.Approval` | 3 |
| `ITGC.ChangeMgmt.Authorization` | 3 |
| `ITGC.Logging.Continuity` | 3 |
| `ITGC.Logging.Integrity` | 3 |
| `SOX close` | 3 |

## Installation

1. **Review the SPL.**  Every saved search under `default/savedsearches.conf` ships disabled.  Before enabling, replace placeholder `index=` patterns with your site's indexes and macros.
2. **Install.**  Copy this directory into `$SPLUNK_HOME/etc/apps/` or package it with `tar czf splunk-uc-sox-itgc.spl splunk-uc-sox-itgc/` and deploy via the Splunk app manager.
3. **Open the compliance posture dashboard.**  The navigation lands on `sox_itgc_compliance_posture` — a Simple XML dashboard that reads the shipped `uc_compliance_mappings` lookup and works before any saved search is scheduled.  Use it to brief auditors, track clause coverage, and spot mappings with thin assurance.
4. **Enable selectively.**  In *Settings → Searches, reports, and alerts*, enable and schedule the stanzas your team is ready to operate.
5. **Audit trail.**  Every saved search carries the UC id, the regulation version, and the full clause list on its `action.uc_compliance.param.*` attributes.  These are auditor-friendly and survive Splunk's saved-search lifecycle (no lookup required).


## Compliance posture dashboard

The app ships a Simple XML dashboard at `default/data/ui/views/sox_itgc_compliance_posture.xml` that reads the per-app `uc_compliance_mappings` lookup.  The dashboard needs zero saved searches to render — install the app, open the dashboard, brief your auditor.

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
| UC-7.1.13 | Schema Change Detection |  | ITGC.ChangeMgmt.Authorization |
| UC-7.1.21 | Database User and Privilege Change Audit |  | ITGC.AccessMgmt.Privileged |
| UC-7.1.40 | Database Audit Log Tampering Detection |  | ITGC.Logging.Continuity |
| UC-9.5.15 | Okta User Lifecycle Events (Provisioning / Deprovisioning) |  | ITGC.AccessMgmt.Provisioning |
| UC-12.2.17 | Deploy Approval Bypass Detection |  | ITGC.ChangeMgmt.Approval |
| UC-16.4.1 | Unauthorized Change Detection |  | ITGC.ChangeMgmt.Authorization |
| UC-22.6.55 | ISO/IEC 27001:2022 Clause 8.1 — Operational planning: change advisory board (CAB) approval evidence | medium | ITGC.ChangeMgmt.Approval |
| UC-22.11.95 | PCI-DSS 6.2 — Bespoke-software SDLC: code-review + SAST completion before CDE deploy | high | ITGC.ChangeMgmt.Testing |
| UC-22.11.99 | PCI-DSS 10.3 — Audit log integrity: tampering/deletion detection on CDE log source | critical | ITGC.Logging.Integrity |
| UC-22.11.102 | PCI-DSS 10.7 — Log retention: CDE data-source retention + immutability attestation | high | ITGC.Logging.Integrity |
| UC-22.12.1 | User provisioning evidence tied to financial application accounts | high | COSO |
| UC-22.12.2 | Privileged access review completion and aging for financial systems | medium | SOX §404 |
| UC-22.12.3 | Segregation of duties conflicts across SAP / Oracle financial roles | low | SOX §404 |
| UC-22.12.4 | Administrator and break-glass usage on production financial hosts | critical | SOX §404 |
| UC-22.12.5 | Terminated-user authentication after HR termination date | high | SOX §404 |
| UC-22.12.6 | Periodic access certification exceptions for in-scope applications | medium | SOX §404 |
| UC-22.12.7 | Orphaned and dormant accounts with recent interactive activity | low | SOX §404 |
| UC-22.12.8 | Emergency change retrospective documentation completeness | critical | SOX ITGC |
| UC-22.12.9 | Production configuration drift without matching approved change | high | SOX ITGC |
| UC-22.12.10 | Change approval workflow evidence for financially material CIs | medium | SOX ITGC |
| UC-22.12.11 | CAB evidence and high-risk change documentation gaps | low | SOX ITGC |
| UC-22.12.12 | Production change volume during financial close windows | critical | SOX close |
| UC-22.12.13 | Failed change rollback and backout evidence tracking | high | SOX ITGC |
| UC-22.12.14 | Changes executed outside approved maintenance windows | medium | SOX ITGC |
| UC-22.12.15 | Financial close batch job failures and runtime SLA breaches | low | SOX close |
| UC-22.12.16 | General ledger database backup success within policy windows | critical | SOX ITGC |
| UC-22.12.17 | Unauthorized batch schedule or dependency modifications | high | SOX ITGC |
| UC-22.12.18 | ITSI service health for financial reporting dependency chain | medium | SOX availability |
| UC-22.12.19 | Close-processing cluster CPU saturation during peak windows | low | SOX performance |
| UC-22.12.20 | Disaster recovery test execution and evidence correlation | critical | SOX DR |
| UC-22.12.21 | Priority incident aging for finance-critical configuration items | high | SOX operations |
| UC-22.12.22 | Financial close checklist task completion by owner | medium | SOX close |
| UC-22.12.23 | After-hours and high-value journal entry concentration | low | SOX JE |
| UC-22.12.24 | Sequential ERP document number gap detection | critical | SOX audit trail |
| UC-22.12.25 | Duplicate disbursement pattern detection in AP subledger | high | SOX cash |
| UC-22.12.26 | Sensitive management financial report access and export | medium | SOX reporting |
| UC-22.12.27 | Subledger-to-general-ledger reconciliation variance monitoring | low | SOX reconciliation |
| UC-22.12.28 | Quarterly privileged ERP role population for sign-off | critical | SOX access |
| UC-22.12.29 | IT control testing sample evidence retrieval by control ID | high | SOX testing |
| UC-22.12.30 | Open IT control exception aging and escalation tiers | medium | SOX exceptions |
| UC-22.12.31 | Audit finding remediation milestone and due-date risk | low | SOX remediation |
| UC-22.12.32 | External audit IT finding closure and retest documentation | critical | SOX audit |
| UC-22.12.33 | IT control self-assessment questionnaire completion rates | high | SOX CSA |
| UC-22.12.34 | IT risk register residual score movement for financial reporting risks | medium | SOX risk |
| UC-22.12.35 | Monthly ITGC KPI pack for management review evidence | low | SOX management review |
| UC-22.12.36 | SOX-ITGC AccessMgmt.Provisioning — Financial-system user provisioning SLA & workflow adherence | high | ITGC.AccessMgmt.Provisioning |
| UC-22.12.37 | SOX-ITGC AccessMgmt.Termination — Deprovisioning SLA after HR termination event | critical | ITGC.AccessMgmt.Termination |
| UC-22.12.38 | SOX-ITGC ChangeMgmt.Testing — Financial-system change test-evidence completeness | high | ITGC.ChangeMgmt.Testing |
| UC-22.12.39 | SOX-ITGC ChangeMgmt.Approval — Segregation of duties in financial-system change approval | critical | ITGC.ChangeMgmt.Approval |
| UC-22.12.40 | SOX-ITGC Operations.JobSchedule — Batch-schedule monitoring: financial-job exception visibility | medium | ITGC.Operations.JobSchedule |
| UC-22.35.1 | Audit-log continuity: detect indexing gap indicating lost evidence | critical | ITGC.Logging.Continuity |
| UC-22.35.2 | Log tamper detection via write-once-read-many chain-of-custody | critical | ITGC.Logging.Continuity |
| UC-22.35.4 | Log signing chain integrity — cryptographic signature drift on evidence archive | critical | ITGC.Logging.Integrity |
| UC-22.40.1 | Privileged session recording — missing recordings for elevated sessions | critical | ITGC.AccessMgmt.Privileged |
| UC-22.40.2 | Break-glass account usage review with mandatory post-use approval | critical | ITGC.AccessMgmt.Privileged |
| UC-22.40.3 | Periodic access review SLA — stale certifications by control owner | high | ITGC.AccessMgmt.Review |
| UC-22.40.4 | Standing-privilege credential vaulting drift — admin accounts outside PAM | critical | ITGC.AccessMgmt.Privileged |
| UC-22.40.5 | High-risk privileged-session command without JIT approval | critical | ITGC.Privileged.JIT |
| UC-22.41.5 | Key custodian SoD — same identity creates AND approves a key | high | ITGC.Crypto.SoD |
| UC-22.42.1 | Unauthorized production change — no approved CR matches the observed change | critical | ITGC.ChangeMgmt.Authorization |
| UC-22.42.3 | Change rollback execution evidence — declared rollback vs actual | medium | ITGC.Change.Rollback |
| UC-22.42.4 | CAB approval bypass — change pushed before scheduled window | high | ITGC.Change.Approval |
| UC-22.45.3 | Backup completeness — unprotected workloads with regulated data | high | ITGC.Operations.Backup |
| UC-22.47.2 | Repeat audit findings — same control deficiency across consecutive audit cycles | high | ITGC.Logging.Review |
| UC-22.47.4 | Evidence-pack drift — auditor-facing vs pre-production evidence | high | ITGC.Evidence.Integrity |
| UC-22.48.1 | Segregation of duties — toxic role combinations in IAM | critical | ITGC.AccessMgmt.SOD |
| UC-22.48.2 | SoD violations via break-glass usage — emergency role abuse | critical | ITGC.AccessMgmt.SOD |
| UC-22.48.3 | Developer-to-production SoD — same developer submits AND approves merge | high | ITGC.Change.SoD |
| UC-22.48.4 | Financial SoD — same identity posts AND approves a journal entry | critical | ITGC.Financial.SoD |
| UC-22.48.5 | Vendor-master SoD — same identity creates vendor AND approves payment | critical | ITGC.Vendor.SoD |
| UC-22.49.3 | Litigation-hold override audit — holds applied/released without ticket | high | ITGC.Logging.Review |

---

_This app is generated; edits in place will be overwritten.  File bug reports and content requests at https://github.com/fenre/splunk-monitoring-use-cases/issues._
