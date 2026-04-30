<!-- AUTO-GENERATED from UC-8.4.28.json — DO NOT EDIT -->

---
id: "8.4.28"
title: "Kafka Log Cleaner Backlog and Compaction Errors"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.4.28 · Kafka Log Cleaner Backlog and Compaction Errors

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity &middot; **Status:** Draft

*We help you prevent silent growth of uncompacted segments and highlights disks or file handles that are nearing limits on brokers running log compaction.*

---

## Description

Cleaner WARN/ERROR lines signal compaction stalls, I/O errors deleting segments, or topics that cannot keep up with delete-retention—often precursors to disk exhaustion on compacted topics.

## Value

Prevents silent growth of uncompacted segments and highlights disks or file handles that are nearing limits on brokers running log compaction.

## Implementation

Enable collection of `log-cleaner.log` alongside other Kafka logs. For deeper coverage, join with host disk metrics. Tune thresholds per cluster; some WARN noise is normal during rebalance.

## SPL

```spl
index=kafka sourcetype="kafka:logCleanerLog"
| rex "^\[[^\]]+\]\s+(?<log_level>\w+)"
| where log_level IN ("WARN","ERROR")
| stats count by host, log_level
| where count > 0
```

## Visualization

Timeline (cleaner errors), Bar chart (count by host), Table (recent raw messages).

## Known False Positives

Queues grow during consumer maintenance, slow consumers, or burst producer activity. Seasonal traffic can also create sustained backlog without a hard fault.

## References

- [Source types for the Splunk Add-on for Kafka](https://docs.splunk.com/Documentation/AddOns/released/Kafka/Sourcetypes)
- [Apache Kafka — Log compaction](https://kafka.apache.org/documentation/#compaction)
