<!-- AUTO-GENERATED from UC-4.1.35.json — DO NOT EDIT -->

---
id: "4.1.35"
title: "S3 Replication Lag and Failed Replication"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.1.35 · S3 Replication Lag and Failed Replication

## Description

Replication lag or failures break DR and compliance. Detecting failures ensures data is replicated within RPO.

## Value

Replication lag or failures break DR and compliance. Detecting failures ensures data is replicated within RPO.

## Implementation

Enable S3 Replication metrics in CloudWatch. Configure event notifications for replication failures (s3:Replication:OperationFailedReplication). Alert on ReplicationLatency > 15 min or any failure event.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: S3 Replication metrics (ReplicationLatency, BytesPendingReplication), S3 event notifications for replication failures.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable S3 Replication metrics in CloudWatch. Configure event notifications for replication failures (s3:Replication:OperationFailedReplication). Alert on ReplicationLatency > 15 min or any failure event.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/S3" metric_name="ReplicationLatency"
| where Average > 900
| timechart span=15m avg(Average) by SourceBucket, DestinationBucket
```

Understanding this SPL

**S3 Replication Lag and Failed Replication** — Replication lag or failures break DR and compliance. Detecting failures ensures data is replicated within RPO.

Documented **Data sources**: S3 Replication metrics (ReplicationLatency, BytesPendingReplication), S3 event notifications for replication failures. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where Average > 900` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=15m** buckets with a separate series **by SourceBucket, DestinationBucket** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (latency by bucket pair), Table (failed replications), Single value (bytes pending).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/S3" metric_name="ReplicationLatency"
| where Average > 900
| timechart span=15m avg(Average) by SourceBucket, DestinationBucket
```

## CIM SPL

```spl
| tstats `summariesonly` max(Performance.cpu_load_percent) as peak
  from datamodel=Performance.Performance
  by Performance.object Performance.host span=1h
| where isnotnull(peak)
| sort - peak
```

## Visualization

Line chart (latency by bucket pair), Table (failed replications), Single value (bytes pending).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
