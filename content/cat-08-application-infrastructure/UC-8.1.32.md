<!-- AUTO-GENERATED from UC-8.1.32.json — DO NOT EDIT -->

---
id: "8.1.32"
title: "ActiveMQ Broker Memory Limit Pressure"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.1.32 · ActiveMQ Broker Memory Limit Pressure

## Description

Broker memory percent tracks usage against the broker-wide memory limit before producers are blocked or messages are spooled to temp storage.

## Value

Prevents broker-wide flow control and slow-consumer spirals by catching memory pressure before the store or temp limits are hit.

## Implementation

Poll broker MBean every 60s via JMX. Map attribute names to Splunk fields (`MemoryPercentUsage` is common on Classic brokers). Correlate with slow consumer advisories and destination memory usage. Alert at 70% sustained 10 minutes; tune per broker sizing.

## SPL

```spl
index=messaging sourcetype="activemq:broker"
| eval mem_pct=coalesce(MemoryPercentUsage, memory_percent_usage)
| where mem_pct > 70
| timechart span=5m max(mem_pct) as broker_memory_pct by broker_name
```

## Visualization

Gauge (current memory %), Line chart (memory % trend), Table (brokers over threshold).

## References

- [Apache ActiveMQ — JMX](https://activemq.apache.org/components/classic/documentation/jmx)
- [Apache ActiveMQ — Performance](https://activemq.apache.org/components/classic/documentation/performance-tuning)
