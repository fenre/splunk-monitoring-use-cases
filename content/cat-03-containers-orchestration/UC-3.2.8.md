---
id: "3.2.8"
title: "etcd Cluster Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.2.8 · etcd Cluster Health

## Description

etcd stores all Kubernetes state. etcd problems (leader elections, compaction failures, high latency) cascade into cluster-wide failures.

## Value

etcd stores all Kubernetes state. etcd problems (leader elections, compaction failures, high latency) cascade into cluster-wide failures.

## Implementation

Scrape etcd metrics via OTel Collector. Monitor disk fsync latency (<10ms healthy), database size, leader changes, and proposal failures. Alert on leader changes (indicates instability) and high fsync latency.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk OTel Collector, etcd metrics.
• Ensure the following data sources are available: etcd Prometheus metrics (scraped by OTel).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Scrape etcd metrics via OTel Collector. Monitor disk fsync latency (<10ms healthy), database size, leader changes, and proposal failures. Alert on leader changes (indicates instability) and high fsync latency.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:etcd"
| timechart span=5m avg(etcd_disk_wal_fsync_duration_seconds) as fsync_latency, sum(etcd_server_leader_changes_seen_total) as leader_changes
| where fsync_latency > 0.01 OR leader_changes > 0
```

Understanding this SPL

**etcd Cluster Health** — etcd stores all Kubernetes state. etcd problems (leader elections, compaction failures, high latency) cascade into cluster-wide failures.

Documented **Data sources**: etcd Prometheus metrics (scraped by OTel). **App/TA** (typical add-on context): Splunk OTel Collector, etcd metrics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:etcd. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:etcd". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets — ideal for trending and alerting on this use case.
• Filters the current rows with `where fsync_latency > 0.01 OR leader_changes > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (fsync latency, db size), Single value (leader changes), Gauge (db size).

## SPL

```spl
index=k8s sourcetype="kube:etcd"
| timechart span=5m avg(etcd_disk_wal_fsync_duration_seconds) as fsync_latency, sum(etcd_server_leader_changes_seen_total) as leader_changes
| where fsync_latency > 0.01 OR leader_changes > 0
```

## Visualization

Line chart (fsync latency, db size), Single value (leader changes), Gauge (db size).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
