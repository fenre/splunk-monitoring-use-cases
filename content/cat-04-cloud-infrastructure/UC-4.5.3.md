---
id: "4.5.3"
title: "Lambda Concurrent Execution Limits and Throttling"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.5.3 · Lambda Concurrent Execution Limits and Throttling

## Description

Account- and function-level concurrency caps cause synchronous throttles and async retries; monitoring utilization prevents dropped work during traffic spikes.

## Value

Account- and function-level concurrency caps cause synchronous throttles and async retries; monitoring utilization prevents dropped work during traffic spikes.

## Implementation

Ingest `ConcurrentExecutions`, `Throttles`, and reserved concurrency settings (from tags or a nightly inventory lookup). Compare concurrent usage to reserved and account limits. Alert on any non-zero throttles or when concurrent executions approach the configured cap for bursty functions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudwatch` (namespace `AWS/Lambda`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest `ConcurrentExecutions`, `Throttles`, and reserved concurrency settings (from tags or a nightly inventory lookup). Compare concurrent usage to reserved and account limits. Alert on any non-zero throttles or when concurrent executions approach the configured cap for bursty functions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Lambda" (metric_name="ConcurrentExecutions" OR metric_name="Throttles")
| stats sum(Sum) as volume by FunctionName, metric_name
| xyseries FunctionName metric_name volume
| fillnull value=0
| where Throttles>0
```

Understanding this SPL

**Lambda Concurrent Execution Limits and Throttling** — Account- and function-level concurrency caps cause synchronous throttles and async retries; monitoring utilization prevents dropped work during traffic spikes.

Documented **Data sources**: `sourcetype=aws:cloudwatch` (namespace `AWS/Lambda`). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by FunctionName, metric_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Pivots fields for charting with `xyseries`.
• Fills null values with `fillnull`.
• Filters the current rows with `where Throttles>0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (ConcurrentExecutions vs limit by function), Single value (throttle count), Area chart (stacked concurrency by function).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Lambda" (metric_name="ConcurrentExecutions" OR metric_name="Throttles")
| stats sum(Sum) as volume by FunctionName, metric_name
| xyseries FunctionName metric_name volume
| fillnull value=0
| where Throttles>0
```

## Visualization

Line chart (ConcurrentExecutions vs limit by function), Single value (throttle count), Area chart (stacked concurrency by function).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
