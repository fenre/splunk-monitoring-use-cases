<!-- AUTO-GENERATED from UC-8.5.23.json — DO NOT EDIT -->

---
id: "8.5.23"
title: "RabbitMQ Unacknowledged Message Growth Rate (Consumer Stall Signal)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.5.23 · RabbitMQ Unacknowledged Message Growth Rate (Consumer Stall Signal)

## Description

A sustained rise in `messages_unacknowledged` while `consumer_utilisation` stays low usually means consumers have stalled, prefetch is exhausted, or processing latency jumped before queue depth (`messages_ready`) explodes. Catching the growth rate early limits backlog and memory pressure on the broker.

## Value

Reduces time-to-detect silent consumer failure, preventing publisher throttling and SLA breaches on latency-sensitive workloads.

## Implementation

Poll `/api/queues` at least every 60s; normalize `name`/`vhost` consistently. Tune `unacked_growth` and minimum `unacked` to your traffic. Exclude federation/shovel internal queues via a lookup if needed.

## SPL

```spl
index=messaging sourcetype="rabbitmq:queue" earliest=-4h
| bin _time span=5m
| stats latest(messages_unacknowledged) as unacked latest(consumer_utilisation) as cu by _time, vhost, name
| sort 0 vhost name _time
| streamstats window=2 global=f current=f last(unacked) as prev_unacked by vhost, name
| eval unacked_growth=unacked-prev_unacked
| where unacked_growth >= 100 AND unacked >= 200 AND (isnull(cu) OR cu < 0.4)
| table _time, vhost, name, unacked, prev_unacked, unacked_growth, cu
```

## Visualization

Line chart (`messages_unacknowledged` per queue), overlay `consumer_utilisation`; single-value alert on growth; table of worst queues.

## References

- [RabbitMQ — Queue metrics (ready vs unacknowledged)](https://www.rabbitmq.com/docs/management#queue-metrics)
- [Splunk — AMQP Messaging Modular Input](https://splunkbase.splunk.com/app/1812)
