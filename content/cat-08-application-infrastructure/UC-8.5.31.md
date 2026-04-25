<!-- AUTO-GENERATED from UC-8.5.31.json — DO NOT EDIT -->

---
id: "8.5.31"
title: "ActiveMQ Dead Letter Queue (DLQ) Accumulation"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.5.31 · ActiveMQ Dead Letter Queue (DLQ) Accumulation

## Description

Poison messages and repeated redeliveries land in ActiveMQ dead-letter destinations; any sustained `QueueSize` above zero usually means a consumer or schema defect is starving healthy traffic. Tracking DLQ depth by broker catches regressions after deployments.

## Value

Surfaces application-level failures that do not trip generic broker health checks but still block business transactions until someone replays or discards bad messages.

## Implementation

Normalize DLQ naming (`ActiveMQ.DLQ` vs custom) via lookup. Alert on any non-zero depth for golden paths, or rate-of-change for high-volume environments. Pair with message sampling outside Splunk if bodies contain PII.

## SPL

```spl
index=messaging sourcetype="activemq:broker" earliest=-24h
| eval dest=coalesce(DestinationName, destination_name)
| eval qsize=coalesce(QueueSize, queue_size, QueueDepth)
| where match(dest, "(?i)DLQ|dead\\.letter|ActiveMQ\\.DLQ")
| where qsize > 0
| timechart span=15m max(qsize) as dlq_depth by dest, broker_name limit=20
```

## Visualization

Line chart (DLQ depth), table (broker, destination, depth), single value (total DLQ messages).

## References

- [Apache ActiveMQ — Redelivery and Dead Letter](https://activemq.apache.org/message-redelivery-and-dlq-handling)
- [Apache ActiveMQ — JMX](https://activemq.apache.org/jmx.html)
