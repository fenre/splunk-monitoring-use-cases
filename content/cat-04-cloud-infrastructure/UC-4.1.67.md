---
id: "4.1.67"
title: "SNS Delivery Failures"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.1.67 · SNS Delivery Failures

## Description

Failed SMS, email, or HTTP subscriptions break alerting and fan-out; monitoring delivery failures prevents silent notification loss.

## Value

Failed SMS, email, or HTTP subscriptions break alerting and fan-out; monitoring delivery failures prevents silent notification loss.

## Implementation

Enable delivery status logging for HTTP/S endpoints. Ingest CloudWatch metrics per topic. Alert on any failed count sustained 15 minutes. Validate endpoint URLs and DLQ for failed deliveries if configured.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudwatch` (AWS/SNS — NumberOfNotificationsFailed), delivery status logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable delivery status logging for HTTP/S endpoints. Ingest CloudWatch metrics per topic. Alert on any failed count sustained 15 minutes. Validate endpoint URLs and DLQ for failed deliveries if configured.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/SNS" metric_name="NumberOfNotificationsFailed"
| timechart span=15m sum(Sum) as failed by TopicName
| where failed > 0
```

Understanding this SPL

**SNS Delivery Failures** — Failed SMS, email, or HTTP subscriptions break alerting and fan-out; monitoring delivery failures prevents silent notification loss.

Documented **Data sources**: `sourcetype=aws:cloudwatch` (AWS/SNS — NumberOfNotificationsFailed), delivery status logs. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=15m** buckets with a separate series **by TopicName** — ideal for trending and alerting on this use case.
• Filters the current rows with `where failed > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (failures by topic), Table (topic, failed count), Single value (total failures).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/SNS" metric_name="NumberOfNotificationsFailed"
| timechart span=15m sum(Sum) as failed by TopicName
| where failed > 0
```

## Visualization

Line chart (failures by topic), Table (topic, failed count), Single value (total failures).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
