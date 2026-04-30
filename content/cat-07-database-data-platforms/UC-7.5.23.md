<!-- AUTO-GENERATED from UC-7.5.23.json — DO NOT EDIT -->

---
id: "7.5.23"
title: "ClickHouse Mutation and Lightweight Delete Backlog"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.5.23 · ClickHouse Mutation and Lightweight Delete Backlog

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Change, Performance &middot; **Status:** Draft

*We log unexpected schema and object changes so we can tie database drift to a change ticket or an investigation when something does not look intentional.*

---

## Description

Large parts_to_do counts mean ALTER UPDATE/DELETE mutations are not finishing—common after bulk changes or schema migrations on MergeTree tables.

## Value

Avoids surprise query slowdowns and replication delay when mutations pile up across shards.

## Implementation

Ingest mutations every few minutes; normalize is_done as boolean. Alert when any open mutation exceeds parts_to_do policy. Correlate with disk IO and merges. Cancel or throttle mutations per runbook.

## SPL

```spl
index=database sourcetype="clickhouse:mutations"
| where is_done==0 OR is_done=="false"
| where parts_to_do > 100
| stats max(parts_to_do) as backlog latest(create_time) as started by database, table, mutation_id, host
| sort -backlog
```

## Visualization

Table (table, mutation_id, backlog), Line chart (parts_to_do), Single value (open mutations).

## Known False Positives

Planned failovers, network maintenance, or heavy bulk replication can extend lag for a time without an outage; align the alert with the DR runbook and change window.

## References

- [ClickHouse Mutations guide](https://clickhouse.com/docs/en/sql-reference/statements/kill#kill-mutation)
