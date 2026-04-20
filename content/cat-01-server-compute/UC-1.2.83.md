---
id: "1.2.83"
title: "Boot Configuration Changes (BCDEdit)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.83 · Boot Configuration Changes (BCDEdit)

## Description

Boot configuration changes can disable Secure Boot, enable test signing (rootkit loading), or modify boot chain integrity. Used by advanced threats.

## Value

Boot configuration changes can disable Secure Boot, enable test signing (rootkit loading), or modify boot chain integrity. Used by advanced threats.

## Implementation

Requires process creation with command line auditing (EventCode 4688). Alert on any bcdedit execution that modifies security settings: `testsigning on` (allows unsigned drivers), `nointegritychecks` (disables code integrity), `debug on` (enables kernel debugging), `disableelamdrivers` (disables early launch anti-malware). All of these weaken the boot chain. Legitimate uses are rare and limited to development environments.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 4688, CommandLine containing bcdedit).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Requires process creation with command line auditing (EventCode 4688). Alert on any bcdedit execution that modifies security settings: `testsigning on` (allows unsigned drivers), `nointegritychecks` (disables code integrity), `debug on` (enables kernel debugging), `disableelamdrivers` (disables early launch anti-malware). All of these weaken the boot chain. Legitimate uses are rare and limited to development environments.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4688
  CommandLine="*bcdedit*"
| where match(CommandLine, "(?i)(testsigning|nointegritychecks|safeboot|debug|disableelamdrivers)")
| table _time, host, SubjectUserName, CommandLine, ParentProcessName
| sort -_time
```

Understanding this SPL

**Boot Configuration Changes (BCDEdit)** — Boot configuration changes can disable Secure Boot, enable test signing (rootkit loading), or modify boot chain integrity. Used by advanced threats.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4688, CommandLine containing bcdedit). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where match(CommandLine, "(?i)(testsigning|nointegritychecks|safeboot|debug|disableelamdrivers)")` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Boot Configuration Changes (BCDEdit)**): table _time, host, SubjectUserName, CommandLine, ParentProcessName
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Boot Configuration Changes (BCDEdit)** — Boot configuration changes can disable Secure Boot, enable test signing (rootkit loading), or modify boot chain integrity. Used by advanced threats.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4688, CommandLine containing bcdedit). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (bcdedit commands), Single value (security-affecting changes — target: 0), Alert.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4688
  CommandLine="*bcdedit*"
| where match(CommandLine, "(?i)(testsigning|nointegritychecks|safeboot|debug|disableelamdrivers)")
| table _time, host, SubjectUserName, CommandLine, ParentProcessName
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

Table (bcdedit commands), Single value (security-affecting changes — target: 0), Alert.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
