---
id: "9.4.9"
title: "Cross-Domain Trust Change Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.4.9 · Cross-Domain Trust Change Detection

## Description

Trust relationship changes can enable cross-domain abuse. Early detection prevents privilege escalation across forests.

## Value

Trust relationship changes can enable cross-domain abuse. Early detection prevents privilege escalation across forests.

## Implementation

Forward DC Security logs. Alert on any trust creation or modification. Require change approval for trust changes. Report on trust topology for audit.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: Security Event Log (4706 — trust modified, 4714 — trust created).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward DC Security logs. Alert on any trust creation or modification. Require change approval for trust changes. Report on trust topology for audit.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4706, 4714)
| table _time, SubjectUserName, TargetDomainName, TrustType, TrustDirection
| sort -_time
```

Understanding this SPL

**Cross-Domain Trust Change Detection** — Trust relationship changes can enable cross-domain abuse. Early detection prevents privilege escalation across forests.

Documented **Data sources**: Security Event Log (4706 — trust modified, 4714 — trust created). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Cross-Domain Trust Change Detection**): table _time, SubjectUserName, TargetDomainName, TrustType, TrustDirection
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

Understanding this CIM / accelerated SPL

**Cross-Domain Trust Change Detection** — Trust relationship changes can enable cross-domain abuse. Early detection prevents privilege escalation across forests.

Documented **Data sources**: Security Event Log (4706 — trust modified, 4714 — trust created). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (trust changes), Timeline (events), Single value (changes this week).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4706, 4714)
| table _time, SubjectUserName, TargetDomainName, TrustType, TrustDirection
| sort -_time
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

## Visualization

Table (trust changes), Timeline (events), Single value (changes this week).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
