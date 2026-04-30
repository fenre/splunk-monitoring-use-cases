<!-- AUTO-GENERATED from UC-7.4.17.json — DO NOT EDIT -->

---
id: "7.4.17"
title: "ClickHouse Active Data Parts Growth"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.4.17 · ClickHouse Active Data Parts Growth

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Capacity &middot; **Status:** Draft

*We watch how fast active data parts grow in ClickHouse so we can tune merges and storage before disk pressure or slow queries catch us off guard.*

---

## Description

Too many active parts increases merge pressure and degrades queries. Operators watch parts count and on-disk bytes per table as core ClickHouse capacity metrics.

## Value

Predicts when merges and inserts will fall behind and when storage costs will jump unexpectedly.

## Implementation

Hourly aggregate from system.parts with active=1. Store active_parts and size_bytes numerically. Alert when parts exceed policy for hot tiers or bytes cross purchase thresholds. Pair with TTL and partition key reviews.

## SPL

```spl
index=database sourcetype="clickhouse:parts_summary"
| where active_parts > 5000 OR size_bytes > 1099511627776
| timechart span=1h max(active_parts) as parts max(size_bytes) as bytes by database, table
```

## Visualization

Line chart (parts over time), Table (largest tables), Single value (max parts).

## Known False Positives

Merge, part count, and disk signals spike during bulk loads and after schema or partition changes; compare with ETL and migration windows before paging.

## References

- [ClickHouse system.parts](https://clickhouse.com/docs/en/operations/system-tables/parts)
