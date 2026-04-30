<!-- AUTO-GENERATED from UC-7.4.12.json — DO NOT EDIT -->

---
id: "7.4.12"
title: "BigQuery Cost Anomalies"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.4.12 · BigQuery Cost Anomalies

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance

*Sudden jumps in bytes billed or slot usage often trace to one bad query or new scheduled job We use it to stay ahead of pain for applications and the people who depend on the data.*

---

## Description

Sudden jumps in bytes billed or slot usage often trace to one bad query or new scheduled job. Statistical alerting limits surprise invoices.

## Value

Sudden jumps in bytes billed or slot usage often trace to one bad query or new scheduled job. Statistical alerting limits surprise invoices.

## Implementation

Ingest completed jobs daily. Alert on project-day cost outliers. Drill into `job_id` for top offenders. Integrate with GCP billing export for ground truth.

## Detailed Implementation

### Prerequisites
- In operations we confirm in pgAdmin, psql, and `pg_stat*` views, or the managed PostgreSQL console.
- Install and configure the required add-on or app: BigQuery `INFORMATION_SCHEMA.JOBS`, billing export to Splunk.
- Ensure the following data sources are available: `total_bytes_billed`, `total_slot_ms`, `creation_time`.
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Ingest completed jobs daily. Alert on project-day cost outliers. Drill into `job_id` for top offenders. Integrate with GCP billing export for ground truth.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=datawarehouse sourcetype="bigquery:jobs"
| bin _time span=1d
| stats sum(total_bytes_billed) as bytes by project_id, user_email, _time
| eventstats avg(bytes) as avg_b, stdev(bytes) as s by project_id
| where bytes > avg_b + 3*s
| eval gb=round(bytes/1073741824,2)
```

#### Understanding this SPL

**BigQuery Cost Anomalies** — Sudden jumps in bytes billed or slot usage often trace to one bad query or new scheduled job. Statistical alerting limits surprise invoices.

Documented **Data sources**: `total_bytes_billed`, `total_slot_ms`, `creation_time`. **App/TA** (typical add-on context): BigQuery `INFORMATION_SCHEMA.JOBS`, billing export to Splunk. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: datawarehouse; **sourcetype**: bigquery:jobs. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

- Scopes the data: index=datawarehouse, sourcetype="bigquery:jobs". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Discretizes time or numeric ranges with `bin`/`bucket`.
- `stats` rolls up events into metrics; results are split **by project_id, user_email, _time** so each row reflects one combination of those dimensions.
- `eventstats` rolls up events into metrics; results are split **by project_id** so each row reflects one combination of those dimensions.
- Filters the current rows with `where bytes > avg_b + 3*s` — typically the threshold or rule expression for this monitoring goal.
- `eval` defines or adjusts **gb** — often to normalize units, derive a ratio, or prepare for thresholds.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


### Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (daily bytes billed), Table (anomalous days/projects), Bar chart (top users by cost).

## SPL

```spl
index=datawarehouse sourcetype="bigquery:jobs"
| bin _time span=1d
| stats sum(total_bytes_billed) as bytes by project_id, user_email, _time
| eventstats avg(bytes) as avg_b, stdev(bytes) as s by project_id
| where bytes > avg_b + 3*s
| eval gb=round(bytes/1073741824,2)
```

## Visualization

Line chart (daily bytes billed), Table (anomalous days/projects), Bar chart (top users by cost).

## Known False Positives

Planned changes, load tests, and vendor maintenance in the data platform can move the same metrics this search uses; we compare to baselines, change records, and on-call context before we treat a hit as a production incident.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
