<!-- AUTO-GENERATED from UC-7.1.65.json — DO NOT EDIT -->

---
id: "7.1.65"
title: "ClickHouse Detached Parts Accumulation"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.65 · ClickHouse Detached Parts Accumulation

## Description

Detached parts often follow failed merges, hardware errors, or manual `DETACH PART` operations; unchecked growth implies data integrity work and risks query failures when ATTACH is attempted inconsistently across replicas.

## Value

Surfaces silent disk consumption and replication repair work before backups and restores become mandatory.

## Implementation

If using `system.detached_parts`, emit `database`, `table`, `partition_id`, `name`, `reason` per row or aggregate `count` hourly. If only `system.parts` is available, filter `active=0` and name patterns per your export. Alert on new reasons containing `broken` or sudden partition count jumps.

## SPL

```spl
index=database sourcetype="clickhouse:parts"
| where detached==1 OR match(_raw,"detached")
| stats dc(partition) as detached_partitions sum(rows) as detached_rows latest(reason) as detach_reason by database, table, host
| where detached_partitions > 3 OR detached_rows > 1000000
```

## Visualization

Table (database, table, detached_partitions, detach_reason), Line chart (detached row count).

## References

- [ClickHouse — system.detached_parts](https://clickhouse.com/docs/en/operations/system-tables/detached_parts)
