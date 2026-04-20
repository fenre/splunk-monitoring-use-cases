---
id: "4.2.56"
title: "Azure Storage Queue Depth and Poison Messages"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.2.56 · Azure Storage Queue Depth and Poison Messages

## Description

Storage Queues decouple application components. Growing queue depth indicates consumers cannot keep up; poison messages in the poison queue represent permanently failed processing that needs attention.

## Value

Storage Queues decouple application components. Growing queue depth indicates consumers cannot keep up; poison messages in the poison queue represent permanently failed processing that needs attention.

## Implementation

Collect Azure Monitor metrics for Storage Account queue services. Monitor `QueueMessageCount` for growing backlogs and `QueueCapacity` for storage limits. Set up a separate alert for poison queues (queues ending in `-poison`) with any messages. Alert when main queue depth exceeds baseline by 3x or poison queue is non-empty.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics).
• Ensure the following data sources are available: `sourcetype=azure:monitor:metric` (Microsoft.Storage/storageAccounts/queueServices).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Azure Monitor metrics for Storage Account queue services. Monitor `QueueMessageCount` for growing backlogs and `QueueCapacity` for storage limits. Set up a separate alert for poison queues (queues ending in `-poison`) with any messages. Alert when main queue depth exceeds baseline by 3x or poison queue is non-empty.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.storage/storageaccounts" metric_name="QueueMessageCount"
| timechart span=5m avg(average) as queue_depth by resource_name
| where queue_depth > 1000
```

Understanding this SPL

**Azure Storage Queue Depth and Poison Messages** — Storage Queues decouple application components. Growing queue depth indicates consumers cannot keep up; poison messages in the poison queue represent permanently failed processing that needs attention.

Documented **Data sources**: `sourcetype=azure:monitor:metric` (Microsoft.Storage/storageAccounts/queueServices). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: azure:monitor:metric. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="azure:monitor:metric". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by resource_name** — ideal for trending and alerting on this use case.
• Filters the current rows with `where queue_depth > 1000` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (queue depth over time), Single value (current depth), Table (queues with poison messages).

## SPL

```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.storage/storageaccounts" metric_name="QueueMessageCount"
| timechart span=5m avg(average) as queue_depth by resource_name
| where queue_depth > 1000
```

## Visualization

Line chart (queue depth over time), Single value (current depth), Table (queues with poison messages).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
