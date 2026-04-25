<!-- AUTO-GENERATED from UC-4.1.27.json — DO NOT EDIT -->

---
id: "4.1.27"
title: "API Gateway 4xx/5xx and Throttling"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.1.27 · API Gateway 4xx/5xx and Throttling

## Description

High 4xx/5xx or throttling indicates misconfigured APIs, backend failures, or abuse. Essential for API reliability and quota management.

## Value

High 4xx/5xx or throttling indicates misconfigured APIs, backend failures, or abuse. Essential for API reliability and quota management.

## Implementation

Enable detailed metrics for API Gateway (per-stage). Ingest CloudWatch. Alert on 5XXError rate >1% or ThrottleCount > 0. Optionally enable access logging to S3 for request-level analysis.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: CloudWatch API Gateway metrics (Count, 4XXError, 5XXError, IntegrationLatency).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable detailed metrics for API Gateway (per-stage). Ingest CloudWatch. Alert on 5XXError rate >1% or ThrottleCount > 0. Optionally enable access logging to S3 for request-level analysis.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/ApiGateway" (metric_name="5XXError" OR metric_name="Count")
| timechart span=5m sum(Sum) by metric_name, ApiName, Stage
| eval error_rate = 5XXError / Count * 100
| where error_rate > 1
```

Understanding this SPL

**API Gateway 4xx/5xx and Throttling** — High 4xx/5xx or throttling indicates misconfigured APIs, backend failures, or abuse. Essential for API reliability and quota management.

Documented **Data sources**: CloudWatch API Gateway metrics (Count, 4XXError, 5XXError, IntegrationLatency). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by metric_name, ApiName, Stage** — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **error_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where error_rate > 1` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (errors, count, latency), Table (API, stage, error rate), Single value.

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/ApiGateway" (metric_name="5XXError" OR metric_name="Count")
| timechart span=5m sum(Sum) by metric_name, ApiName, Stage
| eval error_rate = 5XXError / Count * 100
| where error_rate > 1
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Performance.Performance
  by Performance.object Performance.app span=1h
| sort -count
```

## Visualization

Line chart (errors, count, latency), Table (API, stage, error rate), Single value.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
