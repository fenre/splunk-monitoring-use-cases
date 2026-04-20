---
id: "1.2.132"
title: "Windows Scheduled Task Failures"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.2.132 · Windows Scheduled Task Failures

## Description

Detect tasks that failed to run or returned non-zero result codes. Indicates missed backups, sync jobs, or automation failures.

## Value

Detect tasks that failed to run or returned non-zero result codes. Indicates missed backups, sync jobs, or automation failures.

## Implementation

Enable Task Scheduler Operational log input. EventCode 201 = task completed; EventCode 101 = task started. Parse ResultCode (0 = success). Alert on ResultCode != 0. Common codes: 0x1 (incorrect function), 0x2 (file not found), 0x5 (access denied). Exclude known flaky tasks from alert if acceptable.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `WinEventLog:Microsoft-Windows-TaskScheduler/Operational` (EventCode 201, 101).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Task Scheduler Operational log input. EventCode 201 = task completed; EventCode 101 = task started. Parse ResultCode (0 = success). Alert on ResultCode != 0. Common codes: 0x1 (incorrect function), 0x2 (file not found), 0x5 (access denied). Exclude known flaky tasks from alert if acceptable.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-TaskScheduler/Operational" EventCode=201 ResultCode!=0
| stats count by host, TaskName
| sort -count
```

Understanding this SPL

**Windows Scheduled Task Failures** — Detect tasks that failed to run or returned non-zero result codes. Indicates missed backups, sync jobs, or automation failures.

Documented **Data sources**: `WinEventLog:Microsoft-Windows-TaskScheduler/Operational` (EventCode 201, 101). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, TaskName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (task, host, result code), Alert on failed tasks, Bar chart (failed task count by task name).

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-TaskScheduler/Operational" EventCode=201 ResultCode!=0
| stats count by host, TaskName
| sort -count
```

## Visualization

Table (task, host, result code), Alert on failed tasks, Bar chart (failed task count by task name).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
