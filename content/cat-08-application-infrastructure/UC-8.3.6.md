<!-- AUTO-GENERATED from UC-8.3.6.json — DO NOT EDIT -->

---
id: "8.3.6"
title: "Message Throughput Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.3.6 · Message Throughput Trending

## Description

Throughput trending identifies capacity limits and validates scaling decisions. Unexpected drops indicate producer or broker issues.

## Value

Throughput trending identifies capacity limits and validates scaling decisions. Unexpected drops indicate producer or broker issues.

## Implementation

Poll broker throughput metrics via JMX. Track messages and bytes in/out per broker and per topic. Baseline normal patterns. Alert on sudden throughput drops (possible producer failure).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: JMX, broker management APIs.
• Ensure the following data sources are available: Kafka broker metrics (MessagesInPerSec), RabbitMQ message rates.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll broker throughput metrics via JMX. Track messages and bytes in/out per broker and per topic. Baseline normal patterns. Alert on sudden throughput drops (possible producer failure).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=kafka sourcetype="kafka:broker"
| timechart span=5m sum(MessagesInPerSec) as msgs_in, sum(BytesInPerSec) as bytes_in
```

Understanding this SPL

**Message Throughput Trending** — Throughput trending identifies capacity limits and validates scaling decisions. Unexpected drops indicate producer or broker issues.

Documented **Data sources**: Kafka broker metrics (MessagesInPerSec), RabbitMQ message rates. **App/TA** (typical add-on context): JMX, broker management APIs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: kafka; **sourcetype**: kafka:broker. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=kafka, sourcetype="kafka:broker". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets — ideal for trending and alerting on this use case.


Step 3 — Validate
Compare with the broker or gateway’s own UI or CLI (`kafka-consumer-groups`, RabbitMQ management, ActiveMQ console, or Traefik/Envoy access log on the node) for the same period.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (throughput over time), Stacked area (throughput by topic), Dual-axis (messages + bytes).

## SPL

```spl
index=kafka sourcetype="kafka:broker"
| timechart span=5m sum(MessagesInPerSec) as msgs_in, sum(BytesInPerSec) as bytes_in
```

## Visualization

Line chart (throughput over time), Stacked area (throughput by topic), Dual-axis (messages + bytes).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
