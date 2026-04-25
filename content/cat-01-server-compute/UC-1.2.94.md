<!-- AUTO-GENERATED from UC-1.2.94.json — DO NOT EDIT -->

---
id: "1.2.94"
title: "Windows Subsystem for Linux (WSL) Activity"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.2.94 · Windows Subsystem for Linux (WSL) Activity

## Description

WSL can be abused to run Linux-based attack tools while evading Windows-focused security tooling. Monitoring WSL activity closes this visibility gap.

## Value

WSL and Linux userlands on server images expand the attack surface. New distros, shells, or root actions where Linux is not expected often mean policy drift or early foothold activity.

## Implementation

Monitor for WSL process execution (wsl.exe, wslhost.exe, bash.exe from WindowsApps). Track what commands are executed inside WSL via Sysmon process creation. On servers, WSL should not be installed — alert on any WSL activity. On workstations, baseline normal usage and alert on anomalies like network tools (nmap, netcat) or credential access tools.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 1), `sourcetype=WinEventLog:Security` (EventCode 4688).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor for WSL process execution (wsl.exe, wslhost.exe, bash.exe from WindowsApps). Track what commands are executed inside WSL via Sysmon process creation. On servers, WSL should not be installed — alert on any WSL activity. On workstations, baseline normal usage and alert on anomalies like network tools (nmap, netcat) or credential access tools.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog (EventCode=1 OR EventCode=4688)
| where match(Image, "(?i)(wsl\.exe|wslhost\.exe|bash\.exe.*windows)") OR match(ParentImage, "(?i)wsl")
| table _time, host, User, Image, CommandLine, ParentImage, ParentCommandLine
| sort -_time
```

Understanding this SPL

**Windows Subsystem for Linux (WSL) Activity** — WSL can be abused to run Linux-based attack tools while evading Windows-focused security tooling. Monitoring WSL activity closes this visibility gap.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 1), `sourcetype=WinEventLog:Security` (EventCode 4688). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where match(Image, "(?i)(wsl\.exe|wslhost\.exe|bash\.exe.*windows)") OR match(ParentImage, "(?i)wsl")` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Windows Subsystem for Linux (WSL) Activity**): table _time, host, User, Image, CommandLine, ParentImage, ParentCommandLine
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (WSL commands), Timechart (usage patterns), Alert on server WSL usage.

## SPL

```spl
index=wineventlog (EventCode=1 OR EventCode=4688)
| where match(Image, "(?i)(wsl\.exe|wslhost\.exe|bash\.exe.*windows)") OR match(ParentImage, "(?i)wsl")
| table _time, host, User, Image, CommandLine, ParentImage, ParentCommandLine
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Processes
  where (like(Processes.process_name,"wsl%") OR like(Processes.process_name,"bash%"))
  by Processes.user Processes.dest span=1h
| where count > 0
```

## Visualization

Table (WSL commands), Timechart (usage patterns), Alert on server WSL usage.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
