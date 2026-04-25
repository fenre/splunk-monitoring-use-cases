<!-- AUTO-GENERATED from UC-8.5.35.json — DO NOT EDIT -->

---
id: "8.5.35"
title: "ActiveMQ Slow Consumer and Cursor Memory Pressure (Prefetch Backlog)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.5.35 · ActiveMQ Slow Consumer and Cursor Memory Pressure (Prefetch Backlog)

## Description

Slow consumers hold prefetched messages in broker-side cursors; `CursorMemoryUsage` climbing toward limits is the operational mirror of client prefetch backlog. `SlowConsumer` flags on the MBean align with broker-side detection of clients that cannot keep pace.

## Value

Surfaces consumer-side latency before global producer flow control trips, especially on high-prefetch JMS clients.

## Implementation

Poll destination MBeans at moderate frequency to avoid JMX overload. Map `dest` naming to owning teams. Pair results with client GC logs or thread dumps when `SlowConsumer` toggles true.

## SPL

```spl
index=messaging sourcetype="activemq:broker" earliest=-4h
| eval dest=coalesce(DestinationName, destination_name)
| eval cursor_pct=coalesce(cursor_percent_usage, round(CursorMemoryUsage*100/nullif(MemoryLimit,0),1))
| eval slow=coalesce(SlowConsumer, slow_consumer, 0)
| eval mem_pct=coalesce(MemoryPercentUsage, memory_percent_usage)
| where slow==1 OR cursor_pct > 70 OR (mem_pct > 60 AND match(dest, "(?i)consumer|dispatch|tmp"))
| table _time, broker_name, dest, slow, cursor_pct, mem_pct, EnqueueCount, DequeueCount
```

## Visualization

Heatmap (destination × cursor %), line chart of cursor memory, table filtered to `SlowConsumer=1`.

## References

- [Apache ActiveMQ — Slow Consumer Handling](https://activemq.apache.org/slow-consumer-handling)
- [Apache ActiveMQ — JMX](https://activemq.apache.org/jmx.html)
