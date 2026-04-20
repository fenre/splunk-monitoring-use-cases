---
id: "7.5.17"
title: "Elasticsearch Pending Cluster Tasks"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.5.17 · Elasticsearch Pending Cluster Tasks

## Description

A growing backlog of pending cluster tasks indicates the master node cannot process cluster state updates fast enough. This delays shard allocation, mapping updates, and index creation.

## Value

A growing backlog of pending cluster tasks indicates the master node cannot process cluster state updates fast enough. This delays shard allocation, mapping updates, and index creation.

## Implementation

Poll `GET _cluster/pending_tasks` every minute. Track the number of tasks and the `time_in_queue_millis` for the oldest task. Alert when queue depth stays above 5 for multiple consecutive samples or any task waits longer than 30 seconds. Common causes include frequent mapping changes, too many small indices, or an overloaded master node.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom REST scripted input (`_cluster/pending_tasks`).
• Ensure the following data sources are available: `sourcetype=elasticsearch:pending_tasks`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `GET _cluster/pending_tasks` every minute. Track the number of tasks and the `time_in_queue_millis` for the oldest task. Alert when queue depth stays above 5 for multiple consecutive samples or any task waits longer than 30 seconds. Common causes include frequent mapping changes, too many small indices, or an overloaded master node.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="elasticsearch:pending_tasks"
| stats max(insert_order) as queue_depth, max(time_in_queue_millis) as max_wait_ms
| where queue_depth > 5 OR max_wait_ms > 30000
```

Understanding this SPL

**Elasticsearch Pending Cluster Tasks** — A growing backlog of pending cluster tasks indicates the master node cannot process cluster state updates fast enough. This delays shard allocation, mapping updates, and index creation.

Documented **Data sources**: `sourcetype=elasticsearch:pending_tasks`. **App/TA** (typical add-on context): Custom REST scripted input (`_cluster/pending_tasks`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: elasticsearch:pending_tasks. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="elasticsearch:pending_tasks". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` aggregates the pipeline (counts, distinct values, sums, percentiles, etc.) into fewer rows.
• Filters the current rows with `where queue_depth > 5 OR max_wait_ms > 30000` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (pending task count), Single value (current queue depth), Table (pending tasks with wait time).

## SPL

```spl
index=database sourcetype="elasticsearch:pending_tasks"
| stats max(insert_order) as queue_depth, max(time_in_queue_millis) as max_wait_ms
| where queue_depth > 5 OR max_wait_ms > 30000
```

## Visualization

Line chart (pending task count), Single value (current queue depth), Table (pending tasks with wait time).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
