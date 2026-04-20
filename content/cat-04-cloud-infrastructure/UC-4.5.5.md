---
id: "4.5.5"
title: "Azure Functions Execution Duration"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.5.5 · Azure Functions Execution Duration

## Description

Long-running functions tie up scale-out units and can hit timeout limits; duration trending guides right-sizing, connection pooling, and async patterns.

## Value

Long-running functions tie up scale-out units and can hit timeout limits; duration trending guides right-sizing, connection pooling, and async patterns.

## Implementation

Enable Azure Monitor metrics for Function Apps and ingest via the TA (dimensions: function name where available). Establish baselines per function. Alert when p95 duration approaches the function timeout or degrades after releases.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: `sourcetype=mscs:azure:metrics` (Function metrics).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Azure Monitor metrics for Function Apps and ingest via the TA (dimensions: function name where available). Establish baselines per function. Alert when p95 duration approaches the function timeout or degrades after releases.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:metrics" metricName="FunctionExecutionDuration"
| timechart span=5m avg(average) as avg_ms, max(maximum) as max_ms by resourceName
| where max_ms > 10000
```

Understanding this SPL

**Azure Functions Execution Duration** — Long-running functions tie up scale-out units and can hit timeout limits; duration trending guides right-sizing, connection pooling, and async patterns.

Documented **Data sources**: `sourcetype=mscs:azure:metrics` (Function metrics). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:metrics. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by resourceName** — ideal for trending and alerting on this use case.
• Filters the current rows with `where max_ms > 10000` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (avg/max duration by app or function), Heatmap (duration by hour), Table (resourceName, avg_ms, max_ms).

## SPL

```spl
index=azure sourcetype="mscs:azure:metrics" metricName="FunctionExecutionDuration"
| timechart span=5m avg(average) as avg_ms, max(maximum) as max_ms by resourceName
| where max_ms > 10000
```

## Visualization

Line chart (avg/max duration by app or function), Heatmap (duration by hour), Table (resourceName, avg_ms, max_ms).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
