---
id: "7.1.11"
title: "Buffer Cache Hit Ratio"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.1.11 · Buffer Cache Hit Ratio

## Description

Low buffer cache hit ratio means excessive disk I/O. Monitoring guides memory allocation decisions.

## Value

Low buffer cache hit ratio means excessive disk I/O. Monitoring guides memory allocation decisions.

## Implementation

Poll buffer cache performance counters via DB Connect every 15 minutes. Alert when hit ratio drops below 95% for sustained periods. Correlate with memory pressure and query workload changes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: DB Connect, performance counters.
• Ensure the following data sources are available: SQL Server performance counters, PostgreSQL `pg_stat_bgwriter`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll buffer cache performance counters via DB Connect every 15 minutes. Alert when hit ratio drops below 95% for sustained periods. Correlate with memory pressure and query workload changes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:perf_counters"
| where counter_name="Buffer cache hit ratio"
| timechart span=15m avg(cntr_value) as hit_ratio by instance_name
| where hit_ratio < 95
```

Understanding this SPL

**Buffer Cache Hit Ratio** — Low buffer cache hit ratio means excessive disk I/O. Monitoring guides memory allocation decisions.

Documented **Data sources**: SQL Server performance counters, PostgreSQL `pg_stat_bgwriter`. **App/TA** (typical add-on context): DB Connect, performance counters. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:perf_counters. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:perf_counters". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where counter_name="Buffer cache hit ratio"` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=15m** buckets with a separate series **by instance_name** — ideal for trending and alerting on this use case.
• Filters the current rows with `where hit_ratio < 95` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Databases.Database_Instance by Database_Instance.host, Database_Instance.action span=15m | sort - count
```

Understanding this CIM / accelerated SPL

**Buffer Cache Hit Ratio** — Low buffer cache hit ratio means excessive disk I/O. Monitoring guides memory allocation decisions.

Documented **Data sources**: SQL Server performance counters, PostgreSQL `pg_stat_bgwriter`. **App/TA** (typical add-on context): DB Connect, performance counters. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Databases.Database_Instance` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (buffer cache hit ratio), Line chart (hit ratio over time), Single value (current hit ratio %).

## SPL

```spl
index=database sourcetype="dbconnect:perf_counters"
| where counter_name="Buffer cache hit ratio"
| timechart span=15m avg(cntr_value) as hit_ratio by instance_name
| where hit_ratio < 95
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Databases.Database_Instance by Database_Instance.host, Database_Instance.action span=15m | sort - count
```

## Visualization

Gauge (buffer cache hit ratio), Line chart (hit ratio over time), Single value (current hit ratio %).

## References

- [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)
