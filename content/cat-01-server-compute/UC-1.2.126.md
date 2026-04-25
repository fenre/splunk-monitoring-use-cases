<!-- AUTO-GENERATED from UC-1.2.126.json — DO NOT EDIT -->

---
id: "1.2.126"
title: "DCOM Activation Failures"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.2.126 · DCOM Activation Failures

## Description

DCOM failures break distributed applications, WMI remote management, and SCCM client operations. Monitoring identifies misconfigured permissions and network issues.

## Value

DCOM activation failures can break management, monitoring, and integrated apps. Clustering errors by AppID and CLSID speeds up both misconfiguration and malicious COM abuse triage.

## Implementation

DCOM activation errors (10016) are common but mostly benign. Focus on recurring errors that affect application functionality. Map CLSIDs to application names to identify impacted services. Filter known-benign CLSIDs (RuntimeBroker, PerAppRuntimeBroker, ShellServiceHost). Alert on DCOM errors affecting SCCM ({4991D34B}), WMI ({76A64158}), or custom line-of-business applications. Track error count trends — sudden spikes indicate configuration changes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:System` (EventCode 10016).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
DCOM activation errors (10016) are common but mostly benign. Focus on recurring errors that affect application functionality. Map CLSIDs to application names to identify impacted services. Filter known-benign CLSIDs (RuntimeBroker, PerAppRuntimeBroker, ShellServiceHost). Alert on DCOM errors affecting SCCM ({4991D34B}), WMI ({76A64158}), or custom line-of-business applications. Track error count trends — sudden spikes indicate configuration changes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:System" EventCode=10016
| rex field=Message "CLSID\s+(?<CLSID>\{[^}]+\}).*APPID\s+(?<APPID>\{[^}]+\})"
| stats count by host, CLSID, APPID
| where count>10
| sort -count
```

Understanding this SPL

**DCOM Activation Failures** — DCOM failures break distributed applications, WMI remote management, and SCCM client operations. Monitoring identifies misconfigured permissions and network issues.

Documented **Data sources**: `sourcetype=WinEventLog:System` (EventCode 10016). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by host, CLSID, APPID** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count>10` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Services
  by Services.dest Services.name Services.status span=5m
| search Services.status!="running"
```

Understanding this CIM / accelerated SPL

**DCOM Activation Failures** — DCOM failures break distributed applications, WMI remote management, and SCCM client operations. Monitoring identifies misconfigured permissions and network issues.

Documented **Data sources**: `sourcetype=WinEventLog:System` (EventCode 10016). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Endpoint.Services` — enable acceleration for that model.
• Applies an explicit `search` filter to narrow the current result set.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (top CLSIDs), Timechart (error trend), Table (details).

## SPL

```spl
index=wineventlog source="WinEventLog:System" EventCode=10016
| rex field=Message "CLSID\s+(?<CLSID>\{[^}]+\}).*APPID\s+(?<APPID>\{[^}]+\})"
| stats count by host, CLSID, APPID
| where count>10
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.dest span=1h
| where count > 0
```

## Visualization

Bar chart (top CLSIDs), Timechart (error trend), Table (details).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Endpoint](https://docs.splunk.com/Documentation/CIM/latest/User/Endpoint)
