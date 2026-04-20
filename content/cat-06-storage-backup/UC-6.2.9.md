---
id: "6.2.9"
title: "Pre-Signed URL Abuse Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-6.2.9 · Pre-Signed URL Abuse Detection

## Description

Unusual volume of pre-signed GET/PUT or access from unexpected IPs may indicate credential theft or insider abuse.

## Value

Unusual volume of pre-signed GET/PUT or access from unexpected IPs may indicate credential theft or insider abuse.

## Implementation

Parse query string for presigned parameters. Baseline requests per requester/IP. Alert on spikes or geo anomalies. Correlate with IAM changes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws` (S3 access logs), CloudTrail data events.
• Ensure the following data sources are available: S3 server access logs with `queryString` containing `X-Amz-`, `Signature`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Parse query string for presigned parameters. Baseline requests per requester/IP. Alert on spikes or geo anomalies. Correlate with IAM changes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:s3:accesslogs"
| search query_string="*X-Amz-*" OR query_string="*Signature*"
| stats count by bucket_name, requester, remote_ip
| eventstats avg(count) as avg_c, stdev(count) as stdev_c by bucket_name
| where count > avg_c + 3*stdev_c
```

Understanding this SPL

**Pre-Signed URL Abuse Detection** — Unusual volume of pre-signed GET/PUT or access from unexpected IPs may indicate credential theft or insider abuse.

Documented **Data sources**: S3 server access logs with `queryString` containing `X-Amz-`, `Signature`. **App/TA** (typical add-on context): `Splunk_TA_aws` (S3 access logs), CloudTrail data events. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:s3:accesslogs. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:s3:accesslogs". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by bucket_name, requester, remote_ip** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eventstats` rolls up events into metrics; results are split **by bucket_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > avg_c + 3*stdev_c` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (top presigned requesters), Line chart (presigned request rate), Map (remote_ip).

## SPL

```spl
index=aws sourcetype="aws:s3:accesslogs"
| search query_string="*X-Amz-*" OR query_string="*Signature*"
| stats count by bucket_name, requester, remote_ip
| eventstats avg(count) as avg_c, stdev(count) as stdev_c by bucket_name
| where count > avg_c + 3*stdev_c
```

## Visualization

Table (top presigned requesters), Line chart (presigned request rate), Map (remote_ip).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
