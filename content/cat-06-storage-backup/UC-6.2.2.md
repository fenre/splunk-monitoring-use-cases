---
id: "6.2.2"
title: "Access Pattern Anomalies"
criticality: "high"
splunkPillar: "Security"
---

# UC-6.2.2 · Access Pattern Anomalies

## Description

Unusual access patterns may indicate data breaches, compromised credentials, or misconfigured applications.

## Value

Unusual access patterns may indicate data breaches, compromised credentials, or misconfigured applications.

## Implementation

Enable S3 server access logging to a dedicated logging bucket. Ingest via SQS-based S3 input. Baseline normal access patterns and alert on statistical outliers. Correlate with IAM changes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws` (S3 access logs), Azure Blob diagnostics.
• Ensure the following data sources are available: S3 access logs, Azure Blob analytics logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable S3 server access logging to a dedicated logging bucket. Ingest via SQS-based S3 input. Baseline normal access patterns and alert on statistical outliers. Correlate with IAM changes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:s3:accesslogs"
| stats count by bucket_name, requester, operation
| eventstats avg(count) as avg_ops, stdev(count) as stdev_ops by bucket_name, operation
| where count > avg_ops + 3*stdev_ops
```

Understanding this SPL

**Access Pattern Anomalies** — Unusual access patterns may indicate data breaches, compromised credentials, or misconfigured applications.

Documented **Data sources**: S3 access logs, Azure Blob analytics logs. **App/TA** (typical add-on context): `Splunk_TA_aws` (S3 access logs), Azure Blob diagnostics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:s3:accesslogs. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:s3:accesslogs". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by bucket_name, requester, operation** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eventstats` rolls up events into metrics; results are split **by bucket_name, operation** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > avg_ops + 3*stdev_ops` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (access volume over time), Table (anomalous access events), Bar chart (operations by requester).

## SPL

```spl
index=aws sourcetype="aws:s3:accesslogs"
| stats count by bucket_name, requester, operation
| eventstats avg(count) as avg_ops, stdev(count) as stdev_ops by bucket_name, operation
| where count > avg_ops + 3*stdev_ops
```

## Visualization

Line chart (access volume over time), Table (anomalous access events), Bar chart (operations by requester).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
