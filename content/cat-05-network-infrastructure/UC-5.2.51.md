---
id: "5.2.51"
title: "Check Point Log Rate and Capacity (Check Point)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.51 · Check Point Log Rate and Capacity (Check Point)

## Description

Check Point gateways forward logs to the management server or Log Server. When log rate exceeds the management capacity or network bandwidth, logs are queued, delayed, or dropped — creating blind spots in security monitoring. Tracking log rate per gateway and comparing to Log Server capacity prevents log loss before it impacts compliance and incident detection.

## Value

Check Point gateways forward logs to the management server or Log Server. When log rate exceeds the management capacity or network bandwidth, logs are queued, delayed, or dropped — creating blind spots in security monitoring. Tracking log rate per gateway and comparing to Log Server capacity prevents log loss before it impacts compliance and incident detection.

## Implementation

Baseline event rate per gateway. Alert on sudden spikes (possible attack or debug logging left enabled) and drops (log forwarding failure or connectivity issue). Monitor Log Server disk and queue depth. Correlate log drops with gateway CPU and network congestion.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_checkpoint` (Splunkbase 5402), Check Point App for Splunk (Splunkbase 4293), CCX Add-on for Checkpoint Smart-1 Cloud (Splunkbase 7259).
• Ensure the following data sources are available: `sourcetype=cp_log` (system/management logs), log server statistics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Baseline event rate per gateway. Alert on sudden spikes (possible attack or debug logging left enabled) and drops (log forwarding failure or connectivity issue). Monitor Log Server disk and queue depth. Correlate log drops with gateway CPU and network congestion.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=checkpoint sourcetype="cp_log" earliest=-24h
| bin _time span=5m
| stats count as events_5m by _time, orig
| eventstats avg(events_5m) as baseline by orig
| where events_5m > baseline*3 OR events_5m < baseline*0.2
| eval anomaly=if(events_5m > baseline*3, "spike", "drop")
| table _time, orig, events_5m, baseline, anomaly
```

Understanding this SPL

**Check Point Log Rate and Capacity (Check Point)** — Check Point gateways forward logs to the management server or Log Server. When log rate exceeds the management capacity or network bandwidth, logs are queued, delayed, or dropped — creating blind spots in security monitoring. Tracking log rate per gateway and comparing to Log Server capacity prevents log loss before it impacts compliance and incident detection.

Documented **Data sources**: `sourcetype=cp_log` (system/management logs), log server statistics. **App/TA** (typical add-on context): `Splunk_TA_checkpoint` (Splunkbase 5402), Check Point App for Splunk (Splunkbase 4293), CCX Add-on for Checkpoint Smart-1 Cloud (Splunkbase 7259). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: checkpoint; **sourcetype**: cp_log. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=checkpoint, sourcetype="cp_log", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time, orig** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eventstats` rolls up events into metrics; results are split **by orig** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where events_5m > baseline*3 OR events_5m < baseline*0.2` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **anomaly** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Check Point Log Rate and Capacity (Check Point)**): table _time, orig, events_5m, baseline, anomaly

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (log rate per gateway), Single value (current aggregate rate), Table (anomalies), Bar chart (rate by gateway).

## SPL

```spl
index=checkpoint sourcetype="cp_log" earliest=-24h
| bin _time span=5m
| stats count as events_5m by _time, orig
| eventstats avg(events_5m) as baseline by orig
| where events_5m > baseline*3 OR events_5m < baseline*0.2
| eval anomaly=if(events_5m > baseline*3, "spike", "drop")
| table _time, orig, events_5m, baseline, anomaly
```

## Visualization

Line chart (log rate per gateway), Single value (current aggregate rate), Table (anomalies), Bar chart (rate by gateway).

## References

- [Check Point App for Splunk](https://splunkbase.splunk.com/app/4293)
- [CCX Add-on for Checkpoint Smart-1 Cloud](https://splunkbase.splunk.com/app/7259)
- [Splunkbase app 5402](https://splunkbase.splunk.com/app/5402)
