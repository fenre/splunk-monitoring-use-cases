---
id: "7.1.9"
title: "Index Fragmentation"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.1.9 · Index Fragmentation

## Description

Highly fragmented indexes cause excessive I/O and slow query performance. Monitoring guides maintenance scheduling.

## Value

Highly fragmented indexes cause excessive I/O and slow query performance. Monitoring guides maintenance scheduling.

## Implementation

Poll index fragmentation stats via DB Connect weekly (resource-intensive query — schedule during off-hours). Alert when critical indexes exceed 30% fragmentation. Track fragmentation trend to optimize rebuild schedules.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: DB Connect.
• Ensure the following data sources are available: `sys.dm_db_index_physical_stats` (SQL Server), `pg_stat_user_indexes` (PostgreSQL).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll index fragmentation stats via DB Connect weekly (resource-intensive query — schedule during off-hours). Alert when critical indexes exceed 30% fragmentation. Track fragmentation trend to optimize rebuild schedules.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:index_stats"
| where avg_fragmentation_pct > 30
| table server, database_name, table_name, index_name, avg_fragmentation_pct, page_count
| sort -avg_fragmentation_pct
```

Understanding this SPL

**Index Fragmentation** — Highly fragmented indexes cause excessive I/O and slow query performance. Monitoring guides maintenance scheduling.

Documented **Data sources**: `sys.dm_db_index_physical_stats` (SQL Server), `pg_stat_user_indexes` (PostgreSQL). **App/TA** (typical add-on context): DB Connect. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:index_stats. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:index_stats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where avg_fragmentation_pct > 30` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Index Fragmentation**): table server, database_name, table_name, index_name, avg_fragmentation_pct, page_count
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action | sort - count
```

Understanding this CIM / accelerated SPL

**Index Fragmentation** — Highly fragmented indexes cause excessive I/O and slow query performance. Monitoring guides maintenance scheduling.

Documented **Data sources**: `sys.dm_db_index_physical_stats` (SQL Server), `pg_stat_user_indexes` (PostgreSQL). **App/TA** (typical add-on context): DB Connect. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Databases.Instance_Stats` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (fragmented indexes), Bar chart (fragmentation by database), Heatmap (table × index fragmentation).

## SPL

```spl
index=database sourcetype="dbconnect:index_stats"
| where avg_fragmentation_pct > 30
| table server, database_name, table_name, index_name, avg_fragmentation_pct, page_count
| sort -avg_fragmentation_pct
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action | sort - count
```

## Visualization

Table (fragmented indexes), Bar chart (fragmentation by database), Heatmap (table × index fragmentation).

## References

- [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)
