---
id: "4.1.24"
title: "SQS Queue Depth and Age of Oldest Message"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.1.24 · SQS Queue Depth and Age of Oldest Message

## Description

Growing queue depth or old messages indicate consumers are falling behind or failing. Prevents backlog and SLA breaches.

## Value

Growing queue depth or old messages indicate consumers are falling behind or failing. Prevents backlog and SLA breaches.

## Implementation

Collect SQS metrics. Alert when queue depth exceeds threshold (e.g. 1000) or age of oldest message > 5 minutes. Monitor dead-letter queue (ApproximateNumberOfMessagesDelayed) separately.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: CloudWatch SQS metrics (ApproximateNumberOfMessagesVisible, ApproximateAgeOfOldestMessage).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect SQS metrics. Alert when queue depth exceeds threshold (e.g. 1000) or age of oldest message > 5 minutes. Monitor dead-letter queue (ApproximateNumberOfMessagesDelayed) separately.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/SQS" (metric_name="ApproximateNumberOfMessagesVisible" OR metric_name="ApproximateAgeOfOldestMessage")
| bin _time span=5m
| eval depth=if(metric_name="ApproximateNumberOfMessagesVisible", Average, null()),
       age_s=if(metric_name="ApproximateAgeOfOldestMessage", Average, null())
| stats avg(depth) as depth, avg(age_s) as age_s by _time, QueueName
| where depth > 1000 OR age_s > 300
```

Understanding this SPL

**SQS Queue Depth and Age of Oldest Message** — Growing queue depth or old messages indicate consumers are falling behind or failing. Prevents backlog and SLA breaches.

Documented **Data sources**: CloudWatch SQS metrics (ApproximateNumberOfMessagesVisible, ApproximateAgeOfOldestMessage). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `eval` defines or adjusts **depth** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by _time, QueueName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where depth > 1000 OR age_s > 300` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (depth, age by queue), Single value (oldest message age), Table (queue, depth).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/SQS" (metric_name="ApproximateNumberOfMessagesVisible" OR metric_name="ApproximateAgeOfOldestMessage")
| bin _time span=5m
| eval depth=if(metric_name="ApproximateNumberOfMessagesVisible", Average, null()),
       age_s=if(metric_name="ApproximateAgeOfOldestMessage", Average, null())
| stats avg(depth) as depth, avg(age_s) as age_s by _time, QueueName
| where depth > 1000 OR age_s > 300
```

## Visualization

Line chart (depth, age by queue), Single value (oldest message age), Table (queue, depth).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
