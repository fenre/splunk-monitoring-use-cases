<!-- AUTO-GENERATED from UC-7.1.40.json — DO NOT EDIT -->

---
id: "7.1.40"
title: "Database Audit Log Tampering Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-7.1.40 · Database Audit Log Tampering Detection

## Description

Detects unexpected audit trail disable, audit file deletion, or Unified Audit policy changes that may indicate cover-up activity.

## Value

Detects unexpected audit trail disable, audit file deletion, or Unified Audit policy changes that may indicate cover-up activity.

## Implementation

Forward database and OS audit to tamper-evident storage. Alert on any audit disable or policy drop outside CAB. Correlate with DBA group membership.

## Detailed Implementation

Prerequisites
• In operations we cross-check the same window in SQL Server Management Studio, Azure Data Studio, or the Azure SQL portal with `sys.dm_*` views; Oracle Enterprise Manager, SQLcl, or SQL Developer with `V$` views so live metrics match what Splunk shows.
• Install and configure the required add-on or app: OS audit, database audit, syslog.
• Ensure the following data sources are available: Oracle `V$OPTION` where parameter='Unified Auditing', `ALTER SYSTEM AUDIT`, `DROP AUDIT POLICY`, SQL Server audit shutdown events.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward database and OS audit to tamper-evident storage. Alert on any audit disable or policy drop outside CAB. Correlate with DBA group membership.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=db_audit sourcetype=oracle_audit OR sourcetype=mssql:audit
| search action IN ("AUDIT DISABLED","AUDIT_POLICY_DROP","AUDIT_TRAIL_OFF") OR statement="*AUDIT*FALSE*"
| table _time, db_user, action, object_name, statement
| sort -_time
```

Understanding this SPL

**Database Audit Log Tampering Detection** — Detects unexpected audit trail disable, audit file deletion, or Unified Audit policy changes that may indicate cover-up activity.

Documented **Data sources**: Oracle `V$OPTION` where parameter='Unified Auditing', `ALTER SYSTEM AUDIT`, `DROP AUDIT POLICY`, SQL Server audit shutdown events. **App/TA** (typical add-on context): OS audit, database audit, syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: db_audit; **sourcetype**: oracle_audit, mssql:audit. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=db_audit, sourcetype=oracle_audit. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **Database Audit Log Tampering Detection**): table _time, db_user, action, object_name, statement
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (audit config changes), Table (privileged actions), Single value (critical audit events 24h).

## SPL

```spl
index=db_audit sourcetype=oracle_audit OR sourcetype=mssql:audit
| search action IN ("AUDIT DISABLED","AUDIT_POLICY_DROP","AUDIT_TRAIL_OFF") OR statement="*AUDIT*FALSE*"
| table _time, db_user, action, object_name, statement
| sort -_time
```

## Visualization

Timeline (audit config changes), Table (privileged actions), Single value (critical audit events 24h).

## References

- [Splunk — DB Connect](https://docs.splunk.com/Documentation/DBX/latest/DeployDBX/WhatisDBX)
