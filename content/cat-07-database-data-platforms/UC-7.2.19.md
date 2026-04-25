<!-- AUTO-GENERATED from UC-7.2.19.json — DO NOT EDIT -->

---
id: "7.2.19"
title: "Cassandra Tombstone Accumulation"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.2.19 · Cassandra Tombstone Accumulation

## Description

High tombstone counts per read and GC pressure slow queries and repairs. Monitoring `TombstoneHistogram` and read repair backlog prevents timeouts.

## Value

High tombstone counts per read and GC pressure slow queries and repairs. Monitoring `TombstoneHistogram` and read repair backlog prevents timeouts.

## Implementation

Poll tablestats weekly or daily per large tables. Alert on droppable tombstones above baseline. Correlate with TTL/schema design reviews.

## Detailed Implementation

Prerequisites
• In operations we confirm with nodetool, the CQL layer, and cluster logs so ring and replica state match what Splunk shows.
• Install and configure the required add-on or app: JMX, `nodetool tablestats`.
• Ensure the following data sources are available: `Estimated droppable tombstones`, read path tombstone thresholds.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll tablestats weekly or daily per large tables. Alert on droppable tombstones above baseline. Correlate with TTL/schema design reviews.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="cassandra:tablestats"
| where droppable_tombstones > 100000 OR live_sstable_count > 50
| stats latest(droppable_tombstones) as tombstones by keyspace, table, host
| sort -tombstones
```

Understanding this SPL

**Cassandra Tombstone Accumulation** — High tombstone counts per read and GC pressure slow queries and repairs. Monitoring `TombstoneHistogram` and read repair backlog prevents timeouts.

Documented **Data sources**: `Estimated droppable tombstones`, read path tombstone thresholds. **App/TA** (typical add-on context): JMX, `nodetool tablestats`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: cassandra:tablestats. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="cassandra:tablestats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where droppable_tombstones > 100000 OR live_sstable_count > 50` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by keyspace, table, host** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (KS, table, tombstones), Bar chart (top tables), Line chart (tombstone trend).

## SPL

```spl
index=database sourcetype="cassandra:tablestats"
| where droppable_tombstones > 100000 OR live_sstable_count > 50
| stats latest(droppable_tombstones) as tombstones by keyspace, table, host
| sort -tombstones
```

## Visualization

Table (KS, table, tombstones), Bar chart (top tables), Line chart (tombstone trend).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
