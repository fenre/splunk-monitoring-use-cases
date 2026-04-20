---
id: "8.3.5"
title: "Dead Letter Queue Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.3.5 · Dead Letter Queue Monitoring

## Description

Messages in DLQ represent processing failures that need investigation. They may indicate bugs, schema changes, or downstream failures.

## Value

Messages in DLQ represent processing failures that need investigation. They may indicate bugs, schema changes, or downstream failures.

## Implementation

Monitor DLQ/DLT queues specifically. Alert when any DLQ has messages (should normally be 0). Track DLQ ingestion rate to detect ongoing issues. Sample DLQ messages for root cause analysis.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Queue management API, custom input.
• Ensure the following data sources are available: RabbitMQ DLQ queues, AWS SQS DLQ, Kafka DLT topics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor DLQ/DLT queues specifically. Alert when any DLQ has messages (should normally be 0). Track DLQ ingestion rate to detect ongoing issues. Sample DLQ messages for root cause analysis.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=messaging sourcetype="rabbitmq:queue"
| search queue_name="*dead*" OR queue_name="*dlq*" OR queue_name="*error*"
| where messages > 0
| table _time, vhost, queue_name, messages, message_stats.publish_details.rate
```

Understanding this SPL

**Dead Letter Queue Monitoring** — Messages in DLQ represent processing failures that need investigation. They may indicate bugs, schema changes, or downstream failures.

Documented **Data sources**: RabbitMQ DLQ queues, AWS SQS DLQ, Kafka DLT topics. **App/TA** (typical add-on context): Queue management API, custom input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: messaging; **sourcetype**: rabbitmq:queue. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=messaging, sourcetype="rabbitmq:queue". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Filters the current rows with `where messages > 0` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Dead Letter Queue Monitoring**): table _time, vhost, queue_name, messages, message_stats.publish_details.rate


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value (total DLQ messages), Table (DLQs with counts), Line chart (DLQ growth over time).

## SPL

```spl
index=messaging sourcetype="rabbitmq:queue"
| search queue_name="*dead*" OR queue_name="*dlq*" OR queue_name="*error*"
| where messages > 0
| table _time, vhost, queue_name, messages, message_stats.publish_details.rate
```

## Visualization

Single value (total DLQ messages), Table (DLQs with counts), Line chart (DLQ growth over time).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
