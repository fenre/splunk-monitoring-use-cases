---
id: "1.1.30"
title: "Scheduler Latency and Run Queue Depth"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.30 · Scheduler Latency and Run Queue Depth

## Description

High run queue depth with elevated scheduling latency causes visible application performance degradation.

## Value

High run queue depth with elevated scheduling latency causes visible application performance degradation.

## Implementation

Monitor run queue (r) field from vmstat and correlate with process count. When run queue exceeds 2x CPU count, alert on scheduler saturation. Create SPL to identify top CPU-consuming processes during high latency periods.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=vmstat, top, custom:sched_latency`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor run queue (r) field from vmstat and correlate with process count. When run queue exceeds 2x CPU count, alert on scheduler saturation. Create SPL to identify top CPU-consuming processes during high latency periods.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=vmstat host=*
| eval runq_to_cpu=r/procs_cpu
| stats avg(runq_to_cpu) as avg_ratio by host
| where avg_ratio > 2
```

Understanding this SPL

**Scheduler Latency and Run Queue Depth** — High run queue depth with elevated scheduling latency causes visible application performance degradation.

Documented **Data sources**: `sourcetype=vmstat, top, custom:sched_latency`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: vmstat. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=vmstat. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **runq_to_cpu** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where avg_ratio > 2` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.mem_used_percent) as mem_pct
                        avg(Performance.swap_used_percent) as swap_pct
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
| where mem_pct > 95 OR swap_pct > 20
```

Understanding this CIM / accelerated SPL

**Scheduler Latency and Run Queue Depth** — High run queue depth with elevated scheduling latency causes visible application performance degradation.

Documented **Data sources**: `sourcetype=vmstat, top, custom:sched_latency`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.
• Filters the current rows with `where mem_pct > 95 OR swap_pct > 20` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart, Multi-series Line Chart

## SPL

```spl
index=os sourcetype=vmstat host=*
| eval runq_to_cpu=r/procs_cpu
| stats avg(runq_to_cpu) as avg_ratio by host
| where avg_ratio > 2
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.mem_used_percent) as mem_pct
                        avg(Performance.swap_used_percent) as swap_pct
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
| where mem_pct > 95 OR swap_pct > 20
```

## Visualization

Timechart, Multi-series Line Chart

## References

- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
