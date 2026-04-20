---
id: "7.6.3"
title: "Replication Lag Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.6.3 · Replication Lag Trending

## Description

Maximum and average replication lag by replica over 30 days validates disaster-recovery readiness and read-consistency expectations. Gradual lag growth can signal network, disk, or write-volume problems before replica promotion fails.

## Value

Maximum and average replication lag by replica over 30 days validates disaster-recovery readiness and read-consistency expectations. Gradual lag growth can signal network, disk, or write-volume problems before replica promotion fails.

## Implementation

For SQL Server AG, prefer `database_replica` lag fields consistent with your sync mode. Filter out replicas in paused maintenance. Correlate spikes with large index builds or log chain breaks. Use the same clock source (NTP) across primary and replicas to avoid false lag. Cloud replicas may expose lag in milliseconds—normalize to seconds in `eval`.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: MySQL replica status, PostgreSQL replication, Oracle Data Guard, SQL Server AG metrics.
• Ensure the following data sources are available: `index=db` `sourcetype=mysql:slave`, `sourcetype=postgresql:replication`, `sourcetype=oracle:dg`, `sourcetype=mssql:ag`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
For SQL Server AG, prefer `database_replica` lag fields consistent with your sync mode. Filter out replicas in paused maintenance. Correlate spikes with large index builds or log chain breaks. Use the same clock source (NTP) across primary and replicas to avoid false lag. Cloud replicas may expose lag in milliseconds—normalize to seconds in `eval`.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=db sourcetype IN ("mysql:slave","postgresql:replication","oracle:dg","mssql:ag")
| eval lag_sec=coalesce(seconds_behind_source, replay_lag_seconds, commit_lag_sec, ag_synchronization_health_seconds)
| timechart span=1d max(lag_sec) as max_replica_lag_sec avg(lag_sec) as avg_replica_lag_sec by replica_host limit=15
```

Understanding this SPL

**Replication Lag Trending** — Maximum and average replication lag by replica over 30 days validates disaster-recovery readiness and read-consistency expectations. Gradual lag growth can signal network, disk, or write-volume problems before replica promotion fails.

Documented **Data sources**: `index=db` `sourcetype=mysql:slave`, `sourcetype=postgresql:replication`, `sourcetype=oracle:dg`, `sourcetype=mssql:ag`. **App/TA** (typical add-on context): MySQL replica status, PostgreSQL replication, Oracle Data Guard, SQL Server AG metrics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: db.

**Pipeline walkthrough**

• Scopes the data: index=db. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **lag_sec** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by replica_host limit=15** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (max lag per replica), area chart (avg lag), single value (worst replica lag now).

## SPL

```spl
index=db sourcetype IN ("mysql:slave","postgresql:replication","oracle:dg","mssql:ag")
| eval lag_sec=coalesce(seconds_behind_source, replay_lag_seconds, commit_lag_sec, ag_synchronization_health_seconds)
| timechart span=1d max(lag_sec) as max_replica_lag_sec avg(lag_sec) as avg_replica_lag_sec by replica_host limit=15
```

## Visualization

Line chart (max lag per replica), area chart (avg lag), single value (worst replica lag now).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
