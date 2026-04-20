---
id: "7.5.5"
title: "Elasticsearch Indexing Rate Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.5.5 · Elasticsearch Indexing Rate Monitoring

## Description

A sudden drop in docs/s indexed can signal pipeline failures, bulk rejections, or cluster overload; sustained spikes may require scaling or throttling.

## Value

A sudden drop in docs/s indexed can signal pipeline failures, bulk rejections, or cluster overload; sustained spikes may require scaling or throttling.

## Implementation

Poll `GET _nodes/stats` every minute; extract `indices.indexing.index_total`, `index_time_in_millis`, and `index_current`. Store prior sample to compute rate of change. Set dynamic or static baselines; alert on drops below expected ingest or on `indexing` rejections from bulk thread pool.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (`_nodes/stats` indexing).
• Ensure the following data sources are available: `sourcetype=elasticsearch:indexing_stats`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `GET _nodes/stats` every minute; extract `indices.indexing.index_total`, `index_time_in_millis`, and `index_current`. Store prior sample to compute rate of change. Set dynamic or static baselines; alert on drops below expected ingest or on `indexing` rejections from bulk thread pool.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="elasticsearch:indexing_stats"
| timechart span=1m per_second(indexing.index_total) as index_rate by node_name
```

Understanding this SPL

**Elasticsearch Indexing Rate Monitoring** — A sudden drop in docs/s indexed can signal pipeline failures, bulk rejections, or cluster overload; sustained spikes may require scaling or throttling.

Documented **Data sources**: `sourcetype=elasticsearch:indexing_stats`. **App/TA** (typical add-on context): Custom scripted input (`_nodes/stats` indexing). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: elasticsearch:indexing_stats. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="elasticsearch:indexing_stats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1m** buckets with a separate series **by node_name** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (documents indexed per second by node), Single value (cluster aggregate rate), Area chart (indexing time vs. count).

## SPL

```spl
index=database sourcetype="elasticsearch:indexing_stats"
| timechart span=1m per_second(indexing.index_total) as index_rate by node_name
```

## Visualization

Line chart (documents indexed per second by node), Single value (cluster aggregate rate), Area chart (indexing time vs. count).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
