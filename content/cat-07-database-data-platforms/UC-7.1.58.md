<!-- AUTO-GENERATED from UC-7.1.58.json — DO NOT EDIT -->

---
id: "7.1.58"
title: "ClickHouse Stuck or Failed Mutations"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.58 · ClickHouse Stuck or Failed Mutations

## Description

ALTER … UPDATE/DELETE mutations that stall leave schema and data in limbo and block merges. Tracking `parts_to_do` and failure columns prevents silent drift where applications assume DDL has fully applied.

## Value

Avoids incorrect analytics and compliance exposure when partial mutations leave old values visible longer than expected.

## Implementation

Export `SELECT * FROM system.mutations WHERE not is_done OR latest_failed_part != ''` every few minutes. Map `mutation_id`, `command`, `parts_to_do`, `latest_fail_reason`, `latest_failed_part`. Kill or retry policies should be documented in runbooks; alert on backlog growth for >30 minutes.

## SPL

```spl
index=database sourcetype="clickhouse:mutations"
| where is_done==0 OR is_done=="false" OR latest_failed_part!="" OR isNull(is_done)
| eval backlog=tonumber(parts_to_do)
| where backlog > 50 OR match(_raw,"exception") OR match(_raw,"Cannot")
| stats max(backlog) as max_parts_todo latest(latest_fail_reason) as fail_reason by database, table, mutation_id, host
| sort -max_parts_todo
```

## Visualization

Table (mutation_id, command, max_parts_todo, fail_reason), Line chart (parts_to_do trend).

## References

- [ClickHouse — Mutations](https://clickhouse.com/docs/en/sql-reference/statements/alter/update)
- [ClickHouse — system.mutations](https://clickhouse.com/docs/en/operations/system-tables/mutations)
