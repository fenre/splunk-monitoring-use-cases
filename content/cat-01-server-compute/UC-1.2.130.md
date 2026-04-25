<!-- AUTO-GENERATED from UC-1.2.130.json — DO NOT EDIT -->

---
id: "1.2.130"
title: "Scheduled Task Modification for Persistence"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.130 · Scheduled Task Modification for Persistence

## Description

Modifying existing scheduled tasks is stealthier than creating new ones. Attackers replace legitimate task actions to achieve persistence without new artifacts.

## Value

Modifying existing scheduled tasks is stealthier than creating new ones. Attackers replace legitimate task actions to achieve persistence without new artifacts.

## Implementation

Monitor Task Scheduler Operational log for task modifications (140), deletions (141), and disabling (142). Focus on non-Microsoft tasks being modified. Correlate with Sysmon process creation (EventCode 1) to identify what tool made the change. Alert on modifications to security-related tasks (AV scans, backup tasks). Track task action changes — replacing a legitimate executable with malware. Maintain baseline of critical task configurations.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-TaskScheduler/Operational` (EventCode 140, 141, 142).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor Task Scheduler Operational log for task modifications (140), deletions (141), and disabling (142). Focus on non-Microsoft tasks being modified. Correlate with Sysmon process creation (EventCode 1) to identify what tool made the change. Alert on modifications to security-related tasks (AV scans, backup tasks). Track task action changes — replacing a legitimate executable with malware. Maintain baseline of critical task configurations.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-TaskScheduler/Operational" EventCode IN (140, 141, 142)
| eval Action=case(EventCode=140,"Task_Updated", EventCode=141,"Task_Deleted", EventCode=142,"Task_Disabled", 1=1,"Other")
| table _time, host, TaskName, Action, UserContext
| where NOT match(TaskName, "(?i)(\\\\Microsoft\\\\Windows\\\\)")
| sort -_time
```

Understanding this SPL

**Scheduled Task Modification for Persistence** — Modifying existing scheduled tasks is stealthier than creating new ones. Attackers replace legitimate task actions to achieve persistence without new artifacts.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-TaskScheduler/Operational` (EventCode 140, 141, 142). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **Action** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Scheduled Task Modification for Persistence**): table _time, host, TaskName, Action, UserContext
• Filters the current rows with `where NOT match(TaskName, "(?i)(\\\\Microsoft\\\\Windows\\\\)")` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Scheduled Task Modification for Persistence** — Modifying existing scheduled tasks is stealthier than creating new ones. Attackers replace legitimate task actions to achieve persistence without new artifacts.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-TaskScheduler/Operational` (EventCode 140, 141, 142). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (task changes), Alert on modification of critical tasks, Timeline.

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-TaskScheduler/Operational" EventCode IN (140, 141, 142)
| eval Action=case(EventCode=140,"Task_Updated", EventCode=141,"Task_Deleted", EventCode=142,"Task_Disabled", 1=1,"Other")
| table _time, host, TaskName, Action, UserContext
| where NOT match(TaskName, "(?i)(\\\\Microsoft\\\\Windows\\\\)")
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

## Visualization

Table (task changes), Alert on modification of critical tasks, Timeline.

## References

- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
