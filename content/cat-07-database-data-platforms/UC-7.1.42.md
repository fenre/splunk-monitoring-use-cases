<!-- AUTO-GENERATED from UC-7.1.42.json — DO NOT EDIT -->

---
id: "7.1.42"
title: "MySQL and MariaDB Temp Table Disk Spill Rate"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.1.42 · MySQL and MariaDB Temp Table Disk Spill Rate

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Status:** Draft

*We surface slow and blocking queries so we can fix the worst offenders first and keep applications and batch jobs within the response times we promise.*

---

## Description

High Created_tmp_disk_tables indicates sorts and joins spilling from memory to disk, a common cause of sudden query slowdowns on MySQL and MariaDB. Practitioners track this alongside tmp_table_size and max_heap_table_size.

## Value

Detects expensive queries and memory misconfiguration before disk-saturated temp I/O dominates warehouse and OLTP latency.

## Implementation

Poll global status on a fixed interval and emit both counters on the same event for ratio math. Tag instance (host:port). Alert on absolute spikes or when disk temp tables exceed a small fraction of all internal temp tables. Correlate with slow query log and explain plans.

## SPL

```spl
index=database sourcetype="mysql:status"
| eval disk_spill_ratio=if(Created_tmp_tables>0, round(Created_tmp_disk_tables/Created_tmp_tables,4), null())
| where Created_tmp_disk_tables > 100 OR disk_spill_ratio > 0.05
| timechart span=1h sum(Created_tmp_disk_tables) as tmp_disk_tables, sum(Created_tmp_tables) as tmp_tables by instance
```

## Visualization

Line chart (Created_tmp_disk_tables rate), Area chart (spill ratio), Table (top instances).

## Known False Positives

Slow queries during full backup windows, statistics updates, or after index rebuilds; correlate with maintenance and batch schedules before paging.

## References

- [MySQL Server Status Variables](https://dev.mysql.com/doc/refman/8.0/en/server-status-variables.html)
- [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)
