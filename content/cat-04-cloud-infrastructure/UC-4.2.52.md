---
id: "4.2.52"
title: "Azure Virtual Desktop Session Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.2.52 · Azure Virtual Desktop Session Health

## Description

Azure Virtual Desktop provides remote desktop infrastructure. Connection failures, high round-trip latency, and session drops directly impact end-user productivity.

## Value

Azure Virtual Desktop provides remote desktop infrastructure. Connection failures, high round-trip latency, and session drops directly impact end-user productivity.

## Implementation

Enable diagnostics on AVD host pools to route `WVDConnections`, `WVDErrors`, and `WVDCheckpoints` to Splunk. Monitor connection success rate, average session duration, and round-trip time. Alert on connection failure spikes, session host unavailability, and high input delay (>200ms). Track session host resource utilization (CPU, memory, disk) from Azure Monitor metrics.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices` (Azure Monitor diagnostics).
• Ensure the following data sources are available: `sourcetype=azure:diagnostics` (WVDConnections, WVDErrors, WVDCheckpoints).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable diagnostics on AVD host pools to route `WVDConnections`, `WVDErrors`, and `WVDCheckpoints` to Splunk. Monitor connection success rate, average session duration, and round-trip time. Alert on connection failure spikes, session host unavailability, and high input delay (>200ms). Track session host resource utilization (CPU, memory, disk) from Azure Monitor metrics.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="azure:diagnostics" Category="WVDConnections"
| eval duration_min=round(SessionDuration/60000,1)
| stats count as connections, avg(duration_min) as avg_session_min, dc(UserName) as unique_users by HostPoolName, SessionHostName
| join type=left max=1 SessionHostName [
    search index=cloud sourcetype="azure:diagnostics" Category="WVDErrors"
    | stats count as errors by SessionHostName
]
| where errors > 0
| sort -errors
```

Understanding this SPL

**Azure Virtual Desktop Session Health** — Azure Virtual Desktop provides remote desktop infrastructure. Connection failures, high round-trip latency, and session drops directly impact end-user productivity.

Documented **Data sources**: `sourcetype=azure:diagnostics` (WVDConnections, WVDErrors, WVDCheckpoints). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices` (Azure Monitor diagnostics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: azure:diagnostics. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="azure:diagnostics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **duration_min** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by HostPoolName, SessionHostName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
• Filters the current rows with `where errors > 0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (session hosts with errors), Line chart (connections and failures over time), Single value (active sessions).

## SPL

```spl
index=cloud sourcetype="azure:diagnostics" Category="WVDConnections"
| eval duration_min=round(SessionDuration/60000,1)
| stats count as connections, avg(duration_min) as avg_session_min, dc(UserName) as unique_users by HostPoolName, SessionHostName
| join type=left max=1 SessionHostName [
    search index=cloud sourcetype="azure:diagnostics" Category="WVDErrors"
    | stats count as errors by SessionHostName
]
| where errors > 0
| sort -errors
```

## Visualization

Table (session hosts with errors), Line chart (connections and failures over time), Single value (active sessions).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
