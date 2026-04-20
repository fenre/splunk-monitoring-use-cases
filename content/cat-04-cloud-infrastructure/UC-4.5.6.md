---
id: "4.5.6"
title: "Azure Functions Queue Trigger Backlog and Failures"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.5.6 · Azure Functions Queue Trigger Backlog and Failures

## Description

Queue-triggered functions depend on storage or Service Bus depth; growing backlogs mean consumers cannot keep pace or messages are poisoned.

## Value

Queue-triggered functions depend on storage or Service Bus depth; growing backlogs mean consumers cannot keep pace or messages are poisoned.

## Implementation

Ingest queue depth metrics for the storage account or Service Bus namespace backing the trigger. Correlate with FunctionAppLogs for dequeue/processing errors. Alert when depth exceeds threshold or poison-message handling spikes. Map queue resource to Function App via tags or a lookup.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: `sourcetype=mscs:azure:metrics` (Storage Queue / Service Bus), `sourcetype=mscs:azure:diagnostics`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest queue depth metrics for the storage account or Service Bus namespace backing the trigger. Correlate with FunctionAppLogs for dequeue/processing errors. Alert when depth exceeds threshold or poison-message handling spikes. Map queue resource to Function App via tags or a lookup.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:metrics" (metricName="QueueMessageCount" OR metricName="ActiveMessages")
| timechart span=5m avg(average) as depth by resourceName, metricName
| join type=left max=1 resourceName
    [ search index=azure sourcetype="mscs:azure:diagnostics" Category="FunctionAppLogs" "QueueTrigger"
    | stats count as trigger_errors by resourceName ]
| where depth > 1000 OR trigger_errors > 0
```

Understanding this SPL

**Azure Functions Queue Trigger Backlog and Failures** — Queue-triggered functions depend on storage or Service Bus depth; growing backlogs mean consumers cannot keep pace or messages are poisoned.

Documented **Data sources**: `sourcetype=mscs:azure:metrics` (Storage Queue / Service Bus), `sourcetype=mscs:azure:diagnostics`. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:metrics. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by resourceName, metricName** — ideal for trending and alerting on this use case.
• Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
• Filters the current rows with `where depth > 1000 OR trigger_errors > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Dual-axis line chart (queue depth vs successful executions), Table (queue, depth, errors), Single value (oldest message age if exported).

## SPL

```spl
index=azure sourcetype="mscs:azure:metrics" (metricName="QueueMessageCount" OR metricName="ActiveMessages")
| timechart span=5m avg(average) as depth by resourceName, metricName
| join type=left max=1 resourceName
    [ search index=azure sourcetype="mscs:azure:diagnostics" Category="FunctionAppLogs" "QueueTrigger"
    | stats count as trigger_errors by resourceName ]
| where depth > 1000 OR trigger_errors > 0
```

## Visualization

Dual-axis line chart (queue depth vs successful executions), Table (queue, depth, errors), Single value (oldest message age if exported).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
