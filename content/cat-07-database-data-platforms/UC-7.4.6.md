---
id: "7.4.6"
title: "Elasticsearch Cluster Health and Shard Status"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.4.6 · Elasticsearch Cluster Health and Shard Status

## Description

Red/yellow cluster, unassigned shards, and JVM pressure indicate data availability risk. Early detection prevents data loss and service degradation.

## Value

Red/yellow cluster, unassigned shards, and JVM pressure indicate data availability risk. Early detection prevents data loss and service degradation.

## Implementation

Poll `GET _cluster/health?level=shards` and `GET _cat/shards?v&h=index,shard,prirep,state,node` every 1–2 minutes via REST API scripted input. Parse status (green/yellow/red), unassigned_shards, active_primary_shards. Poll `_cluster/stats` for JVM heap usage. Alert on red status (critical) or yellow (warning). Alert when unassigned_shards >0. Correlate with disk space, JVM pressure, and node availability.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (ES REST API).
• Ensure the following data sources are available: `_cluster/health`, `_cluster/stats`, `_cat/shards`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `GET _cluster/health?level=shards` and `GET _cat/shards?v&h=index,shard,prirep,state,node` every 1–2 minutes via REST API scripted input. Parse status (green/yellow/red), unassigned_shards, active_primary_shards. Poll `_cluster/stats` for JVM heap usage. Alert on red status (critical) or yellow (warning). Alert when unassigned_shards >0. Correlate with disk space, JVM pressure, and node availability.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="elasticsearch:cluster_health"
| eval status_num=case(status="green",0, status="yellow",1, status="red",2)
| where status_num > 0 OR unassigned_shards > 0
| timechart span=5m latest(status_num) as health, latest(unassigned_shards) as unassigned, latest(active_primary_shards) as primary by cluster_name
```

Understanding this SPL

**Elasticsearch Cluster Health and Shard Status** — Red/yellow cluster, unassigned shards, and JVM pressure indicate data availability risk. Early detection prevents data loss and service degradation.

Documented **Data sources**: `_cluster/health`, `_cluster/stats`, `_cat/shards`. **App/TA** (typical add-on context): Custom scripted input (ES REST API). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: elasticsearch:cluster_health. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="elasticsearch:cluster_health". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **status_num** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where status_num > 0 OR unassigned_shards > 0` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by cluster_name** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status indicator (green/yellow/red), Single value (unassigned shards), Table (unassigned shard details), Line chart (cluster health and JVM heap over time).

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=database sourcetype="elasticsearch:cluster_health"
| eval status_num=case(status="green",0, status="yellow",1, status="red",2)
| where status_num > 0 OR unassigned_shards > 0
| timechart span=5m latest(status_num) as health, latest(unassigned_shards) as unassigned, latest(active_primary_shards) as primary by cluster_name
```

## Visualization

Status indicator (green/yellow/red), Single value (unassigned shards), Table (unassigned shard details), Line chart (cluster health and JVM heap over time).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
