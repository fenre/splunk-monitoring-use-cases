<!-- AUTO-GENERATED from UC-7.1.62.json — DO NOT EDIT -->

---
id: "7.1.62"
title: "ClickHouse Mark Cache and Uncompressed Cache Hit Ratio"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.1.62 · ClickHouse Mark Cache and Uncompressed Cache Hit Ratio

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Status:** Draft

*We surface slow and blocking queries so we can fix the worst offenders first and keep applications and batch jobs within the response times we promise.*

---

## Description

Low mark or uncompressed cache hit ratios force more disk reads for the same queries, inflating latency after restarts or cache churn. Watching the hit ratio explains sudden query slowdowns that CPU metrics miss.

## Value

Speeds diagnosis of cold-cache incidents and validates sizing after hardware changes.

## Implementation

Emit asynchronous metrics every 60s with fields `metric`, `value`. Pivot Hits/Misses pairs for MarkCache and UncompressedCache in Splunk (metric names follow ClickHouse defaults). After restart, expect temporary drops; alert only when sustained below baseline for >1 hour compared to prior week.

## SPL

```spl
index=database sourcetype="clickhouse:asynchronous_metrics"
| where match(metric,"MarkCache") OR match(metric,"UncompressedCache")
| eval hit=if(match(metric,"Hits"), value, null())
| eval miss=if(match(metric,"Misses"), value, null())
| stats sum(hit) as hits sum(miss) as misses by host, _time
| eval hit_ratio=round(hits/(hits+misses+0.001)*100,2)
| where hit_ratio < 70
```

## Visualization

Line chart (hit_ratio), Area chart (hits vs misses stacked).

## Known False Positives

Merge, part count, and disk signals spike during bulk loads and after schema or partition changes; compare with ETL and migration windows before paging.

## References

- [ClickHouse — system.asynchronous_metrics](https://clickhouse.com/docs/en/operations/system-tables/asynchronous_metrics)
