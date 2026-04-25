<!-- AUTO-GENERATED from UC-8.7.5.json — DO NOT EDIT -->

---
id: "8.7.5"
title: "Message Queue Backlog Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.7.5 · Message Queue Backlog Trending

## Description

Queue depth over 7 and 30 days shows sustained consumer lag versus transient spikes. Growth trends drive consumer scaling, partition adds, or poison-message handling before disk limits or SLA misses.

## Value

Queue depth over 7 and 30 days shows sustained consumer lag versus transient spikes. Growth trends drive consumer scaling, partition adds, or poison-message handling before disk limits or SLA misses.

## Implementation

Align Kafka lag with consumer group and partition; use `max` across partitions for worst-case visibility. Exclude retry/DLQ topics from primary charts or show separately. Set thresholds from peak business hours using historical baselines. For cloud queues, map metric dimensions to the same `qname` namespace.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Kafka, RabbitMQ, ActiveMQ, AWS MSK / Azure Event Hubs TAs.
• Ensure the following data sources are available: `index=middleware` `sourcetype=kafka:consumer`, `rabbitmq:queue`, `activemq:queue`, `azure:eventhub:metrics`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Align Kafka lag with consumer group and partition; use `max` across partitions for worst-case visibility. Exclude retry/DLQ topics from primary charts or show separately. Set thresholds from peak business hours using historical baselines. For cloud queues, map metric dimensions to the same `qname` namespace.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=middleware earliest=-30d (sourcetype="kafka:consumer" OR sourcetype="rabbitmq:queue" OR sourcetype="activemq:queue")
| eval depth=coalesce(consumer_lag, lag, queue_depth, backlog_messages)
| eval qname=coalesce(topic_queue, queue, destination)
| timechart span=1d max(depth) as queue_depth by qname limit=15
```

Understanding this SPL

**Message Queue Backlog Trending** — Queue depth over 7 and 30 days shows sustained consumer lag versus transient spikes. Growth trends drive consumer scaling, partition adds, or poison-message handling before disk limits or SLA misses.

Documented **Data sources**: `index=middleware` `sourcetype=kafka:consumer`, `rabbitmq:queue`, `activemq:queue`, `azure:eventhub:metrics`. **App/TA** (typical add-on context): Splunk Add-on for Kafka, RabbitMQ, ActiveMQ, AWS MSK / Azure Event Hubs TAs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: middleware; **sourcetype**: kafka:consumer, rabbitmq:queue, activemq:queue. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=middleware, sourcetype="kafka:consumer", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **depth** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **qname** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by qname limit=15** — ideal for trending and alerting on this use case.


Step 3 — Validate
Compare with the application or platform source of truth (logs, UI, or metrics) for the same time range, and with known change or maintenance windows.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (max depth by queue), area chart (7d vs 30d overlay using `timewrap`), table (top queues by growth rate).

## SPL

```spl
index=middleware earliest=-30d (sourcetype="kafka:consumer" OR sourcetype="rabbitmq:queue" OR sourcetype="activemq:queue")
| eval depth=coalesce(consumer_lag, lag, queue_depth, backlog_messages)
| eval qname=coalesce(topic_queue, queue, destination)
| timechart span=1d max(depth) as queue_depth by qname limit=15
```

## Visualization

Line chart (max depth by queue), area chart (7d vs 30d overlay using `timewrap`), table (top queues by growth rate).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
