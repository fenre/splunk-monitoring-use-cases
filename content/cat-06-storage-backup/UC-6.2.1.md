<!-- AUTO-GENERATED from UC-6.2.1.json — DO NOT EDIT -->

---
id: "6.2.1"
title: "Bucket Capacity Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-6.2.1 · Bucket Capacity Trending

## Description

Tracks storage growth for cost forecasting and lifecycle policy effectiveness. Prevents unexpected cloud bills.

## Value

Tracks storage growth for cost forecasting and lifecycle policy effectiveness. Prevents unexpected cloud bills.

## Implementation

Enable S3 storage metrics in CloudWatch (request metrics may incur cost). Ingest via Splunk Add-on for AWS. Create trending reports by bucket and apply `predict` for growth forecasting.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws` (CloudWatch), Splunk_TA_microsoft-cloudservices.
• Ensure the following data sources are available: CloudWatch S3 metrics (BucketSizeBytes), Azure Blob metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable S3 storage metrics in CloudWatch (request metrics may incur cost). Ingest via Splunk Add-on for AWS. Create trending reports by bucket and apply `predict` for growth forecasting.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" metric_name="BucketSizeBytes"
| timechart span=1d latest(Average) as size_bytes by bucket_name
| eval size_gb=size_bytes/1024/1024/1024
```

Understanding this SPL

**Bucket Capacity Trending** — Tracks storage growth for cost forecasting and lifecycle policy effectiveness. Prevents unexpected cloud bills.

Documented **Data sources**: CloudWatch S3 metrics (BucketSizeBytes), Azure Blob metrics. **App/TA** (typical add-on context): `Splunk_TA_aws` (CloudWatch), Splunk_TA_microsoft-cloudservices. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by bucket_name** — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **size_gb** — often to normalize units, derive a ratio, or prepare for thresholds.


Step 3 — Validate
Compare the same metric, object name, and interval in the vendor or cloud console (array, backup, or object store) that is the source of truth for this feed.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Include who owns the cloud account and the bucket lifecycle policy, because object alerts often need a finance or app owner, not only the storage team. Consider visualizations: Line chart (bucket size over time), Stacked area (total storage by bucket), Table (largest buckets).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" metric_name="BucketSizeBytes"
| timechart span=1d latest(Average) as size_bytes by bucket_name
| eval size_gb=size_bytes/1024/1024/1024
```

## CIM SPL

```spl
| tstats `summariesonly` max(Performance.storage_used_percent) as used_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.object span=1h
| where used_pct > 80
| sort - used_pct
```

## Visualization

Line chart (bucket size over time), Stacked area (total storage by bucket), Table (largest buckets).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
