<!-- AUTO-GENERATED from UC-7.5.6.json — DO NOT EDIT -->

---
id: "7.5.6"
title: "Solr Query Cache Hit Ratio"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.5.6 · Solr Query Cache Hit Ratio

## Description

Low filter/query cache hit rates increase CPU and latency; tuning caches and queries improves headroom without adding nodes.

## Value

Low filter/query cache hit rates increase CPU and latency; tuning caches and queries improves headroom without adding nodes.

## Implementation

Poll `GET /solr/admin/metrics` (or per-core metrics) every 5 minutes. Map `QUERY.queryResultCache` and `FILTER.filterCache` hits/misses. Compute hit ratio; alert below team-defined threshold (e.g., 0.7). Correlate with query pattern changes and deployments.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (Solr `metrics` API), Solr log ingestion.
• Ensure the following data sources are available: `sourcetype=solr:metrics`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `GET /solr/admin/metrics` (or per-core metrics) every 5 minutes. Map `QUERY.queryResultCache` and `FILTER.filterCache` hits/misses. Compute hit ratio; alert below team-defined threshold (e.g., 0.7). Correlate with query pattern changes and deployments.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="solr:metrics"
| where like(metric_path,"%queryResultCache%") OR like(metric_path,"%filterCache%")
| eval hit_ratio=lookup_hits / nullif(lookup_hits+lookup_misses,0)
| where hit_ratio < 0.7
| timechart span=15m avg(hit_ratio) as cache_hit_ratio by core, metric_path
```

Understanding this SPL

**Solr Query Cache Hit Ratio** — Low filter/query cache hit rates increase CPU and latency; tuning caches and queries improves headroom without adding nodes.

Documented **Data sources**: `sourcetype=solr:metrics`. **App/TA** (typical add-on context): Custom scripted input (Solr `metrics` API), Solr log ingestion. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: solr:metrics. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="solr:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where like(metric_path,"%queryResultCache%") OR like(metric_path,"%filterCache%")` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **hit_ratio** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where hit_ratio < 0.7` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=15m** buckets with a separate series **by core, metric_path** — ideal for trending and alerting on this use case.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (cache hit ratio per core), Line chart (hit ratio trend), Table (cores below threshold).

## SPL

```spl
index=database sourcetype="solr:metrics"
| where like(metric_path,"%queryResultCache%") OR like(metric_path,"%filterCache%")
| eval hit_ratio=lookup_hits / nullif(lookup_hits+lookup_misses,0)
| where hit_ratio < 0.7
| timechart span=15m avg(hit_ratio) as cache_hit_ratio by core, metric_path
```

## Visualization

Gauge (cache hit ratio per core), Line chart (hit ratio trend), Table (cores below threshold).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
