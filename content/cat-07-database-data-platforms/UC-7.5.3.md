---
id: "7.5.3"
title: "OpenSearch Index Performance"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.5.3 · OpenSearch Index Performance

## Description

Slow merges, refresh intervals, and segment counts drive query latency and heap use; tracking per-index stats keeps search SLAs achievable.

## Value

Slow merges, refresh intervals, and segment counts drive query latency and heap use; tracking per-index stats keeps search SLAs achievable.

## Implementation

Poll `GET /<index>/_stats` or per-index `_stats` every 15 minutes. Extract merges, refresh, indexing, and store size. Compare against baselines; alert when merge or refresh time spikes without matching traffic increase. Review ILM/ISM policies for hot indices.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (OpenSearch `_stats`, `_cat/indices`).
• Ensure the following data sources are available: `sourcetype=opensearch:index_stats`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `GET /<index>/_stats` or per-index `_stats` every 15 minutes. Extract merges, refresh, indexing, and store size. Compare against baselines; alert when merge or refresh time spikes without matching traffic increase. Review ILM/ISM policies for hot indices.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="opensearch:index_stats"
| eval merge_ms=primaries.merges.total_time_in_millis
| eval search_qps=primaries.search.query_total / nullif(uptime_sec,0)
| where merge_ms > 600000 OR primaries.refresh.total_time_in_millis > 300000
| table index, merge_ms, primaries.refresh.total_time_in_millis, store.size_in_bytes
```

Understanding this SPL

**OpenSearch Index Performance** — Slow merges, refresh intervals, and segment counts drive query latency and heap use; tracking per-index stats keeps search SLAs achievable.

Documented **Data sources**: `sourcetype=opensearch:index_stats`. **App/TA** (typical add-on context): Custom scripted input (OpenSearch `_stats`, `_cat/indices`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: opensearch:index_stats. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="opensearch:index_stats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **merge_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **search_qps** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where merge_ms > 600000 OR primaries.refresh.total_time_in_millis > 300000` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **OpenSearch Index Performance**): table index, merge_ms, primaries.refresh.total_time_in_millis, store.size_in_bytes


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (merge and refresh time by index), Table (top indices by merge cost), Bar chart (segment count if extracted).

## SPL

```spl
index=database sourcetype="opensearch:index_stats"
| eval merge_ms=primaries.merges.total_time_in_millis
| eval search_qps=primaries.search.query_total / nullif(uptime_sec,0)
| where merge_ms > 600000 OR primaries.refresh.total_time_in_millis > 300000
| table index, merge_ms, primaries.refresh.total_time_in_millis, store.size_in_bytes
```

## Visualization

Line chart (merge and refresh time by index), Table (top indices by merge cost), Bar chart (segment count if extracted).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
