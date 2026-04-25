<!-- AUTO-GENERATED from UC-8.1.31.json — DO NOT EDIT -->

---
id: "8.1.31"
title: "RabbitMQ Queue Consumer Utilisation Degradation"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.31 · RabbitMQ Queue Consumer Utilisation Degradation

## Description

`consumer_utilisation` near zero with ready messages indicates consumers are connected but not keeping up (poison messages, prefetch misuse, or slow handlers), which drives queue latency.

## Value

Detects ineffective consumption early—before only queue depth alarms fire—so teams can fix consumer code, scaling, or prefetch settings.

## Implementation

Ingest queue JSON from `/api/queues` at least every minute. Confirm `consumer_utilisation` is extracted as a number (0–1). Exclude federated/shovel-only queues via a lookup. Page when the condition holds for two consecutive polls on tier-1 queues.

## SPL

```spl
index=messaging sourcetype="rabbitmq:queue"
| where consumers > 0 AND isnotnull(consumer_utilisation) AND consumer_utilisation < 0.50 AND messages_ready > 100
| table _time, vhost, name, consumers, consumer_utilisation, messages_ready
```

## Visualization

Line chart (consumer_utilisation by queue), Table (worst queues), Bar chart (messages_ready).

## References

- [RabbitMQ — Monitoring](https://www.rabbitmq.com/docs/monitoring)
- [RabbitMQ Management HTTP API](https://www.rabbitmq.com/docs/management#http-api)
