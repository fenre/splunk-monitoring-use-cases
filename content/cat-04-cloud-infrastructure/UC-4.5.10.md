---
id: "4.5.10"
title: "Lambda Dead Letter Queue Depth and Message Rate"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.5.10 · Lambda Dead Letter Queue Depth and Message Rate

## Description

Messages landing in DLQs mean unprocessed events—often billing, inventory, or security actions—until replayed or dropped.

## Value

Messages landing in DLQs mean unprocessed events—often billing, inventory, or security actions—until replayed or dropped.

## Implementation

Tag or name DLQ queues consistently (`*dlq*`). Ingest SQS CloudWatch metrics per queue. Correlate queue to owning Lambda via Event Source Mapping inventory (lookup table). Alert on any sustained visible message count or sudden spikes after bad deployments.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudwatch` (namespace `AWS/SQS`), optional `sourcetype=aws:cloudwatch:events`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Tag or name DLQ queues consistently (`*dlq*`). Ingest SQS CloudWatch metrics per queue. Correlate queue to owning Lambda via Event Source Mapping inventory (lookup table). Alert on any sustained visible message count or sudden spikes after bad deployments.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/SQS" metric_name="ApproximateNumberOfMessagesVisible"
| where match(QueueName, "(?i)dlq|dead")
| timechart span=5m max(Maximum) as visible by QueueName
| where visible > 0
```

Understanding this SPL

**Lambda Dead Letter Queue Depth and Message Rate** — Messages landing in DLQs mean unprocessed events—often billing, inventory, or security actions—until replayed or dropped.

Documented **Data sources**: `sourcetype=aws:cloudwatch` (namespace `AWS/SQS`), optional `sourcetype=aws:cloudwatch:events`. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where match(QueueName, "(?i)dlq|dead")` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by QueueName** — ideal for trending and alerting on this use case.
• Filters the current rows with `where visible > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value (DLQ depth), Line chart (visible messages by queue), Table (QueueName, linked function, visible).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/SQS" metric_name="ApproximateNumberOfMessagesVisible"
| where match(QueueName, "(?i)dlq|dead")
| timechart span=5m max(Maximum) as visible by QueueName
| where visible > 0
```

## Visualization

Single value (DLQ depth), Line chart (visible messages by queue), Table (QueueName, linked function, visible).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
