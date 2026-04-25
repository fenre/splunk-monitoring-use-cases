<!-- AUTO-GENERATED from UC-8.3.14.json — DO NOT EDIT -->

---
id: "8.3.14"
title: "RabbitMQ Queue Depth Alerts"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.3.14 · RabbitMQ Queue Depth Alerts

## Description

Per-queue `messages_ready` thresholds with business priority tags. Alert routing by `queue` name pattern (`critical.*`).

## Value

Per-queue `messages_ready` thresholds with business priority tags. Alert routing by `queue` name pattern (`critical.*`).

## Implementation

Maintain SLA lookup per queue. Page on critical queue depth. Auto-scale consumers from orchestrator if integrated.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: RabbitMQ management API.
• Ensure the following data sources are available: `rabbitmq:queue` `messages`, `messages_ready`, `consumers`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Maintain SLA lookup per queue. Page on critical queue depth. Auto-scale consumers from orchestrator if integrated.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=messaging sourcetype="rabbitmq:queue"
| lookup rabbitmq_queue_sla queue_name OUTPUT max_depth
| where messages_ready > max_depth OR consumers=0 OR consumers IS NULL
| table vhost name messages_ready consumers max_depth
```

Understanding this SPL

**RabbitMQ Queue Depth Alerts** — Per-queue `messages_ready` thresholds with business priority tags. Alert routing by `queue` name pattern (`critical.*`).

Documented **Data sources**: `rabbitmq:queue` `messages`, `messages_ready`, `consumers`. **App/TA** (typical add-on context): RabbitMQ management API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: messaging; **sourcetype**: rabbitmq:queue. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=messaging, sourcetype="rabbitmq:queue". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where messages_ready > max_depth OR consumers=0 OR consumers IS NULL` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **RabbitMQ Queue Depth Alerts**): table vhost name messages_ready consumers max_depth


Step 3 — Validate
Compare with the broker or gateway’s own UI or CLI (`kafka-consumer-groups`, RabbitMQ management, ActiveMQ console, or Traefik/Envoy access log on the node) for the same period.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (depth vs threshold), Table (breached queues), Single value (queues in alert).

## SPL

```spl
index=messaging sourcetype="rabbitmq:queue"
| lookup rabbitmq_queue_sla queue_name OUTPUT max_depth
| where messages_ready > max_depth OR consumers=0 OR consumers IS NULL
| table vhost name messages_ready consumers max_depth
```

## Visualization

Line chart (depth vs threshold), Table (breached queues), Single value (queues in alert).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
