---
id: "4.1.25"
title: "SQS Dead-Letter Queue Message Count"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-4.1.25 · SQS Dead-Letter Queue Message Count

## Description

Messages in DLQ indicate processing failures. Immediate alerting ensures failed messages are investigated and reprocessed.

## Value

Messages in DLQ indicate processing failures. Immediate alerting ensures failed messages are investigated and reprocessed.

## Implementation

Tag or identify DLQ queues (naming convention or tags). Alert when ApproximateNumberOfMessagesVisible > 0 for any DLQ. Create runbook for DLQ investigation and replay.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: CloudWatch SQS metrics for DLQ (ApproximateNumberOfMessagesVisible).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Tag or identify DLQ queues (naming convention or tags). Alert when ApproximateNumberOfMessagesVisible > 0 for any DLQ. Create runbook for DLQ investigation and replay.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/SQS" metric_name="ApproximateNumberOfMessagesVisible"
| search QueueName="*dlq*" OR QueueName="*dead*"
| where Average > 0
| table _time QueueName Average
```

Understanding this SPL

**SQS Dead-Letter Queue Message Count** — Messages in DLQ indicate processing failures. Immediate alerting ensures failed messages are investigated and reprocessed.

Documented **Data sources**: CloudWatch SQS metrics for DLQ (ApproximateNumberOfMessagesVisible). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Filters the current rows with `where Average > 0` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **SQS Dead-Letter Queue Message Count**): table _time QueueName Average


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value (DLQ messages), Table (queue, count), Timeline.

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/SQS" metric_name="ApproximateNumberOfMessagesVisible"
| search QueueName="*dlq*" OR QueueName="*dead*"
| where Average > 0
| table _time QueueName Average
```

## Visualization

Single value (DLQ messages), Table (queue, count), Timeline.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
