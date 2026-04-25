<!-- AUTO-GENERATED from UC-1.2.30.json — DO NOT EDIT -->

---
id: "1.2.30"
title: "LSASS Memory Access (Credential Dumping)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.30 · LSASS Memory Access (Credential Dumping)

## Description

Accessing LSASS process memory is the primary technique for credential theft (Mimikatz, ProcDump). Detection is critical to stopping lateral movement.

## Value

Credential dumping is a key step in many breaches—an early, explainable view shortens the IR clock.

## Implementation

Deploy Sysmon with ProcessAccess (EventCode 10) monitoring. Filter out legitimate LSASS accessors (AV engines, csrss, wininit). The GrantedAccess mask 0x1010 (PROCESS_VM_READ + PROCESS_QUERY_LIMITED_INFORMATION) is the Mimikatz signature. Alert immediately with critical priority. Enable Credential Guard (Windows 10+) as a complementary defense.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`, Sysmon required.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 10).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy Sysmon with ProcessAccess (EventCode 10) monitoring. Filter out legitimate LSASS accessors (AV engines, csrss, wininit). The GrantedAccess mask 0x1010 (PROCESS_VM_READ + PROCESS_QUERY_LIMITED_INFORMATION) is the Mimikatz signature. Alert immediately with critical priority. Enable Credential Guard (Windows 10+) as a complementary defense.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=10
  TargetImage="*\\lsass.exe"
  GrantedAccess IN ("0x1010","0x1410","0x1438","0x143a","0x1fffff")
| where NOT match(SourceImage, "(?i)(MsMpEng|csrss|wininit|svchost|mrt\.exe)")
| table _time, host, SourceImage, GrantedAccess, SourceUser
| sort -_time
```

Understanding this SPL

**LSASS Memory Access (Credential Dumping)** — Accessing LSASS process memory is the primary technique for credential theft (Mimikatz, ProcDump). Detection is critical to stopping lateral movement.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 10). **App/TA** (typical add-on context): `Splunk_TA_windows`, Sysmon required. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Microsoft-Windows-Sysmon/Operational. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where NOT match(SourceImage, "(?i)(MsMpEng|csrss|wininit|svchost|mrt\.exe)")` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **LSASS Memory Access (Credential Dumping)**): table _time, host, SourceImage, GrantedAccess, SourceUser
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Endpoint where nodename=Endpoint.Processes
  by Processes.process_name Processes.user Processes.parent_process span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

**LSASS Memory Access (Credential Dumping)** — Accessing LSASS process memory is the primary technique for credential theft (Mimikatz, ProcDump). Detection is critical to stopping lateral movement.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 10). **App/TA** (typical add-on context): `Splunk_TA_windows`, Sysmon required. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Filters the current rows with `where count > 5` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (LSASS access events), Single value (count — target: 0), Alert with MITRE ATT&CK T1003 reference.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=10
  TargetImage="*\\lsass.exe"
  GrantedAccess IN ("0x1010","0x1410","0x1438","0x143a","0x1fffff")
| where NOT match(SourceImage, "(?i)(MsMpEng|csrss|wininit|svchost|mrt\.exe)")
| table _time, host, SourceImage, GrantedAccess, SourceUser
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Endpoint where nodename=Endpoint.Processes
  by Processes.process_name Processes.user Processes.parent_process span=1h
| where count>0
```

## Visualization

Table (LSASS access events), Single value (count — target: 0), Alert with MITRE ATT&CK T1003 reference.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
