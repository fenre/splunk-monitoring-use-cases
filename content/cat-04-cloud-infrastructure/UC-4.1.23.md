---
id: "4.1.23"
title: "CloudFront Cache Hit Ratio and Origin Errors"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.1.23 · CloudFront Cache Hit Ratio and Origin Errors

## Description

Low cache hit ratio increases origin load and latency. Origin errors indicate backend or CDN misconfiguration.

## Value

Low cache hit ratio increases origin load and latency. Origin errors indicate backend or CDN misconfiguration.

## Implementation

Enable CloudFront metrics in CloudWatch. Optionally enable standard logging to S3 for request-level analysis. Calculate cache hit ratio from requests (Hit vs Miss). Alert on 5xxErrorRate > 1%.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: CloudWatch CloudFront metrics, CloudFront access logs (optional, to S3).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable CloudFront metrics in CloudWatch. Optionally enable standard logging to S3 for request-level analysis. Calculate cache hit ratio from requests (Hit vs Miss). Alert on 5xxErrorRate > 1%.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/CloudFront" (metric_name="4xxErrorRate" OR metric_name="5xxErrorRate" OR metric_name="BytesDownloaded")
| timechart span=1h avg(Average) by metric_name, DistributionId
```

Understanding this SPL

**CloudFront Cache Hit Ratio and Origin Errors** — Low cache hit ratio increases origin load and latency. Origin errors indicate backend or CDN misconfiguration.

Documented **Data sources**: CloudWatch CloudFront metrics, CloudFront access logs (optional, to S3). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by metric_name, DistributionId** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (4xx/5xx rate, bytes), Gauge (cache hit %), Table by distribution.

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/CloudFront" (metric_name="4xxErrorRate" OR metric_name="5xxErrorRate" OR metric_name="BytesDownloaded")
| timechart span=1h avg(Average) by metric_name, DistributionId
```

## Visualization

Line chart (4xx/5xx rate, bytes), Gauge (cache hit %), Table by distribution.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
