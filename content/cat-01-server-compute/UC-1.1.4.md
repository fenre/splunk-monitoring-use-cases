---
id: "1.1.4"
title: "Disk I/O Saturation (Linux)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.4 · Disk I/O Saturation (Linux)

## Description

High I/O wait degrades application performance even when CPU and memory look healthy. Catches storage bottlenecks before users complain.

## Value

High I/O wait degrades application performance even when CPU and memory look healthy. Catches storage bottlenecks before users complain.

## Implementation

Enable `iostat` scripted input (interval=60). Key fields: `avgWaitMillis` (await — avg wait in ms), `avgSvcMillis` (svctm — avg service time in ms), `bandwUtilPct` (disk utilization %), `rReq_PS`/`wReq_PS` (read/write IOPS). Alert when avgWaitMillis >20ms sustained over 10 minutes. Correlate with application latency metrics for root cause.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`.
• Ensure the following data sources are available: `sourcetype=iostat`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable `iostat` scripted input (interval=60). Key fields: `avgWaitMillis` (await — avg wait in ms), `avgSvcMillis` (svctm — avg service time in ms), `bandwUtilPct` (disk utilization %), `rReq_PS`/`wReq_PS` (read/write IOPS). Alert when avgWaitMillis >20ms sustained over 10 minutes. Correlate with application latency metrics for root cause.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=iostat host=*
| timechart span=5m avg(avgWaitMillis) as avg_wait, avg(avgSvcMillis) as avg_svc by host
| where avg_wait > 20
```

Understanding this SPL

**Disk I/O Saturation (Linux)** — High I/O wait degrades application performance even when CPU and memory look healthy. Catches storage bottlenecks before users complain.

Documented **Data sources**: `sourcetype=iostat`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: iostat. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=iostat. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where avg_wait > 20` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.read_latency) as read_ms avg(Performance.write_latency) as write_ms
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=5m
| eval worst_ms=max(read_ms, write_ms)
| where worst_ms > 20
```

Understanding this CIM / accelerated SPL

**Disk I/O Saturation (Linux)** — High I/O wait degrades application performance even when CPU and memory look healthy. Catches storage bottlenecks before users complain.

Documented **Data sources**: `sourcetype=iostat`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.
• `eval` defines or adjusts **worst_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where worst_ms > 20` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (latency over time by host), Heatmap of I/O wait across hosts.

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=os sourcetype=iostat host=*
| timechart span=5m avg(avgWaitMillis) as avg_wait, avg(avgSvcMillis) as avg_svc by host
| where avg_wait > 20
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.read_latency) as read_ms avg(Performance.write_latency) as write_ms
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=5m
| eval worst_ms=max(read_ms, write_ms)
| where worst_ms > 20
```

## Visualization

Line chart (latency over time by host), Heatmap of I/O wait across hosts.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
