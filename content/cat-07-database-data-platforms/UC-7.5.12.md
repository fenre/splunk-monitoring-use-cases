---
id: "7.5.12"
title: "Elasticsearch Thread Pool Rejections"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.5.12 · Elasticsearch Thread Pool Rejections

## Description

Thread pool rejections (HTTP 429) mean the cluster cannot keep up with search or indexing load. Sustained rejections cause data loss on ingest and timeouts on search.

## Value

Thread pool rejections (HTTP 429) mean the cluster cannot keep up with search or indexing load. Sustained rejections cause data loss on ingest and timeouts on search.

## Implementation

Poll `GET _nodes/stats/thread_pool/search,write,get` every minute. Store cumulative `rejected` counters and compute deltas between samples. Alert when any node shows rejections in a 5-minute window. Correlate with JVM heap and CPU to determine root cause (undersized cluster vs. expensive queries vs. bulk indexing spikes). Do not increase queue sizes as a fix — address the underlying load.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom REST scripted input (`_nodes/stats/thread_pool`).
• Ensure the following data sources are available: `sourcetype=elasticsearch:thread_pool`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `GET _nodes/stats/thread_pool/search,write,get` every minute. Store cumulative `rejected` counters and compute deltas between samples. Alert when any node shows rejections in a 5-minute window. Correlate with JVM heap and CPU to determine root cause (undersized cluster vs. expensive queries vs. bulk indexing spikes). Do not increase queue sizes as a fix — address the underlying load.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="elasticsearch:thread_pool"
| eval search_rejected_delta=search.rejected-prev_search_rejected, write_rejected_delta=write.rejected-prev_write_rejected
| where search_rejected_delta > 0 OR write_rejected_delta > 0
| timechart span=5m sum(search_rejected_delta) as search_rejections, sum(write_rejected_delta) as write_rejections by node_name
```

Understanding this SPL

**Elasticsearch Thread Pool Rejections** — Thread pool rejections (HTTP 429) mean the cluster cannot keep up with search or indexing load. Sustained rejections cause data loss on ingest and timeouts on search.

Documented **Data sources**: `sourcetype=elasticsearch:thread_pool`. **App/TA** (typical add-on context): Custom REST scripted input (`_nodes/stats/thread_pool`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: elasticsearch:thread_pool. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="elasticsearch:thread_pool". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **search_rejected_delta** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where search_rejected_delta > 0 OR write_rejected_delta > 0` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by node_name** — ideal for trending and alerting on this use case.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t sum(Performance.cpu_load_percent) as agg_value from datamodel=Performance.CPU by Performance.host span=5m | sort - agg_value
```

Understanding this CIM / accelerated SPL

**Elasticsearch Thread Pool Rejections** — Thread pool rejections (HTTP 429) mean the cluster cannot keep up with search or indexing load. Sustained rejections cause data loss on ingest and timeouts on search.

Documented **Data sources**: `sourcetype=elasticsearch:thread_pool`. **App/TA** (typical add-on context): Custom REST scripted input (`_nodes/stats/thread_pool`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance.CPU` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (rejections per pool over time), Bar chart (rejections by node), Single value (total rejections last hour).

## SPL

```spl
index=database sourcetype="elasticsearch:thread_pool"
| eval search_rejected_delta=search.rejected-prev_search_rejected, write_rejected_delta=write.rejected-prev_write_rejected
| where search_rejected_delta > 0 OR write_rejected_delta > 0
| timechart span=5m sum(search_rejected_delta) as search_rejections, sum(write_rejected_delta) as write_rejections by node_name
```

## CIM SPL

```spl
| tstats summariesonly=t sum(Performance.cpu_load_percent) as agg_value from datamodel=Performance.CPU by Performance.host span=5m | sort - agg_value
```

## Visualization

Line chart (rejections per pool over time), Bar chart (rejections by node), Single value (total rejections last hour).

## References

- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
