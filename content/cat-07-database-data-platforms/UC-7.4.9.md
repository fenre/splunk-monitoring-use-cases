<!-- AUTO-GENERATED from UC-7.4.9.json — DO NOT EDIT -->

---
id: "7.4.9"
title: "Snowflake Warehouse Credit Usage"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.4.9 · Snowflake Warehouse Credit Usage

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity

*We watch Snowflake Warehouse Credit Usage so we can keep this part of the data platform within the capacity and quality targets our teams expect.*

---

## Description

Credits consumed per warehouse and role drive chargeback and right-sizing. Spikes indicate runaway queries or undersized warehouses thrashing.

## Value

Credits consumed per warehouse and role drive chargeback and right-sizing. Spikes indicate runaway queries or undersized warehouses thrashing.

## Implementation

Daily load from `ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY`. Alert on statistical spikes. Dashboard top warehouses by credits.

## Detailed Implementation

### Prerequisites
- In operations we confirm in pgAdmin, psql, and `pg_stat*` views, or the managed PostgreSQL console.
- Install and configure the required add-on or app: Snowflake SQL via DB Connect, `ACCOUNT_USAGE` export.
- Ensure the following data sources are available: `WAREHOUSE_METERING_HISTORY`, `QUERY_HISTORY` (credits).
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Daily load from `ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY`. Alert on statistical spikes. Dashboard top warehouses by credits.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=datawarehouse sourcetype="snowflake:warehouse_metering"
| bin _time span=1d
| stats sum(credits_used) as credits by warehouse_name, _time
| eventstats avg(credits) as avg_c, stdev(credits) as s by warehouse_name
| where credits > avg_c + 3*s
| table warehouse_name credits avg_c
```

#### Understanding this SPL

**Snowflake Warehouse Credit Usage** — Credits consumed per warehouse and role drive chargeback and right-sizing. Spikes indicate runaway queries or undersized warehouses thrashing.

Documented **Data sources**: `WAREHOUSE_METERING_HISTORY`, `QUERY_HISTORY` (credits). **App/TA** (typical add-on context): Snowflake SQL via DB Connect, `ACCOUNT_USAGE` export. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: datawarehouse; **sourcetype**: snowflake:warehouse_metering. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

- Scopes the data: index=datawarehouse, sourcetype="snowflake:warehouse_metering". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Discretizes time or numeric ranges with `bin`/`bucket`.
- `stats` rolls up events into metrics; results are split **by warehouse_name, _time** so each row reflects one combination of those dimensions.
- `eventstats` rolls up events into metrics; results are split **by warehouse_name** so each row reflects one combination of those dimensions.
- Filters the current rows with `where credits > avg_c + 3*s` — typically the threshold or rule expression for this monitoring goal.
- Pipeline stage (see **Snowflake Warehouse Credit Usage**): table warehouse_name credits avg_c

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


### Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (credits per day by warehouse), Bar chart (top consumers), Single value (total credits MTD).

## SPL

```spl
index=datawarehouse sourcetype="snowflake:warehouse_metering"
| bin _time span=1d
| stats sum(credits_used) as credits by warehouse_name, _time
| eventstats avg(credits) as avg_c, stdev(credits) as s by warehouse_name
| where credits > avg_c + 3*s
| table warehouse_name credits avg_c
```

## Visualization

Line chart (credits per day by warehouse), Bar chart (top consumers), Single value (total credits MTD).

## Known False Positives

Larger ETL or analyst workloads and seasonal reporting can raise warehouse credits or queueing without a fault; tune to business hours and team-specific baselines.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
