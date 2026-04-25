<!-- AUTO-GENERATED from UC-7.4.7.json — DO NOT EDIT -->

---
id: "7.4.7"
title: "Elasticsearch Index Size and Document Count Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.4.7 · Elasticsearch Index Size and Document Count Trending

## Description

Growth forecasting for indices enables proactive storage provisioning and index lifecycle management (ILM) tuning.

## Value

Growth forecasting for indices enables proactive storage provisioning and index lifecycle management (ILM) tuning.

## Implementation

Poll `GET _cat/indices?v&h=index,docs.count,store.size&bytes=b` or `GET _stats` every 6–24 hours. Parse index name, document count, store size. Track per-index and cluster-wide growth. Use `predict` for 30-day forecast. Alert when projected size exceeds available storage. Support ILM policy tuning based on growth rate.

## Detailed Implementation

Prerequisites
• In operations we confirm in pgAdmin, psql, and `pg_stat*` views, or the managed PostgreSQL console.
• Install and configure the required add-on or app: Custom scripted input (ES REST API).
• Ensure the following data sources are available: `_cat/indices`, `_stats`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `GET _cat/indices?v&h=index,docs.count,store.size&bytes=b` or `GET _stats` every 6–24 hours. Parse index name, document count, store size. Track per-index and cluster-wide growth. Use `predict` for 30-day forecast. Alert when projected size exceeds available storage. Support ILM policy tuning based on growth rate.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="elasticsearch:indices"
| eval size_gb=round(store.size_in_bytes/1073741824, 2)
| timechart span=1d sum(size_gb) as total_gb, sum(docs.count) as doc_count by index
| predict total_gb as predicted_gb future_timespan=30
```

Understanding this SPL

**Elasticsearch Index Size and Document Count Trending** — Growth forecasting for indices enables proactive storage provisioning and index lifecycle management (ILM) tuning.

Documented **Data sources**: `_cat/indices`, `_stats`. **App/TA** (typical add-on context): Custom scripted input (ES REST API). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: elasticsearch:indices. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="elasticsearch:indices". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **size_gb** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by index** — ideal for trending and alerting on this use case.
• Pipeline stage (see **Elasticsearch Index Size and Document Count Trending**): predict total_gb as predicted_gb future_timespan=30


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (index size and doc count with prediction), Table (indices by size and growth rate), Bar chart (top growing indices).

## SPL

```spl
index=database sourcetype="elasticsearch:indices"
| eval size_gb=round(store.size_in_bytes/1073741824, 2)
| timechart span=1d sum(size_gb) as total_gb, sum(docs.count) as doc_count by index
| predict total_gb as predicted_gb future_timespan=30
```

## Visualization

Line chart (index size and doc count with prediction), Table (indices by size and growth rate), Bar chart (top growing indices).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
