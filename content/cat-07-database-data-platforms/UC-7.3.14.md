<!-- AUTO-GENERATED from UC-7.3.14.json — DO NOT EDIT -->

---
id: "7.3.14"
title: "Managed Backup Retention Compliance"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.3.14 · Managed Backup Retention Compliance

## Description

Verifies automated backup snapshots exist within required retention for RDS, Azure SQL LTR, and Cloud SQL backups.

## Value

Verifies automated backup snapshots exist within required retention for RDS, Azure SQL LTR, and Cloud SQL backups.

## Implementation

Ingest daily snapshot inventory from AWS/Azure/GCP APIs. Compare to RPO policy (e.g., last snapshot <25h). Alert on missing snapshot for production tier.

## Detailed Implementation

Prerequisites
• In operations we cross-check backup reality in the right console for each engine: `msdb` and SSMS for SQL Server, RMAN and Enterprise Manager (or DBA views) for Oracle, and the postgres or managed-service view for PostgreSQL, alongside Splunk.
• Install and configure the required add-on or app: Cloud APIs (describe-db-snapshots, backup list).
• Ensure the following data sources are available: Snapshot timestamps, backup policy metadata.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest daily snapshot inventory from AWS/Azure/GCP APIs. Compare to RPO policy (e.g., last snapshot <25h). Alert on missing snapshot for production tier.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="rds:snapshot_inventory"
| stats latest(snapshot_time) as last_snap by db_instance_identifier
| eval days_since=round((now()-strptime(last_snap,"%Y-%m-%d %H:%M:%S"))/86400)
| where days_since > 1
| table db_instance_identifier last_snap days_since
```

Understanding this SPL

**Managed Backup Retention Compliance** — Verifies automated backup snapshots exist within required retention for RDS, Azure SQL LTR, and Cloud SQL backups.

Documented **Data sources**: Snapshot timestamps, backup policy metadata. **App/TA** (typical add-on context): Cloud APIs (describe-db-snapshots, backup list). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: rds:snapshot_inventory. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="rds:snapshot_inventory". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by db_instance_identifier** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **days_since** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_since > 1` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Managed Backup Retention Compliance**): table db_instance_identifier last_snap days_since


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (instances missing recent backup), Single value (non-compliant count), Calendar (snapshot coverage).

## SPL

```spl
index=cloud sourcetype="rds:snapshot_inventory"
| stats latest(snapshot_time) as last_snap by db_instance_identifier
| eval days_since=round((now()-strptime(last_snap,"%Y-%m-%d %H:%M:%S"))/86400)
| where days_since > 1
| table db_instance_identifier last_snap days_since
```

## Visualization

Table (instances missing recent backup), Single value (non-compliant count), Calendar (snapshot coverage).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
