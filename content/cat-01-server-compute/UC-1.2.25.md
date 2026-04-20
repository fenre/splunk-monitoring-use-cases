---
id: "1.2.25"
title: "Processor Queue Length"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.2.25 · Processor Queue Length

## Description

Processor queue length >2 per core indicates threads waiting for CPU time. Detects CPU contention even when average utilization looks normal due to burst patterns.

## Value

Processor queue length >2 per core indicates threads waiting for CPU time. Detects CPU contention even when average utilization looks normal due to burst patterns.

## Implementation

Add `Processor Queue Length` to Perfmon System object inputs (interval=30). A sustained queue >2× number of cores indicates saturation. Correlate with `Context Switches/sec` from the same object to distinguish CPU-bound workloads from excessive threading.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=Perfmon:System` (counter: Processor Queue Length).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Add `Processor Queue Length` to Perfmon System object inputs (interval=30). A sustained queue >2× number of cores indicates saturation. Correlate with `Context Switches/sec` from the same object to distinguish CPU-bound workloads from excessive threading.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=perfmon sourcetype="Perfmon:System" counter="Processor Queue Length"
| timechart span=5m avg(Value) as queue_len by host
| where queue_len > 4
```

Understanding this SPL

**Processor Queue Length** — Processor queue length >2 per core indicates threads waiting for CPU time. Detects CPU contention even when average utilization looks normal due to burst patterns.

Documented **Data sources**: `sourcetype=Perfmon:System` (counter: Processor Queue Length). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: perfmon; **sourcetype**: Perfmon:System. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=perfmon, sourcetype="Perfmon:System". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where queue_len > 4` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```

Understanding this CIM / accelerated SPL

**Processor Queue Length** — Processor queue length >2 per core indicates threads waiting for CPU time. Detects CPU contention even when average utilization looks normal due to burst patterns.

Documented **Data sources**: `sourcetype=Perfmon:System` (counter: Processor Queue Length). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.
• Filters the current rows with `where avg_cpu > 90` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (queue trend), Heatmap (hosts × time), Single value (current queue).

## SPL

```spl
index=perfmon sourcetype="Perfmon:System" counter="Processor Queue Length"
| timechart span=5m avg(Value) as queue_len by host
| where queue_len > 4
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```

## Visualization

Line chart (queue trend), Heatmap (hosts × time), Single value (current queue).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
