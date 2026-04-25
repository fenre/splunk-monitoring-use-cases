<!-- AUTO-GENERATED from UC-4.6.2.json — DO NOT EDIT -->

---
id: "4.6.2"
title: "Lambda/Function Invocation Volume Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.6.2 · Lambda/Function Invocation Volume Trending

## Description

Daily invocation counts show traffic growth, seasonal patterns, and the impact of new features or batch jobs. Sharp changes often precede cost spikes or throttling if concurrency limits are fixed.

## Value

Daily invocation counts show traffic growth, seasonal patterns, and the impact of new features or batch jobs. Sharp changes often precede cost spikes or throttling if concurrency limits are fixed.

## Implementation

Enable CloudWatch metric ingestion for AWS/Lambda Invocations with FunctionName dimension. For Azure, use Microsoft.Web/sites/functions equivalent metrics. Normalize time to UTC for daily buckets. Use top-N functions by volume to keep the chart readable. Correlate step changes with deployments from CI/CD timestamps.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for AWS (CloudWatch metrics), Azure Monitor.
• Ensure the following data sources are available: `index=cloud sourcetype=aws:cloudwatch` (Lambda Invocations metric); Azure Functions metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable CloudWatch metric ingestion for AWS/Lambda Invocations with FunctionName dimension. For Azure, use Microsoft.Web/sites/functions equivalent metrics. Normalize time to UTC for daily buckets. Use top-N functions by volume to keep the chart readable. Correlate step changes with deployments from CI/CD timestamps.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="aws:cloudwatch" Namespace="AWS/Lambda" MetricName="Invocations"
| bin _time span=1d
| stats sum(Sum) as invocations by _time, FunctionName
| timechart span=1d sum(invocations) as total_invocations
| trendline sma7(total_invocations) as invocation_trend
```

Understanding this SPL

**Lambda/Function Invocation Volume Trending** — Daily invocation counts show traffic growth, seasonal patterns, and the impact of new features or batch jobs. Sharp changes often precede cost spikes or throttling if concurrency limits are fixed.

Documented **Data sources**: `index=cloud sourcetype=aws:cloudwatch` (Lambda Invocations metric); Azure Functions metrics. **App/TA** (typical add-on context): Splunk Add-on for AWS (CloudWatch metrics), Azure Monitor. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: aws:cloudwatch. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time, FunctionName** so each row reflects one combination of those dimensions.
• `timechart` plots the metric over time using **span=1d** buckets — ideal for trending and alerting on this use case.
• Pipeline stage (see **Lambda/Function Invocation Volume Trending**): trendline sma7(total_invocations) as invocation_trend


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (daily invocations with 7-day SMA, 30 days), column chart (top functions by volume).

## SPL

```spl
index=cloud sourcetype="aws:cloudwatch" Namespace="AWS/Lambda" MetricName="Invocations"
| bin _time span=1d
| stats sum(Sum) as invocations by _time, FunctionName
| timechart span=1d sum(invocations) as total_invocations
| trendline sma7(total_invocations) as invocation_trend
```

## Visualization

Line chart (daily invocations with 7-day SMA, 30 days), column chart (top functions by volume).

## References

- [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)
