---
id: "1.2.90"
title: "Shadow Copy Deletion (Ransomware Indicator)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.90 · Shadow Copy Deletion (Ransomware Indicator)

## Description

Ransomware deletes volume shadow copies to prevent file recovery. Detecting vssadmin/wmic shadow deletion commands is a high-confidence ransomware indicator.

## Value

Ransomware deletes volume shadow copies to prevent file recovery. Detecting vssadmin/wmic shadow deletion commands is a high-confidence ransomware indicator.

## Implementation

Monitor process creation (EventCode 4688 or Sysmon 1) for commands: `vssadmin delete shadows`, `wmic shadowcopy delete`, `bcdedit /set {default} recoveryenabled no`, `wbadmin delete catalog`. Any of these commands executed outside backup maintenance is a near-certain indicator of ransomware or destructive attack. Alert with critical priority and trigger automated response (network isolation). MITRE ATT&CK T1490.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 4688), `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 1).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor process creation (EventCode 4688 or Sysmon 1) for commands: `vssadmin delete shadows`, `wmic shadowcopy delete`, `bcdedit /set {default} recoveryenabled no`, `wbadmin delete catalog`. Any of these commands executed outside backup maintenance is a near-certain indicator of ransomware or destructive attack. Alert with critical priority and trigger automated response (network isolation). MITRE ATT&CK T1490.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog EventCode IN (4688, 1)
| where match(CommandLine, "(?i)(vssadmin.*delete.*shadows|wmic.*shadowcopy.*delete|bcdedit.*recoveryenabled.*no|wbadmin.*delete.*catalog)")
| table _time, host, User, CommandLine, ParentProcessName, Image
| sort -_time
```

Understanding this SPL

**Shadow Copy Deletion (Ransomware Indicator)** — Ransomware deletes volume shadow copies to prevent file recovery. Detecting vssadmin/wmic shadow deletion commands is a high-confidence ransomware indicator.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4688), `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 1). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where match(CommandLine, "(?i)(vssadmin.*delete.*shadows|wmic.*shadowcopy.*delete|bcdedit.*recoveryenabled.*no|wbadmin.*del…` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Shadow Copy Deletion (Ransomware Indicator)**): table _time, host, User, CommandLine, ParentProcessName, Image
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value (count — target: 0), Table (events), Alert with automated containment trigger.

## SPL

```spl
index=wineventlog EventCode IN (4688, 1)
| where match(CommandLine, "(?i)(vssadmin.*delete.*shadows|wmic.*shadowcopy.*delete|bcdedit.*recoveryenabled.*no|wbadmin.*delete.*catalog)")
| table _time, host, User, CommandLine, ParentProcessName, Image
| sort -_time
```

## Visualization

Single value (count — target: 0), Table (events), Alert with automated containment trigger.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
