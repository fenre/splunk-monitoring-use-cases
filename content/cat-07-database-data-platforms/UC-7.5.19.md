---
id: "7.5.19"
title: "Elasticsearch Segment Merge Pressure"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.5.19 · Elasticsearch Segment Merge Pressure

## Description

Heavy segment merge activity competes with search for disk I/O, causing latency spikes. Merge throttling slows indexing. Monitoring merge pressure helps balance indexing throughput against search performance.

## Value

Heavy segment merge activity competes with search for disk I/O, causing latency spikes. Merge throttling slows indexing. Monitoring merge pressure helps balance indexing throughput against search performance.

## Implementation

Poll `GET _nodes/stats/indices/merges` for `current`, `total_size_in_bytes`, `total_time_in_millis`, and `total_throttled_time_in_millis`. Compute merge rate and throttle ratio. Alert when active merges remain high (>3) for sustained periods, or when throttle time exceeds 50% of total merge time. Correlate with indexing rate and search latency to detect I/O contention.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom REST scripted input (`_nodes/stats/indices/merges`).
• Ensure the following data sources are available: `sourcetype=elasticsearch:merge_stats`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `GET _nodes/stats/indices/merges` for `current`, `total_size_in_bytes`, `total_time_in_millis`, and `total_throttled_time_in_millis`. Compute merge rate and throttle ratio. Alert when active merges remain high (>3) for sustained periods, or when throttle time exceeds 50% of total merge time. Correlate with indexing rate and search latency to detect I/O contention.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="elasticsearch:merge_stats"
| eval merge_rate_mb=merges.total_size_in_bytes/1048576
| timechart span=5m avg(merges.current) as active_merges, sum(merge_rate_mb) as merge_mb by node_name
| where active_merges > 3
```

Understanding this SPL

**Elasticsearch Segment Merge Pressure** — Heavy segment merge activity competes with search for disk I/O, causing latency spikes. Merge throttling slows indexing. Monitoring merge pressure helps balance indexing throughput against search performance.

Documented **Data sources**: `sourcetype=elasticsearch:merge_stats`. **App/TA** (typical add-on context): Custom REST scripted input (`_nodes/stats/indices/merges`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: elasticsearch:merge_stats. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="elasticsearch:merge_stats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **merge_rate_mb** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by node_name** — ideal for trending and alerting on this use case.
• Filters the current rows with `where active_merges > 3` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t sum(Performance.cpu_load_percent) as agg_value from datamodel=Performance.Network by Performance.host span=5m | sort - agg_value
```

Understanding this CIM / accelerated SPL

**Elasticsearch Segment Merge Pressure** — Heavy segment merge activity competes with search for disk I/O, causing latency spikes. Merge throttling slows indexing. Monitoring merge pressure helps balance indexing throughput against search performance.

Documented **Data sources**: `sourcetype=elasticsearch:merge_stats`. **App/TA** (typical add-on context): Custom REST scripted input (`_nodes/stats/indices/merges`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance.Network` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (active merges over time), Stacked area (merge vs. throttle time), Single value (current merge count).

## SPL

```spl
index=database sourcetype="elasticsearch:merge_stats"
| eval merge_rate_mb=merges.total_size_in_bytes/1048576
| timechart span=5m avg(merges.current) as active_merges, sum(merge_rate_mb) as merge_mb by node_name
| where active_merges > 3
```

## CIM SPL

```spl
| tstats summariesonly=t sum(Performance.cpu_load_percent) as agg_value from datamodel=Performance.Network by Performance.host span=5m | sort - agg_value
```

## Visualization

Line chart (active merges over time), Stacked area (merge vs. throttle time), Single value (current merge count).

## References

- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
