---
id: "1.1.101"
title: "Context Switch Anomalies Detection"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.101 · Context Switch Anomalies Detection

## Description

Context switch anomalies indicate scheduler issues or unexpected process workload changes.

## Value

Context switch anomalies indicate scheduler issues or unexpected process workload changes.

## Implementation

Use vmstat context switch field with statistical anomaly detection. Alert on 3-sigma deviations from baseline. Include process state analysis to identify cause.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`.
• Ensure the following data sources are available: `sourcetype=vmstat`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use vmstat context switch field with statistical anomaly detection. Alert on 3-sigma deviations from baseline. Include process state analysis to identify cause.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=vmstat host=*
| stats avg(cs) as baseline
| eventstats stdev(cs) as stddev
| where cs > baseline + 3*stddev
```

Understanding this SPL

**Context Switch Anomalies Detection** — Context switch anomalies indicate scheduler issues or unexpected process workload changes.

Documented **Data sources**: `sourcetype=vmstat`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: vmstat. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=vmstat. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` aggregates the pipeline (counts, distinct values, sums, percentiles, etc.) into fewer rows.
• `eventstats` aggregates the pipeline (counts, distinct values, sums, percentiles, etc.) into fewer rows.
• Filters the current rows with `where cs > baseline + 3*stddev` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.mem_used_percent) as mem_pct
                        avg(Performance.swap_used_percent) as swap_pct
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
| where mem_pct > 95 OR swap_pct > 20
```

Understanding this CIM / accelerated SPL

**Context Switch Anomalies Detection** — Context switch anomalies indicate scheduler issues or unexpected process workload changes.

Documented **Data sources**: `sourcetype=vmstat`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.
• Filters the current rows with `where mem_pct > 95 OR swap_pct > 20` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart, Anomaly Detector

## SPL

```spl
index=os sourcetype=vmstat host=*
| stats avg(cs) as baseline
| eventstats stdev(cs) as stddev
| where cs > baseline + 3*stddev
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

Timechart, Anomaly Detector

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
