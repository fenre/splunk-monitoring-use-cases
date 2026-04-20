---
id: "4.1.51"
title: "Lambda Concurrent Executions and Throttling"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.1.51 · Lambda Concurrent Executions and Throttling

## Description

Throttling occurs when concurrent executions hit account or function limits. Monitoring prevents dropped invocations and supports quota increase requests.

## Value

Throttling occurs when concurrent executions hit account or function limits. Monitoring prevents dropped invocations and supports quota increase requests.

## Implementation

Collect Lambda metrics. Alert on Throttles > 0. Monitor ConcurrentExecutions vs account limit (1000 default). Consider reserved concurrency for critical functions. Dashboard invocations, duration, errors, throttles together.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: CloudWatch Lambda metrics (ConcurrentExecutions, Throttles).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Lambda metrics. Alert on Throttles > 0. Monitor ConcurrentExecutions vs account limit (1000 default). Consider reserved concurrency for critical functions. Dashboard invocations, duration, errors, throttles together.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Lambda" metric_name="Throttles"
| where Sum > 0
| timechart span=5m sum(Sum) by FunctionName
```

Understanding this SPL

**Lambda Concurrent Executions and Throttling** — Throttling occurs when concurrent executions hit account or function limits. Monitoring prevents dropped invocations and supports quota increase requests.

Documented **Data sources**: CloudWatch Lambda metrics (ConcurrentExecutions, Throttles). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where Sum > 0` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by FunctionName** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (concurrent, throttles by function), Table (function, throttles), Single value (account concurrent %).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Lambda" metric_name="Throttles"
| where Sum > 0
| timechart span=5m sum(Sum) by FunctionName
```

## Visualization

Line chart (concurrent, throttles by function), Table (function, throttles), Single value (account concurrent %).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
