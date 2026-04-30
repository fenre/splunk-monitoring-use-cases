<!-- AUTO-GENERATED from UC-7.1.71.json — DO NOT EDIT -->

---
id: "7.1.71"
title: "Cassandra Hinted Handoff Queue Growth"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.71 · Cassandra Hinted Handoff Queue Growth

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Availability, Resilience &middot; **Status:** Draft

*We watch Cassandra Hinted Handoff Queue Growth so we can keep this part of the data platform within the capacity and quality targets our teams expect.*

---

## Description

Growing hinted handoff backlogs mean writes could not be delivered while peers were down; if hints cannot drain, you risk data loss after TTL on hints expires. Trending queue growth highlights nodes that cannot catch up after outages.

## Value

Supports RPO/RTO commitments after partial failures by forcing repair and capacity actions before hints expire.

## Implementation

Prefer JMX `TotalHintsInProgress` or `HintsService` MBean counters every 60s via `jmx.conf`. If log-only, parse periodic diagnostic jobs that emit numeric hints. Baseline per cluster; alert on sustained upward slope for 45+ minutes. Pair with `cassandra:nodetool_status` DOWN nodes.

## SPL

```spl
index=database sourcetype="cassandra:system"
| search "HintsService" OR "hints in progress" OR "HintsDescriptor"
| eval hints_pending=coalesce(tonumber(total_hints), tonumber(hints_in_progress))
| where hints_pending > 10000
| timechart span=15m max(hints_pending) as hints by host
| streamstats window=3 global=f delta(hints) as hints_delta
| where hints_delta > 5000
```

## Visualization

Area chart (hints by host), Single value (cluster total hints).

## Known False Positives

Repairs, bootstraps, and heavy write bursts increase compaction and hinted-handoff backlog as part of normal Cassandra self-healing — alert on stuck or growing queues outside known batch jobs.

## References

- [Apache Cassandra — Hinted handoff](https://cassandra.apache.org/doc/latest/cassandra/architecture/storage-engine.html#hints)
