<!-- AUTO-GENERATED from UC-1.2.2.json — DO NOT EDIT -->

---
id: "1.2.2"
title: "Memory Utilization & Paging (Windows)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.2.2 · Memory Utilization & Paging (Windows)

## Description

High memory and excessive paging degrade performance. Page file usage indicates the system is under memory pressure.

## Value

Pressure here shows up as slow apps and stability risk—catching it early avoids paging storms and OOM pain.

## Implementation

Configure Perfmon input for Memory object: counters = `% Committed Bytes In Use`, `Available MBytes`, `Pages/sec`. Alert when committed bytes >90% or pages/sec sustained >1000.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=Perfmon:Memory`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Perfmon input for Memory object: counters = `% Committed Bytes In Use`, `Available MBytes`, `Pages/sec`. Alert when committed bytes >90% or pages/sec sustained >1000.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=perfmon sourcetype="Perfmon:Memory" (counter="% Committed Bytes In Use" OR counter="Pages/sec")
| timechart span=5m avg(Value) by counter, host
```

Understanding this SPL

**Memory Utilization & Paging (Windows)** — High memory and excessive paging degrade performance. Page file usage indicates the system is under memory pressure.

Documented **Data sources**: `sourcetype=Perfmon:Memory`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: perfmon; **sourcetype**: Perfmon:Memory. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=perfmon, sourcetype="Perfmon:Memory". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by counter, host** — ideal for trending and alerting on this use case.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.mem_used) as mem_used
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
```

Understanding this CIM / accelerated SPL

**Memory Utilization & Paging (Windows)** — High memory and excessive paging degrade performance. Page file usage indicates the system is under memory pressure.

Documented **Data sources**: `sourcetype=Perfmon:Memory`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.
• Filters the current rows with `where mem_pct > 95 OR swap_pct > 20` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Dual-axis line chart (memory % + pages/sec), Gauge widget.

## SPL

```spl
index=perfmon sourcetype="Perfmon:Memory" (counter="% Committed Bytes In Use" OR counter="Pages/sec")
| timechart span=5m avg(Value) by counter, host
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.mem_used) as mem_used
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
```

## Visualization

Dual-axis line chart (memory % + pages/sec), Gauge widget.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
