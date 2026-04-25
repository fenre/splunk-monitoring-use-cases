<!-- AUTO-GENERATED from UC-6.2.7.json — DO NOT EDIT -->

---
id: "6.2.7"
title: "Cross-Region Replication Lag (SLA)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.7 · Cross-Region Replication Lag (SLA)

## Description

Tracks replication backlog and oldest replicated object age for S3 CRR and Azure geo-replication. Complements byte-level lag with time-based SLA views.

## Value

Tracks replication backlog and oldest replicated object age for S3 CRR and Azure geo-replication. Complements byte-level lag with time-based SLA views.

## Implementation

Set thresholds from RPO (e.g., pending operations or max lag minutes). Alert when backlog grows for >1h. For Azure Blob, ingest replication health metrics from Monitor diagnostics.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Cloud TAs, CloudWatch, Azure Monitor.
• Ensure the following data sources are available: S3 `OperationsPendingReplication`, Azure `GeoReplicationLag` (where available).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Set thresholds from RPO (e.g., pending operations or max lag minutes). Alert when backlog grows for >1h. For Azure Blob, ingest replication health metrics from Monitor diagnostics.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" metric_name="OperationsPendingReplication"
| timechart span=1h max(Maximum) as pending_ops by bucket_name
| where pending_ops > 100000
```

Understanding this SPL

**Cross-Region Replication Lag (SLA)** — Tracks replication backlog and oldest replicated object age for S3 CRR and Azure geo-replication. Complements byte-level lag with time-based SLA views.

Documented **Data sources**: S3 `OperationsPendingReplication`, Azure `GeoReplicationLag` (where available). **App/TA** (typical add-on context): Cloud TAs, CloudWatch, Azure Monitor. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by bucket_name** — ideal for trending and alerting on this use case.
• Filters the current rows with `where pending_ops > 100000` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare the same metric, object name, and interval in the vendor or cloud console (array, backup, or object store) that is the source of truth for this feed.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Include who owns the cloud account and the bucket lifecycle policy, because object alerts often need a finance or app owner, not only the storage team. Consider visualizations: Line chart (pending replication / lag), Table (buckets breaching SLA), Single value (max lag minutes).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" metric_name="OperationsPendingReplication"
| timechart span=1h max(Maximum) as pending_ops by bucket_name
| where pending_ops > 100000
```

## Visualization

Line chart (pending replication / lag), Table (buckets breaching SLA), Single value (max lag minutes).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
