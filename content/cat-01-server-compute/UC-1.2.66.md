<!-- AUTO-GENERATED from UC-1.2.66.json — DO NOT EDIT -->

---
id: "1.2.66"
title: "Sysmon File Creation in Suspicious Paths"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.2.66 · Sysmon File Creation in Suspicious Paths

## Description

Files created in temp directories, startup folders, and system paths by unexpected processes indicate malware dropping payloads or establishing persistence.

## Value

Catching odd file drops early helps security teams stop malware staging and persistence before it spreads to other systems or causes outages.

## Implementation

Deploy Sysmon with FileCreate (EventCode 11) monitoring, filtered to suspicious target paths: Temp, Startup, ProgramData, AppData. Executables (.exe, .dll, .bat, .ps1, .vbs) created in these paths by non-installer processes are suspicious. Exclude known deployment tools (SCCM client, Intune agent). Cross-reference with process creation events to build full attack chain.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`, Sysmon required.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 11).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy Sysmon with FileCreate (EventCode 11) monitoring, filtered to suspicious target paths: Temp, Startup, ProgramData, AppData. Executables (.exe, .dll, .bat, .ps1, .vbs) created in these paths by non-installer processes are suspicious. Exclude known deployment tools (SCCM client, Intune agent). Cross-reference with process creation events to build full attack chain.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=11
| where match(TargetFilename, "(?i)(\\\\Temp\\\\.*\\.exe|\\\\Startup\\\\|\\\\Tasks\\\\|\\\\ProgramData\\\\.*\\.exe|\\\\AppData\\\\.*\\.bat|\\\\AppData\\\\.*\\.ps1)")
| table _time, host, Image, TargetFilename, User
| sort -_time
```

Understanding this SPL

**Sysmon File Creation in Suspicious Paths** — Files created in temp directories, startup folders, and system paths by unexpected processes indicate malware dropping payloads or establishing persistence.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 11). **App/TA** (typical add-on context): `Splunk_TA_windows`, Sysmon required. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Microsoft-Windows-Sysmon/Operational. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where match(TargetFilename, "(?i)(\\\\Temp\\\\.*\\.exe|\\\\Startup\\\\|\\\\Tasks\\\\|\\\\ProgramData\\\\.*\\.exe|\\\\AppDat…` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Sysmon File Creation in Suspicious Paths**): table _time, host, Image, TargetFilename, User
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (Sysmon EventCode 11 mapped to Endpoint.Filesystem — requires CIM tagging from the same host feed):

```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Filesystem
  where (like(Filesystem.file_path,"%\\Temp\\%") OR like(Filesystem.file_path,"%\\Startup\\%") OR like(Filesystem.file_path,"%\\Tasks\\%") OR like(Filesystem.file_path,"%\\ProgramData\\%") OR like(Filesystem.file_path,"%\\AppData\\%.bat") OR like(Filesystem.file_path,"%\\AppData\\%.ps1") OR like(Filesystem.file_path,"%\\Temp\\%.exe") OR like(Filesystem.file_path,"%\\ProgramData\\%.exe"))
  by Filesystem.dest Filesystem.file_path Filesystem.user span=1h
| where count >= 1
```

Enable **data model acceleration** on `Endpoint` (Filesystem). If `tstats` returns nothing, confirm CIM tags and field aliases for Sysmon file-create events.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (suspicious file creations), Bar chart (top dropping processes), Timeline.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=11
| where match(TargetFilename, "(?i)(\\\\Temp\\\\.*\\.exe|\\\\Startup\\\\|\\\\Tasks\\\\|\\\\ProgramData\\\\.*\\.exe|\\\\AppData\\\\.*\\.bat|\\\\AppData\\\\.*\\.ps1)")
| table _time, host, Image, TargetFilename, User
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Filesystem
  where (like(Filesystem.file_path,"%\\Temp\\%") OR like(Filesystem.file_path,"%\\Startup\\%") OR like(Filesystem.file_path,"%\\Tasks\\%") OR like(Filesystem.file_path,"%\\ProgramData\\%") OR like(Filesystem.file_path,"%\\AppData\\%.bat") OR like(Filesystem.file_path,"%\\AppData\\%.ps1") OR like(Filesystem.file_path,"%\\Temp\\%.exe") OR like(Filesystem.file_path,"%\\ProgramData\\%.exe"))
  by Filesystem.dest Filesystem.file_path Filesystem.user span=1h
| where count >= 1
```

## Visualization

Table (suspicious file creations), Bar chart (top dropping processes), Timeline.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Endpoint](https://docs.splunk.com/Documentation/CIM/latest/User/Endpoint)
