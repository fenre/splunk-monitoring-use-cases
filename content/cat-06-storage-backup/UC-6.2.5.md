---
id: "6.2.5"
title: "Cross-Region Replication Lag"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.5 · Cross-Region Replication Lag

## Description

Replication lag affects DR readiness. Monitoring ensures geo-redundant data meets RPO requirements.

## Value

Replication lag affects DR readiness. Monitoring ensures geo-redundant data meets RPO requirements.

## Implementation

Enable S3 replication metrics in CloudWatch. Ingest and alert when replication latency or pending operations exceed thresholds. Correlate with data ingestion spikes that may cause temporary lag.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Cloud provider TAs.
• Ensure the following data sources are available: S3 replication metrics (ReplicationLatency, OperationsPendingReplication).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable S3 replication metrics in CloudWatch. Ingest and alert when replication latency or pending operations exceed thresholds. Correlate with data ingestion spikes that may cause temporary lag.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" metric_name="ReplicationLatency"
| timechart span=1h avg(Average) as replication_lag_sec by bucket_name
| where replication_lag_sec > 3600
```

Understanding this SPL

**Cross-Region Replication Lag** — Replication lag affects DR readiness. Monitoring ensures geo-redundant data meets RPO requirements.

Documented **Data sources**: S3 replication metrics (ReplicationLatency, OperationsPendingReplication). **App/TA** (typical add-on context): Cloud provider TAs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by bucket_name** — ideal for trending and alerting on this use case.
• Filters the current rows with `where replication_lag_sec > 3600` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (replication lag over time), Single value (max lag), Table (buckets with lag exceeding SLA).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" metric_name="ReplicationLatency"
| timechart span=1h avg(Average) as replication_lag_sec by bucket_name
| where replication_lag_sec > 3600
```

## Visualization

Line chart (replication lag over time), Single value (max lag), Table (buckets with lag exceeding SLA).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
