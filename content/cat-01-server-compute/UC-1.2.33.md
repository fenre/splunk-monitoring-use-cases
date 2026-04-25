<!-- AUTO-GENERATED from UC-1.2.33.json — DO NOT EDIT -->

---
id: "1.2.33"
title: "Audit Policy Changes"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.33 · Audit Policy Changes

## Description

Attackers modify audit policies to disable logging and hide their activities. Any unauthorized audit policy change must be investigated immediately.

## Value

Weaker auditing means blind spots in IR—seeing who changed it is a governance must.

## Implementation

EventCode 4719 fires when an audit policy is changed via `auditpol.exe` or Group Policy. Any change outside planned GPO updates is suspicious. Alert with critical priority. Pay special attention to "Success removed" or "Failure removed" changes that reduce auditing coverage. Correlate with GPO change events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 4719).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
EventCode 4719 fires when an audit policy is changed via `auditpol.exe` or Group Policy. Any change outside planned GPO updates is suspicious. Alert with critical priority. Pay special attention to "Success removed" or "Failure removed" changes that reduce auditing coverage. Correlate with GPO change events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4719
| table _time, host, SubjectUserName, SubjectDomainName, CategoryId, SubcategoryGuid, AuditPolicyChanges
| sort -_time
```

Understanding this SPL

**Audit Policy Changes** — Attackers modify audit policies to disable logging and hide their activities. Any unauthorized audit policy change must be investigated immediately.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4719). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Audit Policy Changes**): table _time, host, SubjectUserName, SubjectDomainName, CategoryId, SubcategoryGuid, AuditPolicyChanges
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

**Audit Policy Changes** — Attackers modify audit policies to disable logging and hide their activities. Any unauthorized audit policy change must be investigated immediately.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4719). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (policy changes with user context), Timeline, Single value (count — target: 0 outside maintenance).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4719
| table _time, host, SubjectUserName, SubjectDomainName, CategoryId, SubcategoryGuid, AuditPolicyChanges
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| where count>0
```

## Visualization

Table (policy changes with user context), Timeline, Single value (count — target: 0 outside maintenance).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
