<!-- AUTO-GENERATED from UC-8.3.11.json — DO NOT EDIT -->

---
id: "8.3.11"
title: "RabbitMQ Queue Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.3.11 · RabbitMQ Queue Monitoring

## Description

Queue depth, consumer count, message rate, and unacknowledged messages indicate message processing health. Growing depth or unacked messages signal consumer lag or failures.

## Value

Queue depth, consumer count, message rate, and unacknowledged messages indicate message processing health. Growing depth or unacked messages signal consumer lag or failures.

## Implementation

Enable RabbitMQ Management Plugin. Poll `/api/queues` via scripted input (curl with auth) every minute. Parse name, vhost, messages, messages_unacknowledged, messages_ready, consumers, message_stats.publish_details.rate, message_stats.deliver_get_details.rate. Forward to Splunk via HEC. Alert when queue depth exceeds threshold, unacked messages grow, or consumer_count drops to 0 for critical queues. Track publish vs deliver rate delta for backlog detection.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom (RabbitMQ Management API).
• Ensure the following data sources are available: RabbitMQ Management API (`/api/queues`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable RabbitMQ Management Plugin. Poll `/api/queues` via scripted input (curl with auth) every minute. Parse name, vhost, messages, messages_unacknowledged, messages_ready, consumers, message_stats.publish_details.rate, message_stats.deliver_get_details.rate. Forward to Splunk via HEC. Alert when queue depth exceeds threshold, unacked messages grow, or consumer_count drops to 0 for critical queues. Track publish vs deliver rate delta for backlog detection.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=messaging sourcetype="rabbitmq:queue"
| eval unacked_pct=if(messages>0, round(messages_unacknowledged/messages*100,1), 0)
| where messages > 1000 OR messages_unacknowledged > 100 OR consumer_count==0
| timechart span=5m max(messages) as queue_depth, avg(messages_unacknowledged) as unacked by vhost, name
```

Understanding this SPL

**RabbitMQ Queue Monitoring** — Queue depth, consumer count, message rate, and unacknowledged messages indicate message processing health. Growing depth or unacked messages signal consumer lag or failures.

Documented **Data sources**: RabbitMQ Management API (`/api/queues`). **App/TA** (typical add-on context): Custom (RabbitMQ Management API). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: messaging; **sourcetype**: rabbitmq:queue. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=messaging, sourcetype="rabbitmq:queue". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **unacked_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where messages > 1000 OR messages_unacknowledged > 100 OR consumer_count==0` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by vhost, name** — ideal for trending and alerting on this use case.


Step 3 — Validate
Compare with the broker or gateway’s own UI or CLI (`kafka-consumer-groups`, RabbitMQ management, ActiveMQ console, or Traefik/Envoy access log on the node) for the same period.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (queue depth and unacked over time), Table (queues with high depth), Single value (queues with no consumers), Bar chart (message rate by queue).

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=messaging sourcetype="rabbitmq:queue"
| eval unacked_pct=if(messages>0, round(messages_unacknowledged/messages*100,1), 0)
| where messages > 1000 OR messages_unacknowledged > 100 OR consumer_count==0
| timechart span=5m max(messages) as queue_depth, avg(messages_unacknowledged) as unacked by vhost, name
```

## Visualization

Line chart (queue depth and unacked over time), Table (queues with high depth), Single value (queues with no consumers), Bar chart (message rate by queue).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
