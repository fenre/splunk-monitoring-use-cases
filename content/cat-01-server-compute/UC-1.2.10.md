<!-- AUTO-GENERATED from UC-1.2.10.json — DO NOT EDIT -->

---
id: "1.2.10"
title: "Scheduled Task Failures"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.2.10 · Scheduled Task Failures

## Description

Failed scheduled tasks break batch jobs, cleanup scripts, and automated processes. Often goes unnoticed until downstream effects appear.

## Value

Failed tasks often mean skipped backups or drift—fixing the task before data loss beats discovering it at restore time.

## Implementation

Enable Task Scheduler operational log collection. Alert on non-zero ResultCode values. Maintain a lookup of critical tasks per server role.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-TaskScheduler/Operational`, EventCode=201.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Task Scheduler operational log collection. Alert on non-zero ResultCode values. Maintain a lookup of critical tasks per server role.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-TaskScheduler/Operational" EventCode=201
| where ActionName!="0" AND ResultCode!="0"
| table _time host TaskName ResultCode ActionName
| sort -_time
```

Understanding this SPL

**Scheduled Task Failures** — Failed scheduled tasks break batch jobs, cleanup scripts, and automated processes. Often goes unnoticed until downstream effects appear.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-TaskScheduler/Operational`, EventCode=201. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Microsoft-Windows-TaskScheduler/Operational. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Microsoft-Windows-TaskScheduler/Operational". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where ActionName!="0" AND ResultCode!="0"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Scheduled Task Failures**): table _time host TaskName ResultCode ActionName
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.object All_Changes.action All_Changes.dest span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

CIM tstats is an approximate mirror when Windows TA field extractions and CIM tags are complete. Enable the matching data model acceleration or tstats may return no rows.



Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of failures, Single value (failures last 24h), Bar chart by task name.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-TaskScheduler/Operational" EventCode=201
| where ActionName!="0" AND ResultCode!="0"
| table _time host TaskName ResultCode ActionName
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.object All_Changes.action All_Changes.dest span=1h
| where count>0
```

## Visualization

Table of failures, Single value (failures last 24h), Bar chart by task name.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
