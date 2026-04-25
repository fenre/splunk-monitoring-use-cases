<!-- AUTO-GENERATED from UC-1.2.51.json — DO NOT EDIT -->

---
id: "1.2.51"
title: "Process Creation with Command Line Auditing"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.2.51 · Process Creation with Command Line Auditing

## Description

Full command-line visibility on process creation is the foundation of threat detection. Reveals encoded PowerShell, LOLBin abuse, and suspicious child processes.

## Value

Living-off-the-land binary chains are a staple of post-ex—pattern plus lineage beats raw volume.

## Implementation

Enable "Audit Process Creation" and "Include command line in process creation events" via GPO (Computer Configuration → Administrative Templates → System → Audit Process Creation). EventCode 4688 then includes full CommandLine. Search for known LOLBins (Living Off the Land Binaries): certutil, bitsadmin, mshta, regsvr32, rundll32 with suspicious parameters. High volume — use summary indexing or data model acceleration.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 4688).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable "Audit Process Creation" and "Include command line in process creation events" via GPO (Computer Configuration → Administrative Templates → System → Audit Process Creation). EventCode 4688 then includes full CommandLine. Search for known LOLBins (Living Off the Land Binaries): certutil, bitsadmin, mshta, regsvr32, rundll32 with suspicious parameters. High volume — use summary indexing or data model acceleration.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4688
| where match(CommandLine, "(?i)(certutil.*-urlcache|bitsadmin.*\/transfer|mshta.*http|regsvr32.*\/s.*\/n.*\/u|rundll32.*javascript)")
| table _time, host, SubjectUserName, NewProcessName, CommandLine, ParentProcessName
| sort -_time
```

Understanding this SPL

**Process Creation with Command Line Auditing** — Full command-line visibility on process creation is the foundation of threat detection. Reveals encoded PowerShell, LOLBin abuse, and suspicious child processes.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4688). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where match(CommandLine, "(?i)(certutil.*-urlcache|bitsadmin.*\/transfer|mshta.*http|regsvr32.*\/s.*\/n.*\/u|rundll32.*java…` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Process Creation with Command Line Auditing**): table _time, host, SubjectUserName, NewProcessName, CommandLine, ParentProcessName
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Endpoint where nodename=Endpoint.Processes
  by Processes.parent_process_name Processes.process_name Processes.user span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

**Process Creation with Command Line Auditing** — Full command-line visibility on process creation is the foundation of threat detection. Reveals encoded PowerShell, LOLBin abuse, and suspicious child processes.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4688). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Endpoint.Processes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (suspicious processes), Timeline, Search interface for hunting.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4688
| where match(CommandLine, "(?i)(certutil.*-urlcache|bitsadmin.*\/transfer|mshta.*http|regsvr32.*\/s.*\/n.*\/u|rundll32.*javascript)")
| table _time, host, SubjectUserName, NewProcessName, CommandLine, ParentProcessName
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Endpoint where nodename=Endpoint.Processes
  by Processes.parent_process_name Processes.process_name Processes.user span=1h
| where count>0
```

## Visualization

Table (suspicious processes), Timeline, Search interface for hunting.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Endpoint](https://docs.splunk.com/Documentation/CIM/latest/User/Endpoint)
