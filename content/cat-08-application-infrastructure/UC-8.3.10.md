---
id: "8.3.10"
title: "Message Age Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.3.10 · Message Age Monitoring

## Description

Old messages in queues indicate processing delays that may violate SLAs. Age tracking provides a business-relevant metric beyond raw queue depth.

## Value

Old messages in queues indicate processing delays that may violate SLAs. Age tracking provides a business-relevant metric beyond raw queue depth.

## Implementation

Poll message age metrics from queue management APIs. For Kafka, compare consumer offset timestamp with current time. Alert when message age exceeds SLA (e.g., >5 minutes for real-time queues). Differentiate by queue priority.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Queue management API.
• Ensure the following data sources are available: RabbitMQ management API (message age), custom consumer timestamp comparison.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll message age metrics from queue management APIs. For Kafka, compare consumer offset timestamp with current time. Alert when message age exceeds SLA (e.g., >5 minutes for real-time queues). Differentiate by queue priority.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=messaging sourcetype="rabbitmq:queue"
| eval message_age_sec=now()-oldest_message_timestamp
| where message_age_sec > 300
| table queue_name, vhost, messages, message_age_sec
| sort -message_age_sec
```

Understanding this SPL

**Message Age Monitoring** — Old messages in queues indicate processing delays that may violate SLAs. Age tracking provides a business-relevant metric beyond raw queue depth.

Documented **Data sources**: RabbitMQ management API (message age), custom consumer timestamp comparison. **App/TA** (typical add-on context): Queue management API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: messaging; **sourcetype**: rabbitmq:queue. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=messaging, sourcetype="rabbitmq:queue". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **message_age_sec** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where message_age_sec > 300` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Message Age Monitoring**): table queue_name, vhost, messages, message_age_sec
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (queues with old messages), Bar chart (message age by queue), Single value (max message age).

## SPL

```spl
index=messaging sourcetype="rabbitmq:queue"
| eval message_age_sec=now()-oldest_message_timestamp
| where message_age_sec > 300
| table queue_name, vhost, messages, message_age_sec
| sort -message_age_sec
```

## Visualization

Table (queues with old messages), Bar chart (message age by queue), Single value (max message age).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
