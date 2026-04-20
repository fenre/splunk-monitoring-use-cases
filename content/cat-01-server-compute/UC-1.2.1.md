---
id: "1.2.1"
title: "CPU Utilization Trending (Windows)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.2.1 · CPU Utilization Trending (Windows)

## Description

Sustained high CPU causes application timeouts and service degradation. Trending enables capacity planning and helps identify runaway processes.

## Value

Sustained high CPU causes application timeouts and service degradation. Trending enables capacity planning and helps identify runaway processes.

## Implementation

Configure Perfmon inputs in `inputs.conf` on the UF: `[perfmon://CPU]`, object=Processor, counters=% Processor Time, instances=_Total, interval=60. Alert on sustained >90% for 15+ minutes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=Perfmon:CPU` (Perfmon input: `Processor`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Perfmon inputs in `inputs.conf` on the UF: `[perfmon://CPU]`, object=Processor, counters=% Processor Time, instances=_Total, interval=60. Alert on sustained >90% for 15+ minutes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=perfmon sourcetype="Perfmon:CPU" counter="% Processor Time" instance="_Total"
| timechart span=1h avg(Value) as avg_cpu by host
| where avg_cpu > 90
```

Understanding this SPL

**CPU Utilization Trending (Windows)** — Sustained high CPU causes application timeouts and service degradation. Trending enables capacity planning and helps identify runaway processes.

Documented **Data sources**: `sourcetype=Perfmon:CPU` (Perfmon input: `Processor`). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: perfmon; **sourcetype**: Perfmon:CPU. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=perfmon, sourcetype="Perfmon:CPU". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where avg_cpu > 90` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```

Understanding this CIM / accelerated SPL

**CPU Utilization Trending (Windows)** — Sustained high CPU causes application timeouts and service degradation. Trending enables capacity planning and helps identify runaway processes.

Documented **Data sources**: `sourcetype=Perfmon:CPU` (Perfmon input: `Processor`). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.
• Filters the current rows with `where avg_cpu > 90` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (timechart), Single value (current), Heatmap across hosts.

## SPL

```spl
index=perfmon sourcetype="Perfmon:CPU" counter="% Processor Time" instance="_Total"
| timechart span=1h avg(Value) as avg_cpu by host
| where avg_cpu > 90
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```

## Visualization

Line chart (timechart), Single value (current), Heatmap across hosts.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
