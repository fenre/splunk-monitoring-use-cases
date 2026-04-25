<!-- AUTO-GENERATED from UC-8.6.31.json — DO NOT EDIT -->

---
id: "8.6.31"
title: "RabbitMQ Message Redelivery Rate Spike"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.6.31 · RabbitMQ Message Redelivery Rate Spike

## Description

Sustained redeliveries indicate consumers that ack late, crash mid-processing, or encounter poison messages—often before queue depth alarms fire.

## Value

Surfaces flaky consumers and retry storms that waste broker resources and inflate end-to-end latency.

## Implementation

Normalize field names after JSON extraction (some collectors flatten with underscores). Baseline per queue. Alert when redeliver rate exceeds historical p95 for 15 minutes.

## SPL

```spl
index=messaging sourcetype="rabbitmq:queue"
| eval redeliver_rate=coalesce(message_stats.redeliver_details.rate, redeliver_rate, 0)
| where redeliver_rate > 5
| timechart span=5m sum(redeliver_rate) as redeliver_eps by vhost, name
```

## Visualization

Line chart (redeliver rate by queue), Table (worst queues), Single value (cluster redeliver EPS).

## References

- [RabbitMQ — Confirms and Acknowledgements](https://www.rabbitmq.com/docs/confirms)
- [RabbitMQ — Consumer Prefetch](https://www.rabbitmq.com/docs/consumer-prefetch)
