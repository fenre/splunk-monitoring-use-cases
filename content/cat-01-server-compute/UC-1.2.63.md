---
id: "1.2.63"
title: "Windows Installer Failures"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.2.63 · Windows Installer Failures

## Description

MSI installation failures affect patching, software deployment, and SCCM/Intune compliance. Repeated failures indicate corrupted Windows Installer service or disk issues.

## Value

MSI installation failures affect patching, software deployment, and SCCM/Intune compliance. Repeated failures indicate corrupted Windows Installer service or disk issues.

## Implementation

EventCode 11708=installation failed, 11724=removal completed (track uninstalls). Track installation failures per host — repeated failures for the same product indicate systematic issues. Correlate with SCCM/Intune deployment status. Common causes: pending reboots, insufficient disk space, corrupted Windows Installer cache. Alert when critical patches fail to install across >5% of fleet.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Application` (Source=MsiInstaller, EventCode 11708, 11724).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
EventCode 11708=installation failed, 11724=removal completed (track uninstalls). Track installation failures per host — repeated failures for the same product indicate systematic issues. Correlate with SCCM/Intune deployment status. Common causes: pending reboots, insufficient disk space, corrupted Windows Installer cache. Alert when critical patches fail to install across >5% of fleet.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Application" Source="MsiInstaller" EventCode IN (11708, 11724)
| table _time, host, EventCode, ProductName, ProductVersion, Message
| stats count by host, ProductName
| where count > 2
| sort -count
```

Understanding this SPL

**Windows Installer Failures** — MSI installation failures affect patching, software deployment, and SCCM/Intune compliance. Repeated failures indicate corrupted Windows Installer service or disk issues.

Documented **Data sources**: `sourcetype=WinEventLog:Application` (Source=MsiInstaller, EventCode 11708, 11724). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Application. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Application". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Windows Installer Failures**): table _time, host, EventCode, ProductName, ProductVersion, Message
• `stats` rolls up events into metrics; results are split **by host, ProductName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 2` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Services
  by Services.dest Services.name Services.status span=5m
| search Services.status!="running"
```

Understanding this CIM / accelerated SPL

**Windows Installer Failures** — MSI installation failures affect patching, software deployment, and SCCM/Intune compliance. Repeated failures indicate corrupted Windows Installer service or disk issues.

Documented **Data sources**: `sourcetype=WinEventLog:Application` (Source=MsiInstaller, EventCode 11708, 11724). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Endpoint.Services` — enable acceleration for that model.
• Applies an explicit `search` filter to narrow the current result set.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (failed installs), Bar chart (top failing products), Timechart (failure rate).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Application" Source="MsiInstaller" EventCode IN (11708, 11724)
| table _time, host, EventCode, ProductName, ProductVersion, Message
| stats count by host, ProductName
| where count > 2
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Services
  by Services.dest Services.name Services.status span=5m
| search Services.status!="running"
```

## Visualization

Table (failed installs), Bar chart (top failing products), Timechart (failure rate).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Endpoint](https://docs.splunk.com/Documentation/CIM/latest/User/Endpoint)
