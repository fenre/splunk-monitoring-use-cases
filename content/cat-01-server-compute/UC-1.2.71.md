<!-- AUTO-GENERATED from UC-1.2.71.json — DO NOT EDIT -->

---
id: "1.2.71"
title: "Scheduled Task Creation (Persistence)"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.2.71 · Scheduled Task Creation (Persistence)

## Description

Scheduled tasks are a common persistence mechanism for malware. New tasks created outside change management warrant investigation.

## Value

Unexpected scheduled tasks on servers are a favorite way to stay hidden. Flagging new tasks that do not look like your deployment tools gives identity and server teams a head start on cleanup.

## Implementation

Enable "Audit Other Object Access Events" for EventCode 4698 (task created). The TaskContent XML field contains the full task definition including command, arguments, and triggers. Alert on tasks created by non-SYSTEM/non-admin accounts, tasks with commands in temp/user directories, or tasks executing encoded PowerShell. Cross-reference with Sysmon process creation for execution context.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 4698), `sourcetype=WinEventLog:Microsoft-Windows-TaskScheduler/Operational` (EventCode 106).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable "Audit Other Object Access Events" for EventCode 4698 (task created). The TaskContent XML field contains the full task definition including command, arguments, and triggers. Alert on tasks created by non-SYSTEM/non-admin accounts, tasks with commands in temp/user directories, or tasks executing encoded PowerShell. Cross-reference with Sysmon process creation for execution context.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4698
| rex field=TaskContent "<Command>(?<command>[^<]+)</Command>"
| rex field=TaskContent "<Arguments>(?<arguments>[^<]+)</Arguments>"
| table _time, host, SubjectUserName, TaskName, command, arguments
| where NOT match(SubjectUserName, "(?i)(SYSTEM|sccm|intune)")
| sort -_time
```

Understanding this SPL

**Scheduled Task Creation (Persistence)** — Scheduled tasks are a common persistence mechanism for malware. New tasks created outside change management warrant investigation.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4698), `sourcetype=WinEventLog:Microsoft-Windows-TaskScheduler/Operational` (EventCode 106). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Extracts fields with `rex` (regular expression).
• Pipeline stage (see **Scheduled Task Creation (Persistence)**): table _time, host, SubjectUserName, TaskName, command, arguments
• Filters the current rows with `where NOT match(SubjectUserName, "(?i)(SYSTEM|sccm|intune)")` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (4698 as directory/task change in `Change`):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  where (like(All_Changes.object,"%Scheduled Task%") OR like(All_Changes.object,"%.xml%") OR like(All_Changes.object,"%\\Microsoft\\Windows\\Task%"))
  by All_Changes.user All_Changes.dest span=1h
| where count >= 1
```

Enable **data model acceleration** on `Change` (All_Changes). The primary `WinEventLog:Security` search remains authoritative if CIM tagging for task XML is not complete.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (new tasks with commands), Timeline, Bar chart (tasks created by user).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4698
| rex field=TaskContent "<Command>(?<command>[^<]+)</Command>"
| rex field=TaskContent "<Arguments>(?<arguments>[^<]+)</Arguments>"
| table _time, host, SubjectUserName, TaskName, command, arguments
| where NOT match(SubjectUserName, "(?i)(SYSTEM|sccm|intune)")
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  where (like(All_Changes.object,"%Scheduled Task%") OR like(All_Changes.object,"%.xml%") OR like(All_Changes.object,"%\\Microsoft\\Windows\\Task%"))
  by All_Changes.user All_Changes.dest span=1h
| where count >= 1
```

## Visualization

Table (new tasks with commands), Timeline, Bar chart (tasks created by user).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
