---
id: "7.2.10"
title: "Elasticsearch Cluster Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.2.10 · Elasticsearch Cluster Health

## Description

Elasticsearch cluster status directly indicates data availability. Yellow/red status requires immediate attention to prevent data loss.

## Value

Elasticsearch cluster status directly indicates data availability. Yellow/red status requires immediate attention to prevent data loss.

## Implementation

Poll `_cluster/health` endpoint every minute. Alert on yellow status (warning) and red status (critical). Track unassigned shard count and node count. Correlate with JVM metrics and disk space to identify root cause.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom REST API input.
• Ensure the following data sources are available: Elasticsearch `_cluster/health` API.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `_cluster/health` endpoint every minute. Alert on yellow status (warning) and red status (critical). Track unassigned shard count and node count. Correlate with JVM metrics and disk space to identify root cause.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="elasticsearch:cluster_health"
| eval status_num=case(status="green",0, status="yellow",1, status="red",2)
| timechart span=5m latest(status_num) as health, latest(unassigned_shards) as unassigned by cluster_name
| where health > 0
```

Understanding this SPL

**Elasticsearch Cluster Health** — Elasticsearch cluster status directly indicates data availability. Yellow/red status requires immediate attention to prevent data loss.

Documented **Data sources**: Elasticsearch `_cluster/health` API. **App/TA** (typical add-on context): Custom REST API input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: elasticsearch:cluster_health. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="elasticsearch:cluster_health". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **status_num** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by cluster_name** — ideal for trending and alerting on this use case.
• Filters the current rows with `where health > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status indicator (green/yellow/red), Single value (unassigned shards), Line chart (cluster health timeline), Table (cluster details).

## SPL

```spl
index=database sourcetype="elasticsearch:cluster_health"
| eval status_num=case(status="green",0, status="yellow",1, status="red",2)
| timechart span=5m latest(status_num) as health, latest(unassigned_shards) as unassigned by cluster_name
| where health > 0
```

## Visualization

Status indicator (green/yellow/red), Single value (unassigned shards), Line chart (cluster health timeline), Table (cluster details).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
