---
id: "4.1.37"
title: "SNS Delivery Failures and Bounce/Complaint"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.1.37 · SNS Delivery Failures and Bounce/Complaint

## Description

SNS delivery failures mean subscribers are not receiving notifications. Bounce/complaint (for email) affects sender reputation and deliverability.

## Value

SNS delivery failures mean subscribers are not receiving notifications. Bounce/complaint (for email) affects sender reputation and deliverability.

## Implementation

Collect SNS metrics. Alert when NumberOfNotificationsFailed > 0. For email subscriptions, enable bounce/complaint feedback and ingest via SNS or EventBridge. Track delivery success rate.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: CloudWatch SNS metrics (NumberOfNotificationsFailed, NumberOfMessagesFailed).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect SNS metrics. Alert when NumberOfNotificationsFailed > 0. For email subscriptions, enable bounce/complaint feedback and ingest via SNS or EventBridge. Track delivery success rate.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/SNS" metric_name="NumberOfNotificationsFailed"
| where Sum > 0
| timechart span=5m sum(Sum) by TopicName
```

Understanding this SPL

**SNS Delivery Failures and Bounce/Complaint** — SNS delivery failures mean subscribers are not receiving notifications. Bounce/complaint (for email) affects sender reputation and deliverability.

Documented **Data sources**: CloudWatch SNS metrics (NumberOfNotificationsFailed, NumberOfMessagesFailed). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where Sum > 0` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by TopicName** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (failures by topic), Table (topic, failure count), Single value (failed notifications).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/SNS" metric_name="NumberOfNotificationsFailed"
| where Sum > 0
| timechart span=5m sum(Sum) by TopicName
```

## Visualization

Line chart (failures by topic), Table (topic, failure count), Single value (failed notifications).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
