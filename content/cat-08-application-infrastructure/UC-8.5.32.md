<!-- AUTO-GENERATED from UC-8.5.32.json — DO NOT EDIT -->

---
id: "8.5.32"
title: "ActiveMQ Combined Memory and Persistent Store Percent Usage"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.5.32 · ActiveMQ Combined Memory and Persistent Store Percent Usage

## Description

Classic brokers enforce separate limits for JVM memory (`MemoryLimit`) and the persistence store (`StoreLimit`). Either limit triggers producer blocking or paging, so a single view of both percentages avoids blind spots where memory is fine but disk-backed store is pegged, or the reverse.

## Value

Gives operators one alert surface for the two dominant resource ceilings that throttle messaging throughput.

## Implementation

Poll broker MBeans every 60–300s. Align thresholds with `systemUsage` configuration. Include `TempPercentUsage` in the same dashboard row for non-persistent spillover.

## SPL

```spl
index=messaging sourcetype="activemq:broker" earliest=-4h
| eval mem_pct=coalesce(MemoryPercentUsage, memory_percent_usage, round(memory_used*100/nullif(memory_limit,0),1))
| eval store_pct=coalesce(StorePercentUsage, store_percent_usage, round(store_used*100/nullif(store_limit,0),1))
| where mem_pct > 75 OR store_pct > 75
| table _time, broker_name, mem_pct, store_pct, TempPercentUsage
```

## Visualization

Dual-axis line chart (memory % vs store %), gauge pair per broker, table of breaches.

## References

- [Apache ActiveMQ — SystemUsage (memory, store, temp)](https://activemq.apache.org/producer-flow-control)
- [Apache ActiveMQ — JMX](https://activemq.apache.org/jmx.html)
