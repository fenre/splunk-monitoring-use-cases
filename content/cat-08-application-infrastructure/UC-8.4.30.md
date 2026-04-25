<!-- AUTO-GENERATED from UC-8.4.30.json — DO NOT EDIT -->

---
id: "8.4.30"
title: "ActiveMQ Temporary Storage Limit Pressure"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.4.30 · ActiveMQ Temporary Storage Limit Pressure

## Description

Non-persistent and slow-consumer spillover lands in temp storage; hitting `TempLimit` blocks producers even when the persistent store is healthy.

## Value

Isolates slow-consumer and large-message issues before they convert into broker-wide producer blocking.

## Implementation

Map JMX attributes to Splunk fields (`TempLimit`, `TempUsage`, or percent usage). Poll every 60s. Correlate with destination memory usage and consumer advisories. Alert at 70% sustained.

## SPL

```spl
index=messaging sourcetype="activemq:broker"
| eval temp_pct=coalesce(TempPercentUsage, round(temp_used/temp_limit*100,1))
| where temp_pct > 70
| timechart span=5m max(temp_pct) as temp_usage_pct by broker_name
```

## Visualization

Gauge (temp %), Line chart (temp usage trend), Table (brokers over threshold).

## References

- [Apache ActiveMQ — Producer Flow Control](https://activemq.apache.org/components/classic/documentation/producer-flow-control)
- [Apache ActiveMQ — Performance](https://activemq.apache.org/components/classic/documentation/performance-tuning)
