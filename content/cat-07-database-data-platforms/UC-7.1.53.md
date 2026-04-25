<!-- AUTO-GENERATED from UC-7.1.53.json — DO NOT EDIT -->

---
id: "7.1.53"
title: "ClickHouse Merge Rate vs Insert Rate Imbalance (Part Accumulation)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.1.53 · ClickHouse Merge Rate vs Insert Rate Imbalance (Part Accumulation)

## Description

When inserts create parts faster than background merges retire them, part count balloons toward `Too many parts` errors and queries slow dramatically. Comparing part growth to merge activity surfaces the imbalance before merges fall permanently behind.

## Value

Avoids emergency `OPTIMIZE` fire drills and read outages caused by wide part counts on hot tables.

## Implementation

Schedule a SQL job (or DB Connect query) every five minutes selecting `database`, `table`, `sum(active)` as `active_parts` from `system.parts` group by database, table. Emit to HEC with sourcetype `clickhouse:parts`. Separately log `system.merges` rows or count merge threads as `clickhouse:merges`. Set `props.conf` TIMESTAMP_FIELDS. Alert when active_parts climbs 50% above a four-window baseline while merge_events drop toward zero.

## SPL

```spl
index=database sourcetype="clickhouse:parts"
| bin _time span=15m
| stats sum(active_parts) as parts by database, table, host, _time
| join type=inner database table host _time [
    search index=database sourcetype="clickhouse:merges"
    | bin _time span=15m
    | stats count as merge_events by database, table, host, _time
  ]
| streamstats window=4 global=f avg(parts) as parts_baseline by database, table, host
| where parts > parts_baseline*1.5 AND merge_events < 1
```

## Visualization

Dual-axis line (active_parts vs merge_events), Table (database, table, growth rate).

## References

- [ClickHouse — MergeTree merges](https://clickhouse.com/docs/en/engines/table-engines/mergetree-family/mergetree)
- [ClickHouse — system.parts](https://clickhouse.com/docs/en/operations/system-tables/parts)
