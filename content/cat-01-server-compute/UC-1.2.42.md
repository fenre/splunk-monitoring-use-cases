---
id: "1.2.42"
title: ".NET CLR Performance Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.2.42 · .NET CLR Performance Monitoring

## Description

.NET garbage collection pauses and high exception rates cause application latency and instability. CLR monitoring reveals issues invisible to external health checks.

## Value

.NET garbage collection pauses and high exception rates cause application latency and instability. CLR monitoring reveals issues invisible to external health checks.

## Implementation

Configure Perfmon inputs for `.NET CLR Memory` object: `% Time in GC`, `# Gen 2 Collections`, `Large Object Heap size`. Also monitor `.NET CLR Exceptions` → `# of Exceps Thrown / sec`. >20% time in GC indicates memory pressure in .NET apps. Frequent Gen 2 collections signal large object allocation issues. Target specific app pool instances (w3wp) for IIS applications.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=Perfmon:dotNET_CLR_Memory` (counters: % Time in GC, Gen 2 Collections).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Perfmon inputs for `.NET CLR Memory` object: `% Time in GC`, `# Gen 2 Collections`, `Large Object Heap size`. Also monitor `.NET CLR Exceptions` → `# of Exceps Thrown / sec`. >20% time in GC indicates memory pressure in .NET apps. Frequent Gen 2 collections signal large object allocation issues. Target specific app pool instances (w3wp) for IIS applications.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=perfmon sourcetype="Perfmon:dotNET_CLR_Memory" counter="% Time in GC" instance!="_Global_"
| timechart span=5m avg(Value) as pct_gc by host, instance
| where pct_gc > 20
```

Understanding this SPL

**.NET CLR Performance Monitoring** — .NET garbage collection pauses and high exception rates cause application latency and instability. CLR monitoring reveals issues invisible to external health checks.

Documented **Data sources**: `sourcetype=Perfmon:dotNET_CLR_Memory` (counters: % Time in GC, Gen 2 Collections). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: perfmon; **sourcetype**: Perfmon:dotNET_CLR_Memory. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=perfmon, sourcetype="Perfmon:dotNET_CLR_Memory". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host, instance** — ideal for trending and alerting on this use case.
• Filters the current rows with `where pct_gc > 20` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```

Understanding this CIM / accelerated SPL

**.NET CLR Performance Monitoring** — .NET garbage collection pauses and high exception rates cause application latency and instability. CLR monitoring reveals issues invisible to external health checks.

Documented **Data sources**: `sourcetype=Perfmon:dotNET_CLR_Memory` (counters: % Time in GC, Gen 2 Collections). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.
• Filters the current rows with `where avg_cpu > 90` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (GC time %), Bar chart (Gen 2 collections by app), Dual-axis (GC time + exceptions).

## SPL

```spl
index=perfmon sourcetype="Perfmon:dotNET_CLR_Memory" counter="% Time in GC" instance!="_Global_"
| timechart span=5m avg(Value) as pct_gc by host, instance
| where pct_gc > 20
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```

## Visualization

Line chart (GC time %), Bar chart (Gen 2 collections by app), Dual-axis (GC time + exceptions).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
