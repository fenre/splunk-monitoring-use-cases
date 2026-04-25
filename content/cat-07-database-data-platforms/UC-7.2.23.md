<!-- AUTO-GENERATED from UC-7.2.23.json — DO NOT EDIT -->

---
id: "7.2.23"
title: "MongoDB Index Inefficiency (Usage vs Size)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.2.23 · MongoDB Index Inefficiency (Usage vs Size)

## Description

Indexes with near-zero `accesses.ops` and large `size` waste RAM and slow writes. Identifies candidates for drop or partial indexes.

## Value

Indexes with near-zero `accesses.ops` and large `size` waste RAM and slow writes. Identifies candidates for drop or partial indexes.

## Implementation

Weekly job exports `$indexStats`. Flag large indexes with minimal usage. Exclude `_id` and required unique indexes via lookup.

## Detailed Implementation

Prerequisites
• In operations we confirm in mongosh, MongoDB Compass, or the Atlas metrics UI so replication, elections, and cluster operations match what Splunk shows.
• Install and configure the required add-on or app: mongosh `$indexStats`, log export.
• Ensure the following data sources are available: `collStats`, `$indexStats` output.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Weekly job exports `$indexStats`. Flag large indexes with minimal usage. Exclude `_id` and required unique indexes via lookup.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="mongodb:index_stats"
| eval usage=ops_since_start
| where index_size_bytes > 104857600 AND usage < 10
| table ns, name, index_size_bytes, usage
| sort -index_size_bytes
```

Understanding this SPL

**MongoDB Index Inefficiency (Usage vs Size)** — Indexes with near-zero `accesses.ops` and large `size` waste RAM and slow writes. Identifies candidates for drop or partial indexes.

Documented **Data sources**: `collStats`, `$indexStats` output. **App/TA** (typical add-on context): mongosh `$indexStats`, log export. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: mongodb:index_stats. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="mongodb:index_stats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **usage** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where index_size_bytes > 104857600 AND usage < 10` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **MongoDB Index Inefficiency (Usage vs Size)**): table ns, name, index_size_bytes, usage
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (namespace, index, size, ops), Bar chart (wasted index size), Single value (low-usage large indexes count).

## SPL

```spl
index=database sourcetype="mongodb:index_stats"
| eval usage=ops_since_start
| where index_size_bytes > 104857600 AND usage < 10
| table ns, name, index_size_bytes, usage
| sort -index_size_bytes
```

## Visualization

Table (namespace, index, size, ops), Bar chart (wasted index size), Single value (low-usage large indexes count).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
