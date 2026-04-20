---
id: "7.5.18"
title: "Elasticsearch Fielddata and Cache Evictions"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.5.18 · Elasticsearch Fielddata and Cache Evictions

## Description

Fielddata evictions force expensive re-computation of in-memory data structures, causing search latency spikes. Query cache evictions reduce the benefit of repeated queries. Tracking eviction rates guides memory tuning.

## Value

Fielddata evictions force expensive re-computation of in-memory data structures, causing search latency spikes. Query cache evictions reduce the benefit of repeated queries. Tracking eviction rates guides memory tuning.

## Implementation

Poll `GET _nodes/stats/indices/fielddata,query_cache,request_cache` and compute deltas for `evictions` counters. Any fielddata eviction is significant — alert immediately and investigate which fields use fielddata (should be using doc_values instead). For query cache, alert when eviction rate exceeds a percentage of total cache entries. Correlate with heap usage.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom REST scripted input (`_nodes/stats/indices/fielddata,query_cache,request_cache`).
• Ensure the following data sources are available: `sourcetype=elasticsearch:cache_stats`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `GET _nodes/stats/indices/fielddata,query_cache,request_cache` and compute deltas for `evictions` counters. Any fielddata eviction is significant — alert immediately and investigate which fields use fielddata (should be using doc_values instead). For query cache, alert when eviction rate exceeds a percentage of total cache entries. Correlate with heap usage.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="elasticsearch:cache_stats"
| eval fd_evict_delta=fielddata.evictions-prev_fd_evictions, qc_evict_delta=query_cache.evictions-prev_qc_evictions
| where fd_evict_delta > 0 OR qc_evict_delta > 100
| timechart span=5m sum(fd_evict_delta) as fielddata_evictions, sum(qc_evict_delta) as query_cache_evictions by node_name
```

Understanding this SPL

**Elasticsearch Fielddata and Cache Evictions** — Fielddata evictions force expensive re-computation of in-memory data structures, causing search latency spikes. Query cache evictions reduce the benefit of repeated queries. Tracking eviction rates guides memory tuning.

Documented **Data sources**: `sourcetype=elasticsearch:cache_stats`. **App/TA** (typical add-on context): Custom REST scripted input (`_nodes/stats/indices/fielddata,query_cache,request_cache`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: elasticsearch:cache_stats. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="elasticsearch:cache_stats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **fd_evict_delta** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where fd_evict_delta > 0 OR qc_evict_delta > 100` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by node_name** — ideal for trending and alerting on this use case.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t sum(Performance.cpu_load_percent) as agg_value from datamodel=Performance.CPU by Performance.host span=5m | sort - agg_value
```

Understanding this CIM / accelerated SPL

**Elasticsearch Fielddata and Cache Evictions** — Fielddata evictions force expensive re-computation of in-memory data structures, causing search latency spikes. Query cache evictions reduce the benefit of repeated queries. Tracking eviction rates guides memory tuning.

Documented **Data sources**: `sourcetype=elasticsearch:cache_stats`. **App/TA** (typical add-on context): Custom REST scripted input (`_nodes/stats/indices/fielddata,query_cache,request_cache`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance.CPU` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (eviction rate by cache type), Bar chart (evictions by node), Single value (fielddata memory size).

## SPL

```spl
index=database sourcetype="elasticsearch:cache_stats"
| eval fd_evict_delta=fielddata.evictions-prev_fd_evictions, qc_evict_delta=query_cache.evictions-prev_qc_evictions
| where fd_evict_delta > 0 OR qc_evict_delta > 100
| timechart span=5m sum(fd_evict_delta) as fielddata_evictions, sum(qc_evict_delta) as query_cache_evictions by node_name
```

## CIM SPL

```spl
| tstats summariesonly=t sum(Performance.cpu_load_percent) as agg_value from datamodel=Performance.CPU by Performance.host span=5m | sort - agg_value
```

## Visualization

Line chart (eviction rate by cache type), Bar chart (evictions by node), Single value (fielddata memory size).

## References

- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
