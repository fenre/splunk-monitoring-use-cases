---
id: "1.2.104"
title: "Disk Latency and I/O Performance (Windows)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.2.104 · Disk Latency and I/O Performance (Windows)

## Description

High disk latency directly impacts application performance and user experience. Proactive monitoring prevents performance degradation and identifies failing storage.

## Value

High disk latency directly impacts application performance and user experience. Proactive monitoring prevents performance degradation and identifies failing storage.

## Implementation

Configure Perfmon inputs for LogicalDisk counters: Avg. Disk sec/Read, Avg. Disk sec/Write, Current Disk Queue Length, Disk Transfers/sec. Thresholds: <10ms normal, 10-20ms degraded, >20ms poor, >50ms critical. Alert on sustained latency above 20ms. Correlate with application response times and IOPS counters. Track latency trends for capacity planning and storage migration decisions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=Perfmon:LogicalDisk`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Perfmon inputs for LogicalDisk counters: Avg. Disk sec/Read, Avg. Disk sec/Write, Current Disk Queue Length, Disk Transfers/sec. Thresholds: <10ms normal, 10-20ms degraded, >20ms poor, >50ms critical. Alert on sustained latency above 20ms. Correlate with application response times and IOPS counters. Track latency trends for capacity planning and storage migration decisions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=perfmon source="Perfmon:LogicalDisk" counter IN ("Avg. Disk sec/Read", "Avg. Disk sec/Write", "Current Disk Queue Length")
| eval latency_ms=round(Value*1000, 2)
| stats avg(latency_ms) as AvgLatency max(latency_ms) as MaxLatency by host, instance, counter
| where AvgLatency>20 OR MaxLatency>100
| sort -MaxLatency
```

Understanding this SPL

**Disk Latency and I/O Performance (Windows)** — High disk latency directly impacts application performance and user experience. Proactive monitoring prevents performance degradation and identifies failing storage.

Documented **Data sources**: `sourcetype=Perfmon:LogicalDisk`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: perfmon.

**Pipeline walkthrough**

• Scopes the data: index=perfmon. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **latency_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host, instance, counter** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where AvgLatency>20 OR MaxLatency>100` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.storage_used_percent) as disk_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=1h
| where disk_pct > 85
```

Understanding this CIM / accelerated SPL

**Disk Latency and I/O Performance (Windows)** — High disk latency directly impacts application performance and user experience. Proactive monitoring prevents performance degradation and identifies failing storage.

Documented **Data sources**: `sourcetype=Perfmon:LogicalDisk`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.
• Filters the current rows with `where disk_pct > 85` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart (latency trend), Gauge (current latency), Table (high-latency volumes).

## SPL

```spl
index=perfmon source="Perfmon:LogicalDisk" counter IN ("Avg. Disk sec/Read", "Avg. Disk sec/Write", "Current Disk Queue Length")
| eval latency_ms=round(Value*1000, 2)
| stats avg(latency_ms) as AvgLatency max(latency_ms) as MaxLatency by host, instance, counter
| where AvgLatency>20 OR MaxLatency>100
| sort -MaxLatency
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.storage_used_percent) as disk_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=1h
| where disk_pct > 85
```

## Visualization

Timechart (latency trend), Gauge (current latency), Table (high-latency volumes).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
