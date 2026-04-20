---
id: "1.2.4"
title: "Windows Service Failures"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.2.4 · Windows Service Failures

## Description

Stopped critical services directly impact application availability. Auto-restart doesn't always work, and some services can't auto-restart.

## Value

Stopped critical services directly impact application availability. Auto-restart doesn't always work, and some services can't auto-restart.

## Implementation

Enable Windows Event Log collection for the System log. Create alerts on EventCode 7034 and 7031. Maintain a lookup of critical services per server role to filter noise.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:System`, Event IDs 7034 (crash), 7036 (state change), 7031 (unexpected termination).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Windows Event Log collection for the System log. Create alerts on EventCode 7034 and 7031. Maintain a lookup of critical services per server role to filter noise.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:System" (EventCode=7034 OR EventCode=7031 OR EventCode=7036)
| eval status=case(EventCode=7034, "Crashed", EventCode=7031, "Terminated Unexpectedly", EventCode=7036 AND Message LIKE "%stopped%", "Stopped", 1=1, "Changed")
| stats count by host, EventCode, status, Message
| sort -count
```

Understanding this SPL

**Windows Service Failures** — Stopped critical services directly impact application availability. Auto-restart doesn't always work, and some services can't auto-restart.

Documented **Data sources**: `sourcetype=WinEventLog:System`, Event IDs 7034 (crash), 7036 (state change), 7031 (unexpected termination). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:System. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:System". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **status** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host, EventCode, status, Message** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Services
  by Services.dest Services.name Services.status span=5m
| search Services.status!="running"
```

Understanding this CIM / accelerated SPL

**Windows Service Failures** — Stopped critical services directly impact application availability. Auto-restart doesn't always work, and some services can't auto-restart.

Documented **Data sources**: `sourcetype=WinEventLog:System`, Event IDs 7034 (crash), 7036 (state change), 7031 (unexpected termination). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Endpoint.Services` — enable acceleration for that model.
• Applies an explicit `search` filter to narrow the current result set.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status panel (red/green per service), Table of recent events, Timeline.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:System" (EventCode=7034 OR EventCode=7031 OR EventCode=7036)
| eval status=case(EventCode=7034, "Crashed", EventCode=7031, "Terminated Unexpectedly", EventCode=7036 AND Message LIKE "%stopped%", "Stopped", 1=1, "Changed")
| stats count by host, EventCode, status, Message
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

Status panel (red/green per service), Table of recent events, Timeline.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Endpoint](https://docs.splunk.com/Documentation/CIM/latest/User/Endpoint)
