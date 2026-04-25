<!-- AUTO-GENERATED from UC-1.2.29.json — DO NOT EDIT -->

---
id: "1.2.29"
title: "Registry Run Key Modification (Persistence)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.29 · Registry Run Key Modification (Persistence)

## Description

Run/RunOnce registry keys are the most common malware persistence mechanism. Monitoring these keys catches many threats early.

## Value

Run-key persistence is old but still common—this gives you a straight path from change to triage in minutes.

## Implementation

Deploy Sysmon with registry monitoring rules targeting HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run, RunOnce, and HKCU equivalents. Alternatively, enable Object Access auditing (EventCode 4657) with SACLs on Run keys. Alert on any modification outside approved deployment tools (SCCM, GPO). Cross-reference with threat intel.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`, Sysmon recommended.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 13) or `sourcetype=WinEventLog:Security` (EventCode 4657).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy Sysmon with registry monitoring rules targeting HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run, RunOnce, and HKCU equivalents. Alternatively, enable Object Access auditing (EventCode 4657) with SACLs on Run keys. Alert on any modification outside approved deployment tools (SCCM, GPO). Cross-reference with threat intel.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=13
  TargetObject="*\\CurrentVersion\\Run*"
| table _time, host, Image, TargetObject, Details, User
| sort -_time
```

Understanding this SPL

**Registry Run Key Modification (Persistence)** — Run/RunOnce registry keys are the most common malware persistence mechanism. Monitoring these keys catches many threats early.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 13) or `sourcetype=WinEventLog:Security` (EventCode 4657). **App/TA** (typical add-on context): `Splunk_TA_windows`, Sysmon recommended. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Microsoft-Windows-Sysmon/Operational. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Registry Run Key Modification (Persistence)**): table _time, host, Image, TargetObject, Details, User
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.object All_Changes.user All_Changes.dest span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

**Registry Run Key Modification (Persistence)** — Run/RunOnce registry keys are the most common malware persistence mechanism. Monitoring these keys catches many threats early.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 13) or `sourcetype=WinEventLog:Security` (EventCode 4657). **App/TA** (typical add-on context): `Splunk_TA_windows`, Sysmon recommended. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (registry changes with process context), Timeline, Alert on non-GPO modifications.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=13
  TargetObject="*\\CurrentVersion\\Run*"
| table _time, host, Image, TargetObject, Details, User
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.object All_Changes.user All_Changes.dest span=1h
| where count>0
```

## Visualization

Table (registry changes with process context), Timeline, Alert on non-GPO modifications.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
