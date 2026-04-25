<!-- AUTO-GENERATED from UC-1.2.21.json — DO NOT EDIT -->

---
id: "1.2.21"
title: "Disk I/O Queue Length (Windows)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.2.21 · Disk I/O Queue Length (Windows)

## Description

Sustained high disk queue lengths indicate storage bottlenecks invisible to CPU/memory monitoring. Causes application hangs and timeout errors.

## Value

Queue depth can show a disk bottleneck long before average CPU looks bad—if you also watch the primary Perfmon search, you catch contention earlier.

## Implementation

Add `Current Disk Queue Length` and `Avg. Disk sec/Transfer` to Perfmon LogicalDisk inputs (interval=30). A sustained queue >2 per spindle indicates saturation. Correlate with application latency. For SSDs, thresholds differ — focus on `Avg. Disk sec/Transfer` >20ms.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=Perfmon:LogicalDisk` (counter: Current Disk Queue Length).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Add `Current Disk Queue Length` and `Avg. Disk sec/Transfer` to Perfmon LogicalDisk inputs (interval=30). A sustained queue >2 per spindle indicates saturation. Correlate with application latency. For SSDs, thresholds differ — focus on `Avg. Disk sec/Transfer` >20ms.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=perfmon sourcetype="Perfmon:LogicalDisk" counter="Current Disk Queue Length" instance!="_Total"
| timechart span=5m avg(Value) as avg_queue by host, instance
| where avg_queue > 2
```

Understanding this SPL

**Disk I/O Queue Length (Windows)** — Sustained high disk queue lengths indicate storage bottlenecks invisible to CPU/memory monitoring. Causes application hangs and timeout errors.

Documented **Data sources**: `sourcetype=Perfmon:LogicalDisk` (counter: Current Disk Queue Length). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: perfmon; **sourcetype**: Perfmon:LogicalDisk. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=perfmon, sourcetype="Perfmon:LogicalDisk". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host, instance** — ideal for trending and alerting on this use case.
• Filters the current rows with `where avg_queue > 2` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.storage_used_percent) as util
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=5m
| where util >= 0
```

Understanding this CIM / accelerated SPL

**Disk I/O Queue Length (Windows)** — Sustained high disk queue lengths indicate storage bottlenecks invisible to CPU/memory monitoring. Causes application hangs and timeout errors.

Documented **Data sources**: `sourcetype=Perfmon:LogicalDisk` (counter: Current Disk Queue Length). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.
• Filters the current rows with `where disk_pct > 85` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (queue by drive), Heatmap (hosts × drives), Single value (worst queue).

## SPL

```spl
index=perfmon sourcetype="Perfmon:LogicalDisk" counter="Current Disk Queue Length" instance!="_Total"
| timechart span=5m avg(Value) as avg_queue by host, instance
| where avg_queue > 2
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.storage_used_percent) as util
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=5m
| where util >= 0
```

## Visualization

Line chart (queue by drive), Heatmap (hosts × drives), Single value (worst queue).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
