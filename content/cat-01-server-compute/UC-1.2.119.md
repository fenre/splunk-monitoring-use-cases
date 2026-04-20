---
id: "1.2.119"
title: "Registry Run Key Persistence Monitoring"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.119 · Registry Run Key Persistence Monitoring

## Description

Registry Run keys are the most common persistence mechanism for malware. Monitoring autostart registry locations detects new malware installations.

## Value

Registry Run keys are the most common persistence mechanism for malware. Monitoring autostart registry locations detects new malware installations.

## Implementation

Sysmon EventCode 13 (RegistryValueSet) monitors registry modifications. Track all autostart locations: Run, RunOnce, RunServices, Winlogon Shell/Userinit, Explorer Shell Folders, and AppInit_DLLs. Filter known-legitimate entries (Program Files, System32). Alert on entries pointing to temp directories, AppData, user profiles, or encoded/obfuscated paths. Monitor both HKLM (system-wide) and HKCU (per-user). MITRE ATT&CK T1547.001.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 13).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Sysmon EventCode 13 (RegistryValueSet) monitors registry modifications. Track all autostart locations: Run, RunOnce, RunServices, Winlogon Shell/Userinit, Explorer Shell Folders, and AppInit_DLLs. Filter known-legitimate entries (Program Files, System32). Alert on entries pointing to temp directories, AppData, user profiles, or encoded/obfuscated paths. Monitor both HKLM (system-wide) and HKCU (per-user). MITRE ATT&CK T1547.001.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog EventCode=13
| where match(TargetObject, "(?i)(CurrentVersion\\\\Run|CurrentVersion\\\\RunOnce|Winlogon\\\\Shell|Winlogon\\\\Userinit|Explorer\\\\Shell Folders)")
| where NOT match(Details, "(?i)(program files|windows\\\\system32|syswow64)")
| table _time, host, User, Image, TargetObject, Details
| sort -_time
```

Understanding this SPL

**Registry Run Key Persistence Monitoring** — Registry Run keys are the most common persistence mechanism for malware. Monitoring autostart registry locations detects new malware installations.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 13). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where match(TargetObject, "(?i)(CurrentVersion\\\\Run|CurrentVersion\\\\RunOnce|Winlogon\\\\Shell|Winlogon\\\\Userinit|Expl…` — typically the threshold or rule expression for this monitoring goal.
• Filters the current rows with `where NOT match(Details, "(?i)(program files|windows\\\\system32|syswow64)")` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Registry Run Key Persistence Monitoring**): table _time, host, User, Image, TargetObject, Details
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Registry Run Key Persistence Monitoring** — Registry Run keys are the most common persistence mechanism for malware. Monitoring autostart registry locations detects new malware installations.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 13). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (new Run key entries), Alert on suspicious paths, Timeline.

## SPL

```spl
index=wineventlog EventCode=13
| where match(TargetObject, "(?i)(CurrentVersion\\\\Run|CurrentVersion\\\\RunOnce|Winlogon\\\\Shell|Winlogon\\\\Userinit|Explorer\\\\Shell Folders)")
| where NOT match(Details, "(?i)(program files|windows\\\\system32|syswow64)")
| table _time, host, User, Image, TargetObject, Details
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

Table (new Run key entries), Alert on suspicious paths, Timeline.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
