---
id: "7.1.19"
title: "Table and Index Bloat and Maintenance Window"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.1.19 · Table and Index Bloat and Maintenance Window

## Description

Table and index bloat (PostgreSQL) or fragmentation (SQL Server) degrades query performance and wastes space. Tracking bloat and last vacuum/rebuild supports maintenance scheduling.

## Value

Table and index bloat (PostgreSQL) or fragmentation (SQL Server) degrades query performance and wastes space. Tracking bloat and last vacuum/rebuild supports maintenance scheduling.

## Implementation

Poll table/index stats and last maintenance timestamps. Compute dead tuple ratio or fragmentation %. Alert when bloat exceeds threshold or last vacuum/rebuild is older than 7 days for critical tables.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `splunk_app_db_connect`, maintenance job logs.
• Ensure the following data sources are available: PostgreSQL `pg_stat_user_tables`/bloat estimates, SQL Server `sys.dm_db_index_physical_stats`, Oracle segment size.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll table/index stats and last maintenance timestamps. Compute dead tuple ratio or fragmentation %. Alert when bloat exceeds threshold or last vacuum/rebuild is older than 7 days for critical tables.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| dbxquery connection="pg_prod" query="SELECT schemaname, relname, n_dead_tup, n_live_tup, last_vacuum, last_autovacuum FROM pg_stat_user_tables WHERE n_dead_tup > 10000"
| eval dead_ratio=round(n_dead_tup/n_live_tup*100, 2)
| where dead_ratio > 5
| table schemaname relname n_dead_tup last_autovacuum dead_ratio
```

Understanding this SPL

**Table and Index Bloat and Maintenance Window** — Table and index bloat (PostgreSQL) or fragmentation (SQL Server) degrades query performance and wastes space. Tracking bloat and last vacuum/rebuild supports maintenance scheduling.

Documented **Data sources**: PostgreSQL `pg_stat_user_tables`/bloat estimates, SQL Server `sys.dm_db_index_physical_stats`, Oracle segment size. **App/TA** (typical add-on context): `splunk_app_db_connect`, maintenance job logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Pipeline stage (see **Table and Index Bloat and Maintenance Window**): dbxquery connection="pg_prod" query="SELECT schemaname, relname, n_dead_tup, n_live_tup, last_vacuum, last_autovacuum FROM pg_stat_user_t…
• `eval` defines or adjusts **dead_ratio** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where dead_ratio > 5` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Table and Index Bloat and Maintenance Window**): table schemaname relname n_dead_tup last_autovacuum dead_ratio


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (table, bloat %, last vacuum), Bar chart (bloat by table), Single value (tables overdue for vacuum).

## SPL

```spl
| dbxquery connection="pg_prod" query="SELECT schemaname, relname, n_dead_tup, n_live_tup, last_vacuum, last_autovacuum FROM pg_stat_user_tables WHERE n_dead_tup > 10000"
| eval dead_ratio=round(n_dead_tup/n_live_tup*100, 2)
| where dead_ratio > 5
| table schemaname relname n_dead_tup last_autovacuum dead_ratio
```

## Visualization

Table (table, bloat %, last vacuum), Bar chart (bloat by table), Single value (tables overdue for vacuum).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
